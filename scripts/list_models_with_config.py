import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import config
import google.generativeai as genai

print(f"API Key found: {'Yes' if config.GEMINI_API_KEY else 'No'}")
genai.configure(api_key=config.GEMINI_API_KEY)

try:
    print("Listing models...")
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"- {m.name}")
except Exception as e:
    print(f"Error: {e}")
