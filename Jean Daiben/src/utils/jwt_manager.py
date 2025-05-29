import os
import jwt
from datetime import datetime, timedelta
from flask import request, jsonify
from functools import wraps

# Leer clave secreta desde variable de entorno para seguridad
SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'tu_clave_jwt_segura')

def generar_token(usuario_id, nombre, rol, expiracion=60):
    """
    Genera un token JWT con datos del usuario y expiración en minutos.
    """
    payload = {
        'usuario_id': usuario_id,
        'nombre': nombre,
        'rol': rol,
        'exp': datetime.utcnow() + timedelta(minutes=expiracion)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    if isinstance(token, bytes):
        token = token.decode('utf-8')
    return token

def verificar_token(token):
    """
    Verifica un token JWT y devuelve el payload si es válido, sino None.
    """
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        # Token expirado
        return None
    except jwt.InvalidTokenError:
        # Token inválido
        return None

def login_requerido(f):
    """
    Decorador para proteger rutas Flask, valida token JWT en header Authorization.
    Si el token es válido, añade 'usuario' al objeto request.
    """
    @wraps(f)
    def decorador(*args, **kwargs):
        auth_header = request.headers.get('Authorization', None)
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            datos = verificar_token(token)
            if datos:
                request.usuario = datos
                return f(*args, **kwargs)
        return jsonify({'error': 'Token inválido o expirado'}), 401
    return decorador
