from .model import entrenar_y_predecir
import pandas as pd
from .schema import EntradaPrediccion

def procesar_prediccion(request: EntradaPrediccion):
    ventas_df = pd.DataFrame([v.dict() for v in request.ventas])
    resultado = entrenar_y_predecir(ventas_df, request.semanas_a_predecir)
    return {
        "producto": request.producto,
        "predicciones": resultado
    }
