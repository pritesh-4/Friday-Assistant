"""
Pre-download voice models during the build phase.

This script ensures that large models (Whisper, Kokoro) are baked into the
deployment image (e.g. on Render) so that the backend starts up instantly
without downloading gigabytes of data on the first request.
"""

import os
from pathlib import Path

# Add backend dir to pythonpath if needed, but we don't need app modules here.

def download_kokoro(models_dir: Path):
    """Download Kokoro ONNX model and voices file."""
    import httpx
    
    kokoro_dir = models_dir / "kokoro"
    kokoro_dir.mkdir(parents=True, exist_ok=True)
    
    model_url = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files/kokoro-v0_19.onnx"
    voices_url = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files/voices.json"
    
    model_path = kokoro_dir / "kokoro-v0_19.onnx"
    voices_path = kokoro_dir / "voices.json"
    
    with httpx.Client(follow_redirects=True) as client:
        if not model_path.exists():
            print(f"Downloading Kokoro model to {model_path}...")
            with client.stream("GET", model_url) as response:
                response.raise_for_status()
                with open(model_path, "wb") as f:
                    for chunk in response.iter_bytes(chunk_size=8192):
                        f.write(chunk)
            print("Kokoro model downloaded successfully.")
        else:
            print("Kokoro model already exists.")
            
        if not voices_path.exists():
            print(f"Downloading Kokoro voices to {voices_path}...")
            with client.stream("GET", voices_url) as response:
                response.raise_for_status()
                with open(voices_path, "wb") as f:
                    for chunk in response.iter_bytes(chunk_size=8192):
                        f.write(chunk)
            print("Kokoro voices downloaded successfully.")
        else:
            print("Kokoro voices already exist.")


def download_whisper(models_dir: Path):
    """Download Faster-Whisper model via huggingface_hub."""
    try:
        from huggingface_hub import snapshot_download
    except ImportError as e:
        print(f"huggingface_hub not installed: {e}")
        print("Falling back to faster_whisper download_model...")
        try:
            from faster_whisper.utils import download_model
            print("Downloading Whisper small...")
            download_model("small", cache_dir=str(models_dir / "whisper"))
            print("Whisper model downloaded successfully.")
            return
        except ImportError as e2:
            raise RuntimeError(f"Failed to download Whisper model. Neither huggingface_hub nor faster_whisper is available. Error: {e2}")

    whisper_dir = models_dir / "whisper"
    whisper_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Downloading Whisper small to {whisper_dir}...")
    snapshot_download(
        repo_id="Systran/faster-whisper-small",
        cache_dir=str(whisper_dir),
        local_files_only=False
    )
    print("Whisper model downloaded successfully.")


if __name__ == "__main__":
    # Base directory for models
    base_dir = Path(os.environ.get("MODELS_DIR", "./data/models")).resolve()
    print(f"Models directory: {base_dir}")
    
    download_kokoro(base_dir)
    download_whisper(base_dir)
    
    print("All models downloaded successfully.")
