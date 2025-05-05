import pandas as pd
import numpy as np
import mysql.connector
from db_config import get_db_connection
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, LSTM
from tensorflow.keras.callbacks import EarlyStopping
import os

# 1. Conectar a la base de datos y extraer ventas por producto y mes
def obtener_datos_ventas():
    conn = get_db_connection()
    query = """
        SELECT 
            DV.ProductoID,
            DATE_FORMAT(V.Fecha, '%%Y-%%m') AS Mes,
            SUM(DV.Cantidad) AS TotalVendido
        FROM DetalleVentas DV
        INNER JOIN Ventas V ON DV.VentaID = V.VentaID
        GROUP BY DV.ProductoID, Mes
        ORDER BY DV.ProductoID, Mes;
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

# 2. Preparar datos para entrenamiento LSTM
def preparar_datos(df, secuencia=3):
    modelos = {}
    productos = df['ProductoID'].unique()
    for producto in productos:
        df_prod = df[df['ProductoID'] == producto].copy()
        df_prod.set_index('Mes', inplace=True)
        serie = df_prod['TotalVendido'].values.astype('float32')

        if len(serie) < secuencia + 1:
            continue  # no hay suficientes datos

        X, y = [], []
        for i in range(len(serie) - secuencia):
            X.append(serie[i:i+secuencia])
            y.append(serie[i+secuencia])
        X = np.array(X).reshape(-1, secuencia, 1)
        y = np.array(y)

        modelos[producto] = (X, y)
    return modelos

# 3. Entrenar modelo por producto y guardar
def entrenar_y_guardar_modelos(modelos, carpeta_modelos='modelos'):
    os.makedirs(carpeta_modelos, exist_ok=True)
    for producto_id, (X, y) in modelos.items():
        model = Sequential([
            LSTM(50, activation='relu', input_shape=(X.shape[1], 1)),
            Dense(1)
        ])
        model.compile(optimizer='adam', loss='mse')
        model.fit(X, y, epochs=100, verbose=0, callbacks=[EarlyStopping(patience=10, restore_best_weights=True)])

        path = os.path.join(carpeta_modelos, f'modelo_producto_{producto_id}.h5')
        model.save(path)
        print(f"Modelo guardado: {path}")

# 4. Entrenar modelo para un producto específico (para usar desde Flask)
def entrenar_modelo_para_producto(producto_id, conn, secuencia=3, carpeta_modelos='modelos'):
    query = """
        SELECT 
            DATE_FORMAT(V.Fecha, '%%Y-%%m') AS Mes,
            SUM(DV.Cantidad) AS TotalVendido
        FROM DetalleVentas DV
        INNER JOIN Ventas V ON DV.VentaID = V.VentaID
        WHERE DV.ProductoID = %s
        GROUP BY Mes
        ORDER BY Mes;
    """
    df = pd.read_sql(query, conn, params=(producto_id,))
    
    if df.empty or len(df) < secuencia + 1:
        print(f"No hay suficientes datos para entrenar el modelo del producto {producto_id}")
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
    model.compile(optimizer='adam', loss='mse')
    model.fit(X, y, epochs=100, verbose=0, callbacks=[EarlyStopping(patience=10, restore_best_weights=True)])

    os.makedirs(carpeta_modelos, exist_ok=True)
    model.save(os.path.join(carpeta_modelos, f'modelo_producto_{producto_id}.h5'))
    print(f"Modelo entrenado y guardado para producto {producto_id}")
    return True

# 5. Si se ejecuta directamente, entrena todos los modelos
if __name__ == "__main__":
    print("Obteniendo datos de ventas...")
    df = obtener_datos_ventas()
    print("Preparando datos...")
    modelos = preparar_datos(df)
    print("Entrenando modelos...")
    entrenar_y_guardar_modelos(modelos)
    print("¡Modelos entrenados y guardados!")
