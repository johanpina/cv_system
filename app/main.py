from fastapi import FastAPI
from app.core.config import settings
from app.api.v1.api import api_router
from app.core.database import init_db

# Inicializar la app
app = FastAPI(title=settings.PROJECT_NAME)

# Evento de inicio (opcional, para crear tablas si no existe la DB)
@app.on_event("startup")
def on_startup():
    init_db()

# Incluir rutas
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
def root():
    return {"message": "Bienvenido al Motor de Recomendación de RRHH"}