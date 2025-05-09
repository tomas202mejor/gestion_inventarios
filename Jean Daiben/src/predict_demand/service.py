from .model import entrenar_y_predecir
import pandas as pd
from .schema import EntradaPrediccion

def procesar_prediccion(request: EntradaPrediccion):
    # Convertir los datos de las ventas en un DataFrame
    ventas_df = pd.DataFrame([v.dict() for v in request.ventas])
    
    # Llamar a la función de predicción
    resultado = entrenar_y_predecir(ventas_df, request.semanas_a_predecir)
    
    return {
        "producto": request.producto,
        "predicciones": resultado
    }

