import logging
import urllib.request
from pathlib import Path
from kokoro_onnx import Kokoro

logger = logging.getLogger(__name__)

_tts_engine: Kokoro | None = None

def download_file(url: str, dest: Path):
    if not dest.exists():
        logger.info(f"Downloading {url} to {dest}...")
        urllib.request.urlretrieve(url, dest)
        logger.info(f"Successfully downloaded {dest.name}.")

def initialize_tts_model():
    """
    Initializes the Kokoro TTS engine as a singleton.
    Downloads the required ONNX model and voices config if missing.
    """
    global _tts_engine
    if _tts_engine is not None:
        return

    try:
        models_dir = Path(__file__).parent / "models"
        models_dir.mkdir(exist_ok=True, parents=True)

        model_path = models_dir / "kokoro-v0_19.onnx"
        voices_path = models_dir / "voices.json"

        # Download from kokoro-onnx GitHub releases if missing
        download_file("https://github.com/thewh1teagle/kokoro-onnx/releases/download/model/kokoro-v0_19.onnx", model_path)
        download_file("https://github.com/thewh1teagle/kokoro-onnx/releases/download/model/voices.json", voices_path)

        _tts_engine = Kokoro(str(model_path), str(voices_path))
        logger.info("Kokoro TTS engine initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to load Kokoro TTS engine: {e}")

def get_tts_engine() -> Kokoro | None:
    return _tts_engine
