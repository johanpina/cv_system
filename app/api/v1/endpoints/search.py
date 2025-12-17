from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.pinecone_service import search_best_matches

router = APIRouter()

# --- Modelos de Datos (Request/Response) ---
class SearchRequest(BaseModel):
    query: str
    municipio: Optional[str] = None
    top_k: int = 10

class SearchResult(BaseModel):
    id_aspirante: str
    nombre: str
    score_semantico: float
    score_final: float
    municipios: List[str]
    titulo_profesional: str
    titulo_posgrado: str
    resumen: str
    bonificaciones: List[str] # Para explicar por qué subió el puntaje

# --- Lógica de Re-ranking ---
def calcular_reranking(match) -> (float, List[str]):
    """
    Aplica reglas de negocio para ajustar el puntaje.
    """
    score_base = match.score
    meta = match.metadata
    bonus_log = []
    
    nuevo_score = score_base
    
    # Regla 1: Bonificación por Doctorado (+0.2)
    posgrado = meta.get('titulo_posgrado', '').lower()
    if 'doctor' in posgrado or 'phd' in posgrado:
        nuevo_score += 0.2
        bonus_log.append("Doctorado (+0.2)")
    # Regla 2: Bonificación por Maestría (+0.1) si no es doctor
    elif 'maestr' in posgrado or 'magister' in posgrado or 'master' in posgrado:
        nuevo_score += 0.1
        bonus_log.append("Maestría (+0.1)")
        
    # Regla 3: Bonificación por Experiencia (+0.05)
    # Nota: Aquí podríamos ser más precisos si tuviéramos años exactos parseados
    experiencia = meta.get('tiene_experiencia', '').lower()
    if 'si' in experiencia or 'yes' in experiencia:
        nuevo_score += 0.05
        bonus_log.append("Tiene Experiencia (+0.05)")

    return round(nuevo_score, 4), bonus_log

# --- Endpoint ---
@router.post("/", response_model=List[SearchResult])
def search_candidates(request: SearchRequest):
    """
    Buscador Híbrido: Semántica + Filtros + Lógica de Negocio
    """
    print(f"📡 Recibiendo búsqueda: {request.query}")
    
    # 1. Construir filtros para Pinecone
    filtros = {}
    if request.municipio:
        # Sintaxis de Pinecone para arrays: "municipios" contiene el valor X
        filtros["municipios"] = {"$in": [request.municipio]}
    
    # 2. Búsqueda Semántica (Traemos más candidatos para luego filtrar/reordenar)
    # Traemos el doble (20) para tener margen en el re-ranking
    raw_results = search_best_matches(request.query, filters=filtros if filtros else None, top_k=request.top_k * 2)
    
    if not raw_results or not hasattr(raw_results, 'matches'):
        return []

    processed_results = []
    
    # 3. Procesamiento y Re-ranking
    for match in raw_results.matches:
        meta = match.metadata or {}
        
        final_score, bonuses = calcular_reranking(match)
        
        processed_results.append(SearchResult(
            id_aspirante=match.id,
            nombre=meta.get('nombre', 'Anónimo'),
            score_semantico=round(match.score, 4),
            score_final=final_score,
            municipios=meta.get('municipios', []),
            titulo_profesional=meta.get('titulo_profesional', 'No registrado'),
            titulo_posgrado=meta.get('titulo_posgrado', 'No registrado'),
            resumen=meta.get('text', '')[:300] + "...", # Recorte para la UI
            bonificaciones=bonuses
        ))

    # 4. Ordenar por Score Final (Mayor a menor)
    processed_results.sort(key=lambda x: x.score_final, reverse=True)
    
    # 5. Devolver solo el top solicitado por el usuario
    return processed_results[:request.top_k]