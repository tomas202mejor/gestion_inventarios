from db_config import get_db_connection
from datetime import datetime

def obtener_usuario_por_email(email):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Usuarios WHERE Email = %s", (email,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return user

def actualizar_ultimo_acceso(usuario_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE Usuarios SET UltimoAcceso = %s WHERE UsuarioID = %s", (datetime.now(), usuario_id))
    conn.commit()
    cursor.close()
    conn.close()

