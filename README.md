# Intellema VDK

Intellema VDK is a unified Voice Development Kit designed to simplify the integration and management of various voice agent platforms. It provides a consistent, factory-based API to interact with providers like LiveKit and Retell AI, enabling developers to build scalable voice applications with ease. Whether you need real-time streaming, outbound calling, or participant management, Intellema VDK abstracts the complexity into a single, intuitive interface.

## Features

- **Room Management**: Create and delete rooms dynamically.
- **Participant Management**: Generate tokens, kick users, and mute tracks.
- **SIP Outbound Calling**: Initiate calls to phone numbers via SIP trunks.
- **Streaming & Recording**: Stream to RTMP destinations and record room sessions directly to AWS S3.
- **Real-time Alerts**: Send data packets (alerts) to participants.

## Prerequisites

- Python 3.8+
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
OPENAI_API_KEY=your-openai-key
```


