from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from db_config import get_db_connection
import hashlib  # Importamos hashlib para calcular el hash
from datetime import datetime

api_login = Blueprint('api_login', __name__)

@api_login.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Usuarios WHERE Email = %s AND Activo = TRUE", (email,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user:
            # Generamos el hash de la contraseña ingresada
            hashed_password = hashlib.sha256(password.encode()).hexdigest()

            # Comparamos el hash generado con el hash almacenado en la base de datos
            if hashed_password == user['ContrasenaHash']:
                session['usuario_id'] = user['UsuarioID']
                session['usuario_nombre'] = user['Nombre']
                session['usuario_rol'] = user['Rol']

                # Guardar el último acceso
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("UPDATE Usuarios SET UltimoAcceso = %s WHERE UsuarioID = %s", (datetime.now(), user['UsuarioID']))
                conn.commit()
                cursor.close()
                conn.close()

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
