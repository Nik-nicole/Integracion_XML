from flask import request, jsonify, Blueprint
from services.services import BaseService
from app.models.models import Usuarios

usuarios_service = BaseService(Usuarios)

usuarios = Blueprint('usuarios', __name__, url_prefix='/usuarios')

# Obtener todos los usuarios
@usuarios.route('/', methods=['GET'])
def get_all_usuarios():
    usuarios_list = usuarios_service.get_all()
    return jsonify([{
        'id_usuario': usuario.id_usuario,
        'nombre_usuario': usuario.nombre_usuario,
        'estado': usuario.estado,
        # 'persona': usuario.persona.nombres if usuario.persona else None,
        'persona': f"{usuario.persona.primer_nombre} {usuario.persona.primer_apellido}" if usuario.persona else None,
        'rol': usuario.rol.nombre_rol if usuario.rol else None
    } for usuario in usuarios_list]), 200

# Obtener un usuario por ID
@usuarios.route('/<int:id_usuario>', methods=['GET'])
def get_usuario_by_id(id_usuario):
    usuario = usuarios_service.get_by_id(id_usuario)
    if not usuario:
        return jsonify({'message': 'Usuario no encontrado'}), 404
    return jsonify({
        'id_usuario': usuario.id_usuario,
        'nombre_usuario': usuario.nombre_usuario,
        'estado': usuario.estado,
        # 'persona': usuario.persona.nombres if usuario.persona else None,
        'persona': f"{usuario.persona.primer_nombre} {usuario.persona.primer_apellido}" if usuario.persona else None,
        'rol': usuario.rol.nombre_rol if usuario.rol else None
    }), 200

# Crear un nuevo usuario
@usuarios.route('/', methods=['POST'])
def create_usuario():
    data = request.json
    if not data or 'nombre_usuario' not in data or 'password' not in data or 'id_persona' not in data or 'id_rol' not in data:
        return jsonify({'message': 'Datos incompletos'}), 400
    
    new_usuario = usuarios_service.create(
        nombre_usuario=data['nombre_usuario'],
        password=data['password'],  # Asegúrate de aplicar hashing a la contraseña antes de guardarla
        estado=data.get('estado', True),  # Asignar estado como True si no se especifica
        id_persona=data['id_persona'],
        id_rol=data['id_rol']
    )
    return jsonify({
        'id_usuario': new_usuario.id_usuario,
        'nombre_usuario': new_usuario.nombre_usuario,
        'estado': new_usuario.estado,
        # 'persona': new_usuario.persona.nombres if new_usuario.persona else None,
        'persona': f"{new_usuario.persona.primer_nombre} {new_usuario.persona.primer_apellido}" if new_usuario.persona else None,
        'rol': new_usuario.rol.nombre_rol if new_usuario.rol else None
    }), 201

# Actualizar un usuario por ID
@usuarios.route('/<int:id_usuario>', methods=['PUT'])
def update_usuario_by_id(id_usuario):
    data = request.json
    if not data or 'nombre_usuario' not in data or 'password' not in data or 'id_persona' not in data or 'id_rol' not in data:
        return jsonify({'message': 'Datos incompletos'}), 400

    updated_usuario = usuarios_service.update(
        id_usuario,
        nombre_usuario=data['nombre_usuario'],
        password=data['password'],  # Asegúrate de aplicar hashing a la contraseña
        estado=data.get('estado', True),
        id_persona=data['id_persona'],
        id_rol=data['id_rol']
    )
    if not updated_usuario:
        return jsonify({'message': 'Usuario no encontrado'}), 404
    return jsonify({
        'id_usuario': updated_usuario.id_usuario,
        'nombre_usuario': updated_usuario.nombre_usuario,
        'estado': updated_usuario.estado,
        # 'persona': updated_usuario.persona.nombres if updated_usuario.persona else None,
        'persona': f"{updated_usuario.persona.primer_nombre} {updated_usuario.persona.primer_apellido}" if updated_usuario.persona else None,
        'rol': updated_usuario.rol.nombre_rol if updated_usuario.rol else None
    }), 200

# Eliminar un usuario por ID
@usuarios.route('/<int:id_usuario>', methods=['DELETE'])
def delete_usuario_by_id(id_usuario):
    deleted = usuarios_service.delete(id_usuario)
    if not deleted:
        return jsonify({'message': 'Usuario no encontrado'}), 404
    return jsonify({'message': 'Usuario eliminado exitosamente'}), 200
