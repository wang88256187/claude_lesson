import google.generativeai as genai
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv('GEMINI_API_KEY')
genai.configure(api_key=api_key)

print("Available Gemini models that support generateContent:")
print("=" * 60)
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(f"Model: {m.name}")
        print(f"  Display Name: {m.display_name}")
        print(f"  Description: {m.description[:80]}...")
        print()
