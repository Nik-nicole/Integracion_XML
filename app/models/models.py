# filepath: /E:/integracion/Integracion_XML/app/models/models.py
from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, Date
from sqlalchemy.orm import relationship
from extensions import db
from app import db
from sqlalchemy.dialects.postgresql import UUID
import uuid

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
    id_persona = Column(Integer, primary_key=True)  # id_persona es Integer
    primer_nombre = Column(String(20))
    primer_apellido = Column(String(20))
    tipo_documento = Column(String(10))  # Cambiado a String si el tipo de documento no es solo un número
    numero_documento = Column(String(20))  # Cambiado a String para permitir caracteres como guiones
    telefono_contacto = Column(String(20))  # Cambiado a String para permitir números con guiones
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
    id_persona = Column(Integer, ForeignKey('personas.id_persona'))  # Asegúrate de que sea Integer
    id_rol = Column(Integer, ForeignKey('roles.id_rol'))

    persona = relationship("Personas", backref="usuarios")
    rol = relationship("Roles", backref="usuarios")