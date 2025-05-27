import mysql.connector
from mysql.connector import pooling
import pymysql

# config
class Config:
    SECRET_KEY = 'tu_clave_secreta_segura'
    JWT_SECRET_KEY = 'tu_clave_jwt_super_segura'


# Crear el pool una sola vez al importar el archivo
dbconfig = {
    "host": "localhost",
    "user": "root",
    "password": "1234",
    "database": "jeandeiben2",
    "pool_name": "mypool",
    "pool_size": 5,
    "pool_reset_session": True,
    "connection_timeout": 30,
    "autocommit": True
}

connection_pool = pooling.MySQLConnectionPool(**dbconfig)

def get_db_connection():
    return connection_pool.get_connection()



