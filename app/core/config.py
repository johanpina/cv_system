from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str
    API_V1_STR: str = "/api/v1"
    DATABASE_URL: str
    
    # AGREGAR ESTAS LÍNEAS:
    # Definimos las variables de IA. Usamos = "" para que no fallen si están vacías al inicio.
    GOOGLE_API_KEY: str = ""
    PINECONE_API_KEY: str = ""
    PINECONE_ENV: str = "" 

    class Config:
        env_file = ".env"
        # Esto permite que si hay variables extra en el .env que no usamos aquí, no lance error
        extra = "ignore" 

settings = Settings()