import os
import logging
from typing import Optional
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class SpeechToText:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")

        if not self.api_key:
            logger.error("OPENAI_API_KEY not found.")
            raise ValueError("OPENAI_API_KEY must be set in your .env file or passed to the constructor.")
        
        self.openai_client = OpenAI(api_key=self.api_key)

    def transcribe_audio(self, file_path: str, model: str = "whisper-1") -> str:
        """
        Transcribes an audio file using OpenAI's whisper model.

        Args:
            file_path: The path to the audio file to transcribe. 
                       Supported formats: mp3, mp4, mpeg, mpga, m4a, wav, and webm.
            model: The name of the whisper model to use (default is "whisper-1").
                   Note: The OpenAI API currently only supports "whisper-1".
        Returns:
            The transcribed text as a string.
        """
        logger.info(f"Starting transcription for file: {file_path}")
        if not os.path.exists(file_path):
            logger.error(f"Audio file not found at: {file_path}")
            raise FileNotFoundError(f"Audio file not found at: {file_path}")

        try:
            with open(file_path, "rb") as audio_file:
                transcript = self.openai_client.audio.transcriptions.create(
                    model=model,
                    file=audio_file
                )
            logger.info(f"Successfully transcribed file: {file_path}")

            return transcript.text
        except Exception as e:
            logger.error(f"Error during transcription for file {file_path}: {e}", exc_info=True)
            raise 

# Example of how to use the STT class:
# if __name__ == '__main__':
#     try:
#         stt_manager = SpeechToText()
#         audio_file_path = 'audio.mp3' 
#         transcribed_text = stt_manager.transcribe_audio(audio_file_path)
#         print(transcribed_text)

#     except Exception as e:
#         # Catches errors like FileNotFoundError or issues with the API key
#         print(f"An error occurred: {e}")