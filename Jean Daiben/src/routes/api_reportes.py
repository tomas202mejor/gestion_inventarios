from flask import Blueprint, request, jsonify, send_file
import datetime
import secrets
import string
import io
import openpyxl
from db_config import get_db_connection

api_reportes = Blueprint('api_reportes', __name__)

def generar_codigo_reportes():
    fecha = datetime.datetime.now().strftime('%Y%m%d')
    chars = string.ascii_uppercase + string.digits
    random_string = ''.join(secrets.choice(chars) for _ in range(5))
    return f"INV-{fecha}-{random_string}"

def generar_excel(titulo, labels, data):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Reporte"
    ws.append([titulo])
    ws.append([])
    ws.append(["Categoría", "Valor"])
    for label, value in zip(labels, data):
        ws.append([label, value])
    archivo = io.BytesIO()
    wb.save(archivo)
    archivo.seek(0)
    return archivo

# Función común para obtener datos según tipo
def obtener_datos_reporte(tipo, cursor):
    if tipo == 'stock':
        cursor.execute("SELECT Nombre, Cantidad FROM Productos")
        resultados = cursor.fetchall()
        return [row['Nombre'] for row in resultados], [row['Cantidad'] for row in resultados]

    elif tipo == 'ventas':
        cursor.execute("SELECT Estado, COUNT(*) as Total FROM Ventas GROUP BY Estado")
        resultados = cursor.fetchall()
        return [row['Estado'] for row in resultados], [row['Total'] for row in resultados]

    else:
        return None, None

# API para datos
@api_reportes.route('/api/reportes/<tipo>', methods=['GET'])
def generar_reporte(tipo):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        labels, data = obtener_datos_reporte(tipo, cursor)
        if labels is None:
            return jsonify({'error': 'Tipo de reporte no válido'}), 400

        return jsonify({
            'codigo_reporte': generar_codigo_reportes(),
            'labels': labels,
            'data': data
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

    finally:
        if conn:
            cursor.close()
            conn.close()

# API para descarga en Excel
@api_reportes.route('/api/reportes/<tipo>/excel', methods=['GET'])
def descargar_excel(tipo):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        labels, data = obtener_datos_reporte(tipo, cursor)
        if labels is None:
            return jsonify({'error': 'Tipo de reporte no válido'}), 400

        archivo = generar_excel(f"Reporte {tipo.capitalize()}", labels, data)
        filename = f"reporte-{tipo}.xlsx"

        return send_file(
            archivo,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    except Exception as e:
        return jsonify({'error': str(e)}), 500

    finally:
        if conn:
            cursor.close()
            conn.close()
