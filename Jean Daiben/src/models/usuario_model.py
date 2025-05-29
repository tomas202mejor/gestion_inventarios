from db_config import get_db_connection
from datetime import datetime

def obtener_usuario_por_email(email):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT UsuarioID, Nombre, Email, Rol, ContrasenaHash, Activo, UltimoAcceso FROM Usuarios WHERE Email = %s",
            (email,)
        )
        user = cursor.fetchone()
        return user
    finally:
        cursor.close()
        conn.close()

def crear_usuario(nombre, email, contrasena_hash, rol):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO Usuarios (Nombre, Email, ContrasenaHash, Rol, Activo) "
            "VALUES (%s, %s, %s, %s, 1)",
            (nombre, email, contrasena_hash, rol)
        )
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"Error al crear usuario: {e}")
        return False
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