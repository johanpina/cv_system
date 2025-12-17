from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
from sqlmodel import Session, select
from typing import List
from app.core.database import engine
from app.models.models import Url_HojaDeVida, Aspirante_Sede

router = APIRouter()

# --- Endpoint 1: Lista de Municipios para el Select ---
@router.get("/municipios", response_model=List[str])
def get_municipios_list():
    """Retorna la lista de municipios disponibles para filtrar."""
    # Estos son los campos booleanos de tu tabla Aspirante_Sede
    return [
        "Manizales", "Chinchiná", "Villamaría", "Neira", "Palestina", 
        "Risaralda", "Riosucio", "Anserma", "La_Dorada", "Supia", 
        "Palestina_Arauca", "Arauca", "Viterbo", "Salamina", "Belalcazar", 
        "Filadelfia", "Aguadas", "San_José", "Pacora", "Victoria", 
        "Manzanares", "Norcasia", "Samaná"
    ]

# --- Endpoint 2: Redirección a la Hoja de Vida ---
@router.get("/cv/{id_aspirante}")
def redirect_to_cv(id_aspirante: int):
    """Redirige al link de Google Drive asociado al aspirante."""
    with Session(engine) as session:
        statement = select(Url_HojaDeVida).where(Url_HojaDeVida.id_aspirante == id_aspirante)
        resultado = session.exec(statement).first()
        
        if not resultado or not resultado.url_hoja_de_vida:
            raise HTTPException(status_code=404, detail="Hoja de vida no encontrada")
            
        return RedirectResponse(url=resultado.url_hoja_de_vida)