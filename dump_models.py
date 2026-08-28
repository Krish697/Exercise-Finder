import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
url = f'https://generativelanguage.googleapis.com/v1beta/models?key={GEMINI_API_KEY}&pageSize=100'
resp = requests.get(url)
data = resp.json()

with open("models_dump.txt", "w") as f:
    for model in data.get('models', []):
        f.write(model.get('name') + "\n")
