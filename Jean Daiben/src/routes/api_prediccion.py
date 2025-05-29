from flask import Blueprint, request, jsonify
import os
import sys
import numpy as np
import pandas as pd
from keras.models import load_model
from keras.losses import MeanSquaredError
from db_config import get_db_connection

# Añadir carpeta utils al path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'utils')))
from entrenar_modelo_producto import entrenar_modelo_para_producto

# Definir blueprint
api_prediccion = Blueprint('api_prediccion', __name__, url_prefix='/api')

@api_prediccion.route('/prediccion', methods=['POST'])
def prediccion_api():
    # Leer producto_id desde JSON correctamente
    data = request.get_json()
    print("request.get_json():", data)

    producto_id = data.get('producto_id') if data else None
    print(f"producto_id recibido: {producto_id}")

    if not producto_id:
        return jsonify({'error': 'Producto no especificado'}), 400

    conn = get_db_connection()

    try:
        # Ruta del modelo
        modelo_dir = 'predict_demand'
        modelo_path = os.path.join(modelo_dir, f'modelo_producto_{producto_id}.h5')

        # Entrenar modelo si no existe
        if not os.path.exists(modelo_path):
            exito = entrenar_modelo_para_producto(producto_id, conn, carpeta_modelos=modelo_dir)
            if not exito:
                return jsonify({'error': 'No hay suficientes datos para entrenar el modelo'}), 400

        # Cargar modelo
        modelo = load_model(modelo_path, compile=False)
        modelo.compile(optimizer='adam', loss=MeanSquaredError())

        # Obtener ventas mensuales recientes
        query = """
            SELECT 
                DATE(V.Fecha) AS Fecha,
                SUM(DV.Cantidad) AS TotalVendido
            FROM DetalleVentas DV
            INNER JOIN Ventas V ON DV.VentaID = V.VentaID
            WHERE DV.ProductoID = %s
            GROUP BY Fecha
            ORDER BY Fecha;
        """
        df = pd.read_sql(query, conn, params=(producto_id,))

        if df.empty:
            return jsonify({'error': 'No hay ventas recientes para el producto'}), 400

        # Preprocesamiento
        df['Fecha'] = pd.to_datetime(df['Fecha'])
        df.set_index('Fecha', inplace=True)
        df = df.resample('M').sum().fillna(0)

        secuencia = 6
        if len(df) < secuencia:
            return jsonify({'error': 'No hay suficientes datos recientes para predecir'}), 400

        serie = df['TotalVendido'].values.astype('float32')
        datos_entrada = serie[-secuencia:].reshape(1, secuencia, 1)

        prediccion = modelo.predict(datos_entrada)
        valor = float(prediccion[0][0])

        return jsonify({'prediccion': round(valor, 2)})

    except Exception as e:
        print(f"Error durante la predicción: {e}")
        return jsonify({'error': f'Error al obtener la predicción. Detalles: {str(e)}'}), 500

    finally:
        conn.close()
