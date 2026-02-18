import google.generativeai as genai
from config.settings import config
import asyncio

genai.configure(api_key=config.GEMINI_API_KEY)

async def list_models():
    print("Listing embedding models...")
    for m in genai.list_models():
        if 'embedContent' in m.supported_generation_methods:
            print(f"Name: {m.name}")
            print(f"Description: {m.description}")
            print(f"Output Token Limit: {m.output_token_limit}")
            print("-" * 20)

if __name__ == "__main__":
    asyncio.run(list_models())
