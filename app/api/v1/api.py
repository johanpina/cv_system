from fastapi import APIRouter
from app.api.v1.endpoints import health, search, stats, resources# <--- Importar search

api_router = APIRouter()

api_router.include_router(health.router, tags=["Estado"])
api_router.include_router(search.router, prefix="/search", tags=["Búsqueda"]) # <--- Registrar ruta
api_router.include_router(stats.router, prefix="/stats", tags=["Métricas"]) # <--- Registrar
api_router.include_router(stats.router, prefix="/stats", tags=["Métricas"])
api_router.include_router(resources.router, prefix="/resources", tags=["Recursos"]) # <--- Registrar