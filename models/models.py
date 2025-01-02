from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, Date
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from app.extensions import db

class InformacionTerceros(db.Model):
    __tablename__ = 'informacion_terceros'
    id_terceros = Column(Integer, primary_key=True)
    identificacion = Column(String)
    tipo_persona = Column(String(20))
    nombre_razon_social = Column(String(100))
    representante_legal = Column(String(100))
    direccion = Column(String(40))
    telefono = Column(String(20))
    email = Column(String(100))
    actividad_economica = Column(String(20))

class Personas(db.Model):
    __tablename__ = 'personas'
    id_persona = Column(String(20), primary_key=True)
    primer_nombre = Column(String(20))
    primer_apellido = Column(String(20))
    tipo_documento = Column(Integer)
    numero_documento = Column(Integer)
    telefono_contacto = Column(Integer)
    email = Column(String(100))

class Empresa(db.Model):
    __tablename__ = 'empresa'
    id_empresa = Column(Integer, primary_key=True)
    nombre_empresa = Column(String(150))
    nit = Column(String(20))
    direccion = Column(String(200))
    telefono = Column(String(15))
    email_contacto = Column(String(100))

class Roles(db.Model):
    __tablename__ = 'roles'
    id_rol = Column(Integer, primary_key=True)
    nombre_rol = Column(String(50))
    descripcion_rol = Column(String(20))

class Usuarios(db.Model):
    __tablename__ = 'usuarios'
    id_usuario = Column(Integer, primary_key=True)
    nombre_usuario = Column(String(50))
    password = Column(String(200))
    estado = Column(Boolean)
    id_persona = Column(String(20), ForeignKey('personas.id_persona'))
    id_rol = Column(Integer, ForeignKey('roles.id_rol'))

    persona = relationship("Personas", backref="usuarios")
    rol = relationship("Roles", backref="usuarios")

# Conexión a la base de datos (cambia 'sqlite:///test.db' por tu configuración)


# Crear todas las tablas

