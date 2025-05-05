from flask import Flask, render_template, redirect, url_for
from routes.api_productos import api_productos  # Blueprint de productos
from routes.api_notificaciones import api_notificaciones  # Blueprint de notificaciones
from routes.api_ventas import api_ventas  # Blueprint de ventas
from routes.api_inicio import api_inicio
from routes.api_notifi_guardadas import api_notifi_guardadas
import os

app = Flask(__name__)
# Registrar los blueprints
app.register_blueprint(api_productos)
app.register_blueprint(api_notificaciones)
app.register_blueprint(api_inicio)
app.register_blueprint(api_notifi_guardadas)  # CORREGIDO
app.register_blueprint(api_ventas)

# Rutas del frontend
@app.route('/')
def index():
    return redirect(url_for('inicio'))

@app.route('/login')
def login():
    return render_template('index.html')

@app.route('/inicio')
def inicio():
    return render_template('inicio.html')

@app.route('/notifi_guardadas')
def notificaciones():
    return render_template('notificaciones.html')

@app.route('/productos')
def productos():
    return render_template('inventario.html')

@app.route('/prediccion')
def prediccion():
    return render_template('prediccion.html')

@app.route('/ventas')
def ventas():
    return render_template('ventas.html')

@app.route('/ventas/nueva')
def nueva_venta():
    return render_template('ventas_nueva.html')

@app.route('/productos/agregar')
def agregar_producto():
    return render_template('agregar.html')

@app.route('/productos/editar/<int:id>')
def editar_producto(id):
    return render_template('editar.html', producto_id=id)

@app.route('/factura/<int:factura_id>')
def ver_factura(factura_id):
    return render_template('ver_factura.html', factura_id=factura_id)

# Nueva ruta para la página de envío de factura por email
@app.route('/factura/<int:factura_id>/enviar')
def enviar_factura(factura_id):
    # En este punto, normalmente buscaríamos los datos de la factura en la base de datos
    # y los pasaríamos a la plantilla, pero aquí solo redirigimos a la plantilla
    return render_template('enviar_factura.html', factura_id=factura_id)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)