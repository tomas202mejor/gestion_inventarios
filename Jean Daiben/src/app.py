from flask import Flask, render_template, redirect, url_for
from routes.api_productos import api_productos  # Blueprint de productos
from routes.api_notificaciones import api_notificaciones  # Nuevo blueprint de notificaciones
import os
from routes.api_inicio import api_inicio
from routes.api_notifi_guradadas import api_notifi_guradadas

app = Flask(__name__)

# Registrar los blueprints
app.register_blueprint(api_productos)
app.register_blueprint(api_notificaciones) # <--- Aquí agregas el nuevo
app.register_blueprint(api_inicio)
app.register_blueprint(api_notifi_guradadas)

# Rutas del frontend
@app.route('/')
def index():
    return redirect(url_for('productos'))  # Redirige a la página de productos

@app.route('/inicio')
def inicio():
    return render_template('inicio.html')

@app.route('/notifi_guradadas')
def notificaciones():
    return render_template('notificaciones.html')

@app.route('/productos')
def productos():
    return render_template('inventario.html')

@app.route('/productos/agregar')
def agregar_producto():
    return render_template('agregar.html')

@app.route('/productos/editar/<int:id>')
def editar_producto(id):
    return render_template('editar.html', producto_id=id)

# Ejecutar la aplicación
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)



