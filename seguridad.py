from functools import wraps
from tkinter import messagebox

# variable global donde guardaremos el usuario actual
USUARIO_ACTUAL = {"usuario": None, "rol": None}

def establecer_usuario(nombre, rol):
    USUARIO_ACTUAL["usuario"] = nombre
    USUARIO_ACTUAL["rol"] = rol

def requiere_permiso(roles_permitidos):
    def decorador(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if USUARIO_ACTUAL["rol"] in roles_permitidos:
                return func(*args, **kwargs)
            messagebox.showerror(
                "Permiso denegado",
                "No tienes privilegios para realizar esta acción."
            )
        return wrapper
    return decorador
