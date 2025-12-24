import asyncio
import aiohttp

async def test_ollama_llm():
    payload = {
        "model": "llama3.1:8b",
        "prompt": "What does Cognee do if it turns documents into AI memory?",
        "stream": False
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "http://localhost:11434/api/generate",
            json=payload,
            timeout=60.0
        ) as response:
            data = await response.json()
            print("Response:")
            print(data.get("response", "No response"))

if __name__ == "__main__":
    asyncio.run(test_ollama_llm())
