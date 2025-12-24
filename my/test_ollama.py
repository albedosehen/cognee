import aiohttp
import asyncio
import json

async def test_ollama():
    payload = {
        "model": "mxbai-embed-large:latest",
        "prompt": "test"
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "http://localhost:11434/api/embeddings",
            json=payload,
            timeout=60.0
        ) as response:
            data = await response.json()
            print("Response:")
            print(json.dumps(data, indent=2))
            print("\nKeys in response:")
            print(list(data.keys()))

if __name__ == "__main__":
    asyncio.run(test_ollama())
