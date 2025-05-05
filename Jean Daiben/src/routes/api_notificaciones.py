from flask import Blueprint, jsonify
import mysql.connector
from db_config import get_db_connection 

# Crear Blueprint
api_notificaciones = Blueprint('api_notificaciones', __name__)

# Endpoint para notificar productos con stock bajo
@api_notificaciones.route('/api/notificaciones/stock-bajo', methods=['GET'])
def notificar_stock_bajo():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Nivel mínimo definido para alerta
        nivel_bajo = 10

        cursor.execute("""
            SELECT ProductoID as id, Nombre as nombre, Cantidad as cantidad, Tipo as tipo, Proveedor as proveedor
            FROM Productos
            WHERE Cantidad < %s
        """, (nivel_bajo,))

        productos_bajo_stock = cursor.fetchall()

        return jsonify({
            "stock_bajo": productos_bajo_stock,
            "mensaje": "Productos con stock por debajo del nivel mínimo" if productos_bajo_stock else "Todos los productos tienen stock suficiente"
        })
    except mysql.connector.Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()
