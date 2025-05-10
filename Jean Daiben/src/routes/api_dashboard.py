from flask import Blueprint, request, jsonify
import mysql.connector
from mysql.connector import Error
import datetime
from db_config import get_db_connection

# Configuración del blueprint
api_dashboard = Blueprint('api_dashboard', __name__)

# Ruta para obtener todas las ventas con posibles filtros y detalles
@api_dashboard.route('/api/dashboard/ventas', methods=['GET'])
def obtener_ventas_dashboard():
    try:
        # Obtener parámetros de filtro
        estado = request.args.get('estado')
        fecha_inicio = request.args.get('fecha_inicio')
        fecha_fin = request.args.get('fecha_fin')
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Construir la consulta base - Modificada para incluir DetalleVentas
        query = """
        SELECT v.VentaID, v.Fecha, v.Subtotal, v.Impuestos, v.Total, v.MetodoPago, v.Estado,
               c.Nombre as NombreCliente, c.ClienteID, f.NumeroFactura, f.Estado as EstadoFactura, f.FacturaID,
               (SELECT COUNT(*) FROM DetalleVentas dv WHERE dv.VentaID = v.VentaID) as CantidadProductos
        FROM Ventas v
        JOIN Clientes c ON v.ClienteID = c.ClienteID
        LEFT JOIN Facturas f ON v.VentaID = f.VentaID
        WHERE 1=1
        """
        
        # Parámetros para la consulta
        params = []
        
        # Añadir filtros si existen
        if estado:
            query += " AND v.Estado = %s"
            params.append(estado)
        
        if fecha_inicio:
            query += " AND DATE(v.Fecha) >= %s"
            params.append(fecha_inicio)
        
        if fecha_fin:
            query += " AND DATE(v.Fecha) <= %s"
            params.append(fecha_fin)
        
        # Ordenar por fecha descendente
        query += " ORDER BY v.Fecha DESC"
        
        cursor.execute(query, params)
        ventas = cursor.fetchall()
        
        # Para cada venta, obtener detalles de los productos (limitado a primeros 3 para preview)
        for venta in ventas:
            detalle_query = """
            SELECT dv.DetalleVentaID, dv.ProductoID, p.Nombre as NombreProducto, 
                   dv.Cantidad, dv.PrecioUnitario, dv.Descuento, dv.Subtotal
            FROM DetalleVentas dv
            JOIN Productos p ON dv.ProductoID = p.ProductoID
            WHERE dv.VentaID = %s
            LIMIT 3
            """
            cursor.execute(detalle_query, (venta['VentaID'],))
            venta['Detalles'] = cursor.fetchall()
            
            # Convertir valores Decimal a float para serialización JSON
            for key in ['Subtotal', 'Impuestos', 'Total']:
                if key in venta and venta[key] is not None:
                    venta[key] = float(venta[key])
            
            # Convertir fechas a formato ISO
            if 'Fecha' in venta and venta['Fecha'] is not None:
                venta['Fecha'] = venta['Fecha'].isoformat()
        
        # Calcular estadísticas
        # Query para total de ventas completadas/pendientes
        stats_query = """
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN Estado = 'completada' THEN 1 ELSE 0 END) as completadas,
            SUM(CASE WHEN Estado = 'pendiente' THEN 1 ELSE 0 END) as pendientes,
            SUM(CASE WHEN Estado = 'cancelada' THEN 1 ELSE 0 END) as canceladas,
            SUM(CASE WHEN Estado != 'cancelada' THEN Total ELSE 0 END) as total_ventas
        FROM Ventas
        """
        
        # Aplicar los mismos filtros a las estadísticas
        stats_params = []
        stats_where_clauses = []
        
        if estado:
            stats_where_clauses.append("Estado = %s")
            stats_params.append(estado)
        
        if fecha_inicio:
            stats_where_clauses.append("DATE(Fecha) >= %s")
            stats_params.append(fecha_inicio)
        
        if fecha_fin:
            stats_where_clauses.append("DATE(Fecha) <= %s")
            stats_params.append(fecha_fin)
        
        if stats_where_clauses:
            stats_query += " WHERE " + " AND ".join(stats_where_clauses)
        
        cursor.execute(stats_query, stats_params)
        stats_results = cursor.fetchone()
        
        stats = {
            "total": stats_results['total'],
            "completadas": stats_results['completadas'],
            "pendientes": stats_results['pendientes'],
            "canceladas": stats_results['canceladas'],
            "total_ventas": float(stats_results['total_ventas'] or 0)
        }
        
        cursor.close()
        conn.close()
        
        return jsonify({
            "ventas": ventas,
            "estadisticas": stats
        })
    except Error as e:
        return jsonify({"error": str(e)}), 500

# Ruta para obtener resumen por método de pago
@api_dashboard.route('/api/dashboard/metodos-pago', methods=['GET'])
def obtener_resumen_metodos_pago():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        query = """
        SELECT MetodoPago, COUNT(*) as Cantidad, SUM(Total) as Total
        FROM Ventas
        WHERE Estado != 'cancelada'
        GROUP BY MetodoPago
        ORDER BY Total DESC
        """
        
        cursor.execute(query)
        resumen = cursor.fetchall()
        
        # Convertir valores Decimal a float para serialización JSON
        for item in resumen:
            if 'Total' in item and item['Total'] is not None:
                item['Total'] = float(item['Total'])
        
        cursor.close()
        conn.close()
        
        return jsonify({"metodos_pago": resumen})
    except Error as e:
        return jsonify({"error": str(e)}), 500

# Ruta para obtener resumen por estado de factura
@api_dashboard.route('/api/dashboard/estados-factura', methods=['GET'])
def obtener_resumen_estados_factura():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        query = """
        SELECT Estado, COUNT(*) as Cantidad
        FROM Facturas
        GROUP BY Estado
        ORDER BY Cantidad DESC
        """
        
        cursor.execute(query)
        resumen = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify({"estados_factura": resumen})
    except Error as e:
        return jsonify({"error": str(e)}), 500

# Ruta para obtener detalles de una venta específica
@api_dashboard.route('/api/dashboard/ventas/<int:venta_id>', methods=['GET'])
def obtener_detalle_venta(venta_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Obtener información de la venta
        venta_query = """
        SELECT v.VentaID, v.Fecha, v.Subtotal, v.Impuestos, v.Total, v.MetodoPago, v.Estado,
               v.Observaciones, c.ClienteID, c.Nombre as NombreCliente, c.Email as EmailCliente, 
               c.Telefono as TelefonoCliente, f.NumeroFactura, f.Estado as EstadoFactura, f.FacturaID
        FROM Ventas v
        JOIN Clientes c ON v.ClienteID = c.ClienteID
        LEFT JOIN Facturas f ON v.VentaID = f.VentaID
        WHERE v.VentaID = %s
        """
        cursor.execute(venta_query, (venta_id,))
        venta = cursor.fetchone()
        
        if not venta:
            return jsonify({"error": "Venta no encontrada"}), 404
        
        # Convertir valores Decimal a float para serialización JSON
        for key in ['Subtotal', 'Impuestos', 'Total']:
            if key in venta and venta[key] is not None:
                venta[key] = float(venta[key])
        
        # Convertir fechas a formato ISO
        if 'Fecha' in venta and venta['Fecha'] is not None:
            venta['Fecha'] = venta['Fecha'].isoformat()
        
        # Obtener detalles de los productos
        detalle_query = """
        SELECT dv.DetalleVentaID, dv.ProductoID, p.Nombre as NombreProducto, p.Codigo as CodigoProducto,
               dv.Cantidad, dv.PrecioUnitario, dv.Descuento, dv.Subtotal
        FROM DetalleVentas dv
        JOIN Productos p ON dv.ProductoID = p.ProductoID
        WHERE dv.VentaID = %s
        """
        cursor.execute(detalle_query, (venta_id,))
        detalles = cursor.fetchall()
        
        # Convertir valores Decimal a float en los detalles
        for detalle in detalles:
            for key in ['PrecioUnitario', 'Descuento', 'Subtotal']:
                if key in detalle and detalle[key] is not None:
                    detalle[key] = float(detalle[key])
        
        venta['Detalles'] = detalles
        
        cursor.close()
        conn.close()
        
        return jsonify({"venta": venta})
    except Error as e:
        return jsonify({"error": str(e)}), 500