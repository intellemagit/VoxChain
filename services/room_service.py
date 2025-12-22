import json
import uuid
from livekit import api
from core.livekit import lk_api, SIP_OUTBOUND_TRUNK_ID

async def start_outbound_call(phone_number: str, prompt_content: str, room_name: str = None, timeout: int = 600):
    if not room_name:
        room_name = f"outbound_call_{uuid.uuid4().hex[:12]}"

    metadata = json.dumps({
        "phone_number": phone_number,
        "prompt_content": prompt_content
    })

    # 1. Create room with metadata
    room = await lk_api.room.create_room(
        api.CreateRoomRequest(
            name=room_name,
            empty_timeout=timeout,
            metadata=metadata
        )
    )

    # 2. Dispatch agent
    await lk_api.agent_dispatch.create_dispatch(
        api.CreateAgentDispatchRequest(
            room=room_name,
            agent_name="outbound-caller",
            metadata=metadata
        )
    )

    # 3. Initiate Outbound Call (SIP/PSTN)
    if not SIP_OUTBOUND_TRUNK_ID:
        raise ValueError("SIP_OUTBOUND_TRUNK_ID is not configured in environment.")

    sip_participant_identity = f"phone-{phone_number}"

    await lk_api.sip.create_sip_participant(
        api.CreateSIPParticipantRequest(
            room_name=room_name,
            sip_trunk_id=SIP_OUTBOUND_TRUNK_ID,
            sip_call_to=phone_number,
            participant_identity=sip_participant_identity,
            wait_until_answered=True,
        )
    )

    return room