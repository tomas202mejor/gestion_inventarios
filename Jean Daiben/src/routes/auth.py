from flask import Blueprint, request, jsonify, render_template, redirect, url_for
from firebase_admin import auth as firebase_auth
from config import init_firebase, create_token

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# Inicializa Firebase al registrar el blueprint
@auth_bp.before_app_first_request
def init_firebase_app():
    init_firebase()

# Login: recibe ID Token de Firebase y devuelve JWT propio
@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    id_token = data.get('idToken')
    if not id_token:
        return jsonify({'error': 'idToken es requerido'}), 400

    try:
        decoded = firebase_auth.verify_id_token(id_token)
        uid = decoded['uid']
        email = decoded.get('email')
        # Creamos JWT interno
        access_token = create_token(uid)
        return jsonify({
            'access_token': access_token,
            'usuario': {'uid': uid, 'email': email}
        }), 200

    except Exception as e:
        return jsonify({'error': f'Invalid token: {str(e)}'}), 401

# Signup opcional: crea user en Firebase
@auth_bp.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    nombre = data.get('nombre')
    if not all([email, password, nombre]):
        return jsonify({'error': 'email, password y nombre son requeridos'}), 400

    try:
        user = firebase_auth.create_user(email=email, password=password, display_name=nombre)
        return jsonify({'uid': user.uid, 'email': user.email}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400
