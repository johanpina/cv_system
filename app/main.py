from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.api import api_router
from app.core.database import init_db

# Inicializar la app
app = FastAPI(title=settings.PROJECT_NAME)

# --- 2. CONFIGURACIÓN DE CORS ---
# Permitir cualquier origen ("*") es ideal para desarrollo rápido.
# En producción, aquí pondrías la URL real de tu frontend (ej: https://mi-app.com)
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Permitir todos los métodos (GET, POST, PUT, DELETE...)
    allow_headers=["*"],  # Permitir todos los headers (Authorization, Content-Type...)
)

# Evento de inicio (opcional, para crear tablas si no existe la DB)
@app.on_event("startup")
def on_startup():
    init_db()

# Incluir rutas
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
def root():
    return {"message": "Bienvenido al Motor de Recomendación de RRHH"}