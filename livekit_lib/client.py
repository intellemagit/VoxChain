import os
import json
import uuid
import asyncio
import time
import boto3
from typing import List, Optional
from dotenv import load_dotenv
from livekit import api

# Load environment variables
load_dotenv(dotenv_path=".env.local")
load_dotenv()

class LiveKitManager:
    def __init__(self):
        self.url = os.getenv("LIVEKIT_URL")
        self.api_key = os.getenv("LIVEKIT_API_KEY")
        self.api_secret = os.getenv("LIVEKIT_API_SECRET")
        self.sip_trunk_id = os.getenv("SIP_OUTBOUND_TRUNK_ID")

        if not self.url or not self.api_key or not self.api_secret:
            raise ValueError("LIVEKIT_URL, LIVEKIT_API_KEY, and LIVEKIT_API_SECRET must be set.")

        self.lk_api = api.LiveKitAPI(
            url=self.url,
            api_key=self.api_key,
            api_secret=self.api_secret,
        )

    async def close(self):
        await self.lk_api.aclose()

    async def start_outbound_call(self, phone_number: str, prompt_content: str, room_name: str = None, timeout: int = 600):
        if not room_name:
            room_name = f"outbound_call_{uuid.uuid4().hex[:12]}"

        metadata = json.dumps({
            "phone_number": phone_number,
            "prompt_content": prompt_content
        })

        # 1. Create room with metadata
        room = await self.lk_api.room.create_room(
            api.CreateRoomRequest(
                name=room_name,
                empty_timeout=timeout,
                metadata=metadata
            )
        )

        # 2. Dispatch agent
        await self.lk_api.agent_dispatch.create_dispatch(
            api.CreateAgentDispatchRequest(
                room=room_name,
                agent_name="outbound-caller",
                metadata=metadata
            )
        )

        # 3. Initiate Outbound Call (SIP/PSTN)
        if not self.sip_trunk_id:
            raise ValueError("SIP_OUTBOUND_TRUNK_ID is not configured in environment.")

        sip_participant_identity = f"phone-{phone_number}"

        try:
            await self.lk_api.sip.create_sip_participant(
                api.CreateSIPParticipantRequest(
                    room_name=room_name,
                    sip_trunk_id=self.sip_trunk_id,
                    sip_call_to=phone_number,
                    participant_identity=sip_participant_identity,
                    wait_until_answered=True,
                )
            )
        except Exception as e:
            # Handle SIP Busy/Error 
            if "Busy Here" in str(e) or "486" in str(e):
                print(f"Call failed: User is busy ({phone_number})")
                # We might want to clean up the room if the call failed
                await self.delete_room(room_name)
                raise ValueError("User is busy")
            raise e

        return room

    async def create_token(self, room_name: str, participant_name: str) -> str:
        token = api.AccessToken(self.api_key, self.api_secret)
        token.with_identity(participant_name)
        token.with_name(participant_name)
        token.with_grants(api.VideoGrants(
            room_join=True,
            room=room_name,
        ))
        return token.to_jwt()

    async def delete_room(self, room_name: str):
        await self.lk_api.room.delete_room(api.DeleteRoomRequest(room=room_name))

    async def start_stream(self, room_name: str, rtmp_urls: List[str]):
        await self.lk_api.egress.start_room_composite_egress(
            api.RoomCompositeEgressRequest(
                room_name=room_name,
                layout="speaker",
                stream_outputs=[
                    api.StreamOutput(
                        protocol=api.StreamProtocol.RTMP,
                        urls=rtmp_urls
                    )
                ]
            )
        )

    async def start_recording(self, room_name: str, output_filepath: Optional[str] = None, upload_to_s3: bool = True, wait_for_completion: bool = True):
        """
        Start recording a room.
        
        Args:
            room_name: Name of the room to record.
            output_filepath: Optional path/filename for the recording.
            upload_to_s3: If True, uploads to S3 (requires env vars). If False, saves locally on Egress server.
            wait_for_completion: If True, waits for the recording to finish and downloads it locally (if upload_to_s3 is True).
        """
        file_output = None
        filename = output_filepath if output_filepath else f"{room_name}-{uuid.uuid4().hex[:6]}.mp4"

        if upload_to_s3:
            access_key = os.getenv("AWS_ACCESS_KEY_ID")
            secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
            bucket = os.getenv("AWS_S3_BUCKET")
            region = os.getenv("AWS_REGION")
            
            if not access_key or not secret_key or not bucket:
                raise ValueError("AWS credentials (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_S3_BUCKET) are required for S3 upload.")
            
            file_output = api.EncodedFileOutput(
                file_type=api.EncodedFileType.MP4,
                filepath=filename,
                s3=api.S3Upload(
                    access_key=access_key,
                    secret=secret_key,
                    bucket=bucket,
                    region=region,
                ),
            )
            print(f"Starting recording. File will be saved to S3: s3://{bucket}/{filename}")
        else:
            file_output = api.EncodedFileOutput(
                file_type=api.EncodedFileType.MP4,
                filepath=filename,
            )
            print(f"Starting recording. File will be saved locally: {filename}")
        
        egress_info = await self.lk_api.egress.start_room_composite_egress(
            api.RoomCompositeEgressRequest(
                room_name=room_name,
                layout="grid",
                preset=api.EncodingOptionsPreset.H264_720P_30,
                file_outputs=[file_output]
            )
        )

        if wait_for_completion and upload_to_s3:
            egress_id = egress_info.egress_id
            print(f"Waiting for egress {egress_id} to complete...")
            
            while True:
                try:
                    egress_list = await self.lk_api.egress.list_egress(api.ListEgressRequest(egress_id=egress_id))
                except Exception as e:
                    print(f"Error checking egress status: {e}")
                    await asyncio.sleep(5)
                    continue

                if not egress_list.items:
                    print("Egress info not found during polling.")
                    break
                
                info = egress_list.items[0]
                if info.status == api.EgressStatus.EGRESS_COMPLETE:
                    print("Egress completed successfully.")
                    break
                elif info.status == api.EgressStatus.EGRESS_FAILED:
                    raise RuntimeError(f"Egress failed: {info.error}")
                elif info.status == api.EgressStatus.EGRESS_LIMIT_REACHED:
                     raise RuntimeError(f"Egress limit reached: {info.error}")
                
                await asyncio.sleep(5)

            # Download from S3
            print(f"Downloading {filename} from S3 bucket {bucket}...")
            s3 = boto3.client(
                's3',
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                region_name=region
            )
            
            local_dir = "recordings"
            os.makedirs(local_dir, exist_ok=True)
            local_path = os.path.join(local_dir, filename)
            
            try:
                s3.download_file(bucket, filename, local_path)
                print(f"Recording downloaded to: {local_path}")
            except Exception as e:
                print(f"Failed to download recording: {e}")
                raise e

    
