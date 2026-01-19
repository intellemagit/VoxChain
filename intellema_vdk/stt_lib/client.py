import os
import logging
import httpx
from typing import Optional
from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv()
logger = logging.getLogger(__name__)


class STTClient:
    def __init__(self, agent_api_url: Optional[str] = None):
        """
        Initializes the STTClient.

        Args:
            agent_api_url: Optional URL for the agent API.
        Note:
            The following must be set in your .env file:
            - OPENAI_API_KEY
            - AGENT_API_URL (if not passing as an argument)
        """
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY must be set in your .env file.")
        
        self.openai_client = AsyncOpenAI(api_key=self.api_key)
        self.agent_api_url = agent_api_url or os.getenv("AGENT_API_URL")

        if not self.agent_api_url:
            logger.warning("AGENT_API_URL is not set. Posting to agent will be disabled.")

    async def transcribe_audio(self, file_path: str, model: str = "whisper-1") -> str:
        """
        Transcribes an audio file using OpenAI's whisper model.

        Args:
            file_path: The path to the audio file to transcribe. 
                       Supported formats: mp3, mp4, mpeg, mpga, m4a, wav, and webm.
            model: The name of the whisper model to use.
                   Note: The OpenAI API currently only supports "whisper-1".
        Returns:
            The transcribed text as a string.
        """
        logger.info(f"Starting transcription for file: {file_path}")
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Audio file not found at: {file_path}")

        try:
            with open(file_path, "rb") as audio_file:
                transcript = await self.openai_client.audio.transcriptions.create(
                    model=model,
                    file=audio_file
                )
            logger.info(f"Successfully transcribed file: {file_path}")

            return transcript.text
        except Exception as e:
           raise

    async def transcribe_and_post(self, file_path: str):
        """
        Processes an audio file by transcribing it and posting the result to the agent API.

        Args:
            file_path: The path to the audio file to process.
                       Supported formats: mp3, mp4, mpeg, mpga, m4a, wav, and webm.
        Returns:
            The transcribed text as a string.
        """
        try:
            # Transcribe the audio file
            transcript_text = await self.transcribe_audio(file_path)

            # Post the transcribed text to the agent API
            if self.agent_api_url:
                await self.post_to_agent(transcript_text)
            else:
                logger.info("AGENT_API_URL not set, skipping post to agent.")
            
            return transcript_text

        except FileNotFoundError:
            logger.error(f"Audio file not found at: {file_path}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"An error occurred during processing of {file_path}: {e}", exc_info=True)
            raise

    async def post_to_agent(self, text: str):
        """
        Posts the transcribed text to the agent API.
        
        Args:
            text: The transcribed text to post.
        """
        payload = {"text": text}
        try:
            logger.info(f"Posting to agent with payload: {payload}")
            async with httpx.AsyncClient() as client:
                response = await client.post(self.agent_api_url, json=payload)
                response.raise_for_status()
            logger.info(f"Successfully posted to agent. Status: {response.status_code}")
        except httpx.HTTPError as e:
            logger.error(f"Failed to post to agent API: {e}", exc_info=True)
            raise

# Example usage:
# if __name__ == "__main__":
#     stt_client = STTClient("http://your-agent-api-url.com")
#     import asyncio
#     async def main():
#         transcript = await stt_client.transcribe_and_post("audio.mp3")
#         print("Transcription:", transcript)
#     asyncio.run(main())