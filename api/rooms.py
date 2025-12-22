from fastapi import APIRouter, HTTPException
from services import room_service
from schemas.rooms import StartCallRequest

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