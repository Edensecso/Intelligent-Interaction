from google import genai
from dotenv import load_dotenv
import os

load_dotenv()

try:
    # Conectamos con Google
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    
    print("--- Modelos Disponibles ---")
    # Simplemente listamos todo lo que haya
    for model in client.models.list():
        print(f"ID: {model.name}")
        
except Exception as e:
    print(f"Error: {e}")