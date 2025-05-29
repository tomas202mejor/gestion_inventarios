from entrenar_modelo_producto import entrenar_modelo_para_producto 
from model import cargar_modelo, predecir_demanda
import pandas as pd
from db_config import get_db_connection
import numpy as np

def predecir_demanda_producto(producto_id):
    conn = get_db_connection()

    # Entrenar modelo para el producto (puedes condicionar para no entrenar siempre)
    entrenar_modelo_para_producto(producto_id, conn)

    # Cargar modelo entrenado
    model = cargar_modelo(producto_id)
    if model is None:
        return {"error": "No se pudo cargar el modelo."}

    # Consulta para obtener las últimas 6 fechas de ventas (para formar secuencia)
    query = """
        SELECT 
            DATE(V.Fecha) AS Fecha,
            SUM(DV.Cantidad) AS TotalVendido
        FROM DetalleVentas DV
        INNER JOIN Ventas V ON DV.VentaID = V.VentaID
        WHERE DV.ProductoID = %s
        GROUP BY Fecha
        ORDER BY Fecha DESC
        LIMIT 6;
    """
    df = pd.read_sql(query, conn, params=(producto_id,))

    if df.empty or len(df) < 6:
        return {"error": "No hay suficientes datos recientes para hacer la predicción."}

    df['Fecha'] = pd.to_datetime(df['Fecha'])
    # Ordenar ascendente para que la secuencia sea cronológica
    df = df.set_index('Fecha').sort_index()
    # Re-muestrear para agrupar ventas mensuales, si hace falta
    df = df.resample('M').sum().fillna(0)

    serie = df['TotalVendido'].values.astype('float32')
    if len(serie) < 6:
        return {"error": "No hay suficientes datos mensuales para la predicción."}

    # Usar últimos 6 meses para predecir el siguiente
    secuencia_entrada = serie[-6:]

    # Ajustar la entrada para la forma que espera el modelo (batch, timesteps, features)
    secuencia_entrada = secuencia_entrada.reshape((1, 6, 1))

    prediccion = predecir_demanda(model, secuencia_entrada)

    # Si la predicción es un arreglo numpy, obtener el valor escalar
    if isinstance(prediccion, (np.ndarray, list)):
        prediccion = float(prediccion[0])

    return {"prediccion": round(prediccion, 2)}
