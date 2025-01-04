from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from extensions import db, migrate
from config import Config
from rutas.informacion_terceros import informacion_terceros  # Importa el Blueprint
from rutas.personas import personas  # Importa el Blueprint
from rutas.xml_upload import xml_upload_bp  # Importar el Blueprint
from rutas.roles import roles
from rutas.usuarios import usuarios
from rutas.empresa import empresa

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)

    # Registrar el Blueprint de información de terceros
    app.register_blueprint(informacion_terceros)
    
    # Registrar el Blueprint de personas
    app.register_blueprint(personas)
    
    # Registrar el Blueprint de roles
    app.register_blueprint(roles)
    
    # Registrar el blueprint de usuarios
    app.register_blueprint(usuarios)
    
    # Registrar el Blueprint de empresa
    app.register_blueprint(empresa)
    
    # Registrar el Blueprint de carga de XML
    app.register_blueprint(xml_upload_bp)

    # Importar modelos para asegurarnos de que se reconocen durante las migraciones
    with app.app_context():
        from app.models import models  # Importa tus modelos

    return app
