from flask import Blueprint, request, jsonify, session, render_template, redirect, url_for, flash
from models.usuario_model import obtener_usuario_por_email, actualizar_ultimo_acceso, crear_usuario
import hashlib
from flask_jwt_extended import create_access_token
from datetime import timedelta
from db_config import get_db_connection

api_login = Blueprint('api_login', __name__)

# API Login (JSON)
@api_login.route('/login-json', methods=['POST'])
def login_api():  # <- Renombrada para evitar colisión con el Blueprint
    if not request.is_json:
        return jsonify({"message": "La solicitud debe ser JSON"}), 400

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

            session['usuario_id'] = user['UsuarioID']
            session['nombre'] = user.get('Nombre', '')
            session['usuario_rol'] = user.get('Rol', '')

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


# Web Login (HTML)
@api_login.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if not email or not password:
            flash('Por favor ingresa email y contraseña.', 'warning')
            return render_template('index.html')

        user = obtener_usuario_por_email(email)

        if user and user.get('Activo'):
            hashed_password = hashlib.sha256(password.encode()).hexdigest()
            if hashed_password == user.get('ContrasenaHash'):
                session['usuario_id'] = user['UsuarioID']
                session['usuario_nombre'] = user.get('Nombre', '')
                session['usuario_rol'] = user.get('Rol', '')

                actualizar_ultimo_acceso(user['UsuarioID'])

                return redirect(url_for('inicio'))
            else:
                flash('Correo o contraseña incorrectos, o cuenta inactiva.', 'danger')
        else:
            flash('Correo o contraseña incorrectos, o cuenta inactiva.', 'danger')

    return render_template('index.html')


# API Logout (JSON)
@api_login.route('/api/logout', methods=['POST'])
def api_logout():
    session.clear()
    return jsonify({"message": "Logout exitoso"}), 200


# Web Logout (HTML)
@api_login.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('api_login.login'))


# Web Register (HTML)
@api_login.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        email = request.form.get('email')
        password = request.form.get('password')
        rol = 'vendedor'  # o el valor predeterminado que quieras

        if not nombre or not email or not password:
            flash('Por favor completa todos los campos.', 'warning')
            return redirect(url_for('api_login.register'))

        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        if obtener_usuario_por_email(email):
            flash('Ya existe una cuenta con ese correo.', 'danger')
            return redirect(url_for('api_login.register'))

        crear_usuario(nombre, email, hashed_password, rol)

        flash('Cuenta creada exitosamente. Ahora puedes iniciar sesión.', 'success')
        return redirect(url_for('api_login.login'))

    return render_template('register.html')


# Web Password Recovery (HTML)
@api_login.route('/recuperar', methods=['GET', 'POST'])
def recuperar_contraseña():
    if request.method == 'POST':
        email = request.form.get('email')
        if not email:
            flash('Por favor ingresa un correo electrónico.', 'warning')
            return redirect(url_for('api_login.recuperar_contraseña'))

        user = obtener_usuario_por_email(email)
        if user:
            return redirect(url_for('api_login.restablecer_contraseña', email=email))
        else:
            flash('No se encontró ninguna cuenta con ese correo.', 'danger')
            return redirect(url_for('api_login.recuperar_contraseña'))

    return render_template('recuperar.html')


# Web Password Reset (HTML)
@api_login.route('/restablecer', methods=['GET', 'POST'])
def restablecer_contraseña():
    email = request.args.get('email')
    if not email:
        flash('Falta el correo electrónico.', 'danger')
        return redirect(url_for('api_login.login'))

    if request.method == 'POST':
        nueva_contrasena = request.form.get('password')
        if not nueva_contrasena:
            flash('Por favor ingresa una nueva contraseña.', 'warning')
            return render_template('restablecer.html', email=email)

        hashed = hashlib.sha256(nueva_contrasena.encode()).hexdigest()
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE Usuarios SET ContrasenaHash = %s WHERE Email = %s", (hashed, email))
        conn.commit()
        cursor.close()
        conn.close()
        flash('Contraseña restablecida correctamente. Inicia sesión.', 'success')
        return redirect(url_for('api_login.login'))

    return render_template('restablecer.html', email=email)
