"""
Pre-download STT models during the build phase.

This script ensures that large STT models (Whisper) are baked into the
deployment image (e.g. on Render) so that the backend starts up instantly
without downloading data on the first request.
"""

import os
from pathlib import Path


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
            raise RuntimeError(
                f"Failed to download Whisper model. Neither huggingface_hub nor faster_whisper is available. Error: {e2}"
            )

    whisper_dir = models_dir / "whisper"
    whisper_dir.mkdir(parents=True, exist_ok=True)

    print(f"Downloading Whisper small to {whisper_dir}...")
    snapshot_download(
        repo_id="Systran/faster-whisper-small",
        cache_dir=str(whisper_dir),
        local_files_only=False,
    )
    print("Whisper model downloaded successfully.")


if __name__ == "__main__":
    base_dir = Path(os.environ.get("MODELS_DIR", "./data/models")).resolve()
    print(f"Models directory: {base_dir}")

    download_whisper(base_dir)

    print("All models downloaded successfully.")
