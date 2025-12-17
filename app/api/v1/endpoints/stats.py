from fastapi import APIRouter
from sqlmodel import Session, select, func
from app.core.database import engine
from app.models.models import Aspirante, Aspirante_Informacion, Aspirante_Sede, Url_HojaDeVida

router = APIRouter()

@router.get("/")
def get_dashboard_stats():
    """
    Retorna métricas avanzadas para el Dashboard de RRHH.
    """
    with Session(engine) as session:
        # --- 1. KPIs Generales ---
        total_aspirantes = session.exec(select(func.count(Aspirante.id_aspirante))).one()
        
        # KPI Procesamiento IA (Cuántos tienen resumen generado)
        total_procesados = session.exec(
            select(func.count(Url_HojaDeVida.id_url))
            .where(Url_HojaDeVida.resumen_estructurado != None)
        ).one()

        # --- 2. Análisis de Información Académica y Laboral ---
        infos = session.exec(select(Aspirante_Informacion)).all()
        
        # Inicializadores
        niveles = {"Doctorado": 0, "Maestría": 0, "Especialización": 0, "Pregrado/Otro": 0}
        disponibilidad_count = {}
        experiencia_si = 0
        
        for info in infos:
            # A. Niveles (Normalización)
            titulo = (info.titulo_posgrado or "").lower()
            if "doctor" in titulo or "phd" in titulo:
                niveles["Doctorado"] += 1
            elif "maestr" in titulo or "magister" in titulo or "master" in titulo:
                niveles["Maestría"] += 1
            elif "especiali" in titulo:
                niveles["Especialización"] += 1
            else:
                niveles["Pregrado/Otro"] += 1
            
            # B. Experiencia (Lógica robusta para detectar 'Sí', 'Si', 'sí', 'SÍ')
            exp = (info.tiene_experiencia or "").lower().strip()
            if exp in ['si', 'sí', 's', 'true', '1']:
                experiencia_si += 1

            # C. Disponibilidad (Limpieza básica)
            disp = (info.disponibilidad or "No especificada").strip().title()
            # Agrupar textos largos si es necesario, por ahora conteo directo
            disponibilidad_count[disp] = disponibilidad_count.get(disp, 0) + 1

        # Formateo para Charts
        chart_niveles = [{"name": k, "value": v} for k, v in niveles.items() if v > 0]
        
        # Tomamos el Top 5 de disponibilidades para no ensuciar el gráfico
        chart_disponibilidad = sorted(
            [{"name": k, "value": v} for k, v in disponibilidad_count.items()],
            key=lambda x: x['value'], reverse=True
        )[:5]

        # --- 3. Análisis Geográfico (Sedes) ---
        sedes = session.exec(select(Aspirante_Sede)).all()
        municipios_count = {}
        # Lista explícita de tus columnas booleanas más relevantes
        targets = ["Manizales", "Chinchiná", "Villamaría", "Neira", "Riosucio", "La_Dorada", "Anserma"]
        
        for s in sedes:
            for m in targets:
                if getattr(s, m, False):
                    municipios_count[m] = municipios_count.get(m, 0) + 1
        
        chart_municipios = sorted(
            [{"name": k, "value": v} for k, v in municipios_count.items()],
            key=lambda x: x['value'], reverse=True
        )

        return {
            "kpi_total": total_aspirantes,
            "kpi_procesados_ia": total_procesados,
            "kpi_con_experiencia": experiencia_si,
            "chart_niveles": chart_niveles,
            "chart_disponibilidad": chart_disponibilidad,
            "chart_municipios": chart_municipios
        }