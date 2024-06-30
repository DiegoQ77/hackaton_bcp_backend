from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import httpx
from dotenv import load_dotenv
import os
import random
import google.generativeai as genai
import json


load_dotenv()

# api_key = os.getenv("API_KEY")
# api_secret = os.getenv("API_SECRET")

# print(api_key)

app = FastAPI()
templates = Jinja2Templates(directory="templates")


# Ruta para servir la página HTML
@app.get("/", response_class=HTMLResponse)
async def read_item(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Ruta para buscar y mostrar el GIF
@app.post("/search", response_class=HTMLResponse)
async def search_and_display_gif(request: Request):
    form = await request.form()
    query = form.get("query")
    
    api_key = os.getenv("GIPHY_API_KEY")  # Reemplaza con tu clave de API de Giphy
    limit = 12
    rating = "pg" # g pg pg-13 r
    language = "es" # español
    url = f"https://api.giphy.com/v1/gifs/search?api_key={api_key}&q={query}&limit={limit}&rating={rating}&lang={language}"

    async with httpx.AsyncClient() as client:
        response = await client.get(url)
    
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Error al buscar GIF")

    data = response.json()
    
    if len(data["data"]) == 0:
        gif_url = None
    else:
        gif_url = data["data"][random.randint(0, 9)]["images"]["original"]["url"]
        #gif_url = data["data"][0]["images"]["original"]["url"]
    
    return templates.TemplateResponse("index.html", {"request": request, "gif_url": gif_url})


generation_config = {
    "temperature": 0.35,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "application/json",
}

safety_settings = [
    {
        "category": "HARM_CATEGORY_HARASSMENT",
        "threshold": "BLOCK_LOW_AND_ABOVE"
    },
    {
        "category": "HARM_CATEGORY_HATE_SPEECH",
        "threshold": "BLOCK_LOW_AND_ABOVE"
    },
    {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": "BLOCK_LOW_AND_ABOVE"
    },
    {
        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
        "threshold": "BLOCK_LOW_AND_ABOVE"
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

    # prompt_parts = [
    #     f"""Eres un asesor financiero muy amistoso y amigable, tus repuestas seran lo mas parecidas a las de un humano. Proporciona consejos en tres categorías basadas en el texto de entrada: Ahorro, Inversión, Manejo de Deudas y estado de animo de la conversacion\n
    #     texto: Tengo muchas deudas y no sé cómo manejarlas.\n
    #     **Ahorro:**\n\n"Empieza creando un presupuesto que rastree tus ingresos y gastos. Asigna una parte de tus ingresos a un fondo de ahorro de emergencia para asegurarte de tener una red de seguridad."\n\n
    #     **Inversión:**\n\n"Considera inversiones de bajo riesgo como bonos o fondos mutuos para aumentar tu riqueza gradualmente mientras gestionas el riesgo."\n\n
    #     **Manejo de Deudas:**\n\n"Es crucial desarrollar un plan de pago de deudas. Enfócate en pagar primero las deudas con intereses altos, considera consolidar tus deudas y evita asumir nuevas deudas."\n\n
    #     **Estado:**\n\nSolo usa una palabra para describir la respuesta\n\n
    #     **Respuesta:\n\nResponde al texto normalmente\n\n
    #     texto: {text}""",
    # ]
    prompt_parts = [
        f"""Eres un asesor financiero muy amistoso y amigable, tus repuestas seran lo mas parecidas a las de un humano. Proporciona consejos en tres categorías basadas en el texto de entrada: Ahorro, Inversión, Manejo de Deudas y estado de animo de la conversacion. Puedes usar emojis.\n
        **Respuesta:\n\nResponde al texto normalmente\n\n
        **Estado:**\n\nSolo usa una palabra para describir la respuesta\n\n
        **Opciones:** \n\nLista algunas opciones de respuestas\n\n
        texto: {text}""",
    ]
    # chat_session = model.start_chat(
    #     history=[
    #         "role": "user",
    #     ],
    # )
    response = model.generate_content(prompt_parts)
    print(response.text)

    return json.loads(response.text)