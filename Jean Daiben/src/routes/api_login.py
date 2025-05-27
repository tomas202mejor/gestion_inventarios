from flask import Blueprint, request, jsonify, session
from models.usuario_model import obtener_usuario_por_email, actualizar_ultimo_acceso
import hashlib
from flask_jwt_extended import create_access_token
from datetime import timedelta

api_login = Blueprint('api_login', __name__)

@api_login.route('/login', methods=['POST'])
def login():
    email = request.json.get('email')
    password = request.json.get('password')

    if not email or not password:
        return jsonify({"message": "Faltan datos de email o contraseña"}), 400

    user = obtener_usuario_por_email(email)

    if user and user.get('Activo'):
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        if hashed_password == user.get('ContrasenaHash'):
            access_token = create_access_token(identity=user['UsuarioID'], expires_delta=timedelta(hours=1))
            actualizar_ultimo_acceso(user['UsuarioID'])

            # Guardar info usuario en sesión para renderizado server-side
            session['usuario_id'] = user['UsuarioID']
            session['nombre'] = user.get('Nombre', '')

            return jsonify({
                "token": access_token,
                "usuario": {
                    "id": user['UsuarioID'],
                    "nombre": user.get('Nombre', ''),
                    "rol": user.get('Rol', '')
                }
            }), 200
        else:
            return jsonify({"message": "Correo o contraseña incorrectos."}), 401
    else:
        return jsonify({"message": "Usuario no existe o está inactivo."}), 401

@api_login.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({"message": "Logout exitoso"}), 200
