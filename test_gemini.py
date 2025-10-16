import google.generativeai as genai
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv('GEMINI_API_KEY')

if not api_key or api_key == 'your-gemini-api-key-here':
    print('ERROR: GEMINI_API_KEY not set in .env file')
    exit(1)

print(f'[OK] API Key found: {api_key[:20]}...')

try:
    genai.configure(api_key=api_key)

    # List available models
    print('[INFO] Listing available models...')
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f'  - {m.name}')

    # Try gemini-pro
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content('Say hello in one word')
    print('[OK] API Key is valid!')
    print(f'[OK] Test response: {response.text}')
except Exception as e:
    print(f'[ERROR] API Key test failed: {e}')
    exit(1)
