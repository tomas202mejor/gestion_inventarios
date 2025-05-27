# Importamos BaseModel de Pydantic para definir modelos de datos con validación automática
from pydantic import BaseModel

# Importamos List para definir listas tipadas y date para manejar fechas
from typing import List
from datetime import date

# Definimos el modelo de una venta individual
class Venta(BaseModel):
    fecha: date         # Fecha en la que se realizó la venta
    unidades: int       # Número de unidades vendidas en esa fecha

# Definimos el modelo de entrada que se usará para solicitar una predicción
class EntradaPrediccion(BaseModel):
    producto: str                  # Identificador o nombre del producto
    ventas: List[Venta]            # Lista de ventas históricas del producto
    semanas_a_predecir: int = 4    # Número de semanas hacia el futuro que se desea predecir (valor por defecto: 4)


