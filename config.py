import os
from dotenv import load_dotenv

# Cargar las variables de entorno
load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'Manager1978*.')  # Clave secreta para proteger formularios
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "postgresql://postgres:TmX85col@localhost:5432/integracion")
    SQLALCHEMY_TRACK_MODIFICATIONS = False