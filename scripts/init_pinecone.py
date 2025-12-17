import os
import sys
import time
from pinecone import Pinecone, ServerlessSpec

# Setup path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.core.config import settings

def init_pinecone_index():
    print("⚙️ Configurando infraestructura vectorial en Pinecone...")
    
    pc = Pinecone(api_key=settings.PINECONE_API_KEY)
    
    index_name = "hojas-de-vida-index"
    
    # Verificar si ya existe
    existing_indexes = [i.name for i in pc.list_indexes()]
    
    if index_name in existing_indexes:
        print(f"✅ El índice '{index_name}' ya existe. No es necesario hacer nada.")
        return

    print(f"🏗️ Creando índice '{index_name}' (Esto puede tardar unos segundos)...")
    
    # AQUÍ es donde usamos el PINECONE_ENV (Region)
    # Si no definiste PINECONE_ENV en .env, usa 'us-east-1' por defecto
    region = settings.PINECONE_ENV if settings.PINECONE_ENV else "us-east-1"
    
    try:
        pc.create_index(
            name=index_name,
            dimension=768, # Dimensión estándar para text-embedding-004 y 001
            metric="cosine", # La mejor para similitud semántica de texto
            spec=ServerlessSpec(
                cloud="aws", # Pinecone Serverless corre mayormente en AWS
                region=region
            )
        )
        
        # Esperar a que esté listo
        while not pc.describe_index(index_name).status['ready']:
            time.sleep(1)
            
        print(f"✅ Índice '{index_name}' creado exitosamente en la región {region}.")
        
    except Exception as e:
        print(f"❌ Error creando el índice: {e}")
        print("💡 Pista: Verifica que tu 'PINECONE_ENV' en el .env coincida con una región soportada (ej: us-east-1).")

if __name__ == "__main__":
    init_pinecone_index()