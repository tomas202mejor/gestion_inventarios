from pydantic import BaseModel
from typing import List
from datetime import date

class Venta(BaseModel):
    fecha: date
    unidades: int

class EntradaPrediccion(BaseModel):
    producto_id: int             # Ahora es producto_id tipo int
    ventas: List[Venta] = []     # Opcional, puede venir vacío si solo usas base datos
    semanas_a_predecir: int = 4
