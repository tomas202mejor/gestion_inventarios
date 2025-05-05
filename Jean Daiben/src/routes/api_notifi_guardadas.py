from flask import Blueprint, render_template

# Definir el Blueprint para la página de notificaciones
api_notifi_guardadas = Blueprint('api_notifi_guardadas', __name__)

@api_notifi_guardadas.route('/notificaciones')  # Ruta para la página de notificaciones
def notificaciones():
    return render_template('notificaciones.html')  # Renderiza la plantilla 'notificaciones.html'
