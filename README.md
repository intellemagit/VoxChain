# Open Source LiveKit Project

This project implements a LiveKit server wrapper with SIP outbound calling capabilities.

## Setup

1.  **Create Virtual Environment**:
    ```bash
    python -m venv venv
    .\venv\Scripts\activate
    ```

2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Environment Configuration**:
    - Copy `.env.example` to `.env`.
    - Fill in your LiveKit credentials and SIP Trunk ID.
    ```env
    LIVEKIT_URL=wss://your-project.livekit.cloud
    LIVEKIT_API_KEY=your_api_key
    LIVEKIT_API_SECRET=your_api_secret
    SIP_OUTBOUND_TRUNK_ID=your_sip_trunk_id
    ```

## Running the Server

Start the FastAPI server with hot-reload enabled:
```bash
uvicorn main:app --reload
```

## API Usage

### Start Outbound Call
**Endpoint**: `POST /api/start_call`

**Body**:
```json
{
  "phone_number": "+1234567890",
  "prompt_content": "Hello, this is a test call.",
  "room_name": "optional-room-name"
}
```

**Example**:
```bash
curl -X POST "http://127.0.0.1:8000/api/start_call" \
     -H "Content-Type: application/json" \
     -d "{\"phone_number\": \"+1234567890\", \"prompt_content\": \"Hello from LiveKit!\"}"
```

### Enter Call (Join Room)
**Endpoint**: `POST /api/enter_call`

Generates an access token for a participant to join an existing room via a client application (Web/Mobile). This does NOT initiate a phone call.

**Body**:
```json
{
  "room_name": "existing-room-name",
  "participant_name": "user-identity"
}
```

**Example**:
```bash
curl -X POST "http://127.0.0.1:8000/api/enter_call" \
     -H "Content-Type: application/json" \
     -d "{\"room_name\": \"outbound_call_123\", \"participant_name\": \"agent-007\"}"
```

### End Call
**Endpoint**: `POST /api/end_call`

Terminates the room and disconnects all participants.

**Body**:
```json
{
  "room_name": "room-to-delete"
}
```

**Example**:
```bash
curl -X POST "http://127.0.0.1:8000/api/end_call" \
     -H "Content-Type: application/json" \
     -d "{\"room_name\": \"outbound_call_123\"}"
```