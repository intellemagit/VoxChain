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

---

## API Reference

### `create_token`

Generate an authentication token for a participant to join a LiveKit room.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `room_name` | `str` | Yes | Name of the room to join |
| `participant_name` | `str` | Yes | Unique identifier/display name for the participant |

**Returns**: `str` - JWT token for client authentication

```python
token = await lk_manager.create_token(
    room_name="my-room",
    participant_name="user-1"
)
```

---

### `start_outbound_call`

Initiate an outbound SIP/PSTN call to a phone number. Creates a room, dispatches an agent, and connects the phone participant.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `phone_number` | `str` | Yes | Phone number to call (E.164 format, e.g., `+15551234567`) |
| `prompt_content` | `str` | Yes | Content/context for the AI agent |
| `room_name` | `str` | No | Custom room name (auto-generated if not provided) |
| `timeout` | `int` | No | Room empty timeout in seconds (default: 600) |

**Returns**: `Room` - LiveKit Room object with `name` and `sid` properties

**Raises**: `ValueError` if SIP trunk is not configured or user is busy (SIP 486)

```python
room = await lk_manager.start_outbound_call(
    phone_number="+15550101234",
    prompt_content="Hello, this is a test call.",
    room_name="call-room-01"  # Optional
)
print(f"Room SID: {room.sid}")
```

---

### `delete_room`

Delete a LiveKit room and disconnect all participants.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `room_name` | `str` | Yes | Name of the room to delete |

**Returns**: `None`

```python
await lk_manager.delete_room(room_name="call-room-01")
```

---

### `start_stream`

Stream a room's audio/video to one or more RTMP destinations (YouTube, Twitch, etc.).

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `room_name` | `str` | Yes | Name of the room to stream |
| `rtmp_urls` | `List[str]` | Yes | List of RTMP destination URLs |

**Returns**: `None`

# Use ngrok to test it (Might need to add a card method to acces TCP tunneling)

---

### `start_recording`

Record a room's audio/video to an MP4 file. Supports S3 upload with automatic local download.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `room_name` | `str` | Yes | Name of the room to record |
| `output_filepath` | `str` | No | Custom filename (auto-generated if not provided) |
| `upload_to_s3` | `bool` | No | Upload to S3 (default: `True`). Requires AWS env vars. |
| `wait_for_completion` | `bool` | No | Wait for recording to finish and download locally (default: `True`) |

**Returns**: `None`

**Side Effects**: When `wait_for_completion=True` and `upload_to_s3=True`, downloads the recording to `recordings/` folder.

```python
# Record to S3 and wait for download
await lk_manager.start_recording(
    room_name="call-room-01",
    upload_to_s3=True,
    wait_for_completion=True
)

# Record locally on the Egress server (no download)
await lk_manager.start_recording(
    room_name="call-room-01",
    upload_to_s3=False,
    output_filepath="my_recording.mp4"
)
```

---

### `get_participant_identities`

Get all participants in a room with their published tracks (useful for finding track SIDs for muting).

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `room_name` | `str` | Yes | Name of the room |

**Returns**: `List[dict]` - List of participant info with tracks
```python
[
    {
        "identity": "user-1",
        "name": "John Doe",
        "tracks": [
            {"sid": "TR_abc123", "type": "audio", "muted": False, "source": "MICROPHONE"},
            {"sid": "TR_xyz789", "type": "video", "muted": False, "source": "CAMERA"}
        ]
    }
]
```

```python
participants = await lk_manager.get_participant_identities(room_name="call-room-01")
for p in participants:
    print(f"{p['identity']}: {len(p['tracks'])} tracks")
```

---

### `mute_participant`

Mute or unmute a specific track (audio/video) for a participant.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `room_name` | `str` | Yes | Name of the room |
| `identity` | `str` | Yes | Participant's identity |
| `track_sid` | `str` | Yes | SID of the track to mute (get from `get_participant_identities`) |
| `muted` | `bool` | Yes | `True` to mute, `False` to unmute |

**Returns**: `None`

```python
# First, get the track SID
participants = await lk_manager.get_participant_identities(room_name="call-room-01")
audio_track_sid = participants[0]["tracks"][0]["sid"]

# Mute the audio track
await lk_manager.mute_participant(
    room_name="call-room-01",
    identity="user-1",
    track_sid=audio_track_sid,
    muted=True
)
```

---

### `kick_participant`

Remove a participant from a room.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `room_name` | `str` | Yes | Name of the room |
| `identity` | `str` | Yes | Participant's identity to kick |

**Returns**: `None`

```python
await lk_manager.kick_participant(
    room_name="call-room-01",
    identity="user-1"
)
```

---

### `send_alert`

Send a data packet (alert message) to participants. Only works for LiveKit SDK clients (not SIP/phone participants).

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `room_name` | `str` | Yes | Name of the room |
| `message` | `str` | Yes | Alert message content |
| `participant_identity` | `str` | No | Target participant (all participants if not specified) |

**Returns**: `None`

**Note**: Data packets are received by clients via the `dataReceived` event. SIP/phone participants cannot receive data packets.

```python
# Send to all participants
await lk_manager.send_alert(
    room_name="call-room-01",
    message="Meeting ending in 5 minutes"
)

# Send to specific participant
await lk_manager.send_alert(
    room_name="call-room-01",
    message="Please unmute yourself",
    participant_identity="user-1"
)
```

---

### `close`

Close the LiveKit API connection. Call this when done using the manager.

**Returns**: `None`

```python
await lk_manager.close()
```

