from functools import wraps
from flask import request, jsonify
from config import decode_token

def jwt_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.headers.get('Authorization', None)
        if not auth or not auth.startswith('Bearer '):
            return jsonify({'msg':'Token requerido'}), 401
        token = auth.split()[1]
        try:
            data = decode_token(token)
            request.uid = data['sub']  # UID de Firebase
        except Exception as e:
            return jsonify({'msg': f'Token inválido: {str(e)}'}), 401
        return f(*args, **kwargs)
    return decorated
