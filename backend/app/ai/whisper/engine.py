"""
Whisper inference engine wrapper.
"""
from typing import Dict, Any
import asyncio
from app.ai.whisper.loader import get_whisper_model

class WhisperEngine:
    """
    Wrapper around Faster-Whisper for Speech-to-Text inference.
    """
    def __init__(self):
        # We don't initialize the model here, we fetch the singleton instance
        pass

    async def transcribe(self, audio_path: str) -> Dict[str, Any]:
        """
        Transcribe an audio file using Faster-Whisper.
        
        Args:
            audio_path: Path to the audio file.
            
        Returns:
            A dictionary containing the transcription result, detected language, and segments.
        """
        model = get_whisper_model()
        
        # Run the CPU/GPU bound transcription in a separate thread to avoid blocking the event loop
        loop = asyncio.get_running_loop()
        segments_generator, info = await loop.run_in_executor(
            None,
            lambda: model.transcribe(audio_path, beam_size=5)
        )
        
        # We must iterate over the generator to actually process the audio
        # It's an iterator, so we can convert it to a list
        def collect_segments():
            collected = []
            full_text = ""
            for segment in segments_generator:
                collected.append({
                    "id": segment.id,
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text.strip()
                })
                full_text += segment.text
            return collected, full_text.strip()
            
        segments, transcript = await loop.run_in_executor(None, collect_segments)

        return {
            "transcript": transcript,
            "detected_language": info.language,
            "confidence": info.language_probability,
            "duration": info.duration,
            "segments": segments,
            "metadata": {
                "all_language_probs": info.all_language_probs if hasattr(info, 'all_language_probs') else None
            }
        }
