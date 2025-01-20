from services.services import BaseService
from app.models.models import InformacionTerceros
from flask import request, jsonify, Blueprint
from extensions import db

informacion_terceros_service = BaseService(InformacionTerceros)

informacion_terceros = Blueprint('informacion_terceros', __name__, url_prefix='/informacion_terceros')

@informacion_terceros.route('/', methods=['GET']) 
def get_all():
    informacion_terceros = informacion_terceros_service.get_all()
    return jsonify([{
        'id_terceros': informacion_terceros.id_terceros,
        'identificacion': informacion_terceros.identificacion,
        'tipo_persona': informacion_terceros.tipo_persona,
        'nombre_razon_social': informacion_terceros.nombre_razon_social,
        'representante_legal': informacion_terceros.representante_legal,
        'direccion': informacion_terceros.direccion,
        'telefono': informacion_terceros.telefono,
        'email': informacion_terceros.email,
        'actividad_economica': informacion_terceros.actividad_economica
    } for informacion_terceros in informacion_terceros]), 200
    
@informacion_terceros.route('/<int:id_terceros>', methods=['GET'])
def get_by_id(id_terceros):
    informacion_terceros = informacion_terceros_service.get_by_id(id_terceros)
    if not informacion_terceros:
        return jsonify({'message': 'Informacion de terceros no encontrada'}), 404
    return jsonify({
        'id_terceros': informacion_terceros.id_terceros,
        'identificacion': informacion_terceros.identificacion,
        'tipo_persona': informacion_terceros.tipo_persona,
        'nombre_razon_social': informacion_terceros.nombre_razon_social,
        'representante_legal': informacion_terceros.representante_legal,
        'direccion': informacion_terceros.direccion,
        'telefono': informacion_terceros.telefono,
        'email': informacion_terceros.email,
        'actividad_economica': informacion_terceros.actividad_economica
    }), 200
    
@informacion_terceros.route('/', methods=['POST'])
def create():
    data = request.json
    informacion_terceros = informacion_terceros_service.create(**data)
    return jsonify({
        'id_terceros': informacion_terceros.id_terceros,
        'identificacion': informacion_terceros.identificacion,
        'tipo_persona': informacion_terceros.tipo_persona,
        'nombre_razon_social': informacion_terceros.nombre_razon_social,
        'representante_legal': informacion_terceros.representante_legal,
        'direccion': informacion_terceros.direccion,
        'telefono': informacion_terceros.telefono,
        'email': informacion_terceros.email,
        'actividad_economica': informacion_terceros.actividad_economica
    }), 201
    
@informacion_terceros.route('/<int:id_terceros>', methods=['PUT'])
def update_by_id(id_terceros):
    data = request.json
    informacion_terceros = informacion_terceros_service.update(id_terceros, **data)
    if not informacion_terceros:
        return jsonify({'message': 'Informacion de terceros no encontrada'}), 404
    return jsonify({
        'id_terceros': informacion_terceros.id_terceros,
        'identificacion': informacion_terceros.identificacion,
        'tipo_persona': informacion_terceros.tipo_persona,
        'nombre_razon_social': informacion_terceros.nombre_razon_social,
        'representante_legal': informacion_terceros.representante_legal,
        'direccion': informacion_terceros.direccion,
        'telefono': informacion_terceros.telefono,
        'email': informacion_terceros.email,
        'actividad_economica': informacion_terceros.actividad_economica
    }), 200
    
@informacion_terceros.route('/<int:id_terceros>', methods=['DELETE'])
def delete_by_id(id_terceros):
    informacion_terceros = informacion_terceros_service.delete(id_terceros)
    if not informacion_terceros:
        return jsonify({'message': 'Informacion de terceros no encontrada'}), 404
    return jsonify({'message': 'Informacion de terceros eliminada'}), 200