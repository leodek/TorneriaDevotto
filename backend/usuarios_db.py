import sqlite3
from datetime import datetime

DB_PATH = "mantenimiento.db"

def inicializar_usuarios():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario TEXT NOT NULL UNIQUE,
                contraseña TEXT NOT NULL,
                nombre TEXT NOT NULL,
                rol TEXT NOT NULL,
                imagen TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS log_usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario TEXT,
                accion TEXT,
                fecha TEXT
            )
        """)

def crear_usuario(usuario, contraseña, nombre, rol="usuario", imagen=""):
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("""
                INSERT INTO usuarios (usuario, contraseña, nombre, rol, imagen)
                VALUES (?, ?, ?, ?, ?)
            """, (usuario, contraseña, nombre, rol, imagen))
        return True
    except sqlite3.IntegrityError:
        return False  # Usuario ya existe

def autenticar(usuario, contraseña):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute("""
            SELECT usuario, rol, nombre, imagen
            FROM usuarios
            WHERE usuario = ? AND contraseña = ?
        """, (usuario, contraseña))
        return cursor.fetchone()  # None si no hay coincidencia

def obtener_usuarios():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute("""
            SELECT id, usuario, nombre, rol, imagen
            FROM usuarios
            ORDER BY usuario
        """)
        return cursor.fetchall()

def actualizar_usuario(usuario, nombre=None, contraseña=None, rol=None, imagen=None):
    campos = []
    valores = []

    if nombre:
        campos.append("nombre = ?")
        valores.append(nombre)
    if contraseña:
        campos.append("contraseña = ?")
        valores.append(contraseña)
    if rol:
        campos.append("rol = ?")
        valores.append(rol)
    if imagen is not None:
        campos.append("imagen = ?")
        valores.append(imagen)

    if not campos:
        return False  # Nada que actualizar

    valores.append(usuario)

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(f"""
            UPDATE usuarios SET {", ".join(campos)} WHERE usuario = ?
        """, valores)
        return True

def eliminar_usuario(usuario):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM usuarios WHERE usuario = ?", (usuario,))
        return True

def registrar_accion(usuario, accion):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            INSERT INTO log_usuarios (usuario, accion, fecha)
            VALUES (?, ?, ?)
        """, (usuario, accion, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

def obtener_log():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute("""
            SELECT usuario, accion, fecha
            FROM log_usuarios
            ORDER BY fecha DESC
        """)
        return cursor.fetchall()
