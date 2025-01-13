# filepath: /E:/integracion/Integracion_XML/app/models/models.py
from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, Date
from sqlalchemy.orm import relationship
from extensions import db
from app import db
from sqlalchemy.dialects.postgresql import UUID
import uuid

class InformacionTerceros(db.Model):
    __tablename__ = 'informacion_terceros'
    id = db.Column(db.Integer, primary_key=True)
    registration_name = db.Column(db.String(255), nullable=False)
    company_id = db.Column(db.String(50), unique=True, nullable=False)
    tax_level_code = db.Column(db.String(50))
    address = db.Column(db.String(255))
    city_name = db.Column(db.String(255))
    country_subentity = db.Column(db.String(255))
    country_subentity_code = db.Column(db.String(50))
    country = db.Column(db.String(50))
    country_name = db.Column(db.String(255))
    telephone = db.Column(db.String(50))
    electronic_mail = db.Column(db.String(255))

class Empresa(db.Model):
    __tablename__ = 'empresa'
    id = db.Column(db.Integer, primary_key=True)
    registration_name = db.Column(db.String(255), nullable=False)
    company_id = db.Column(db.String(50), unique=True, nullable=False)
    tax_level_code = db.Column(db.String(50))
    address = db.Column(db.String(255))
    city_name = db.Column(db.String(255))
    country_subentity = db.Column(db.String(255))
    country_subentity_code = db.Column(db.String(50))
    country = db.Column(db.String(50))
    country_name = db.Column(db.String(255))
    telephone = db.Column(db.String(50))
    electronic_mail = db.Column(db.String(255))
    
class Facturacion(db.Model):
    __tablename__ = 'facturacion'
    id = db.Column(db.Integer, primary_key=True)
    ubl_version_id = db.Column(db.String(50))
    customization_id = db.Column(db.String(50))
    profile_id = db.Column(db.String(255))
    profile_execution_id = db.Column(db.String(50))
    document_id = db.Column(db.String(255))
    uuid = db.Column(db.String(255))
    issue_date = db.Column(db.Date)
    issue_time = db.Column(db.Time)
    due_date = db.Column(db.Date)
    invoice_type_code = db.Column(db.String(50))
    document_currency_code = db.Column(db.String(50))
    line_count_numeric = db.Column(db.Integer)
    supplier_id = db.Column(db.Integer, db.ForeignKey('empresa.id'))
    customer_id = db.Column(db.Integer, db.ForeignKey('informacion_terceros.id'))
    supplier = db.relationship('Empresa', backref=db.backref('facturaciones', lazy=True))
    customer = db.relationship('InformacionTerceros', backref=db.backref('facturaciones', lazy=True))
    
class InvoiceLine(db.Model):
    __tablename__ = 'invoice_line'
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('facturacion.id'))
    line_id = db.Column(db.String(50))
    invoiced_quantity = db.Column(db.String(50))
    line_extension_amount = db.Column(db.Float)
    description = db.Column(db.String(255))
    price_amount = db.Column(db.Float)
    invoice = db.relationship('Facturacion', backref=db.backref('invoice_lines', lazy=True))
    
class Personas(db.Model):
    __tablename__ = 'personas'
    id_persona = Column(Integer, primary_key=True)  # id_persona es Integer
    primer_nombre = Column(String(20))
    primer_apellido = Column(String(20))
    tipo_documento = Column(String(10))  # Cambiado a String si el tipo de documento no es solo un número
    numero_documento = Column(String(20))  # Cambiado a String para permitir caracteres como guiones
    telefono_contacto = Column(String(20))  # Cambiado a String para permitir números con guiones
    email = Column(String(100))

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