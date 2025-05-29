from flask import Blueprint, request, jsonify
from models.usuario_model import obtener_usuario_por_email, actualizar_ultimo_acceso
from flask_jwt_extended import create_access_token
from datetime import timedelta
import hashlib

api_auth = Blueprint('api_auth', __name__)

@api_auth.route('/api/login', methods=['POST'])
def api_login():
    try:
        datos = request.get_json(force=True)
    except Exception:
        return jsonify({"message": "Datos JSON inválidos"}), 400

    email = datos.get('email')
    password = datos.get('password')

    if not email or not password:
        return jsonify({'message': 'Email y contraseña son requeridos'}), 400

    user = obtener_usuario_por_email(email)
    if user and user.get('Activo'):
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        if hashed_password == user.get('ContrasenaHash'):
            actualizar_ultimo_acceso(user['UsuarioID'])
            access_token = create_access_token(identity=user['UsuarioID'], expires_delta=timedelta(hours=1))

            return jsonify({
                'token': access_token,
                'usuario': {
                    'id': user['UsuarioID'],
                    'nombre': user.get('Nombre', ''),
                    'rol': user.get('Rol', '')
                }
            }), 200

    return jsonify({'message': 'Credenciales inválidas o cuenta inactiva'}), 401
