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

```bash
pip install intellema-vdk
```

## Usage

### Unified Wrapper (Factory Pattern)

The recommended way to use the library is via the `VoiceClient` factory:

```python
import asyncio
from intellema_vdk import VoiceClient

async def main():
    # 1. Initialize the client
    client = VoiceClient("livekit") 

    # 2. Use methods directly
    call_id = await client.start_outbound_call(
        phone_number="+15551234567",
        prompt_content="Hello from LiveKit"
    )
    
    # 3. Clean API calls
    await client.mute_participant(call_id, "user-1", "track-1", True)
    await client.close()

if __name__ == "__main__":
    asyncio.run(main())
```

### Convenience Function

For quick one-off calls, you can still use the helper:

```python
from intellema_vdk import start_outbound_call

await start_outbound_call("livekit", phone_number="+1...")
```

### Advanced Usage

You can still access the individual managers if you need more granular control:

```python
from intellema_vdk.livekit_lib.client import LiveKitManager
from intellema_vdk.retell_lib.retell_client import RetellManager
```

## Configuration

Create a `.env` file in the root directory:

```bash
LIVEKIT_URL=wss://your-livekit-domain.com
LIVEKIT_API_KEY=your-key
LIVEKIT_API_SECRET=your-secret
SIP_OUTBOUND_TRUNK_ID=your-trunk-id
TWILIO_ACCOUNT_SID=your-sid
TWILIO_AUTH_TOKEN=your-token
TWILIO_PHONE_NUMBER=your-number
RETELL_API_KEY=your-retell-key
RETELL_AGENT_ID=your-agent-id
```


