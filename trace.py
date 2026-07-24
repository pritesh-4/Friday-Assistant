import asyncio
import httpx

async def main():
    async with httpx.AsyncClient(timeout=300.0) as client:
        print("1. Uploading voice...")
        import wave, struct
        with wave.open("backend/tests/test_audio.wav", "wb") as f:
            f.setnchannels(1)
            f.setsampwidth(2)
            f.setframerate(16000)
            for _ in range(16000):
                f.writeframesraw(struct.pack('<h', 0))
            
        with open("backend/tests/test_audio.wav", "rb") as f:
            res = await client.post("http://localhost:8000/voice/transcribe", files={"file": ("test.wav", f, "audio/wav")})
            
        print(f"STT Response: {res.status_code}")
        if res.status_code != 200:
            print(res.text)
            return
            
        transcript = res.json().get("transcript", "")
        print(f"Transcript: {transcript}")
        
        print("2. Sending to Chat...")
        res = await client.post("http://localhost:8000/chat", json={"message": transcript})
        print(f"Chat Response: {res.status_code}")
        if res.status_code != 200:
            print(res.text)
            return
            
        ai_text = res.json().get("assistant_message", {}).get("content", "")
        print(f"AI Text: {ai_text}")
        
        print("3. Generating TTS...")
        res = await client.post("http://localhost:8000/voice/speak", json={"text": ai_text})
        print(f"TTS Response: {res.status_code}")

if __name__ == "__main__":
    asyncio.run(main())
