# Función para obtener conexión a la base de datos
import mysql.connector
from mysql.connector import pooling
# En db_config.py, modifica la función get_db_connection para incluir parámetros adicionales
def get_db_connection():
    return mysql.connector.connect(
        host='localhost',  # Asegúrate de que esto sea correcto
        user='root',
        password='1234',
        database='jeandeiben2',
        pool_name="mypool",
        pool_size=5,
        # Añade estos parámetros para evitar "MySQL server has gone away"
        pool_reset_session=True,
        connection_timeout=30,
        autocommit=True
    )
