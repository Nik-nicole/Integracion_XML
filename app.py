from flask import Flask
from config import Config
from extensions import db, migrate
from rutas.informacion_terceros import informacion_terceros
from rutas.xml_upload import xml_upload_bp

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Register blueprints
    app.register_blueprint(informacion_terceros)
    
    # Register the XML upload blueprint
    app.register_blueprint(xml_upload_bp)
    
    return app