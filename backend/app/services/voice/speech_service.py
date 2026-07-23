import logging
import re
from app.ai.tts.engine import TTSEngine

logger = logging.getLogger(__name__)

class SpeechService:
    """
    Business logic layer for handling Text-to-Speech requests.
    Validates, cleans text, and delegates to the TTS Engine.
    """
    
    def __init__(self):
        self.engine = TTSEngine()
        
    async def synthesize(self, text: str) -> bytes:
        """
        Takes raw text from the AI response, cleans out markdown syntax,
        and generates a WAV audio payload.
        """
        # Clean markdown syntax (bold, italics, code blocks, etc.)
        # Also remove any un-speakable structural characters.
        clean_text = re.sub(r'[*_~`#>\-[\]()]', ' ', text)
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        
        if not clean_text:
            logger.warning("Synthesis requested for empty/fully-cleaned text.")
            raise ValueError("Text contains no speakable content.")
            
        logger.info(f"Synthesizing speech for {len(clean_text)} characters.")
        
        # We can expose voice configuration if we want, but for now we default to F.R.I.D.A.Y.'s voice
        audio_bytes = await self.engine.generate_audio(clean_text, voice="af_sarah", speed=1.0)
        
        return audio_bytes
