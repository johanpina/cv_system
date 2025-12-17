from typing import List, Optional
from fastapi import APIRouter
from pydantic import BaseModel
from sqlmodel import Session, select
from app.core.database import engine
from app.models.models import Aspirante  # Asegúrate de importar tus modelos
from app.services.pinecone_service import search_best_matches

router = APIRouter()

# --- Modelos ---
class SearchRequest(BaseModel):
    query: str
    municipio: Optional[str] = None
    top_k: int = 10

class SearchResult(BaseModel):
    id_aspirante: str
    nombre: str
    email: str
    celular: str
    score_semantico: float
    score_final: float
    municipios: List[str]
    titulo_profesional: str
    titulo_posgrado: str
    resumen: str  # <--- Aquí irá el texto rico
    bonificaciones: List[str]

# --- Lógica de Re-ranking (Sin cambios) ---
def calcular_reranking(match, info_db) -> (float, List[str]):
    score_base = match.score
    nuevo_score = score_base
    bonus_log = []
    
    # Usamos info_db (datos frescos de SQL) para el re-ranking
    if info_db:
        posgrado = (info_db.titulo_posgrado or "").lower()
        if 'doctor' in posgrado or 'phd' in posgrado:
            nuevo_score += 0.2
            bonus_log.append("Doctorado (+0.2)")
        elif 'maestr' in posgrado or 'magister' in posgrado:
            nuevo_score += 0.1
            bonus_log.append("Maestría (+0.1)")
            
        experiencia = (info_db.tiene_experiencia or "").lower()
        if experiencia in ['si', 'sí', 's', 'true']:
            nuevo_score += 0.05
            bonus_log.append("Tiene Experiencia (+0.05)")

    return round(nuevo_score, 4), bonus_log

# --- Función auxiliar para obtener sedes ---
def obtener_sedes_activas(sede_obj) -> List[str]:
    if not sede_obj: return []
    columnas = [
        "Manizales", "Chinchiná", "Villamaría", "Neira", "Palestina", 
        "Risaralda", "Riosucio", "Anserma", "La_Dorada", "Supia", 
        "Palestina_Arauca", "Arauca", "Viterbo", "Salamina", "Belalcazar", 
        "Filadelfia", "Aguadas", "San_José", "Pacora", "Victoria", 
        "Manzanares", "Norcasia", "Samaná"
    ]
    return [c for c in columnas if getattr(sede_obj, c, False)]

# --- Endpoint ---
@router.post("/", response_model=List[SearchResult])
def search_candidates(request: SearchRequest):
    print(f"📡 Recibiendo búsqueda: {request.query}")
    
    # 1. Filtros Pinecone
    filtros = {}
    if request.municipio and request.municipio != "Todos":
        filtros["municipios"] = {"$in": [request.municipio]}
    
    # 2. Búsqueda Vectorial
    raw_results = search_best_matches(request.query, filters=filtros if filtros else None, top_k=request.top_k * 2)
    
    if not raw_results or not hasattr(raw_results, 'matches'):
        return []

    processed_results = []
    
    with Session(engine) as session:
        for match in raw_results.matches:
            # 3. Hidratación de Datos (Consultar SQL por ID)
            aspirante_id = int(match.id)
            aspirante_db = session.get(Aspirante, aspirante_id)
            
            if not aspirante_db:
                continue # Si no está en SQL, saltar
                
            info = aspirante_db.informacion
            sede = aspirante_db.sede
            
            # 4. Construcción del Resumen Rico
            # Armamos un bloque de texto con saltos de línea para que se vea bien en el frontend
            resumen_rico = (
                f"🎓 Título: {info.titulo_profesional if info else 'N/A'}\n"
                f"📚 Posgrado: {info.titulo_posgrado if info else 'N/A'}\n"
                f"🕒 Disponibilidad: {info.disponibilidad if info else 'N/A'}\n"
                f"💼 Detalle Experiencia: {getattr(info, 'detalle_experiencia', getattr(info, 'tiene_experiencia', 'N/A'))}\n"
                f"📧 Email: {aspirante_db.email}\n"
                f"📱 Celular: {aspirante_db.celular}"
            )

            # 5. Cálculos Finales
            final_score, bonuses = calcular_reranking(match, info)
            
            processed_results.append(SearchResult(
                id_aspirante=str(aspirante_db.id_aspirante),
                nombre=aspirante_db.nombre_completo,
                email=aspirante_db.email,
                celular=aspirante_db.celular,
                score_semantico=round(match.score, 4),
                score_final=final_score,
                municipios=obtener_sedes_activas(sede),
                titulo_profesional=info.titulo_profesional if info else "",
                titulo_posgrado=info.titulo_posgrado if info else "",
                resumen=resumen_rico, # <--- Usamos el texto construido
                bonificaciones=bonuses
            ))

    # 6. Ordenar y cortar
    processed_results.sort(key=lambda x: x.score_final, reverse=True)
    return processed_results[:request.top_k]