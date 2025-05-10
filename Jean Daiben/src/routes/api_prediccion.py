from flask import Blueprint, request, jsonify
import os
import sys
import numpy as np
import pandas as pd
from keras.models import load_model
from sklearn.preprocessing import MinMaxScaler
from db_config import get_db_connection

# Añadimos utils al path para poder importar
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'utils')))
from entrenar_modelo_producto import entrenar_modelo_para_producto

# Definimos el blueprint con prefijo /api
api_prediccion = Blueprint('api_prediccion', __name__, url_prefix='/api')

@api_prediccion.route('/prediccion', methods=['POST'])
def prediccion_api():
    producto_id = request.form.get('producto_id')

    if not producto_id:
        return jsonify({'error': 'Producto no especificado'}), 400

    conn = get_db_connection()
    try:
        modelo_path = f'modelos/modelo_producto_{producto_id}.h5'

        # Entrenar si no existe
        if not os.path.exists(modelo_path):
            exito = entrenar_modelo_para_producto(producto_id, conn)
            if not exito:
                return jsonify({'error': 'No hay suficientes datos para entrenar el modelo'}), 400

        # Cargar modelo
        from keras.losses import MeanSquaredError
        modelo = load_model(modelo_path, compile=False)
        modelo.compile(optimizer='adam', loss=MeanSquaredError())

        # Obtener ventas diarias recientes
        query = """
            SELECT Fecha, Cantidad
            FROM Ventas V
            JOIN DetalleVentas DV ON V.VentaID = DV.VentaID
            WHERE DV.ProductoID = %s
            ORDER BY Fecha
        """
        df = pd.read_sql(query, conn, params=(producto_id,))

        if df.empty:
            return jsonify({'error': 'No hay ventas recientes para el producto'}), 400

        df['Fecha'] = pd.to_datetime(df['Fecha'])
        df.set_index('Fecha', inplace=True)
        df = df.resample('D').sum().fillna(0)  # ventas por día

        # Escalado
        scaler = MinMaxScaler()
        datos = scaler.fit_transform(df[['Cantidad']])

        ventana = 7
        if len(datos) < ventana:
            return jsonify({'error': 'No hay suficientes datos recientes para predecir'}), 400

        X_pred = np.array([datos[-ventana:]])
        prediccion = modelo.predict(X_pred)
        valor = float(scaler.inverse_transform(prediccion)[0][0])

        return jsonify({'prediccion': round(valor, 2)})

    except Exception as e:
        print(f"Error durante la predicción: {e}")
        return jsonify({'error': f'Error al obtener la predicción. Detalles: {str(e)}'}), 500

    finally:
        conn.close()
