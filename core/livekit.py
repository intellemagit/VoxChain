import os
from livekit import api
from dotenv import load_dotenv

# Try loading .env.local first, then .env
load_dotenv(dotenv_path=".env.local")
load_dotenv() 

LIVEKIT_URL = os.getenv("LIVEKIT_URL")
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")
SIP_OUTBOUND_TRUNK_ID = os.getenv("SIP_OUTBOUND_TRUNK_ID")

if not LIVEKIT_URL:
    raise ValueError("LIVEKIT_URL is not set in the environment variables.")

lk_api = api.LiveKitAPI(
    url=LIVEKIT_URL,
    api_key=LIVEKIT_API_KEY,
    api_secret=LIVEKIT_API_SECRET,
)

async def close_livekit_api():
    await lk_api.aclose()