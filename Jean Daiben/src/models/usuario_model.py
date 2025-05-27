from db_config import get_db_connection
from datetime import datetime

def obtener_usuario_por_email(email):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT UsuarioID, Nombre, Rol, ContrasenaHash, Activo FROM Usuarios WHERE Email = %s",
            (email,)
        )
        user = cursor.fetchone()
        return user
    finally:
        cursor.close()
        conn.close()

def actualizar_ultimo_acceso(usuario_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE Usuarios SET UltimoAcceso = %s WHERE UsuarioID = %s",
            (datetime.now(), usuario_id)
        )
        conn.commit()
    finally:
        cursor.close()
        conn.close()
