from flask import Blueprint, render_template

# Definir el Blueprint para la página de inicio
api_inicio = Blueprint('api_inicio', __name__)

@api_inicio.route('/inicio')  # Ruta para la página de inicio
def inicio():
    return render_template('inicio.html')  # Renderiza la plantilla 'inicio.html'


