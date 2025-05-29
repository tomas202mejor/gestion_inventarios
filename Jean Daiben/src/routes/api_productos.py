from flask import Blueprint, request, jsonify
import mysql.connector
from db_config import get_db_connection
import logging

# Configurar logging para depuración
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Crear el Blueprint para las rutas de API de productos
api_productos = Blueprint('api_productos', __name__)

# Obtener todos los productos
@api_productos.route('/api/productos', methods=['GET'])
def get_productos():
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Procesar parámetros de consulta opcionales
        tipo = request.args.get('tipo')
        proveedor = request.args.get('proveedor')
        stock_minimo = request.args.get('stock_minimo')
        
        query = "SELECT ProductoID as id, Nombre as nombre, Cantidad as cantidad, Tipo as tipo, Proveedor as proveedor, PrecioVenta as precio_venta, PrecioCompra as precio_compra FROM Productos WHERE 1=1"
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
        logger.error(f"Error de base de datos en get_productos: {e}")
        return jsonify({"error": f"Error de base de datos: {str(e)}"}), 500
    except Exception as e:
        logger.error(f"Error general en get_productos: {e}")
        return jsonify({"error": f"Error interno: {str(e)}"}), 500
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
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT ProductoID as id, Nombre as nombre, Cantidad as cantidad, Tipo as tipo, Proveedor as proveedor, PrecioVenta as precio_venta, PrecioCompra as precio_compra FROM Productos WHERE ProductoID = %s", (id,))
        producto = cursor.fetchone()
        
        if producto:
            return jsonify(producto)
        else:
            return jsonify({"error": "Producto no encontrado"}), 404
            
    except mysql.connector.Error as e:
        logger.error(f"Error de base de datos en get_producto: {e}")
        return jsonify({"error": f"Error de base de datos: {str(e)}"}), 500
    except Exception as e:
        logger.error(f"Error general en get_producto: {e}")
        return jsonify({"error": f"Error interno: {str(e)}"}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# Crear un nuevo producto
@api_productos.route('/api/productos', methods=['POST'])
def crear_producto():
    conn = None
    cursor = None
    try:
        # Log de la solicitud recibida
        logger.debug(f"Recibida solicitud POST: {request.get_json()}")
        
        if not request.is_json:
            return jsonify({"error": "La solicitud debe ser JSON"}), 400
        
        datos = request.get_json()
        logger.debug(f"Datos recibidos: {datos}")
        
        # Validar datos requeridos
        if not datos or not isinstance(datos, dict):
            return jsonify({"error": "Datos inválidos"}), 400
            
        if 'nombre' not in datos or 'cantidad' not in datos:
            return jsonify({"error": "Faltan campos requeridos: nombre y cantidad son obligatorios"}), 400
        
        if not datos['nombre'] or datos['nombre'].strip() == '':
            return jsonify({"error": "El nombre del producto no puede estar vacío"}), 400
            
        try:
            cantidad = int(datos['cantidad'])
            if cantidad < 0:
                return jsonify({"error": "La cantidad no puede ser negativa"}), 400
        except (ValueError, TypeError):
            return jsonify({"error": "La cantidad debe ser un número válido"}), 400
        
        # Conectar a la base de datos
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Preparar los datos para insertar
        nombre = datos['nombre'].strip()
        tipo = datos.get('tipo', 'jeans').strip() if datos.get('tipo') else 'jeans'  # Valor por defecto
        proveedor = datos.get('proveedor', '').strip() if datos.get('proveedor') else None
        precio_venta = datos.get('precio_venta', 0.0)
        precio_compra = datos.get('precio_compra', 0.0)  # NUEVO CAMPO AGREGADO
        
        # Si proveedor está vacío, convertirlo a None
        if proveedor == '':
            proveedor = None
            
        # Validar precios
        try:
            precio_venta = float(precio_venta) if precio_venta is not None else 0.0
            if precio_venta <= 0:
                return jsonify({"error": "El precio de venta debe ser mayor a 0"}), 400
        except (ValueError, TypeError):
            return jsonify({"error": "El precio de venta debe ser un número válido"}), 400
            
        try:
            precio_compra = float(precio_compra) if precio_compra is not None else 0.0
            if precio_compra < 0:
                return jsonify({"error": "El precio de compra no puede ser negativo"}), 400
        except (ValueError, TypeError):
            return jsonify({"error": "El precio de compra debe ser un número válido"}), 400
        
        logger.debug(f"Insertando producto: nombre={nombre}, cantidad={cantidad}, tipo={tipo}, proveedor={proveedor}, precio_venta={precio_venta}, precio_compra={precio_compra}")
        
        # Ejecutar la inserción - INCLUYENDO PrecioCompra
        cursor.execute(
            "INSERT INTO Productos (Nombre, Cantidad, Tipo, Proveedor, PrecioVenta, PrecioCompra) VALUES (%s, %s, %s, %s, %s, %s)",
            (nombre, cantidad, tipo, proveedor, precio_venta, precio_compra)
        )
        conn.commit()
        
        # Obtener el ID del producto recién creado
        producto_id = cursor.lastrowid
        logger.debug(f"Producto creado con ID: {producto_id}")
        
        return jsonify({
            "id": producto_id,
            "nombre": nombre,
            "cantidad": cantidad,
            "tipo": tipo,
            "proveedor": proveedor,
            "precio_venta": precio_venta,
            "precio_compra": precio_compra,  # INCLUIDO EN LA RESPUESTA
            "mensaje": "Producto creado exitosamente"
        }), 201
        
    except mysql.connector.Error as e:
        logger.error(f"Error de MySQL: {e}")
        if conn:
            conn.rollback()
        return jsonify({"error": f"Error de base de datos: {str(e)}"}), 500
    except Exception as e:
        logger.error(f"Error general en crear_producto: {e}")
        if conn:
            conn.rollback()
        return jsonify({"error": f"Error interno del servidor: {str(e)}"}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# Actualizar un producto existente
@api_productos.route('/api/productos/<int:id>', methods=['PUT'])
def actualizar_producto(id):
    conn = None
    cursor = None
    try:
        if not request.is_json:
            return jsonify({"error": "La solicitud debe ser JSON"}), 400
        
        datos = request.get_json()
        logger.debug(f"Actualizando producto {id} con datos: {datos}")
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Verificar si el producto existe
        cursor.execute("SELECT 1 FROM Productos WHERE ProductoID = %s", (id,))
        if not cursor.fetchone():
            return jsonify({"error": "Producto no encontrado"}), 404
        
        # Construir la consulta de actualización
        update_fields = []
        params = []
        
        if 'nombre' in datos and datos['nombre']:
            update_fields.append("Nombre = %s")
            params.append(datos['nombre'].strip())
        
        if 'cantidad' in datos:
            try:
                cantidad = int(datos['cantidad'])
                if cantidad >= 0:
                    update_fields.append("Cantidad = %s")
                    params.append(cantidad)
            except (ValueError, TypeError):
                pass
        
        if 'tipo' in datos:
            tipo = datos['tipo'].strip() if datos['tipo'] else None
            update_fields.append("Tipo = %s")
            params.append(tipo)
        
        if 'proveedor' in datos:
            proveedor = datos['proveedor'].strip() if datos['proveedor'] else None
            update_fields.append("Proveedor = %s")
            params.append(proveedor)
            
        if 'precio_venta' in datos:
            try:
                precio = float(datos['precio_venta'])
                update_fields.append("PrecioVenta = %s")
                params.append(precio)
            except (ValueError, TypeError):
                pass
                
        if 'precio_compra' in datos:  # NUEVO CAMPO AGREGADO
            try:
                precio = float(datos['precio_compra'])
                update_fields.append("PrecioCompra = %s")
                params.append(precio)
            except (ValueError, TypeError):
                pass
        
        if not update_fields:
            return jsonify({"error": "No se proporcionaron campos válidos para actualizar"}), 400
        
        query = f"UPDATE Productos SET {', '.join(update_fields)} WHERE ProductoID = %s"
        params.append(id)
        
        cursor.execute(query, params)
        conn.commit()
        
        # Obtener el producto actualizado
        cursor.execute("SELECT ProductoID as id, Nombre as nombre, Cantidad as cantidad, Tipo as tipo, Proveedor as proveedor, PrecioVenta as precio_venta, PrecioCompra as precio_compra FROM Productos WHERE ProductoID = %s", (id,))
        producto_actualizado = cursor.fetchone()
        
        return jsonify(producto_actualizado)
        
    except mysql.connector.Error as e:
        logger.error(f"Error de MySQL en actualizar_producto: {e}")
        if conn:
            conn.rollback()
        return jsonify({"error": f"Error de base de datos: {str(e)}"}), 500
    except Exception as e:
        logger.error(f"Error general en actualizar_producto: {e}")
        if conn:
            conn.rollback()
        return jsonify({"error": f"Error interno: {str(e)}"}), 500
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
        cursor = conn.cursor()
        
        # Verificar si el producto existe
        cursor.execute("SELECT 1 FROM Productos WHERE ProductoID = %s", (id,))
        if not cursor.fetchone():
            return jsonify({"error": "Producto no encontrado"}), 404
        
        cursor.execute("DELETE FROM Productos WHERE ProductoID = %s", (id,))
        conn.commit()
        
        return jsonify({"mensaje": f"Producto con ID {id} eliminado correctamente"})
        
    except mysql.connector.Error as e:
        logger.error(f"Error de MySQL en eliminar_producto: {e}")
        if conn:
            conn.rollback()
        return jsonify({"error": f"Error de base de datos: {str(e)}"}), 500
    except Exception as e:
        logger.error(f"Error general en eliminar_producto: {e}")
        if conn:
            conn.rollback()
        return jsonify({"error": f"Error interno: {str(e)}"}), 500
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
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT ProductoID as id, Nombre as nombre, Cantidad as cantidad, PrecioVenta as precio_venta, PrecioCompra as precio_compra FROM Productos ORDER BY Nombre")
        productos = cursor.fetchall()
        
        return jsonify(productos)
        
    except mysql.connector.Error as e:
        logger.error(f"Error de MySQL en get_stock_disponible: {e}")
        return jsonify({"error": f"Error de base de datos: {str(e)}"}), 500
    except Exception as e:
        logger.error(f"Error general en get_stock_disponible: {e}")
        return jsonify({"error": f"Error interno: {str(e)}"}), 500
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
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT p.ProductoID as producto_id, p.Nombre as nombre, p.Cantidad as cantidad_actual, 
                   p.PrecioVenta as precio_venta, p.PrecioCompra as precio_compra, 
                   a.NivelBajo as nivel_bajo, a.Fecha as fecha_alerta
            FROM Alertas a
            JOIN Productos p ON a.ProductoID = p.ProductoID
            ORDER BY a.Fecha DESC
        """)
        
        alertas = cursor.fetchall()
        
        return jsonify(alertas)
        
    except mysql.connector.Error as e:
        logger.error(f"Error de MySQL en get_alertas_stock: {e}")
        return jsonify({"error": f"Error de base de datos: {str(e)}"}), 500
    except Exception as e:
        logger.error(f"Error general en get_alertas_stock: {e}")
        return jsonify({"error": f"Error interno: {str(e)}"}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()