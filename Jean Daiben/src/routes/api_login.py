from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models.usuario_model import obtener_usuario_por_email, actualizar_ultimo_acceso
import hashlib
from datetime import datetime

api_login = Blueprint('api_login', __name__)

@api_login.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = obtener_usuario_por_email(email)

        if user and user['Activo']:
            hashed_password = hashlib.sha256(password.encode()).hexdigest()
            if hashed_password == user['ContrasenaHash']:
                session['usuario_id'] = user['UsuarioID']
                session['usuario_nombre'] = user['Nombre']
                session['usuario_rol'] = user['Rol']

                actualizar_ultimo_acceso(user['UsuarioID'])

                return redirect(url_for('inicio'))
            else:
                flash('Correo o contraseña incorrectos, o cuenta inactiva.', 'danger')
        else:
            flash('Correo o contraseña incorrectos, o cuenta inactiva.', 'danger')

    return render_template('index.html')

@api_login.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('api_login.login'))
