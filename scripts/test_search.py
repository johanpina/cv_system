import sys
import os

# Setup path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.pinecone_service import search_best_matches

def main():
    # --- ESCENARIO DE PRUEBA ---
    query = "Ingeniero de sistemas con experiencia docente en inteligencia artificial y bases de datos"
    filtros = None 

    print(f"🔎 QUERY: {query}")
    print("-" * 50)

    # Llamada al servicio
    resultados = search_best_matches(query, filters=filtros, top_k=5)

    # --- CORRECCIÓN CLAVE AQUÍ ---
    # En Pinecone v3, 'resultados' es un OBJETO, no un diccionario.
    # Usamos notación de punto (.) en lugar de corchetes ['']
    
    if resultados and hasattr(resultados, 'matches') and resultados.matches:
        for i, match in enumerate(resultados.matches):
            # 'match' también es un objeto (ScoredVector)
            score = match.score
            meta = match.metadata
            
            # Nota: 'meta' suele ser un diccionario estándar o un objeto que permite .get()
            # Si meta falla, prueba con meta['nombre'] o meta.get('nombre')
            
            print(f"\n🏆 TOP {i+1} (Similitud: {score:.4f})")
            
            # Manejo defensivo por si metadata viene vacío
            if meta:
                print(f"   👤 Nombre: {meta.get('nombre', 'Desconocido')}")
                print(f"   🎓 Título: {meta.get('titulo_profesional', 'N/A')}")
                print(f"   👨‍🏫 Posgrado: {meta.get('titulo_posgrado', 'N/A')}")
                print(f"   📍 Municipios: {meta.get('municipios', [])}")
                
                # Para el texto, a veces Pinecone lo devuelve directo o dentro de metadata
                # Asumimos que lo guardamos en metadata como 'text' en el script de sync
                texto_resumen = meta.get('text', '') 
                print(f"   📄 Extracto: {texto_resumen[:150]}...") 
            else:
                print("   ⚠️ Sin metadatos disponibles.")
                
    else:
        print("❌ No se encontraron resultados o la estructura de respuesta es incorrecta.")

if __name__ == "__main__":
    main()