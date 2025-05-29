from flask import Blueprint, request, render_template, redirect, url_for
from db_config import get_db_connection

api_clientes = Blueprint('api_clientes', __name__)

@api_clientes.route('/clientes/agregar', methods=['GET', 'POST'])
def agregar_cliente():
    if request.method == 'POST':
        nombre = request.form['nombre']
        ruc = request.form['ruc']
        direccion = request.form['direccion']
        telefono = request.form['telefono']
        email = request.form['email']
        tipo_cliente = request.form['tipo_cliente']

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO clientes (Nombre, RUC, Direccion, Telefono, Email, TipoCliente)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (nombre, ruc, direccion, telefono, email, tipo_cliente))
        conn.commit()
        conn.close()

        return redirect(url_for('api_clientes.agregar_cliente'))

    return render_template('agregar_cliente.html')