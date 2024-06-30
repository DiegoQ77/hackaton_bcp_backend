from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import google.generativeai as genai
from dotenv import load_dotenv
import os
import json

load_dotenv()

app = FastAPI()

generation_config = {
    "temperature": 0.9,
    "top_p": 1,
    "top_k": 1,
    "max_output_tokens": 2048,
    "response_mime_type": "application/json",
}

safety_settings = [
    {
        "category": "HARM_CATEGORY_HARASSMENT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    },
    {
        "category": "HARM_CATEGORY_HATE_SPEECH",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    },
    {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    },
    {
        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    },
]

class AdviceRequest(BaseModel):
    text: str

@app.post("/api/v1/gemini_consult")
def gemini_consult(request: AdviceRequest):
    text = request.text
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        raise HTTPException(status_code=500, detail="API Key is not configured.")
    

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name="gemini-1.5-flash",
                                    generation_config=generation_config,
                                    safety_settings=safety_settings)

    prompt_parts = [
        f"""Eres un asesor financiero. Proporciona consejos en tres categorías basadas en el texto de entrada: Ahorro, Inversión, Manejo de Deudas y estado de animo de la conversacion\n
        texto: Tengo muchas deudas y no sé cómo manejarlas.\n
        **Ahorro:**\n\n"Empieza creando un presupuesto que rastree tus ingresos y gastos. Asigna una parte de tus ingresos a un fondo de ahorro de emergencia para asegurarte de tener una red de seguridad."\n\n
        **Inversión:**\n\n"Considera inversiones de bajo riesgo como bonos o fondos mutuos para aumentar tu riqueza gradualmente mientras gestionas el riesgo."\n\n
        **Manejo de Deudas:**\n\n"Es crucial desarrollar un plan de pago de deudas. Enfócate en pagar primero las deudas con intereses altos, considera consolidar tus deudas y evita asumir nuevas deudas."\n\n
        **Estado:**\n\nFeliz|Triste|\n\n
        texto: {text}""",
    ]

    response = model.generate_content(prompt_parts)
    print(response.text)
    return json.loads(response.text)
