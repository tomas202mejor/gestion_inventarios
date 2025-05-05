from pydantic import BaseModel
from typing import List
from datetime import date

class Venta(BaseModel):
    fecha: date
    unidades: int

class EntradaPrediccion(BaseModel):
    producto: str
    ventas: List[Venta]
    semanas_a_predecir: int = 4
