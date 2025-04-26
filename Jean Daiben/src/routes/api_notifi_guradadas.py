from flask import Blueprint, render_template

# Definir el Blueprint para la página de notificaciones
api_notifi_guradadas = Blueprint('api_notifi_guradadas', __name__)

@api_notifi_guradadas.route('/notificaciones')  # Ruta para la página de notificaciones
def notificaciones():
    return render_template('notificaciones.html')  # Renderiza la plantilla 'notificaciones.html'
