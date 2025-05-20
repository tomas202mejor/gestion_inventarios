from flask import Blueprint, request, jsonify
import mysql.connector
from db_config import get_db_connection  # Importa la función de conexión

# Crear el Blueprint para las rutas de API de productos
api_productos = Blueprint('api_productos', __name__)

# Obtener todos los productos
@api_productos.route('/api/productos', methods=['GET'])
def get_productos():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)  # Usar dictionary=True para devolver resultados como diccionarios
    
    # Procesar parámetros de consulta opcionales
    tipo = request.args.get('tipo')
    proveedor = request.args.get('proveedor')
    stock_minimo = request.args.get('stock_minimo')
    
    query = "SELECT ProductoID as id, Nombre as nombre, Cantidad as cantidad, Tipo as tipo, Proveedor as proveedor, PrecioVenta as precio_venta FROM Productos WHERE 1=1"
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
    
    cursor.close()
    conn.close()
    
    return jsonify(productos)

# Obtener un producto específico
@api_productos.route('/api/productos/<int:id>', methods=['GET'])
def get_producto(id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT ProductoID as id, Nombre as nombre, Cantidad as cantidad, Tipo as tipo, Proveedor as proveedor, PrecioVenta as precio_venta FROM Productos WHERE ProductoID = %s", (id,))
    producto = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    if producto:
        return jsonify(producto)
    else:
        return jsonify({"error": "Producto no encontrado"}), 404

# Crear un nuevo producto
@api_productos.route('/api/productos', methods=['POST'])
def crear_producto():
    if not request.is_json:
        return jsonify({"error": "La solicitud debe ser JSON"}), 400
    
    datos = request.get_json()
    
    # Validar datos requeridos
    if not all(key in datos for key in ['nombre', 'cantidad']):
        return jsonify({"error": "Faltan campos requeridos: nombre y cantidad son obligatorios"}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "INSERT INTO Productos (Nombre, Cantidad, Tipo, Proveedor, PrecioVenta) VALUES (%s, %s, %s, %s, %s)",
            (datos['nombre'], datos['cantidad'], datos.get('tipo'), datos.get('proveedor'), datos.get('precio_venta', 0))
        )
        conn.commit()
        
        # Obtener el ID del producto recién creado
        producto_id = cursor.lastrowid
        
        return jsonify({
            "id": producto_id,
            "nombre": datos['nombre'],
            "cantidad": datos['cantidad'],
            "tipo": datos.get('tipo'),
            "proveedor": datos.get('proveedor'),
            "precio_venta": datos.get('precio_venta', 0)
        }), 201
    except mysql.connector.Error as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# Actualizar un producto existente
@api_productos.route('/api/productos/<int:id>', methods=['PUT'])
def actualizar_producto(id):
    if not request.is_json:
        return jsonify({"error": "La solicitud debe ser JSON"}), 400
    
    datos = request.get_json()
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
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
            
        if 'precio_venta' in datos:
            update_fields.append("PrecioVenta = %s")
            params.append(datos['precio_venta'])
        
        if not update_fields:
            return jsonify({"error": "No se proporcionaron campos para actualizar"}), 400
        
        query = f"UPDATE Productos SET {', '.join(update_fields)} WHERE ProductoID = %s"
        params.append(id)
        
        cursor.execute(query, params)
        conn.commit()
        
        # Obtener el producto actualizado
        cursor.execute("SELECT ProductoID as id, Nombre as nombre, Cantidad as cantidad, Tipo as tipo, Proveedor as proveedor, PrecioVenta as precio_venta FROM Productos WHERE ProductoID = %s", (id,))
        producto_actualizado = cursor.fetchone()
        
        return jsonify(producto_actualizado)
    except mysql.connector.Error as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# Eliminar un producto
@api_productos.route('/api/productos/<int:id>', methods=['DELETE'])
def eliminar_producto(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Verificar si el producto existe
        cursor.execute("SELECT 1 FROM Productos WHERE ProductoID = %s", (id,))
        if not cursor.fetchone():
            return jsonify({"error": "Producto no encontrado"}), 404
        
        cursor.execute("DELETE FROM Productos WHERE ProductoID = %s", (id,))
        conn.commit()
        
        return jsonify({"mensaje": f"Producto con ID {id} eliminado correctamente"})
    except mysql.connector.Error as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# Obtener reporte de stock disponible
@api_productos.route('/api/productos/stock', methods=['GET'])
def get_stock_disponible():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # En MySQL se debe llamar a un procedimiento almacenado diferente
        cursor.execute("SELECT ProductoID as id, Nombre as nombre, Cantidad as cantidad, PrecioVenta as precio_venta FROM Productos")
        productos = cursor.fetchall()
        
        return jsonify(productos)
    except mysql.connector.Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# Obtener productos con alertas de stock bajo
@api_productos.route('/api/productos/alertas', methods=['GET'])
def get_alertas_stock():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT p.ProductoID as producto_id, p.Nombre as nombre, p.Cantidad as cantidad_actual, 
                   p.PrecioVenta as precio_venta, a.NivelBajo as nivel_bajo, a.Fecha as fecha_alerta
            FROM Alertas a
            JOIN Productos p ON a.ProductoID = p.ProductoID
            ORDER BY a.Fecha DESC
        """)
        
        alertas = cursor.fetchall()
        
        return jsonify(alertas)
    except mysql.connector.Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()