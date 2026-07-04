
class VoiceService:
    """
    Service responsible for handling speech-to-text (STT) and text-to-speech (TTS) services.
    Currently implemented as a stub placeholder.
    """
    
    async def transcribe_audio(self, audio_data: bytes) -> str:
        """
        Transcribe audio binary content to text.
        """
        return ""

    async def synthesize_speech(self, text: str) -> bytes:
        """
        Synthesize speech audio content from text.
        """
        return b""
