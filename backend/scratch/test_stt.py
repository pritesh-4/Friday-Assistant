import asyncio
from app.ai.whisper.engine import WhisperEngine
from app.ai.whisper.loader import initialize_whisper_model
import os

async def main():
    print("Initializing model...")
    success = initialize_whisper_model(model_name="small", device="cpu", compute_type="int8")
    print(f"Init success: {success}")
    
    engine = WhisperEngine()
    print("Running transcription...")
    
    # create a dummy audio file using python wave module to have something to transcribe if ffmpeg isn't there,
    # or just use a small test audio. Let's create a 1 second silent wav file.
    import wave
    import struct
    with wave.open("test.wav", "w") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(16000)
        for _ in range(16000):
            f.writeframesraw(struct.pack('<h', 0))
            
    try:
        result = await engine.transcribe("test.wav")
        print("Result:", result)
    except Exception as e:
        print("Exception:", e)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
