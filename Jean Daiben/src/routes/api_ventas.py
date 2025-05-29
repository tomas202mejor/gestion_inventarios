from flask import Blueprint, request, jsonify, current_app, render_template, send_from_directory
import mysql.connector
from mysql.connector import Error
import datetime
import pdfkit
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import os
import secrets
import string
from db_config import get_db_connection

# Configuración del blueprint
api_ventas = Blueprint('api_ventas', __name__)

# Configuración de pdfkit con la ruta al ejecutable wkhtmltopdf
# Dependiendo de tu sistema operativo, ajusta esta ruta
# Windows: r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
# Linux/Mac: '/usr/local/bin/wkhtmltopdf' o '/usr/bin/wkhtmltopdf'  # Ajusta esta ruta según tu sistema
config = pdfkit.configuration(wkhtmltopdf=r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe')

# Función para generar números de factura únicos
def generar_numero_factura():
    # Formato: INV-YYYYMMDD-XXXXX (donde XXXXX es un número aleatorio)
    fecha = datetime.datetime.now().strftime('%Y%m%d')
    chars = string.ascii_uppercase + string.digits
    random_string = ''.join(secrets.choice(chars) for _ in range(5))
    return f"INV-{fecha}-{random_string}"

# Función para generar PDF de factura
def generar_pdf_factura(factura_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Obtener datos de la factura
        query = """
        SELECT f.*, v.ClienteID, v.UsuarioID, v.Fecha as FechaVenta, v.MetodoPago,
               c.Nombre as NombreCliente, c.RUC, c.Direccion, c.Telefono, c.Email,
               u.Nombre as NombreVendedor
        FROM Facturas f
        JOIN Ventas v ON f.VentaID = v.VentaID
        JOIN Clientes c ON v.ClienteID = c.ClienteID
        JOIN Usuarios u ON v.UsuarioID = u.UsuarioID
        WHERE f.FacturaID = %s
        """
        cursor.execute(query, (factura_id,))
        factura = cursor.fetchone()
        
        if not factura:
            cursor.close()
            conn.close()
            return None
        
        # Obtener detalles de la venta
        query_detalles = """
        SELECT dv.*, p.Nombre as NombreProducto, p.Codigo
        FROM DetalleVentas dv
        JOIN Productos p ON dv.ProductoID = p.ProductoID
        WHERE dv.VentaID = %s
        """
        cursor.execute(query_detalles, (factura['VentaID'],))
        detalles = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # Preparar datos para la plantilla
        datos_plantilla = {
            'factura': {
                'cliente_nombre': factura['NombreCliente'],
                'cliente_direccion': factura['Direccion'],
                'estado': factura['Estado'],
                'subtotal': factura['Subtotal'],
                'iva': factura['Impuestos'],
                'total': factura['Total']
            },
            'detalles': [],
            'fecha_emision': factura['FechaEmision'].strftime('%d/%m/%Y')
        }
        
        # Preparar detalles para la plantilla
        for detalle in detalles:
            datos_plantilla['detalles'].append({
                'producto_codigo': detalle['Codigo'],
                'producto_nombre': detalle['NombreProducto'],
                'cantidad': detalle['Cantidad'],
                'precio_unitario': detalle['PrecioUnitario'],
                'subtotal': detalle['Subtotal']
            })
        
        # Generar HTML para el PDF
        html_content = render_template(
            'factura_pdf.html',
            **datos_plantilla
        )
        
        # Configurar opciones de pdfkit
        options = {
            'page-size': 'A4',
            'margin-top': '0.75in',
            'margin-right': '0.75in',
            'margin-bottom': '0.75in',
            'margin-left': '0.75in',
            'encoding': 'UTF-8',
        }
        
        # Crear directorio para PDFs si no existe
        pdf_dir = os.path.join(current_app.root_path, 'static', 'pdfs')
        if not os.path.exists(pdf_dir):
            os.makedirs(pdf_dir)
        
        # Ruta del archivo PDF
        pdf_filename = f"factura_{factura_id}_{factura['NumeroFactura']}.pdf"
        pdf_path = os.path.join(pdf_dir, pdf_filename)
        
        # Generar PDF usando la configuración actualizada
        pdfkit.from_string(html_content, pdf_path, options=options, configuration=config)
        
        return pdf_path
    except Error as e:
        current_app.logger.error(f"Error generando PDF: {str(e)}")
        return None
    except Exception as e:
        current_app.logger.error(f"Error inesperado generando PDF: {str(e)}")
        return None

# El resto del código permanece igual
# Ruta para obtener todos los clientes
@api_ventas.route('/api/clientes', methods=['GET'])
def obtener_clientes():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Consulta SQL para obtener clientes activos
        query = "SELECT ClienteID, Nombre, RUC, Telefono, Email, TipoCliente FROM Clientes WHERE Activo = 1"
        cursor.execute(query)
        
        clientes = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return jsonify({"clientes": clientes})
    except Error as e:
        return jsonify({"error": str(e)}), 500

# Ruta para registrar una nueva venta
@api_ventas.route('/api/ventas', methods=['POST'])
def registrar_venta():
    try:
        datos = request.json
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verificar que el cliente exista
        cursor.execute("SELECT ClienteID FROM Clientes WHERE ClienteID = %s AND Activo = 1", 
                      (datos['cliente_id'],))
        cliente = cursor.fetchone()
        if not cliente:
            cursor.close()
            conn.close()
            return jsonify({"error": "Cliente no encontrado o inactivo"}), 400
        
        # Obtener el ID del usuario (para propósitos de demo, usamos ID 1)
        usuario_id = 1  # En un sistema real, esto vendría del sistema de autenticación
        
        # Iniciar transacción
        conn.start_transaction()
        
        # Crear nueva venta
        subtotal = 0
        impuestos = 0
        descuento = datos.get('descuento', 0)
        
        # Crear la venta
        cursor.execute("""
        INSERT INTO Ventas (ClienteID, UsuarioID, Subtotal, Descuento, Impuestos, Total, MetodoPago, Estado)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            datos['cliente_id'],
            usuario_id,
            subtotal,  # Se actualizará después
            descuento,
            impuestos,  # Se actualizará después
            0,  # Se actualizará después
            datos.get('metodo_pago', 'efectivo'),
            'completada'
        ))
        
        venta_id = cursor.lastrowid
        
        # Procesar cada producto de la venta
        for producto in datos['productos']:
            # Verificar stock
            cursor.execute("""
            SELECT ProductoID, Nombre, Cantidad, PrecioVenta 
            FROM Productos 
            WHERE ProductoID = %s AND Activo = 1
            """, (producto['producto_id'],))
            
            producto_db = cursor.fetchone()
            if not producto_db:
                conn.rollback()
                cursor.close()
                conn.close()
                return jsonify({"error": f"Producto con ID {producto['producto_id']} no encontrado o inactivo"}), 400
            
            if producto_db[2] < producto['cantidad']:
                conn.rollback()
                cursor.close()
                conn.close()
                return jsonify({"error": f"Stock insuficiente para el producto {producto_db[1]}"}), 400
            
            # Agregar detalle de venta
            precio_unitario = producto.get('precio', producto_db[3])  # Usar precio proporcionado o el de la BD
            descuento_item = producto.get('descuento', 0)
            subtotal_item = producto['cantidad'] * (precio_unitario - descuento_item)
            
            cursor.execute("""
            INSERT INTO DetalleVentas (VentaID, ProductoID, Cantidad, PrecioUnitario, Descuento, Subtotal)
            VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                venta_id,
                producto['producto_id'],
                producto['cantidad'],
                precio_unitario,
                descuento_item,
                subtotal_item
            ))
            
            # Actualizar stock
            cursor.execute("""
            UPDATE Productos
            SET Cantidad = Cantidad - %s
            WHERE ProductoID = %s
            """, (producto['cantidad'], producto['producto_id']))
            
            # Acumular subtotal
            subtotal += subtotal_item
        
        # Calcular impuestos (IVA 12%)
        impuestos = round(subtotal * 0.12, 2)
        total = subtotal + impuestos - descuento
        
        # Actualizar la venta con los totales
        cursor.execute("""
        UPDATE Ventas
        SET Subtotal = %s, Impuestos = %s, Total = %s
        WHERE VentaID = %s
        """, (subtotal, impuestos, total, venta_id))
        
        # Generar factura
        numero_factura = generar_numero_factura()
        cursor.execute("""
        INSERT INTO Facturas (VentaID, NumeroFactura, Subtotal, Impuestos, Total, Estado)
        VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            venta_id,
            numero_factura,
            subtotal,
            impuestos,
            total,
            'pendiente'  # Cambiado a 'pendiente' hasta que se envíe por correo
        ))
        
        factura_id = cursor.lastrowid
        
        # Confirmar la transacción
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            "mensaje": "Venta registrada correctamente",
            "venta_id": venta_id,
            "factura_id": factura_id
        })
        
    except Error as e:
        if 'conn' in locals() and conn.is_connected():
            conn.rollback()
            cursor.close()
            conn.close()
        return jsonify({"error": str(e)}), 500

@api_ventas.route('/api/facturas/<int:factura_id>', methods=['GET'])
def obtener_factura(factura_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Obtener datos de la factura
        query = """
        SELECT f.*, v.ClienteID, v.UsuarioID, v.Fecha as FechaVenta, v.MetodoPago,
               c.Nombre as NombreCliente, c.RUC, c.Direccion, c.Telefono, c.Email,
               u.Nombre as NombreVendedor
        FROM Facturas f
        JOIN Ventas v ON f.VentaID = v.VentaID
        JOIN Clientes c ON v.ClienteID = c.ClienteID
        JOIN Usuarios u ON v.UsuarioID = u.UsuarioID
        WHERE f.FacturaID = %s
        """
        cursor.execute(query, (factura_id,))
        factura = cursor.fetchone()
        
        if not factura:
            cursor.close()
            conn.close()
            return jsonify({"error": "Factura no encontrada"}), 404
        
        # Obtener detalles de la venta
        query_detalles = """
        SELECT dv.*, p.Nombre as NombreProducto, p.Codigo
        FROM DetalleVentas dv
        JOIN Productos p ON dv.ProductoID = p.ProductoID
        WHERE dv.VentaID = %s
        """
        cursor.execute(query_detalles, (factura['VentaID'],))
        detalles = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # Construir respuesta
        respuesta = {
            "factura": factura,
            "detalles": detalles
        }
        
        return jsonify(respuesta)
    except Error as e:
        return jsonify({"error": str(e)}), 500

# Ruta para servir la vista de factura para el endpoint de envío
@api_ventas.route('/factura/<int:factura_id>/enviar', methods=['GET'])
def vista_enviar_factura(factura_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Obtener datos de la factura
        query = """
        SELECT f.*, v.ClienteID, v.UsuarioID, v.Fecha as FechaVenta, v.MetodoPago,
               c.Nombre as NombreCliente, c.RUC, c.Direccion, c.Telefono, c.Email,
               u.Nombre as NombreVendedor
        FROM Facturas f
        JOIN Ventas v ON f.VentaID = v.VentaID
        JOIN Clientes c ON v.ClienteID = c.ClienteID
        JOIN Usuarios u ON v.UsuarioID = u.UsuarioID
        WHERE f.FacturaID = %s
        """
        cursor.execute(query, (factura_id,))
        factura = cursor.fetchone()
        
        if not factura:
            cursor.close()
            conn.close()
            return render_template('error.html', mensaje="Factura no encontrada"), 404
        
        cursor.close()
        conn.close()
        
        return render_template('enviar_factura.html', factura=factura)
    except Error as e:
        return render_template('error.html', mensaje=f"Error al acceder a la base de datos: {str(e)}"), 500

# Nueva ruta para enviar factura por correo
@api_ventas.route('/api/facturas/<int:factura_id>/enviar', methods=['POST'])
def enviar_factura_api(factura_id):
    try:
        datos = request.json
        email_destino = datos.get('email')
        
        if not email_destino:
            return jsonify({"error": "Se requiere un correo electrónico"}), 400
        
        # Actualizar el email del cliente si es diferente (opcional)
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        query = """
        SELECT f.*, v.ClienteID
        FROM Facturas f
        JOIN Ventas v ON f.VentaID = v.VentaID
        WHERE f.FacturaID = %s
        """
        cursor.execute(query, (factura_id,))
        factura = cursor.fetchone()
        
        if not factura:
            cursor.close()
            conn.close()
            return jsonify({"error": "Factura no encontrada"}), 404
        
        cliente_id = factura['ClienteID']
        
        # Actualizar el email del cliente si se proporciona uno nuevo
        if 'actualizar_cliente' in datos and datos['actualizar_cliente']:
            cursor.execute("""
            UPDATE Clientes
            SET Email = %s
            WHERE ClienteID = %s
            """, (email_destino, cliente_id))
            conn.commit()
            
        # Generar y enviar el PDF
        resultado = generar_pdf_factura(factura_id)
        
        if not resultado:
            cursor.close()
            conn.close()
            return jsonify({"error": "Error al generar el PDF de la factura"}), 500
        
        pdf_path = resultado
        
        # Configuración del correo
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        smtp_user = "jeandaiben12@gmail.com"  # Reemplazar con email real
        smtp_password = "tlyc nfid umfp mrtx"  # Reemplazar con contraseña real
        
        # Crear mensaje
        msg = MIMEMultipart()
        msg['From'] = smtp_user
        msg['To'] = email_destino
        msg['Subject'] = f"Factura #{factura['NumeroFactura']} - Jean Daiben"
        
        # Cuerpo del mensaje
        body = f"""
        Estimado/a cliente,
        
        Gracias por su compra. Adjunto encontrará la factura correspondiente a su compra reciente.
        
        Número de Factura: {factura['NumeroFactura']}
        Fecha: {factura['FechaEmision'].strftime('%d/%m/%Y')}
        Total: ${factura['Total']:.2f}
        
        Si tiene alguna pregunta, no dude en contactarnos.
        
        Saludos cordiales,
        Jean Daiben
        Tienda de Ropa
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Adjuntar PDF
        with open(pdf_path, "rb") as f:
            attachment = MIMEApplication(f.read(), _subtype="pdf")
            attachment.add_header('Content-Disposition', 'attachment', filename=os.path.basename(pdf_path))
            msg.attach(attachment)
        
        # Enviar correo
        try:
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(smtp_user, smtp_password)
            text = msg.as_string()
            server.sendmail(smtp_user, email_destino, text)
            server.quit()
            
            # Actualizar el estado de la factura a "enviada"
            cursor.execute("""
            UPDATE Facturas
            SET Estado = 'enviado'
            WHERE FacturaID = %s
            """, (factura_id,))
            conn.commit()
            
            cursor.close()
            conn.close()
            
            return jsonify({"mensaje": "Factura enviada correctamente por correo electrónico"})
        except Exception as e:
            current_app.logger.error(f"Error al enviar correo: {str(e)}")
            cursor.close()
            conn.close()
            return jsonify({"error": f"Error al enviar el correo electrónico: {str(e)}"}), 500
        
    except Error as e:
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        return jsonify({"error": f"Error inesperado: {str(e)}"}), 500

# Ruta para descargar factura
@api_ventas.route('/api/facturas/<int:factura_id>/descargar', methods=['GET'])
def descargar_factura(factura_id):
    try:
        # Generar el PDF
        pdf_path = generar_pdf_factura(factura_id)
        
        if not pdf_path:
            return jsonify({"error": "Error al generar el PDF de la factura"}), 500
        
        # Obtener datos de la factura para el nombre del archivo
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT NumeroFactura FROM Facturas WHERE FacturaID = %s", (factura_id,))
        factura = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not factura:
            return jsonify({"error": "Factura no encontrada"}), 404
        
        # Obtener el directorio base y el nombre del archivo
        base_dir = os.path.dirname(pdf_path)
        filename = os.path.basename(pdf_path)
        
        # Enviar el archivo como respuesta para descarga
        return send_from_directory(
            directory=base_dir,
            path=filename,
            as_attachment=True,
            download_name=f"factura_{factura['NumeroFactura']}.pdf"
        )
        
    except Exception as e:
        current_app.logger.error(f"Error al descargar la factura: {str(e)}")
        return jsonify({"error": f"Error al descargar la factura: {str(e)}"}), 500

# Ruta para obtener todas las ventas
@api_ventas.route('/api/ventas', methods=['GET'])
def obtener_ventas():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        query = """
        SELECT v.VentaID, v.Fecha, v.Subtotal, v.Impuestos, v.Total, v.MetodoPago, v.Estado,
               c.Nombre as NombreCliente, f.NumeroFactura, f.Estado as EstadoFactura, f.FacturaID
        FROM Ventas v
        JOIN Clientes c ON v.ClienteID = c.ClienteID
        LEFT JOIN Facturas f ON v.VentaID = f.VentaID
        ORDER BY v.Fecha DESC
        """
        cursor.execute(query)
        ventas = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify({"ventas": ventas})
    except Error as e:
        return jsonify({"error": str(e)}), 500

# Ruta para obtener productos
@api_ventas.route('/api/productos', methods=['GET'])
def obtener_productos():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        query = """
        SELECT ProductoID, Codigo, Nombre, Descripcion, Cantidad, PrecioVenta
        FROM Productos
        WHERE Activo = 1 AND Cantidad > 0
        ORDER BY Nombre
        """
        cursor.execute(query)
        productos = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify({"productos": productos})
    except Error as e:
        return jsonify({"error": str(e)}), 500