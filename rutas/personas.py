from services.services import BaseService
from app.models.models import Personas
from flask import request, jsonify, Blueprint
from extensions import db

personas_service = BaseService(Personas)

personas = Blueprint('personas', __name__, url_prefix='/personas')

# Obtener todas las personas
@personas.route('/', methods=['GET'])
def get_all():
    personas_list = personas_service.get_all()
    return jsonify([{
        'id_persona': persona.id_persona,
        'primer_nombre': persona.primer_nombre,
        'primer_apellido': persona.primer_apellido,
        'tipo_documento': persona.tipo_documento,
        'numero_documento': persona.numero_documento,
        'telefono_contacto': persona.telefono_contacto,
        'email': persona.email
    } for persona in personas_list]), 200

# Obtener persona por ID
@personas.route('/<string:id_persona>', methods=['GET'])
def get_by_id(id_persona):
    persona = personas_service.get_by_id(id_persona)
    if not persona:
        return jsonify({'message': 'Persona no encontrada'}), 404
    return jsonify({
        'id_persona': persona.id_persona,
        'primer_nombre': persona.primer_nombre,
        'primer_apellido': persona.primer_apellido,
        'tipo_documento': persona.tipo_documento,
        'numero_documento': persona.numero_documento,
        'telefono_contacto': persona.telefono_contacto,
        'email': persona.email
    }), 200

# Crear una nueva persona
@personas.route('/', methods=['POST'])
def create():
    data = request.json
    persona = personas_service.create(**data)
    return jsonify({
        'id_persona': persona.id_persona,
        'primer_nombre': persona.primer_nombre,
        'primer_apellido': persona.primer_apellido,
        'tipo_documento': persona.tipo_documento,
        'numero_documento': persona.numero_documento,
        'telefono_contacto': persona.telefono_contacto,
        'email': persona.email
    }), 201

# Actualizar persona por ID
@personas.route('/<string:id_persona>', methods=['PUT'])
def update_by_id(id_persona):
    data = request.json
    persona = personas_service.update(id_persona, **data)
    if not persona:
        return jsonify({'message': 'Persona no encontrada'}), 404
    return jsonify({
        'id_persona': persona.id_persona,
        'primer_nombre': persona.primer_nombre,
        'primer_apellido': persona.primer_apellido,
        'tipo_documento': persona.tipo_documento,
        'numero_documento': persona.numero_documento,
        'telefono_contacto': persona.telefono_contacto,
        'email': persona.email
    }), 200

# Eliminar persona por ID
@personas.route('/<string:id_persona>', methods=['DELETE'])
def delete_by_id(id_persona):
    persona = personas_service.delete(id_persona)
    if not persona:
        return jsonify({'message': 'Persona no encontrada'}), 404
    return jsonify({'message': 'Persona eliminada'}), 200
