import firebase_admin
from firebase_admin import credentials
import os
import jwt
import datetime

# Inicializar Firebase Admin
def init_firebase():
    cred = credentials.Certificate('config/firebase_service_account.json')
    firebase_admin.initialize_app(cred)

# Clave secreta para JWT
JWT_SECRET = os.environ.get('JWT_SECRET', 'tu_clave_secreta_aqui')

# Crear un token JWT con UID de Firebase
def create_token(uid):
    payload = {
        'sub': uid,
        'iat': datetime.datetime.utcnow(),
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=2)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm='HS256')

# Verificar y decodificar un token JWT
def decode_token(token):
    return jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
