# Open Source LiveKit Wrapper

This project provides a Python wrapper around the LiveKit API, simplifying common tasks such as managing rooms, handling participants, initiating SIP calls, and recording sessions to AWS S3.

## Features

- **Room Management**: Create and delete rooms dynamically.
- **Participant Management**: Generate tokens, kick users, and mute tracks.
- **SIP Outbound Calling**: Initiate calls to phone numbers via SIP trunks.
- **Streaming & Recording**: Stream to RTMP destinations and record room sessions directly to AWS S3.
- **Real-time Alerts**: Send data packets (alerts) to participants.

## Prerequisites

- Python 3.8+
- A running LiveKit Server
- Redis (if using multi-node LiveKit setup)
- An AWS Account (for recordings)
- A SIP Provider (for outbound calls)

## Installation

1.  Clone the repository:
    ```bash
    git clone <repository-url>
    cd open-source-livekit
    ```

2.  Create and activate a virtual environment:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Configuration

Create a `.env` file in the root directory by copying `.env.example`:

```bash
cp .env.example .env
```

### Environment Variables

Configure the following variables in your `.env` file:

| Variable | Description | Required |
| :--- | :--- | :--- |
| `LIVEKIT_URL` | The WebSocket URL of your LiveKit server (e.g., `wss://your-livekit-domain.com`). | Yes |
| `LIVEKIT_API_KEY` | Your LiveKit API Key. | Yes |
| `LIVEKIT_API_SECRET` | Your LiveKit API Secret. | Yes |
| `SIP_OUTBOUND_TRUNK_ID` | The ID of your SIP Trunk for outbound calls. | Yes (for calls) |
| `AWS_ACCESS_KEY_ID` | AWS Access Key ID for S3 access. | Yes (for recording) |
| `AWS_SECRET_ACCESS_KEY` | AWS Secret Access Key. | Yes (for recording) |
| `AWS_S3_BUCKET` | The name of the S3 bucket to store recordings. | Yes (for recording) |
| `AWS_REGION` | AWS Region of the bucket (default: `us-east-1`). | No |

## AWS S3 Configuration for Recordings

To enable call recordings, you need to configure an AWS S3 bucket.

### 1. Create an S3 Bucket
1.  Log in to the [AWS Management Console](https://aws.amazon.com/console/).
2.  Navigate to **S3**.
3.  Click **Create bucket**.
4.  Enter a unique **Bucket name** (e.g., `my-livekit-recordings`).
5.  Select your desired **AWS Region**.
6.  Keep the default settings (Block Public Access enabled is recommended) and click **Create bucket**.

### 2. Create an IAM User
1.  Navigate to **IAM** in the AWS Console.
2.  Click **Users** > **Create user**.
3.  Enter a name (e.g., `livekit-recorder`).
4.  Click **Next**.

### 3. Attach Permissions
1.  Select **Attach policies directly**.
2.  Click **Create policy**.
3.  Select the **JSON** tab and paste the following policy (replace `YOUR_BUCKET_NAME` with your actual bucket name):

    ```json
    {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "s3:PutObject",
                    "s3:GetObject",
                    "s3:GetBucketLocation"
                ],
                "Resource": [
                    "arn:aws:s3:::YOUR_BUCKET_NAME",
                    "arn:aws:s3:::YOUR_BUCKET_NAME/*"
                ]
            }
        ]
    }
    ```
4.  Click **Next**, name the policy (e.g., `LiveKitS3Access`), and click **Create policy**.
5.  Back in the "Create user" tab, search for and select your new `LiveKitS3Access` policy.
6.  Click **Next** and then **Create user**.

### 4. Get Access Keys
1.  Click on the newly created user (`livekit-recorder`).
2.  Go to the **Security credentials** tab.
3.  Scroll to **Access keys** and click **Create access key**.
4.  Select **Application running outside AWS**, then click **Next**.
5.  Click **Create access key**.
6.  Copy the **Access key** and **Secret access key** and add them to your `.env` file.

## Usage

### Initializing the Client

```python
from livekit_lib.client import LiveKitManager

lk_manager = LiveKitManager()
```

### Creating a Token for a User

```python
token = await lk_manager.create_token(
    room_name="my-room",
    participant_name="user-1"
)
print(f"Join Token: {token}")
```

### Starting an Outbound SIP Call

```python
room = await lk_manager.start_outbound_call(
    phone_number="+15550101234",
    prompt_content="Hello, this is a test call.",
    room_name="call-room-01"
)
```

### Recording a Call

```python
# Record to S3 and wait for completion to download locally
await lk_manager.start_recording(
    room_name="call-room-01",
    upload_to_s3=True,
    wait_for_completion=True
)

# Record locally (on the Egress server)
await lk_manager.start_recording(
    room_name="call-room-01",
    upload_to_s3=False,
    output_filepath="local_recording.mp4"
)
```

### Streaming to RTMP

```python
await lk_manager.start_stream(
    room_name="call-room-01",
    rtmp_urls=["rtmp://live.twitch.tv/app/STREAM_KEY"]
)
```

### Managing Participants

```python
# Mute a participant's track
await lk_manager.mute_participant(
    room_name="call-room-01",
    identity="participant-identity",
    track_sid="track-sid",
    muted=True
)

# Kick a participant
await lk_manager.kick_participant(
    room_name="call-room-01",
    identity="participant-identity"
)
```
