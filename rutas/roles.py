from flask import request, jsonify, Blueprint
from services.services import BaseService
from app.models.models import Roles

roles_service = BaseService(Roles)

roles = Blueprint('roles', __name__, url_prefix='/roles')

# Obtener todos los roles
@roles.route('/', methods=['GET'])
def get_all_roles():
    roles_list = roles_service.get_all()
    return jsonify([{
        'id_rol': rol.id_rol,
        'nombre_rol': rol.nombre_rol,
        'descripcion_rol': rol.descripcion_rol
    } for rol in roles_list]), 200

# Obtener un rol por ID
@roles.route('/<int:id_rol>', methods=['GET'])
def get_role_by_id(id_rol):
    rol = roles_service.get_by_id(id_rol)
    if not rol:
        return jsonify({'message': 'Rol no encontrado'}), 404
    return jsonify({
        'id_rol': rol.id_rol,
        'nombre_rol': rol.nombre_rol,
        'descripcion_rol': rol.descripcion_rol
    }), 200

# Crear un nuevo rol
@roles.route('/', methods=['POST'])
def create_role():
    data = request.json
    if not data or 'nombre_rol' not in data or 'descripcion_rol' not in data:
        return jsonify({'message': 'Datos incompletos'}), 400
    new_rol = roles_service.create(
        nombre_rol=data['nombre_rol'],
        descripcion_rol=data['descripcion_rol']
    )
    return jsonify({
        'id_rol': new_rol.id_rol,
        'nombre_rol': new_rol.nombre_rol,
        'descripcion_rol': new_rol.descripcion_rol
    }), 201

# Actualizar un rol por ID
@roles.route('/<int:id_rol>', methods=['PUT'])
def update_role_by_id(id_rol):
    data = request.json
    if not data or 'nombre_rol' not in data or 'descripcion_rol' not in data:
        return jsonify({'message': 'Datos incompletos'}), 400
    updated_rol = roles_service.update(
        id_rol,
        nombre_rol=data['nombre_rol'],
        descripcion_rol=data['descripcion_rol']
    )
    if not updated_rol:
        return jsonify({'message': 'Rol no encontrado'}), 404
    return jsonify({
        'id_rol': updated_rol.id_rol,
        'nombre_rol': updated_rol.nombre_rol,
        'descripcion_rol': updated_rol.descripcion_rol
    }), 200

# Eliminar un rol por ID
@roles.route('/<int:id_rol>', methods=['DELETE'])
def delete_role_by_id(id_rol):
    deleted = roles_service.delete(id_rol)
    if not deleted:
        return jsonify({'message': 'Rol no encontrado'}), 404
    return jsonify({'message': 'Rol eliminado exitosamente'}), 200
