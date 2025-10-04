import google.generativeai as genai
import os
from dotenv import load_dotenv

# Carga tu clave de API desde el archivo .env
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

print("Buscando modelos que soporten 'generateContent'...")

# Itera sobre los modelos disponibles y muestra solo los compatibles
for model in genai.list_models():
  if 'generateContent' in model.supported_generation_methods:
    print(model.name)