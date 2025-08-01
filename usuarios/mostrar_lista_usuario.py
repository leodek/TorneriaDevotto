from usuarios.lista_usuarios import mostrar_lista_usuarios
import sqlite3
from db_init import get_db_path

conn = sqlite3.connect(get_db_path())

def mostrar_lista_usuarios(frame):
    """
    Wrapper para usar desde el menú principal
    """
    mostrar_lista_usuarios(frame)
