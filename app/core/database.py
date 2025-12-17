from sqlmodel import SQLModel, create_engine, Session
from app.core.config import settings

# check_same_thread=False es necesario solo para SQLite en FastAPI
connect_args = {"check_same_thread": False} 

engine = create_engine(settings.DATABASE_URL, connect_args=connect_args)

def get_session():
    with Session(engine) as session:
        yield session

def init_db():
    # Crea las tablas si no existen
    SQLModel.metadata.create_all(engine)