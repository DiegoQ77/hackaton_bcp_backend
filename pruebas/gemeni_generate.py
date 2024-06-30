import google.generativeai as genai
from dotenv import load_dotenv
import os

load_dotenv()
# Configure the GEMINI LLM
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
model = genai.GenerativeModel("gemini-1.5-flash")

#basic generation
def generate_text(prompt):
    response = model.generate_content(prompt)
    return response.text