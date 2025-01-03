from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from extensions import db, migrate
from config import Config
from rutas.informacion_terceros import informacion_terceros  # Importa el Blueprint

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)

    # Registrar el Blueprint
    app.register_blueprint(informacion_terceros)

    # Importar modelos para asegurarnos de que se reconocen durante las migraciones
    with app.app_context():
        from app.models import models  # Importa tus modelos

    return app
