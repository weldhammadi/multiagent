import httpx
import asyncio

async def test_text_only():
    print("Testing text-only request...")
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/interpret",
            data={
                "user_id": "test_user_api",
                "text": "Hello world",
                "conversation_id": "conv_test",
                "turn_index": 1
            }
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")

async def test_audio_upload():
    print("\nTesting audio upload request...")
    # Create a dummy audio file
    with open("test_audio.mp3", "wb") as f:
        f.write(b"dummy audio content")

    async with httpx.AsyncClient() as client:
        with open("test_audio.mp3", "rb") as f:
            files = {"audio_file": ("test_audio.mp3", f, "audio/mpeg")}
            data = {
                "user_id": "test_user_audio",
                "conversation_id": "conv_audio",
                "turn_index": 1
            }
            response = await client.post(
                "http://localhost:8000/interpret",
                data=data,
                files=files
            )
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")

async def main():
    try:
        await test_text_only()
        await test_audio_upload()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
