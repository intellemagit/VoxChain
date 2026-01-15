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

    def import_phone_number(self, termination_uri: str = None, outbound_agent_id: str = None, inbound_agent_id: str = None, nickname: str = None, sip_trunk_auth_username: str = None, sip_trunk_auth_password: str = None):
        """
        Import/register your Twilio phone number with Retell.
        This is required before you can make outbound calls using the phone number.
        
        Args:
            termination_uri: Twilio SIP trunk termination URI (e.g., "yourtrunk.pstn.twilio.com").
                           If not provided, will try to use a default format.
            outbound_agent_id: Agent ID to use for outbound calls. Defaults to self.retell_agent_id.
            inbound_agent_id: Agent ID to use for inbound calls. Defaults to None (no inbound).
            nickname: Optional nickname for the phone number.
            sip_trunk_auth_username: Username for SIP trunk authentication (if using credential list).
            sip_trunk_auth_password: Password for SIP trunk authentication (if using credential list).
        
        Returns:
            The phone number registration response from Retell.
        """
        # Build the import kwargs
        import_kwargs = {
            "phone_number": self.twilio_number,
        }
        
        # Add termination URI if provided
        if termination_uri:
            import_kwargs["termination_uri"] = termination_uri
        
        # Add SIP credentials if provided
        if sip_trunk_auth_username and sip_trunk_auth_password:
            import_kwargs["sip_trunk_auth_username"] = sip_trunk_auth_username
            import_kwargs["sip_trunk_auth_password"] = sip_trunk_auth_password
        
        # Set outbound agent (required for outbound calls)
        if outbound_agent_id:
            import_kwargs["outbound_agent_id"] = outbound_agent_id
        elif self.retell_agent_id:
            import_kwargs["outbound_agent_id"] = self.retell_agent_id
        
        # Set inbound agent if provided
        if inbound_agent_id:
            import_kwargs["inbound_agent_id"] = inbound_agent_id
        
        # Add nickname if provided
        if nickname:
            import_kwargs["nickname"] = nickname
        
        try:
            response = self.retell_client.phone_number.import_(**import_kwargs)
            print(f"✓ Phone number {self.twilio_number} successfully imported to Retell!")
            print(f"  Phone Number: {response.phone_number}")
            print(f"  Type: {response.phone_number_type}")
            if hasattr(response, 'outbound_agent_id') and response.outbound_agent_id:
                print(f"  Outbound Agent: {response.outbound_agent_id}")
            if hasattr(response, 'inbound_agent_id') and response.inbound_agent_id:
                print(f"  Inbound Agent: {response.inbound_agent_id}")
            return response
        except Exception as e:
            print(f"✗ Error importing phone number: {e}")
            print(f"\nNote: If you're using Twilio, you may need to:")
            print(f"  1. Create an Elastic SIP Trunk in Twilio console")
            print(f"  2. Provide the termination_uri parameter (e.g., 'yourtrunk.pstn.twilio.com')")
            print(f"  3. Or purchase the number directly through Retell dashboard")
            raise


    def start_outbound_call(self, phone_number: str, prompt_content: str = None, call_id: str = None) -> str:
        call_kwargs = {
            "from_number": self.twilio_number,
            "to_number": phone_number,
            "override_agent_id": self.retell_agent_id,
        }
    
        if call_id:
            call_kwargs["metadata"] = {"call_id": call_id}
    
    # Only set up dynamic variables if we have a custom prompt
        if prompt_content:
            enhanced_prompt = (
                f"{prompt_content}\n\n"
                "SYSTEM INSTRUCTION: Continually check the dynamic variable {{force_end}}. "
                "If {{force_end}} == 'true, you must IMMEDIATELY say goodbye and activate your end_call tool to terminate the call."
            )
            call_kwargs["retell_llm_dynamic_variables"] = {
                "prompt_content": enhanced_prompt,
                "force_end": "false"
            }
    
        call_response = self.retell_client.call.create_phone_call(**call_kwargs)
    
        print(f"Call created successfully!")
        print(f"Retell Call ID: {call_response.call_id}")
        print(f"Call Status: {call_response.call_status}")
    
        return call_response.call_id

    def delete_room(self, call_id: str):
        try:
            call_data = self.retell_client.call.retrieve(call_id)
            print(f"Current call status: {call_data.call_status}")

            if call_data.call_status in ['registered', 'ongoing', 'dialing']:
                print(f"Triggering end for Retell call {call_id}...")

                self.retell_client.call.update(
                    call_id,
                    override_dynamic_variables={"force_end": "true"}
                )

                print("✓ force_end override sent to Retell API")
            else:
                print(f"Call already ended: {call_data.call_status}")

        except Exception as e:
            print(f"Error ending call {call_id}: {e}")
            raise

    def start_stream(self, call_id: str, rtmp_urls: List[str]):
        """
        Starts a Twilio Media Stream.
        Note: Twilio streams are WebSocket-based. If rtmp_urls contains a WSS URL, it will work.
        """
        if not rtmp_urls:
            raise ValueError("No stream URLs provided")
            
        self.twilio_client.calls(call_id).streams.create(
            url=rtmp_urls[0]
        )

    def start_recording(self, call_id: str, output_filepath: Optional[str] = None, upload_to_s3: bool = True, wait_for_completion: bool = True):
        """
        Triggers a recording on the active Twilio call.
        
        Args:
            call_id: The Twilio Call SID.
            output_filepath: Optional filename for the recording.
            upload_to_s3: If True, uploads to S3.
            wait_for_completion: If True, waits for recording to finish and then uploads.
        
        Returns:
            The Twilio Recording SID.
        """
        
        # Start Twilio recording
        recording = self.twilio_client.calls(call_id).recordings.create()
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
        
        filename = output_filepath if output_filepath else f"{call_id}-{uuid.uuid4().hex[:6]}.mp3"
        
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

    def mute_participant(self, call_id: str, identity: str, track_sid: str, muted: bool):
        """
        Mutes the participant on the Twilio call.
        This prevents audio from reaching the Retell AI.
        """
        self.twilio_client.calls(call_id).update(muted=muted)

    def kick_participant(self, call_id: str, identity: str):
        """
        Alias for delete_room (hangup).
        """
        self.delete_room(call_id)

    def send_alert(self, call_id: str, message: str, participant_identity: Optional[str] = None):
        """
        Not fully supported in this hybrid model
        """
        raise NotImplementedError("send_alert is not currently supported in RetellManager")
