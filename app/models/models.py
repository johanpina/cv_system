from typing import Optional, List
from sqlmodel import Field, SQLModel, Relationship
from sqlalchemy import Column, Text  # <--- IMPORTANTE: Importar esto

class Aspirante(SQLModel, table=True):
    id_aspirante: Optional[int] = Field(default=None, primary_key=True)
    tipo_documento: str = Field(index=True)
    num_documento: Optional[int] = Field(default=None, index=True)
    nombre_completo: str = Field(index=True)
    email: str = Field(index=True)
    celular: str = Field(index=True)

    # Relaciones para facilitar consultas (JOINs)
    informacion: Optional["Aspirante_Informacion"] = Relationship(back_populates="aspirante")
    hoja_vida: Optional["Url_HojaDeVida"] = Relationship(back_populates="aspirante")
    facultad: Optional["Aspirante_Facultad"] = Relationship(back_populates="aspirante")
    sede: Optional["Aspirante_Sede"] = Relationship(back_populates="aspirante")

class Aspirante_Informacion(SQLModel, table=True):
    id_info: Optional[int] = Field(default=None, primary_key=True)
    id_aspirante: Optional[int] = Field(default=None, foreign_key='aspirante.id_aspirante')
    titulo_profesional: str = Field(index=True)
    disponibilidad: str = Field(index=True)
    titulo_posgrado: str = Field(index=True)
    tiene_experiencia: str = Field(index=True)
    detalle_experiencia: str = Field(index=True)

    aspirante: Optional[Aspirante] = Relationship(back_populates="informacion")

# Actualización clave en Url_HojaDeVida
class Url_HojaDeVida(SQLModel, table=True):
    id_url: Optional[int] = Field(default=None, primary_key=True)
    id_aspirante: Optional[int] = Field(default=None, foreign_key='aspirante.id_aspirante')
    url_hoja_de_vida: str = Field(index=True)
    
    # Campo nuevo para guardar el texto procesado por Gemini
    resumen_estructurado: Optional[str] = Field(default=None, sa_column=Column(Text))

    aspirante: Optional["Aspirante"] = Relationship(back_populates="hoja_vida")

class Aspirante_Facultad(SQLModel, table=True):
    id_facultad: Optional[int] = Field(default=None, primary_key=True)
    id_aspirante: Optional[int] = Field(default=None, foreign_key='aspirante.id_aspirante')
    nombre_facultad: str = Field(index=True)

    aspirante: Optional[Aspirante] = Relationship(back_populates="facultad")

class Aspirante_Sede(SQLModel, table=True):
    id_sede: Optional[int] = Field(default=None, primary_key=True)
    id_aspirante: Optional[int] = Field(default=None, foreign_key='aspirante.id_aspirante')
    Manizales: bool = Field(default=False, index=True)
    Chinchiná: bool = Field(default=False, index=True)
    Villamaría: bool = Field(default=False, index=True)
    Neira: bool = Field(default=False, index=True)
    Palestina: bool = Field(default=False, index=True)
    Risaralda: bool = Field(default=False, index=True)
    Riosucio: bool = Field(default=False, index=True)
    Anserma: bool = Field(default=False, index=True)
    La_Dorada: bool = Field(default=False, index=True)
    Supia: bool = Field(default=False, index=True)
    Palestina_Arauca: bool = Field(default=False, index=True)
    Arauca: bool = Field(default=False, index=True)
    Viterbo: bool = Field(default=False, index=True)
    Salamina: bool = Field(default=False, index=True)
    Belalcazar: bool = Field(default=False, index=True)
    Filadelfia: bool = Field(default=False, index=True)
    Aguadas: bool = Field(default=False, index=True)
    San_José: bool = Field(default=False, index=True)
    Pacora: bool = Field(default=False, index=True)
    Victoria: bool = Field(default=False, index=True)
    Manzanares: bool = Field(default=False, index=True)
    Norcasia: bool = Field(default=False, index=True)
    Samaná: bool = Field(default=False, index=True)

    aspirante: Optional[Aspirante] = Relationship(back_populates="sede")



