import google.generativeai as genai
import os
import sys

# Hack para importar settings desde la carpeta app
sys.path.append(os.getcwd())
from app.core.config import settings

def list_models():
    genai.configure(api_key=settings.GOOGLE_API_KEY)
    print("--- 🤖 Modelos Disponibles para tu API Key ---")
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f" - {m.name}")
    except Exception as e:
        print(f"❌ Error conectando: {e}")

if __name__ == "__main__":
    list_models()