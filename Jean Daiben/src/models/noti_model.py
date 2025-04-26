# models/notificaciones.py
from datetime import datetime

class Notificacion:
    def __init__(self, id, mensaje, fecha=None, leida=False):
        self.id = id
        self.mensaje = mensaje
        self.fecha = fecha if fecha else datetime.now()
        self.leida = leida

# Ejemplo de lista de notificaciones en memoria
notificaciones_db = [
    Notificacion(1, "Producto agregado: Jeans Rojo", leida=False),
    Notificacion(2, "Producto editado: Jeans Azul", leida=True),
    Notificacion(3, "Producto eliminado: Jeans Verde", leida=False)
]
