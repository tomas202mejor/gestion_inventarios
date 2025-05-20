from flask import Blueprint, request, jsonify
import mysql.connector
from mysql.connector import Error
import datetime
from db_config import get_db_connection
import calendar
from datetime import datetime, timedelta

api_dashboard = Blueprint('api_dashboard', __name__)

@api_dashboard.route('/api/dashboard', methods=['GET'])
def obtener_dashboard():
    try:
        estado = request.args.get('estado')
        fecha_inicio = request.args.get('fecha_inicio')
        fecha_fin = request.args.get('fecha_fin')
        metodo_pago = request.args.get('metodo_pago')
        
        # Obtener ventas filtradas
        ventas_result = obtener_ventas_filtradas(estado, fecha_inicio, fecha_fin, metodo_pago)
        ventas = ventas_result.get('ventas', [])
        
        # Obtener estadísticas
        estadisticas = obtener_estadisticas(estado, fecha_inicio, fecha_fin, metodo_pago)
        
        # Obtener datos para el gráfico de ventas
        grafico_ventas = generar_datos_grafico_ventas(fecha_inicio, fecha_fin)
        
        # Obtener datos para el gráfico de métodos de pago
        metodos_pago = obtener_datos_metodos_pago(fecha_inicio, fecha_fin, estado)
        
        return jsonify({
            "ventas": ventas,
            "estadisticas": estadisticas,
            "grafico_ventas": grafico_ventas,
            "metodos_pago": metodos_pago
        })
    except Error as e:
        return jsonify({"error": str(e)}), 500

def obtener_ventas_filtradas(estado=None, fecha_inicio=None, fecha_fin=None, metodo_pago=None):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        query = """
        SELECT v.VentaID, v.Fecha, v.Subtotal, v.Impuestos, v.Total, v.MetodoPago, v.Estado,
               c.Nombre as NombreCliente, c.ClienteID, f.NumeroFactura, f.Estado as EstadoFactura, f.FacturaID,
               (SELECT COUNT(*) FROM DetalleVentas dv WHERE dv.VentaID = v.VentaID) as CantidadProductos
        FROM Ventas v
        JOIN Clientes c ON v.ClienteID = c.ClienteID
        LEFT JOIN Facturas f ON v.VentaID = f.VentaID
        WHERE 1=1
        """
        params = []
        if estado:
            query += " AND v.Estado = %s"
            params.append(estado)
        
        if fecha_inicio:
            query += " AND DATE(v.Fecha) >= %s"
            params.append(fecha_inicio)
        
        if fecha_fin:
            query += " AND DATE(v.Fecha) <= %s"
            params.append(fecha_fin)
            
        if metodo_pago:
            query += " AND v.MetodoPago = %s"
            params.append(metodo_pago)
        
        query += " ORDER BY v.Fecha DESC LIMIT 20"  # Limitamos a las 20 más recientes
        
        cursor.execute(query, params)
        ventas = cursor.fetchall()
        
        for venta in ventas:
            if 'Subtotal' in venta and venta['Subtotal'] is not None:
                venta['Subtotal'] = float(venta['Subtotal'])
            if 'Impuestos' in venta and venta['Impuestos'] is not None:
                venta['Impuestos'] = float(venta['Impuestos'])
            if 'Total' in venta and venta['Total'] is not None:
                venta['Total'] = float(venta['Total'])
            if 'Fecha' in venta and venta['Fecha'] is not None:
                venta['Fecha'] = venta['Fecha'].isoformat()
        
        cursor.close()
        conn.close()
        
        return {"ventas": ventas}
    except Error as e:
        return {"error": str(e), "ventas": []}

def obtener_estadisticas(estado=None, fecha_inicio=None, fecha_fin=None, metodo_pago=None):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        stats_query = """
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN Estado = 'completada' THEN 1 ELSE 0 END) as completadas,
            SUM(CASE WHEN Estado = 'pendiente' THEN 1 ELSE 0 END) as pendientes,
            SUM(CASE WHEN Estado = 'cancelada' THEN 1 ELSE 0 END) as canceladas,
            SUM(CASE WHEN Estado != 'cancelada' THEN Total ELSE 0 END) as total_ventas
        FROM Ventas
        WHERE 1=1
        """
        
        params = []
        
        if estado:
            stats_query += " AND Estado = %s"
            params.append(estado)
        
        if fecha_inicio:
            stats_query += " AND DATE(Fecha) >= %s"
            params.append(fecha_inicio)
        
        if fecha_fin:
            stats_query += " AND DATE(Fecha) <= %s"
            params.append(fecha_fin)
            
        if metodo_pago:
            stats_query += " AND MetodoPago = %s"
            params.append(metodo_pago)
        
        cursor.execute(stats_query, params)
        stats_results = cursor.fetchone()
        
        stats = {
            "total": stats_results['total'],
            "completadas": stats_results['completadas'] or 0,
            "pendientes": stats_results['pendientes'] or 0,
            "canceladas": stats_results['canceladas'] or 0,
            "total_ventas": float(stats_results['total_ventas'] or 0)
        }
        
        cursor.close()
        conn.close()
        
        return stats
    except Error as e:
        return {"error": str(e)}

def generar_datos_grafico_ventas(fecha_inicio=None, fecha_fin=None):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Si no hay fecha de inicio, tomamos los últimos 30 días por defecto
        if not fecha_inicio:
            fecha_inicio = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        # Si no hay fecha de fin, usamos hoy
        if not fecha_fin:
            fecha_fin = datetime.now().strftime('%Y-%m-%d')
        
        # Convertir strings a objetos datetime para cálculos
        start_date = datetime.strptime(fecha_inicio, '%Y-%m-%d')
        end_date = datetime.strptime(fecha_fin, '%Y-%m-%d')
        
        # Calcular la diferencia en días
        days_diff = (end_date - start_date).days + 1
        
        # Decidir el formato basado en la cantidad de días
        if days_diff <= 31:
            # Por día para períodos cortos
            date_format = '%Y-%m-%d'
            group_format = 'YYYY-MM-DD'
            query_group = 'DATE(Fecha)'
            labels_format = '%d/%m'
        elif days_diff <= 90:
            # Por semana para períodos medios
            date_format = '%Y-%U'  # Año-Semana
            group_format = 'YYYY-WW'
            query_group = "CONCAT(YEAR(Fecha), '-', LPAD(WEEK(Fecha), 2, '0'))"
            labels_format = 'Sem %U'
        else:
            # Por mes para períodos largos
            date_format = '%Y-%m'
            group_format = 'YYYY-MM'
            query_group = "DATE_FORMAT(Fecha, '%Y-%m')"
            labels_format = '%b %Y'
        
        # Consulta para obtener ventas por período
        query = f"""
        SELECT {query_group} as periodo, SUM(Total) as total
        FROM Ventas
        WHERE DATE(Fecha) BETWEEN %s AND %s AND Estado != 'cancelada'
        GROUP BY periodo
        ORDER BY periodo
        """
        
        cursor.execute(query, (fecha_inicio, fecha_fin))
        results = cursor.fetchall()
        
        # Convertir resultado a diccionario para facilitar el procesamiento
        data_map = {}
        for row in results:
            periodo = row['periodo']
            if isinstance(periodo, datetime):
                periodo = periodo.strftime(date_format)
            data_map[periodo] = float(row['total'])
        
        # Generar lista de períodos para asegurar que no falte ninguno
        labels = []
        values = []
        
        # Generamos todos los períodos en el rango
        current_date = start_date
        while current_date <= end_date:
            if days_diff <= 31:
                periodo = current_date.strftime(date_format)
                label = current_date.strftime(labels_format)
                current_date += timedelta(days=1)
            elif days_diff <= 90:
                periodo = current_date.strftime(date_format)
                label = current_date.strftime(labels_format)
                # Avanzar a la siguiente semana
                current_date += timedelta(days=7)
            else:
                periodo = current_date.strftime(date_format)
                label = current_date.strftime(labels_format)
                # Avanzar al siguiente mes
                month = current_date.month
                year = current_date.year
                if month == 12:
                    month = 1
                    year += 1
                else:
                    month += 1
                current_date = datetime(year, month, 1)
            
            labels.append(label)
            values.append(data_map.get(periodo, 0))
        
        cursor.close()
        conn.close()
        
        return {
            "labels": labels,
            "values": values
        }
    except Error as e:
        return {"error": str(e), "labels": [], "values": []}

def obtener_datos_metodos_pago(fecha_inicio=None, fecha_fin=None, estado=None):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        query = """
        SELECT 
            MetodoPago, 
            COUNT(*) as cantidad, 
            SUM(Total) as total
        FROM 
            Ventas
        WHERE 
            Estado != 'cancelada'
        """
        
        params = []
        
        if fecha_inicio:
            query += " AND DATE(Fecha) >= %s"
            params.append(fecha_inicio)
        
        if fecha_fin:
            query += " AND DATE(Fecha) <= %s"
            params.append(fecha_fin)
            
        if estado and estado != 'cancelada':
            query += " AND Estado = %s"
            params.append(estado)
        
        query += " GROUP BY MetodoPago ORDER BY total DESC"
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        labels = []
        values = []
        
        for row in results:
            labels.append(row['MetodoPago'].capitalize())
            values.append(float(row['total']))
        
        cursor.close()
        conn.close()
        
        return {
            "labels": labels,
            "values": values
        }
    except Error as e:
        return {"error": str(e), "labels": [], "values": []}

@api_dashboard.route('/api/dashboard/ventas/<int:venta_id>', methods=['GET'])
def obtener_detalle_venta(venta_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
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
        
        for key in ['Subtotal', 'Impuestos', 'Total']:
            if key in venta and venta[key] is not None:
                venta[key] = float(venta[key])
        
        if 'Fecha' in venta and venta['Fecha'] is not None:
            venta['Fecha'] = venta['Fecha'].isoformat()
        
        detalle_query = """
        SELECT dv.DetalleVentaID, dv.ProductoID, p.Nombre as NombreProducto, p.Codigo as CodigoProducto,
               dv.Cantidad, dv.PrecioUnitario, dv.Descuento, dv.Subtotal
        FROM DetalleVentas dv
        JOIN Productos p ON dv.ProductoID = p.ProductoID
        WHERE dv.VentaID = %s
        """
        cursor.execute(detalle_query, (venta_id,))
        detalles = cursor.fetchall()
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

@api_dashboard.route('/api/dashboard/ventas', methods=['GET'])
def obtener_ventas_dashboard():
    result = obtener_ventas_filtradas(
        estado=request.args.get('estado'),
        fecha_inicio=request.args.get('fecha_inicio'),
        fecha_fin=request.args.get('fecha_fin'),
        metodo_pago=request.args.get('metodo_pago')
    )
    return jsonify(result)

@api_dashboard.route('/api/dashboard/metodos-pago', methods=['GET'])
def obtener_resumen_metodos_pago():
    try:
        result = obtener_datos_metodos_pago(
            fecha_inicio=request.args.get('fecha_inicio'),
            fecha_fin=request.args.get('fecha_fin'),
            estado=request.args.get('estado')
        )
        return jsonify({"metodos_pago": result})
    except Error as e:
        return jsonify({"error": str(e)}), 500

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