from fastapi import APIRouter, HTTPException
from services import room_service
from schemas.rooms import StartCallRequest, EnterCallRequest, EndCallRequest

router = APIRouter()

@router.post("/start_call")
async def start_call(payload: StartCallRequest):
    try:
        room = await room_service.start_outbound_call(
            phone_number=payload.phone_number,
            prompt_content=payload.prompt_content,
            room_name=payload.room_name,
            timeout=payload.timeout
        )
        return {
            "success": True, 
            "room_sid": room.sid, 
            "name": room.name,
            "message": "Call dispatched and initiated successfully. Agent is waiting for pickup."
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/enter_call")
async def enter_call(payload: EnterCallRequest):
    """
    Generates a token for a participant to join an existing call (room).
    
    This does not initiate a phone call to the participant. Instead, it returns
    an access token that a client (web or mobile app) can use to connect to the
    LiveKit room via VoIP.
    """
    try:
        token = await room_service.create_token(payload.room_name, payload.participant_name)
        return {"token": token}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/end_call")
async def end_call(payload: EndCallRequest):
    """
    Ends a call by deleting the room.
    
    This disconnects all participants (SIP and VoIP) immediately.
    """
    try:
        await room_service.delete_room(payload.room_name)
        return {"message": f"Room {payload.room_name} deleted and call ended."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))