from flask import request, jsonify, Blueprint
from services.services import BaseService
from app.models.models import Empresa

# Inicializamos el servicio de Empresa usando BaseService
empresa_service = BaseService(Empresa)

# Creamos el Blueprint para la ruta '/empresa'
empresa = Blueprint('empresa', __name__, url_prefix='/empresa')

# Obtener todas las empresas
@empresa.route('/', methods=['GET'])
def get_all_empresas():
    empresas_list = empresa_service.get_all()
    return jsonify([{
        'id_empresa': empresa.id_empresa,
        'nombre_empresa': empresa.nombre_empresa,
        'nit': empresa.nit,
        'direccion': empresa.direccion,
        'telefono': empresa.telefono,
        'email_contacto': empresa.email_contacto
    } for empresa in empresas_list]), 200

# Obtener una empresa por ID
@empresa.route('/<int:id_empresa>', methods=['GET'])
def get_empresa_by_id(id_empresa):
    empresa = empresa_service.get_by_id(id_empresa)
    if not empresa:
        return jsonify({'message': 'Empresa no encontrada'}), 404
    return jsonify({
        'id_empresa': empresa.id_empresa,
        'nombre_empresa': empresa.nombre_empresa,
        'nit': empresa.nit,
        'direccion': empresa.direccion,
        'telefono': empresa.telefono,
        'email_contacto': empresa.email_contacto
    }), 200

# Crear una nueva empresa
@empresa.route('/', methods=['POST'])
def create_empresa():
    data = request.json
    if not data or 'nombre_empresa' not in data or 'nit' not in data:
        return jsonify({'message': 'Datos incompletos'}), 400
    new_empresa = empresa_service.create(
        nombre_empresa=data['nombre_empresa'],
        nit=data['nit'],
        direccion=data.get('direccion', ''),
        telefono=data.get('telefono', ''),
        email_contacto=data.get('email_contacto', '')
    )
    return jsonify({
        'id_empresa': new_empresa.id_empresa,
        'nombre_empresa': new_empresa.nombre_empresa,
        'nit': new_empresa.nit,
        'direccion': new_empresa.direccion,
        'telefono': new_empresa.telefono,
        'email_contacto': new_empresa.email_contacto
    }), 201

# Actualizar una empresa por ID
@empresa.route('/<int:id_empresa>', methods=['PUT'])
def update_empresa_by_id(id_empresa):
    data = request.json
    if not data or 'nombre_empresa' not in data or 'nit' not in data:
        return jsonify({'message': 'Datos incompletos'}), 400
    updated_empresa = empresa_service.update(
        id_empresa,
        nombre_empresa=data['nombre_empresa'],
        nit=data['nit'],
        direccion=data.get('direccion', ''),
        telefono=data.get('telefono', ''),
        email_contacto=data.get('email_contacto', '')
    )
    if not updated_empresa:
        return jsonify({'message': 'Empresa no encontrada'}), 404
    return jsonify({
        'id_empresa': updated_empresa.id_empresa,
        'nombre_empresa': updated_empresa.nombre_empresa,
        'nit': updated_empresa.nit,
        'direccion': updated_empresa.direccion,
        'telefono': updated_empresa.telefono,
        'email_contacto': updated_empresa.email_contacto
    }), 200

# Eliminar una empresa por ID
@empresa.route('/<int:id_empresa>', methods=['DELETE'])
def delete_empresa_by_id(id_empresa):
    deleted = empresa_service.delete(id_empresa)
    if not deleted:
        return jsonify({'message': 'Empresa no encontrada'}), 404
    return jsonify({'message': 'Empresa eliminada exitosamente'}), 200
