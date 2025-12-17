from fastapi import APIRouter
from sqlmodel import Session, select, func
from typing import List, Dict, Any
from app.core.database import engine
from app.models.models import Aspirante, Aspirante_Informacion, Aspirante_Sede

router = APIRouter()

@router.get("/")
def get_dashboard_stats():
    """
    Retorna métricas consolidadas para el Dashboard de RRHH.
    """
    with Session(engine) as session:
        # 1. Total Candidatos
        total_aspirantes = session.exec(select(func.count(Aspirante.id_aspirante))).one()
        
        # 2. Distribución por Nivel de Estudios (Posgrado)
        # Traemos todos y contamos en Python para flexibilidad (son pocos registros)
        infos = session.exec(select(Aspirante_Informacion)).all()
        
        # Conteo rápido
        niveles = {"Doctorado": 0, "Maestría": 0, "Especialización": 0, "Pregrado/Otro": 0}
        experiencia_si = 0
        
        for info in infos:
            titulo = info.titulo_posgrado.lower() if info.titulo_posgrado else ""
            
            if "doctor" in titulo or "phd" in titulo:
                niveles["Doctorado"] += 1
            elif "maestr" in titulo or "magister" in titulo or "master" in titulo:
                niveles["Maestría"] += 1
            elif "especiali" in titulo:
                niveles["Especialización"] += 1
            else:
                niveles["Pregrado/Otro"] += 1
                
            if info.tiene_experiencia and info.tiene_experiencia.lower() == "si":
                experiencia_si += 1

        # Formato para Recharts (Frontend)
        data_niveles = [{"name": k, "value": v} for k, v in niveles.items() if v > 0]
        
        # 3. Top Municipios (Sedes)
        # Esto requiere iterar las columnas booleanas. Lo haremos aproximado escaneando la tabla Sede.
        sedes = session.exec(select(Aspirante_Sede)).all()
        municipios_count = {}
        
        columnas_municipios = [
            "Manizales", "Chinchiná", "Villamaría", "Neira", "La_Dorada", 
            "Riosucio", "Anserma", "Salamina"
        ]
        
        for s in sedes:
            for m in columnas_municipios:
                # getattr obtiene el valor True/False de la columna
                if getattr(s, m, False):
                    municipios_count[m] = municipios_count.get(m, 0) + 1
        
        # Ordenar y tomar el Top 5
        top_municipios = sorted(
            [{"name": k, "value": v} for k, v in municipios_count.items()],
            key=lambda x: x['value'], 
            reverse=True
        )[:5]

        return {
            "kpi_total": total_aspirantes,
            "kpi_con_experiencia": experiencia_si,
            "chart_niveles": data_niveles,
            "chart_municipios": top_municipios
        }