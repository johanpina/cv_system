import os
import sys
import time
from typing import List, Dict, Any
from tqdm import tqdm

# Setup paths
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlmodel import Session, select
from app.core.database import engine
from app.models.models import Url_HojaDeVida, Aspirante
from app.services.pinecone_service import upsert_to_pinecone

# Función auxiliar para extraer las sedes marcadas como True
def obtener_sedes_activas(sede_obj) -> List[str]:
    if not sede_obj:
        return []
    # Lista de columnas booleanas de tu modelo (basado en lo que vi en tus archivos)
    ciudades = [
        "Manizales", "Chinchiná", "Villamaría", "Neira", "Palestina", 
        "Risaralda", "Riosucio", "Anserma", "La_Dorada", "Supia", 
        "Palestina_Arauca", "Arauca", "Viterbo", "Salamina", "Belalcazar", 
        "Filadelfia", "Aguadas", "San_José", "Pacora", "Victoria", 
        "Manzanares", "Norcasia", "Samaná"
    ]
    # Retorna solo las ciudades que están en True
    return [c for c in ciudades if getattr(sede_obj, c, False)]

def main():
    print("🚀 Iniciando Sincronización a Pinecone (Vectores + Metadata)...")
    
    BATCH_SIZE = 50 # Subiremos de 50 en 50 para ser eficientes

    with Session(engine) as session:
        # 1. Seleccionar CVs que YA tienen resumen estructurado (Solo procesamos lo que ya leyó la IA)
        statement = select(Url_HojaDeVida).where(Url_HojaDeVida.resumen_estructurado != None)
        cvs = session.exec(statement).all()
        
        print(f"📊 Encontrados {len(cvs)} candidatos con resumen listo para indexar.")
        
        batch = []
        pbar = tqdm(cvs, desc="Indexando", unit="docs")
        
        for cv in pbar:
            # Validar integridad de datos (que tenga aspirante asociado)
            if not cv.aspirante:
                continue

            # --- A. PREPARAR TEXTO PARA EMBEDDING ---
            # Concatenamos el resumen estructurado. Este es el texto que la IA convertirá en números.
            texto_para_vector = cv.resumen_estructurado
            
            # --- B. PREPARAR METADATOS (FILTROS) ---
            # Extraemos la info de las tablas relacionadas (SQLModel hace el join automático al acceder)
            info = cv.aspirante.informacion # Tabla Aspirante_Informacion
            sede = cv.aspirante.sede        # Tabla Aspirante_Sede
            
            # Construimos el diccionario de metadatos
            metadata = {
                "id_aspirante": cv.id_aspirante,
                "nombre": cv.aspirante.nombre_completo,
                "municipios": obtener_sedes_activas(sede), # Lista de strings, ej: ['Manizales', 'Neira']
                "titulo_profesional": info.titulo_profesional if info else "No registrado",
                "titulo_posgrado": info.titulo_posgrado if info else "No registrado",
                "tiene_experiencia": info.tiene_experiencia if info else "No",
                "disponibilidad": info.disponibilidad if info else "No especificada"
            }
            
            # --- C. AGREGAR AL BATCH ---
            batch.append({
                "id": str(cv.id_aspirante), # ID único en Pinecone
                "text": texto_para_vector,  # Texto base
                "metadata": metadata        # Info extra para filtrar
            })
            
            # --- D. SUBIDA POR LOTES ---
            if len(batch) >= BATCH_SIZE:
                upsert_to_pinecone(batch)
                batch = [] # Vaciar el lote
                
        # Subir los últimos restantes si quedaron en el batch
        if batch:
            upsert_to_pinecone(batch)

    print("\n✅ Sincronización finalizada. Tu motor de búsqueda está listo.")

if __name__ == "__main__":
    main()