from typing import List, Optional, Tuple
from fastapi import APIRouter
from pydantic import BaseModel
from sqlmodel import Session, select, desc
from app.core.database import engine
from app.models.models import Aspirante, Aspirante_Sede, Url_HojaDeVida
from app.services.pinecone_service import search_best_matches

router = APIRouter()

# --- Modelos Actualizados ---
class SearchRequest(BaseModel):
    query: Optional[str] = ""     # Ahora es opcional y por defecto vacío
    municipio: Optional[str] = None
    page: int = 1                 # Paginación: Página actual
    page_size: int = 25           # Paginación: Cantidad por página (Default 25)

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
    resumen: str
    bonificaciones: List[str]

# --- Funciones Auxiliares (Re-ranking y Sedes) ---
# (Se mantienen igual que antes, las incluyo para contexto)
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


def calcular_reranking(match_score, info_db) -> Tuple[float, List[str]]:
    nuevo_score = match_score
    bonus_log = []
    
    if info_db:
        # 1. Reglas de Bonificación
        posgrado = (info_db.titulo_posgrado or "").lower()
        if 'doctor' in posgrado or 'phd' in posgrado:
            nuevo_score += 0.2
            bonus_log.append("Doctorado (+0.2)")
        elif 'maestr' in posgrado or 'magister' in posgrado:
            nuevo_score += 0.1
            bonus_log.append("Maestría (+0.1)")
            
        experiencia = (info_db.tiene_experiencia or "").lower()
        if experiencia in ['si', 'sí', 's', 'true', '1']:
            nuevo_score += 0.05
            bonus_log.append("Tiene Experiencia (+0.05)")

    # 2. ESTANDARIZACIÓN (Tope máximo 100%)
    score_final_normalizado = min(1.0, nuevo_score)

    return round(score_final_normalizado, 4), bonus_log

# --- Endpoint Principal ---
@router.post("/", response_model=List[SearchResult])
def search_candidates(request: SearchRequest):
    print(f"📡 Búsqueda: '{request.query}' | Pag: {request.page} | Muni: {request.municipio}")
    
    processed_results = []
    aspirantes_ids = []
    scores_map = {} # Diccionario para guardar scores si vienen de Pinecone

    # CASO A: Búsqueda Semántica (Hay Texto)
    if request.query and request.query.strip():
        # 1. Filtros Pinecone
        filtros = {}
        if request.municipio and request.municipio != "Todos":
            filtros["municipios"] = {"$in": [request.municipio]}
        
        # 2. Consultar Pinecone (Pedimos más para tener margen)
        # Nota: Pinecone no tiene paginación 'offset' nativa eficiente, 
        # pero para volúmenes bajos (1500) traemos top_k grande y cortamos en Python.
        limit_pinecone = request.page * request.page_size
        raw_results = search_best_matches(request.query, filters=filtros if filtros else None, top_k=limit_pinecone)
        
        if not raw_results or not hasattr(raw_results, 'matches'):
            return []

        # Cortamos manualmente para la paginación (Slicing)
        start_idx = (request.page - 1) * request.page_size
        matches_paginados = raw_results.matches[start_idx : start_idx + request.page_size]

        for match in matches_paginados:
            aid = int(match.id)
            aspirantes_ids.append(aid)
            scores_map[aid] = match.score

    # CASO B: Navegación General (Query Vacío) -> Usamos SQL Directo
    else:
        with Session(engine) as session:
            statement = select(Aspirante)
            
            # Filtro de Municipio en SQL
            if request.municipio and request.municipio != "Todos":
                # Esto es un poco complejo dinámicamente, simplificamos asumiendo JOIN
                statement = statement.join(Aspirante_Sede).where(getattr(Aspirante_Sede, request.municipio) == True)
            
            # Paginación SQL
            statement = statement.offset((request.page - 1) * request.page_size).limit(request.page_size)
            
            results_db = session.exec(statement).all()
            for asp in results_db:
                aspirantes_ids.append(asp.id_aspirante)
                scores_map[asp.id_aspirante] = 0.0 # Score neutro

    # --- Hidratación y Respuesta Unificada ---
    if not aspirantes_ids:
        return []

    with Session(engine) as session:
        # Traemos todos los aspirantes requeridos en una sola query optimizada
        candidates_db = session.exec(select(Aspirante).where(Aspirante.id_aspirante.in_(aspirantes_ids))).all()
        
        # Mapeamos para mantener el orden original de los IDs (importante para Pinecone)
        candidates_map = {c.id_aspirante: c for c in candidates_db}

        for aid in aspirantes_ids:
            aspirante_db = candidates_map.get(aid)
            if not aspirante_db: continue

            info = aspirante_db.informacion
            sede = aspirante_db.sede

            # A. Obtener el texto analizado por la IA (Donde está la experiencia real)
            hoja_vida_obj = session.exec(select(Url_HojaDeVida).where(Url_HojaDeVida.id_aspirante == aspirante_db.id_aspirante)).first()
            texto_ia = hoja_vida_obj.resumen_estructurado if hoja_vida_obj and hoja_vida_obj.resumen_estructurado else "Sin análisis detallado disponible."
            
            
            # Construcción del Resumen Rico
            resumen_rico = (
                f"🎓 Título: {info.titulo_profesional if info else 'N/A'}\n"
                f"📚 Posgrado: {info.titulo_posgrado if info else 'N/A'}\n"
                f"🕒 Disponibilidad: {info.disponibilidad if info else 'No especificada'}\n"
                f"📋 Detalle Experiencia: {getattr(info, 'detalle_experiencia', 'Sin registro manual')}\n"
                f"📧 Email: {aspirante_db.email}\n"
                f"{texto_ia}" # <--- AQUÍ INYECTAMOS LA EXPERIENCIA Y PERFIL
            )

            # Cálculo de Scores
            base_score = scores_map.get(aid, 0.0)
            final_score, bonuses = calcular_reranking(base_score, info)
            
            # Si es búsqueda vacía (Case B), forzamos score visual a 0 o 100% ficticio, 
            # pero mejor lo dejamos en 0 y que el frontend decida no mostrar badge si es 0.
            
            processed_results.append(SearchResult(
                id_aspirante=str(aspirante_db.id_aspirante),
                nombre=aspirante_db.nombre_completo,
                email=aspirante_db.email,
                celular=aspirante_db.celular,
                score_semantico=round(base_score, 4),
                score_final=final_score,
                municipios=obtener_sedes_activas(sede),
                titulo_profesional=info.titulo_profesional if info else "",
                titulo_posgrado=info.titulo_posgrado if info else "",
                resumen=resumen_rico,
                bonificaciones=bonuses
            ))

    # Si venimos de SQL (Case B), tal vez queramos ordenarlos por Doctorado/Maestría por defecto
    if not request.query:
         processed_results.sort(key=lambda x: x.score_final, reverse=True)

    return processed_results