from contextlib import asynccontextmanager
from fastapi import FastAPI
from core.livekit import close_livekit_api
from api import rooms  

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await close_livekit_api()

app = FastAPI(lifespan=lifespan)

# Include the router
app.include_router(rooms.router, prefix="/api")

