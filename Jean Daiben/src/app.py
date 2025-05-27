from flask import Flask, render_template, redirect, url_for, session
from flask_cors import CORS
from flask_jwt_extended import JWTManager

# Importar tus blueprints
from routes.api_productos import api_productos
from routes.api_notificaciones import api_notificaciones
from routes.api_ventas import api_ventas
from routes.api_inicio import api_inicio
from routes.api_notifi_guardadas import api_notifi_guardadas
from routes.api_prediccion import api_prediccion
from routes.api_login import api_login
from routes.api_dashboard import api_dashboard
from routes.api_pedidos import api_pedidos

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta_segura'  # Para sesiones tradicionales
app.config['JWT_SECRET_KEY'] = 'tu_clave_secreta_jwt_segura'  # Clave para JWT

CORS(app)
jwt = JWTManager(app)

# Registrar Blueprints
app.register_blueprint(api_productos)
app.register_blueprint(api_pedidos)
app.register_blueprint(api_notificaciones)
app.register_blueprint(api_inicio)
app.register_blueprint(api_notifi_guardadas)
app.register_blueprint(api_ventas)
app.register_blueprint(api_dashboard)
app.register_blueprint(api_prediccion)

# api_login con prefijo /api para separar rutas API y rutas frontend
app.register_blueprint(api_login, url_prefix='/api')

# Rutas frontend / páginas con protección de sesión

@app.route('/')
def index():
    # Redirige a inicio si hay sesión, sino a login
    if 'usuario_id' in session:
        return redirect(url_for('inicio'))
    return redirect(url_for('login'))


@app.route('/login')
def login():
    # Muestra el formulario login solo si no hay sesión activa
    if 'usuario_id' in session:
        return redirect(url_for('inicio'))
    return render_template('index.html')


@app.route('/inicio')
def inicio():
    # Página principal protegida por sesión
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    usuario_id = session['usuario_id']
    nombre = session.get('nombre', '')
    return render_template('inicio.html', usuario_id=usuario_id, nombre=nombre)


@app.route('/notifi_guardadas')
def notificaciones():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    return render_template('notificaciones.html')


@app.route('/productos')
def productos():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    return render_template('inventario.html')


@app.route('/prediccion')
def prediccion():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    return render_template('prediccion.html')


@app.route('/ventas')
def ventas():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    return render_template('ventas.html')


@app.route('/ventas/nueva')
def nueva_venta():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    return render_template('ventas_nueva.html')


@app.route('/productos/agregar')
def agregar_producto():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    return render_template('agregar.html')


@app.route('/productos/editar/<int:id>')
def editar_producto(id):
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    return render_template('editar.html', producto_id=id)


@app.route('/factura/<int:factura_id>')
def ver_factura(factura_id):
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    return render_template('ver_factura.html', factura_id=factura_id)


@app.route('/dashboard_ventas')
def dashboard_ventas():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard_ventas.html')


@app.route('/factura/<int:factura_id>/enviar')
def enviar_factura(factura_id):
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    return render_template('enviar_factura.html', factura_id=factura_id)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
