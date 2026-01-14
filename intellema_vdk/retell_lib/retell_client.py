import os
from typing import List, Optional
from dotenv import load_dotenv
from twilio.rest import Client
from retell import Retell
import time
import uuid
import requests
import boto3

# Load environment variables
load_dotenv(dotenv_path=".env.local")
load_dotenv()

class RetellManager:
    def __init__(self):
        self.twilio_account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.twilio_auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.twilio_number = os.getenv("TWILIO_PHONE_NUMBER")
        self.retell_api_key = os.getenv("RETELL_API_KEY")
        self.retell_agent_id = os.getenv("RETELL_AGENT_ID")

        if not all([self.twilio_account_sid, self.twilio_auth_token, self.twilio_number, self.retell_api_key, self.retell_agent_id]):
            raise ValueError("Missing necessary environment variables for RetellManager")

        self.twilio_client = Client(self.twilio_account_sid, self.twilio_auth_token)
        self.retell_client = Retell(api_key=self.retell_api_key)

    def start_outbound_call(self, phone_number: str, prompt_content: str = None, call_id: str = None) -> str:
        """
        Initiates an outbound call using Twilio.
        Registers the call with Retell first, then uses TwiML to connect Twilio to Retell's WebSocket.
        
        Args:
            phone_number: The number to call.
            prompt_content: Content to override the agent's prompt (passed as 'prompt_content' dynamic variable).
            call_id: Custom ID for metadata (optional).
        """
        # 1. Register call with Retell to get the WebSocket URL
        register_response = self.retell_client.call.register_phone_call(
            agent_id=self.retell_agent_id,
            direction="outbound",
            from_number=self.twilio_number,
            to_number=phone_number,
            metadata={"call_id": call_id} if call_id else None,
            retell_llm_dynamic_variables={"prompt_content": prompt_content} if prompt_content else None
        )

        # 2. Construct the audio WebSocket URL using the call_id
        audio_websocket_url = f"wss://api.retellai.com/audio-websocket/{register_response.call_id}"

        # 3. Construct TwiML to connect Twilio to Retell
        # Note: We construct the XML string manually to avoid extra dependencies like twilio.twiml
        twiml = f"""<Response>
            <Connect>
                <Stream url="{audio_websocket_url}" />
            </Connect>
        </Response>"""

        # 3. Create the call with Twilio using the generated TwiML
        call = self.twilio_client.calls.create(
            to=phone_number,
            from_=self.twilio_number,
            twiml=twiml
        )
        return call.sid

    def delete_room(self, room_name: str):
        """
        Ends the call. 'room_name' is interpreted as the Twilio Call SID.
        Ends both the Retell agent and the Twilio call.
        """
        try:
            # Attempt to end Retell call if mapped, but primarily hang up Twilio
            # Note: Retell SDK end_call requires retell call id, not twilio sid.
            # If we don't have the mapping, hanging up Twilio is the most effective way to stop everything.
            try:
                self.retell_client.call.end_call(call_id=room_name)
            except Exception:
                pass # Ignore if Retell call fails (e.g. invalid ID), ensure Twilio hangs up
            
            self.twilio_client.calls(room_name).update(status='completed')
        except Exception as e:
            print(f"Error ending call {room_name}: {e}")

    def start_stream(self, room_name: str, rtmp_urls: List[str]):
        """
        Starts a Twilio Media Stream.
        Note: Twilio streams are WebSocket-based. If rtmp_urls contains a WSS URL, it will work.
        """
        if not rtmp_urls:
            raise ValueError("No stream URLs provided")
            
        self.twilio_client.calls(room_name).streams.create(
            url=rtmp_urls[0]
        )

    def start_recording(self, room_name: str, output_filepath: Optional[str] = None, upload_to_s3: bool = True, wait_for_completion: bool = True):
        """
        Triggers a recording on the active Twilio call.
        
        Args:
            room_name: The Twilio Call SID.
            output_filepath: Optional filename for the recording.
            upload_to_s3: If True, uploads to S3.
            wait_for_completion: If True, waits for recording to finish and then uploads.
        
        Returns:
            The Twilio Recording SID.
        """
        
        # Start Twilio recording
        recording = self.twilio_client.calls(room_name).recordings.create()
        print(f"Recording started: {recording.sid}")
        
        if not wait_for_completion:
            return recording.sid
        
        # Poll for recording completion
        print("Waiting for recording to complete...")
        while True:
            rec_status = self.twilio_client.recordings(recording.sid).fetch()
            if rec_status.status == 'completed':
                print("Recording completed.")
                break
            elif rec_status.status in ['failed', 'absent']:
                raise RuntimeError(f"Recording failed with status: {rec_status.status}")
            time.sleep(5)
        
        if not upload_to_s3:
            return recording.sid
        
        # Download recording from Twilio
        media_url = f"https://api.twilio.com/2010-04-01/Accounts/{self.twilio_account_sid}/Recordings/{recording.sid}.mp3"
        print(f"Downloading recording from: {media_url}")
        
        response = requests.get(media_url, auth=(self.twilio_account_sid, self.twilio_auth_token))
        if response.status_code != 200:
            raise RuntimeError(f"Failed to download recording: {response.status_code} {response.text}")
        
        # Upload to S3
        access_key = os.getenv("AWS_ACCESS_KEY_ID")
        secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        bucket = os.getenv("AWS_S3_BUCKET")
        region = os.getenv("AWS_REGION")
        
        if not access_key or not secret_key or not bucket:
            raise ValueError("AWS credentials (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_S3_BUCKET) are required for S3 upload.")
        
        filename = output_filepath if output_filepath else f"{room_name}-{uuid.uuid4().hex[:6]}.mp3"
        
        s3 = boto3.client(
            's3',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region
        )
        
        print(f"Uploading to S3: s3://{bucket}/{filename}")
        s3.put_object(Bucket=bucket, Key=filename, Body=response.content)
        print(f"Upload complete: s3://{bucket}/{filename}")
        
        # Also save locally
        local_dir = "recordings"
        os.makedirs(local_dir, exist_ok=True)
        local_path = os.path.join(local_dir, filename)
        with open(local_path, 'wb') as f:
            f.write(response.content)
        print(f"Recording saved locally: {local_path}")
        
        return recording.sid

    def mute_participant(self, room_name: str, identity: str, track_sid: str, muted: bool):
        """
        Mutes the participant on the Twilio call.
        This prevents audio from reaching the Retell AI.
        """
        self.twilio_client.calls(room_name).update(muted=muted)

    def kick_participant(self, room_name: str, identity: str):
        """
        Alias for delete_room (hangup).
        """
        self.delete_room(room_name)

    def send_alert(self, room_name: str, message: str, participant_identity: Optional[str] = None):
        """
        Not fully supported in this hybrid model
        """
        raise NotImplementedError("send_alert is not currently supported in RetellManager")
