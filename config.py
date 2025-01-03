import os
from dotenv import load_dotenv

# Cargar las variables de entorno
load_dotenv()

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "postgresql://postgres:TmX85col@localhost:5432/integracion")
    SQLALCHEMY_TRACK_MODIFICATIONS = False