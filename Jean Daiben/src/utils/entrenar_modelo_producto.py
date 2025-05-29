import pandas as pd
import numpy as np
import os
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, LSTM
from tensorflow.keras.callbacks import EarlyStopping
from tensorflow.keras.losses import MeanSquaredError

def entrenar_modelo_para_producto(producto_id, conn, secuencia=6, carpeta_modelos='predict_demand'):
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
        print(f"No hay datos para entrenar el modelo del producto {producto_id}")
        return False

    df['Fecha'] = pd.to_datetime(df['Fecha'])
    df.set_index('Fecha', inplace=True)
    df = df.resample('M').sum().fillna(0)  # Agrupamos por mes

    if len(df) <= 0:
        print(f"No hay datos mensuales para entrenar el modelo del producto {producto_id}")
        return False

    promedio_mensual = df['TotalVendido'].mean()
    print(f"Promedio mensual para el producto {producto_id}: {promedio_mensual:.2f} unidades")

    if len(df) < secuencia + 1:
        print(f"No hay suficientes datos para entrenar la secuencia LSTM para producto {producto_id}")
        return False

    serie = df['TotalVendido'].values.astype('float32')
    X, y = [], []
    for i in range(len(serie) - secuencia):
        X.append(serie[i:i+secuencia])
        y.append(serie[i+secuencia])
    X = np.array(X).reshape(-1, secuencia, 1)
    y = np.array(y)

    model = Sequential([
        LSTM(50, activation='relu', input_shape=(X.shape[1], 1)),
        Dense(1)
    ])
    model.compile(optimizer='adam', loss=MeanSquaredError())
    model.fit(X, y, epochs=100, verbose=0, callbacks=[EarlyStopping(patience=10, restore_best_weights=True)])

    os.makedirs(carpeta_modelos, exist_ok=True)
    modelo_path = os.path.join(carpeta_modelos, f'modelo_producto_{producto_id}.h5')
    model.save(modelo_path)

    print(f"Modelo mensual entrenado y guardado para producto {producto_id} en {modelo_path}")
    return True
