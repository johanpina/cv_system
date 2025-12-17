import time
from typing import List, Dict, Any
from pinecone import Pinecone # <--- IMPORTANTE: Así se llama en la nueva versión
import google.generativeai as genai
from app.core.config import settings

# Configurar Gemini y Pinecone
genai.configure(api_key=settings.GOOGLE_API_KEY)
pc = Pinecone(api_key=settings.PINECONE_API_KEY) 

INDEX_NAME = "hojas-de-vida-index"

def get_embedding(text: str) -> List[float]:
    try:
        # Usamos el modelo optimizado 004
        result = genai.embed_content(
            model="models/text-embedding-004",
            content=text,
            task_type="retrieval_document"
        )
        return result['embedding']
    except Exception as e:
        print(f"Error generando embedding: {e}")
        return []

def upsert_to_pinecone(data_batch: List[Dict[str, Any]]):
    try:
        index = pc.Index(INDEX_NAME)
        
        vectors_to_upsert = []
        for item in data_batch:
            vector = get_embedding(item['text'])
            if not vector: continue

            vectors_to_upsert.append({
                "id": str(item['id']),
                "values": vector,
                "metadata": item['metadata']
            })
        
        if vectors_to_upsert:
            index.upsert(vectors=vectors_to_upsert)
            # Un print pequeño para saber que el servicio está trabajando
            # (Opcional, ya que la barra de progreso del sync nos dice cómo vamos)
            
    except Exception as e:
        print(f"❌ Error en servicio Pinecone: {e}")

def search_best_matches(query_text: str, filters: Dict[str, Any] = None, top_k: int = 10):
    """
    Busca los candidatos más similares semánticamente.
    - query_text: Lo que escribe RRHH (ej: "Profesor experto en Python y Data Science")
    - filters: Diccionario de filtros duros (ej: {"municipios": {"$in": ["Manizales"]}})
    """
    try:
        # 1. Convertir la pregunta de RRHH en números (Vector)
        print(f"🧮 Generando embedding para: '{query_text}'...")
        query_vector = get_embedding(query_text)
        
        if not query_vector:
            return {"error": "No se pudo generar el vector del query"}

        # 2. Consultar Pinecone
        index = pc.Index(INDEX_NAME)
        
        print(f"🔍 Buscando en Pinecone con filtros: {filters}...")
        results = index.query(
            vector=query_vector,
            top_k=top_k,
            include_metadata=True, # ¡Clave! Queremos ver quiénes son
            filter=filters         # Aquí ocurre la magia híbrida
        )
        
        return results
        
    except Exception as e:
        print(f"❌ Error buscando en Pinecone: {e}")
        return []