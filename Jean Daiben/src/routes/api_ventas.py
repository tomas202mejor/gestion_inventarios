from flask import Blueprint, request, jsonify
import mysql.connector
import logging
from datetime import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import os
import jinja2
import pdfkit 
from db_config import get_db_connection

# Configurar logging para el API de ventas
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("api_productos.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("api_ventas")

api_ventas = Blueprint('api_ventas', __name__)


# Configuración para enviar correos electrónicos
def enviar_factura_por_correo(destinatario, asunto, contenido_html, pdf_factura):
    try:
        # Configuración del servidor de correo (ajustar según su servidor)
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        smtp_usuario = "sistema@tuempresa.com"  # Cambiar por su cuenta de correo
        smtp_password = "tu_contraseña"         # Cambiar por su contraseña

        # Crear mensaje
        mensaje = MIMEMultipart()
        mensaje['From'] = smtp_usuario
        mensaje['To'] = destinatario
        mensaje['Subject'] = asunto

        # Agregar contenido HTML
        mensaje.attach(MIMEText(contenido_html, 'html'))

        # Adjuntar PDF
        with open(pdf_factura, 'rb') as f:
            adjunto = MIMEApplication(f.read(), _subtype="pdf")
            adjunto.add_header('Content-Disposition', 'attachment', filename=os.path.basename(pdf_factura))
            mensaje.attach(adjunto)

        # Conectar al servidor SMTP y enviar
        with smtplib.SMTP(smtp_server, smtp_port) as servidor:
            servidor.starttls()
            servidor.login(smtp_usuario, smtp_password)
            servidor.send_message(mensaje)
            
        logger.info(f"Factura enviada por correo a {destinatario}")
        return True
    except Exception as e:
        logger.error(f"Error al enviar correo: {str(e)}")
        return False

# Generar PDF de factura
def generar_pdf_factura(factura_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Obtener datos de la factura
        cursor.execute("""
            SELECT f.*, c.nombre as cliente_nombre, c.email as cliente_email, c.direccion as cliente_direccion
            FROM facturas f
            JOIN clientes c ON f.cliente_id = c.id
            WHERE f.id = %s
        """, (factura_id,))
        factura = cursor.fetchone()
        
        if not factura:
            logger.error(f"No se encontró la factura con ID {factura_id}")
            return None
            
        # Obtener detalles de la factura
        cursor.execute("""
            SELECT df.*, p.nombre as producto_nombre, p.codigo as producto_codigo
            FROM detalle_factura df
            JOIN productos p ON df.producto_id = p.id
            WHERE df.factura_id = %s
        """, (factura_id,))
        detalles = cursor.fetchall()
        
        conn.close()
        
        # Crear HTML de la factura
        env = jinja2.Environment(loader=jinja2.FileSystemLoader('templates'))
        template = env.get_template('factura.html')
        
        html_factura = template.render(
            factura=factura,
            detalles=detalles,
            fecha_emision=datetime.now().strftime("%d/%m/%Y")
        )
        
        # Generar PDF
        pdf_path = f"facturas/factura_{factura_id}.pdf"
        # Asegurar que existe el directorio
        os.makedirs("facturas", exist_ok=True)
        
        # Generar PDF usando pdfkit (requiere wkhtmltopdf instalado)
        pdfkit.from_string(html_factura, pdf_path)
        
        logger.info(f"PDF de factura generado: {pdf_path}")
        return pdf_path
        
    except Exception as e:
        logger.error(f"Error al generar PDF de factura: {str(e)}")
        return None

# Endpoint para registrar una nueva venta y generar factura
@api_ventas.route('/api/ventas', methods=['POST'])
def registrar_venta():
    try:
        datos = request.get_json()
        
        # Validar datos mínimos necesarios
        if not datos or 'cliente_id' not in datos or 'productos' not in datos:
            return jsonify({'error': 'Datos incompletos'}), 400
            
        # Obtener conexión a la BD
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Iniciar transacción
        cursor.execute("START TRANSACTION")
        
        # Crear factura
        fecha_actual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Calcular total
        total = sum(item['precio'] * item['cantidad'] for item in datos['productos'])
        
        # Insertar factura
        cursor.execute("""
            INSERT INTO facturas (cliente_id, fecha, total, estado) 
            VALUES (%s, %s, %s, 'EMITIDA')
        """, (datos['cliente_id'], fecha_actual, total))
        
        # Obtener ID de la factura
        factura_id = cursor.lastrowid
        
        # Insertar detalles y actualizar inventario
        for item in datos['productos']:
            # Validar stock suficiente
            cursor.execute("SELECT stock FROM productos WHERE id = %s", (item['producto_id'],))
            producto = cursor.fetchone()
            
            if not producto:
                cursor.execute("ROLLBACK")
                conn.close()
                return jsonify({'error': f'Producto con ID {item["producto_id"]} no encontrado'}), 404
                
            if producto['stock'] < item['cantidad']:
                cursor.execute("ROLLBACK")
                conn.close()
                return jsonify({'error': f'Stock insuficiente para producto ID {item["producto_id"]}'}), 400
            
            # Insertar detalle de factura
            cursor.execute("""
                INSERT INTO detalle_factura (factura_id, producto_id, cantidad, precio_unitario, subtotal)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                factura_id, 
                item['producto_id'], 
                item['cantidad'], 
                item['precio'], 
                item['precio'] * item['cantidad']
            ))
            
            # Actualizar stock
            cursor.execute("""
                UPDATE productos 
                SET stock = stock - %s 
                WHERE id = %s
            """, (item['cantidad'], item['producto_id']))
            
        # Confirmar transacción
        cursor.execute("COMMIT")
        
        # Obtener email del cliente
        cursor.execute("SELECT email FROM clientes WHERE id = %s", (datos['cliente_id'],))
        cliente = cursor.fetchone()
        
        conn.close()
        
        # Generar PDF de factura
        pdf_path = generar_pdf_factura(factura_id)
        
        # Enviar por correo si hay email y se generó el PDF
        if cliente and cliente['email'] and pdf_path:
            enviar_factura_por_correo(
                cliente['email'],
                f"Factura #{factura_id} - Jean Daiben",
                f"Adjunto encontrará su factura #{factura_id}. Gracias por su compra.",
                pdf_path
            )
        
        return jsonify({
            'mensaje': 'Venta registrada correctamente',
            'factura_id': factura_id
        }), 201
        
    except mysql.connector.Error as e:
        logger.error(f"Error de MySQL: {str(e)}")
        return jsonify({'error': 'Error en la base de datos'}), 500
        
    except Exception as e:
        logger.error(f"Error al registrar venta: {str(e)}")
        return jsonify({'error': 'Error al procesar la solicitud'}), 500

# Endpoint para obtener una factura por ID
@api_ventas.route('/api/ventas/<int:factura_id>', methods=['GET'])
def obtener_factura(factura_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Obtener datos de la factura
        cursor.execute("""
            SELECT f.*, c.nombre as cliente_nombre, c.email as cliente_email
            FROM facturas f
            JOIN clientes c ON f.cliente_id = c.id
            WHERE f.id = %s
        """, (factura_id,))
        factura = cursor.fetchone()
        
        if not factura:
            conn.close()
            return jsonify({'error': 'Factura no encontrada'}), 404
            
        # Obtener detalles de la factura
        cursor.execute("""
            SELECT df.*, p.nombre as producto_nombre
            FROM detalle_factura df
            JOIN productos p ON df.producto_id = p.id
            WHERE df.factura_id = %s
        """, (factura_id,))
        detalles = cursor.fetchall()
        
        conn.close()
        
        # Preparar respuesta
        return jsonify({
            'factura': factura,
            'detalles': detalles
        }), 200
        
    except Exception as e:
        logger.error(f"Error al obtener factura: {str(e)}")
        return jsonify({'error': 'Error al procesar la solicitud'}), 500

# Endpoint para listar todas las ventas/facturas
@api_ventas.route('/api/ventas', methods=['GET'])
def listar_ventas():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT f.*, c.nombre as cliente_nombre
            FROM facturas f
            JOIN clientes c ON f.cliente_id = c.id
            ORDER BY f.fecha DESC
        """)
        ventas = cursor.fetchall()
        
        conn.close()
        
        return jsonify({'ventas': ventas}), 200
        
    except Exception as e:
        logger.error(f"Error al listar ventas: {str(e)}")
        return jsonify({'error': 'Error al procesar la solicitud'}), 500

# Endpoint para anular una factura
@api_ventas.route('/api/ventas/<int:factura_id>/anular', methods=['PUT'])
def anular_factura(factura_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Verificar que la factura existe
        cursor.execute("SELECT * FROM facturas WHERE id = %s", (factura_id,))
        factura = cursor.fetchone()
        
        if not factura:
            conn.close()
            return jsonify({'error': 'Factura no encontrada'}), 404
            
        if factura['estado'] == 'ANULADA':
            conn.close()
            return jsonify({'error': 'La factura ya está anulada'}), 400
            
        # Iniciar transacción
        cursor.execute("START TRANSACTION")
        
        # Actualizar estado de la factura
        cursor.execute("""
            UPDATE facturas
            SET estado = 'ANULADA'
            WHERE id = %s
        """, (factura_id,))
        
        # Restaurar stock de productos
        cursor.execute("""
            UPDATE productos p
            JOIN detalle_factura df ON p.id = df.producto_id
            SET p.stock = p.stock + df.cantidad
            WHERE df.factura_id = %s
        """, (factura_id,))
        
        # Confirmar transacción
        cursor.execute("COMMIT")
        
        conn.close()
        
        return jsonify({'mensaje': 'Factura anulada correctamente'}), 200
        
    except Exception as e:
        logger.error(f"Error al anular factura: {str(e)}")
        try:
            cursor.execute("ROLLBACK")
        except:
            pass
        return jsonify({'error': 'Error al procesar la solicitud'}), 500

# Endpoint para reenviar factura por correo
@api_ventas.route('/api/ventas/<int:factura_id>/enviar', methods=['POST'])
def reenviar_factura(factura_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Verificar que la factura existe
        cursor.execute("""
            SELECT f.*, c.email as cliente_email
            FROM facturas f
            JOIN clientes c ON f.cliente_id = c.id
            WHERE f.id = %s
        """, (factura_id,))
        factura = cursor.fetchone()
        
        conn.close()
        
        if not factura:
            return jsonify({'error': 'Factura no encontrada'}), 404
            
        if not factura['cliente_email']:
            return jsonify({'error': 'El cliente no tiene correo electrónico registrado'}), 400
            
        # Generar PDF de la factura
        pdf_path = generar_pdf_factura(factura_id)
        
        if not pdf_path:
            return jsonify({'error': 'Error al generar la factura PDF'}), 500
            
        # Enviar por correo
        result = enviar_factura_por_correo(
            factura['cliente_email'],
            f"Factura #{factura_id} - Jean Daiben",
            f"Adjunto encontrará su factura #{factura_id}. Gracias por su compra.",
            pdf_path
        )
        
        if result:
            return jsonify({'mensaje': 'Factura enviada correctamente'}), 200
        else:
            return jsonify({'error': 'Error al enviar la factura por correo'}), 500
            
    except Exception as e:
        logger.error(f"Error al reenviar factura: {str(e)}")
        return jsonify({'error': 'Error al procesar la solicitud'}), 500