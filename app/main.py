from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import httpx
from dotenv import load_dotenv
import os
import random
from fastapi.middleware.cors import CORSMiddleware

import google.generativeai as genai
import json


load_dotenv()


app = FastAPI()
templates = Jinja2Templates(directory="templates")
# Configuración de CORS
origins = [
    "http://localhost:5173",  # URL de tu frontend
    "*"
    # Agrega más URLs si es necesario
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
    
    # if len(data["data"]) == 0:
    #     gif_url = None
    # else:
    # gif_url = data["data"][random.randint(0, 9)]["images"]["original"]["url"]
    #     #gif_url = data["data"][0]["images"]["original"]["url"]
    
    # return templates.TemplateResponse("index.html", {"request": request, "gif_url": gif_url})
    return data["data"][random.randint(0, 9)]["images"]["original"]["url"]

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
    contexto: str
    informacion: str

@app.post("/api/v1/gemini_consult")
def gemini_consult(request: AdviceRequest):
    contexto = request.contexto
    informacion = request.informacion
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        raise HTTPException(status_code=500, detail="API Key is not configured.")
    

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name="gemini-1.5-flash",
                                    generation_config=generation_config,
                                    safety_settings=safety_settings)
    
    prompt_parts = [
        
        f"""Eres un asesor financiero muy amistoso y amigable, tus repuestas seran lo mas parecidas a las de un humano. Proporciona consejos en tres categorías basadas en el texto de entrada: Ahorro, Inversión, Manejo de Deudas y estado de animo de la conversacion. Puedes usar emojis\n
        *Respuesta:\n\nResponde al texto normalmente\n\n
        *Consejos:\n\n Listado de algunos consejos para la situacion\n\n
        *Estado:\n\nEscoge entre estas palabras, alegria, enojo, miedo, sarcasmo, tristeza\n\n
        *Opciones:\n\nLista algunas opciones de respuestas para continuar con la conversacion, no uses preguntas\n\n
        contexto:{contexto}\n\n
        informacion:{informacion} y tambien conserva la informacion previa"""
        
    ]

    response = model.generate_content(prompt_parts)

    return json.loads(response.text)
