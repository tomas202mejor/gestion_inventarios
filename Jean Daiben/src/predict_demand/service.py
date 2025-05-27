# Importamos la función que entrena el modelo y genera predicciones
from .model import entrenar_y_predecir

# Importamos pandas para trabajar con datos en formato tabular
import pandas as pd

# Importamos el esquema de entrada definido con Pydantic
from .schema import EntradaPrediccion

# Función que procesa una solicitud de predicción de demanda
def procesar_prediccion(request: EntradaPrediccion):
    # Convertimos la lista de objetos Venta (de Pydantic) en una lista de diccionarios,
    # y luego en un DataFrame de Pandas para facilitar el procesamiento
    ventas_df = pd.DataFrame([v.dict() for v in request.ventas])
    
    # Llamamos a la función que entrena el modelo y hace la predicción con los datos
    resultado = entrenar_y_predecir(ventas_df, request.semanas_a_predecir)
    
    # Devolvemos un diccionario con el nombre del producto y las predicciones obtenidas
    return {
        "producto": request.producto,
        "predicciones": resultado
    }


