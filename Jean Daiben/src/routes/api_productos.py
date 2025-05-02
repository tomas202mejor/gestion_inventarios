from flask import Blueprint, request, jsonify
import mysql.connector
from db_config import get_db_connection  # Importa la función de conexión
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("api_productos.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("api_productos")

# Crear el Blueprint para las rutas de API de productos
api_productos = Blueprint('api_productos', __name__)

# Obtener todos los productos
@api_productos.route('/api/productos', methods=['GET'])
def get_productos():
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        if not conn:
            logger.error("No se pudo conectar a la base de datos")
            return jsonify({"error": "Error de conexión a la base de datos"}), 500
            
        cursor = conn.cursor(dictionary=True)  # Usar dictionary=True para devolver resultados como diccionarios
        
        # Procesar parámetros de consulta opcionales
        tipo = request.args.get('tipo')
        proveedor = request.args.get('proveedor')
        stock_minimo = request.args.get('stock_minimo')
        
        query = "SELECT ProductoID as id, Nombre as nombre, Cantidad as cantidad, Tipo as tipo, Proveedor as proveedor FROM Productos WHERE 1=1"
        params = []
        
        if tipo:
            query += " AND Tipo = %s"
            params.append(tipo)
        
        if proveedor:
            query += " AND Proveedor = %s"
            params.append(proveedor)
        
        if stock_minimo:
            query += " AND Cantidad >= %s"
            params.append(int(stock_minimo))
        
        cursor.execute(query, params)
        productos = cursor.fetchall()
        
        return jsonify(productos)
    except mysql.connector.Error as e:
        logger.error(f"Error de MySQL al obtener productos: {str(e)}")
        return jsonify({"error": f"Error al obtener productos: {str(e)}"}), 500
    except Exception as e:
        logger.error(f"Error inesperado al obtener productos: {str(e)}")
        return jsonify({"error": "Error inesperado al obtener productos"}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# Obtener un producto específico
@api_productos.route('/api/productos/<int:id>', methods=['GET'])
def get_producto(id):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        if not conn:
            logger.error(f"No se pudo conectar a la base de datos al buscar producto {id}")
            return jsonify({"error": "Error de conexión a la base de datos"}), 500
            
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT ProductoID as id, Nombre as nombre, Cantidad as cantidad, Tipo as tipo, Proveedor as proveedor FROM Productos WHERE ProductoID = %s", (id,))
        producto = cursor.fetchone()
        
        if producto:
            return jsonify(producto)
        else:
            return jsonify({"error": "Producto no encontrado"}), 404
    except mysql.connector.Error as e:
        logger.error(f"Error de MySQL al obtener producto {id}: {str(e)}")
        return jsonify({"error": f"Error al obtener producto: {str(e)}"}), 500
    except Exception as e:
        logger.error(f"Error inesperado al obtener producto {id}: {str(e)}")
        return jsonify({"error": "Error inesperado al obtener producto"}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# Crear un nuevo producto
@api_productos.route('/api/productos', methods=['POST'])
def crear_producto():
    if not request.is_json:
        return jsonify({"error": "La solicitud debe ser JSON"}), 400
    
    datos = request.get_json()
    
    # Validar datos requeridos
    if not all(key in datos for key in ['nombre', 'cantidad']):
        return jsonify({"error": "Faltan campos requeridos: nombre y cantidad son obligatorios"}), 400
    
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        if not conn:
            logger.error("No se pudo conectar a la base de datos al crear producto")
            return jsonify({"error": "Error de conexión a la base de datos"}), 500
            
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO Productos (Nombre, Cantidad, Tipo, Proveedor) VALUES (%s, %s, %s, %s)",
            (datos['nombre'], datos['cantidad'], datos.get('tipo'), datos.get('proveedor'))
        )
        conn.commit()
        
        # Obtener el ID del producto recién creado
        producto_id = cursor.lastrowid
        
        return jsonify({
            "id": producto_id,
            "nombre": datos['nombre'],
            "cantidad": datos['cantidad'],
            "tipo": datos.get('tipo'),
            "proveedor": datos.get('proveedor')
        }), 201
    except mysql.connector.Error as e:
        if conn:
            conn.rollback()
        logger.error(f"Error de MySQL al crear producto: {str(e)}")
        return jsonify({"error": f"Error al crear producto: {str(e)}"}), 500
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Error inesperado al crear producto: {str(e)}")
        return jsonify({"error": "Error inesperado al crear producto"}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# Actualizar un producto existente
@api_productos.route('/api/productos/<int:id>', methods=['PUT'])
def actualizar_producto(id):
    if not request.is_json:
        return jsonify({"error": "La solicitud debe ser JSON"}), 400
    
    datos = request.get_json()
    
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        if not conn:
            logger.error(f"No se pudo conectar a la base de datos al actualizar producto {id}")
            return jsonify({"error": "Error de conexión a la base de datos"}), 500
            
        cursor = conn.cursor()
        
        # Verificar si el producto existe
        cursor.execute("SELECT 1 FROM Productos WHERE ProductoID = %s", (id,))
        if not cursor.fetchone():
            return jsonify({"error": "Producto no encontrado"}), 404
        
        # Construir la consulta de actualización
        update_fields = []
        params = []
        
        if 'nombre' in datos:
            update_fields.append("Nombre = %s")
            params.append(datos['nombre'])
        
        if 'cantidad' in datos:
            update_fields.append("Cantidad = %s")
            params.append(datos['cantidad'])
        
        if 'tipo' in datos:
            update_fields.append("Tipo = %s")
            params.append(datos['tipo'])
        
        if 'proveedor' in datos:
            update_fields.append("Proveedor = %s")
            params.append(datos['proveedor'])
        
        if not update_fields:
            return jsonify({"error": "No se proporcionaron campos para actualizar"}), 400
        
        query = f"UPDATE Productos SET {', '.join(update_fields)} WHERE ProductoID = %s"
        params.append(id)
        
        cursor.execute(query, params)
        conn.commit()
        
        return jsonify({
            "mensaje": f"Producto con ID {id} actualizado correctamente",
            "id": id
        })
    except mysql.connector.Error as e:
        if conn:
            conn.rollback()
        logger.error(f"Error de MySQL al actualizar producto {id}: {str(e)}")
        return jsonify({"error": f"Error al actualizar producto: {str(e)}"}), 500
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Error inesperado al actualizar producto {id}: {str(e)}")
        return jsonify({"error": "Error inesperado al actualizar producto"}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# Eliminar un producto
@api_productos.route('/api/productos/<int:id>', methods=['DELETE'])
def eliminar_producto(id):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        if not conn:
            logger.error(f"No se pudo conectar a la base de datos al eliminar producto {id}")
            return jsonify({"error": "Error de conexión a la base de datos"}), 500
            
        cursor = conn.cursor()
        
        # Verificar si el producto existe
        cursor.execute("SELECT 1 FROM Productos WHERE ProductoID = %s", (id,))
        if not cursor.fetchone():
            return jsonify({"error": f"Producto con ID {id} no encontrado"}), 404
        
        cursor.execute("DELETE FROM Productos WHERE ProductoID = %s", (id,))
        
        if cursor.rowcount == 0:
            conn.rollback()
            return jsonify({"error": f"No se pudo eliminar el producto con ID {id}"}), 500
            
        conn.commit()
        return jsonify({"mensaje": f"Producto con ID {id} eliminado correctamente"}), 200
        
    except mysql.connector.Error as e:
        if conn:
            conn.rollback()
        error_code = getattr(e, 'errno', None)
        
        if error_code == 1451:  # Error de clave foránea
            return jsonify({
                "error": f"No se puede eliminar el producto con ID {id} porque está siendo referenciado en otras tablas",
                "code": "FOREIGN_KEY_CONSTRAINT"
            }), 400
        else:
            logger.error(f"Error de MySQL: {str(e)}")
            return jsonify({"error": f"Error de base de datos: {str(e)}"}), 500
            
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Error inesperado: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# Obtener reporte de stock disponible
@api_productos.route('/api/productos/stock', methods=['GET'])
def get_stock_disponible():
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        if not conn:
            logger.error("No se pudo conectar a la base de datos al obtener reporte de stock")
            return jsonify({"error": "Error de conexión a la base de datos"}), 500
            
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT ProductoID as id, Nombre as nombre, Cantidad as cantidad FROM Productos")
        productos = cursor.fetchall()
        
        return jsonify(productos)
    except mysql.connector.Error as e:
        logger.error(f"Error de MySQL al obtener reporte de stock: {str(e)}")
        return jsonify({"error": f"Error al obtener reporte de stock: {str(e)}"}), 500
    except Exception as e:
        logger.error(f"Error inesperado al obtener reporte de stock: {str(e)}")
        return jsonify({"error": "Error inesperado al obtener reporte de stock"}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# Obtener productos con alertas de stock bajo
@api_productos.route('/api/productos/alertas', methods=['GET'])
def get_alertas_stock():
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        if not conn:
            logger.error("No se pudo conectar a la base de datos al obtener alertas de stock")
            return jsonify({"error": "Error de conexión a la base de datos"}), 500
            
        cursor = conn.cursor(dictionary=True)
        
        try:
            cursor.execute("""
                SELECT p.ProductoID as producto_id, p.Nombre as nombre, p.Cantidad as cantidad_actual, 
                       a.NivelBajo as nivel_bajo, a.Fecha as fecha_alerta
                FROM Alertas a
                JOIN Productos p ON a.ProductoID = p.ProductoID
                ORDER BY a.Fecha DESC
            """)
            
            alertas = cursor.fetchall()
            
            return jsonify(alertas)
        except mysql.connector.Error as e:
            # Si la tabla no existe o hay otro error específico de la consulta
            logger.error(f"Error de MySQL al consultar alertas: {str(e)}")
            return jsonify({"error": f"Error al obtener alertas: {str(e)}"}), 500
            
    except mysql.connector.Error as e:
        logger.error(f"Error de MySQL al obtener alertas de stock: {str(e)}")
        return jsonify({"error": f"Error al obtener alertas de stock: {str(e)}"}), 500
    except Exception as e:
        logger.error(f"Error inesperado al obtener alertas de stock: {str(e)}")
        return jsonify({"error": "Error inesperado al obtener alertas de stock"}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# Ruta de prueba para verificar conexión a la base de datos
@api_productos.route('/api/test-db', methods=['GET'])
def test_db_connection():
    try:
        conn = get_db_connection()
        if conn and conn.is_connected():
            conn.close()
            return jsonify({"status": "success", "message": "Conexión exitosa a la base de datos"})
        else:
            return jsonify({"status": "error", "message": "No se pudo conectar a la base de datos"})
    except Exception as e:
        return jsonify({"status": "error", "message": f"Error: {str(e)}"})