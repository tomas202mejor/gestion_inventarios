from flask import Blueprint, render_template

# Nombre corregido (agrega la 'd' faltante en "guardadas")
api_notifi_guardadas = Blueprint('api_notifi_guardadas', __name__)

@api_notifi_guardadas.route('/notificaciones')
def notificaciones():
    return render_template('notificaciones.html')