import os
import uuid
from fastapi import HTTPException
from elevenlabs.client import ElevenLabs
import asyncio

from app.config import ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID


class AudioProviderService:
    """
    Service for generating audio using third-party providers like ElevenLabs.
    """
    client = None
    voice_id = ELEVENLABS_VOICE_ID

    @classmethod
    def _initialize_client(cls):
        if cls.client is None:
            if not ELEVENLABS_API_KEY or not cls.voice_id:
                raise HTTPException(
                    status_code=500,
                    detail="ElevenLabs API key or Voice ID is not configured."
                )
            cls.client = ElevenLabs(api_key=ELEVENLABS_API_KEY)

    @staticmethod
    def _blocking_io_call(text: str, voice_id: str):
        """Synchronous function to be run in a thread pool."""
        AudioProviderService._initialize_client()
        
        audio_bytes = AudioProviderService.client.text_to_speech.convert(
            voice_id=voice_id,
            model_id="eleven_multilingual_v2",
            text=text,
        )

        filename = f"{uuid.uuid4()}.mp3"
        save_path = f"static/audio/{filename}"
        os.makedirs(os.path.dirname(save_path), exist_ok=True)

        with open(save_path, "wb") as f:
            for chunk in audio_bytes:
                f.write(chunk)
        
        return {"url": f"/{save_path}"}

    @staticmethod
    async def generate_audio(text: str):
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, AudioProviderService._blocking_io_call, text, AudioProviderService.voice_id)

        return {
            "url": result["url"],
            "duration": 1.5,  # TODO: Haqiqiy davomiylikni aniqlash kerak
            "meta_data": {
                "engine": "elevenlabs",
                "voice_id": AudioProviderService.voice_id
            }
        }
