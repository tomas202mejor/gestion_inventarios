import tensorflow as tf
import numpy as np

def cargar_modelo(producto_id):
    ruta_modelo = f'predict_demand/modelo_producto_{producto_id}.h5'
    try:
        model = tf.keras.models.load_model(ruta_modelo)
        return model
    except Exception as e:
        print(f"Error al cargar modelo para producto {producto_id}: {e}")
        return None

def predecir_demanda(model, datos_entrada):
    """
    datos_entrada: np.array con forma (1, secuencia, 1)
    """
    if model is None:
        return None

    # Aseguramos que la entrada tiene la forma correcta (batch, timesteps, features)
    if len(datos_entrada.shape) == 2:  # Si falta batch dimension
        datos_entrada = datos_entrada.reshape(1, datos_entrada.shape[0], 1)
    
    prediccion = model.predict(datos_entrada)
    return float(prediccion[0][0])
