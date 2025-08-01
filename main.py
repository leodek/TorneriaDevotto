import tkinter as tk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk
import traceback
import os
import sqlite3
import sys  
from datetime import datetime, timedelta
import ctypes
import shutil
import os
from ordenes_trabajo.pestanas import mostrar_ordenes_en_pestanas
from usuarios.lista_usuarios import mostrar_lista_usuarios
from db_init import get_db_path
from db_init import init_db



from typing import Any

class ImageFrame(tk.Frame):
    image: Any 


def conectar():
    db = get_db_path()
    os.makedirs(os.path.dirname(db), exist_ok=True)
    return sqlite3.connect(db, timeout=10)


def crear_tabla_ordenes_trabajo():
    with conectar() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS ordenes_trabajo (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                nro_ot           TEXT,
                cliente          TEXT,
                trabajo          TEXT,
                fecha_ingreso    TEXT,
                insumos          TEXT,
                responsable      TEXT,
                observaciones    TEXT,
                estado           TEXT,
                prioridad        TEXT,
                herramientas     TEXT,
                fecha_estimada   TEXT,
                tiempo_pausado   INTEGER,
                fecha_pausada    INTEGER,
                tiempo_trabajo   INTEGER,
                fecha_iniciado   INTEGER,
                fecha_final      INTEGER,
                imagenes         INTEGER,
                fotos            INTEGER
            )
        """)

def crear_tabla_usuarios():
    with conectar() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario      TEXT UNIQUE NOT NULL,
                nombre       TEXT NOT NULL,
                contraseña   TEXT NOT NULL,
                imagen       TEXT,
                rol          TEXT
            )
            
        """)
        # Inserta el admin solo si no existe
        conn.execute("""
            INSERT OR IGNORE INTO usuarios (id, usuario, nombre, contraseña, imagen, rol)
            VALUES 
                (1, 'admin', 'Administrador', 'admin123', '', 'admin'),
                (2, 'nico.devotto', 'Nicolás', 'nico123', '', 'supervisor')
        """)

def crear_tabla_personal():
    with conectar() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS personal (      
                numero_operario   TEXT PRIMARY KEY,
                nombre_completo   TEXT NOT NULL,
                cargo             TEXT NOT NULL,
                sector            TEXT NOT NULL,
                telefono          TEXT
            )
        """)
def get_db_path():
    
    """
    Devuelve la ruta de la base de datos en un directorio escribible:
    - Si estamos en modo desarrollo (python main.py), apunta a <proyecto>/mantenimiento.db
    - Si estamos en el .exe (PyInstaller), apunta a %APPDATA%\\ManteMoustache\\mantenimiento.db
    """
    if getattr(sys, "frozen", False):
        appdata = os.getenv("APPDATA", os.path.expanduser("~"))
        carpeta_datos = os.path.join(appdata, "ManteMoustache")
        os.makedirs(carpeta_datos, exist_ok=True)
        return os.path.join(carpeta_datos, "mantenimiento.db")
    else:
        return os.path.join(os.path.dirname(__file__), "mantenimiento.db")

def inicializar_bd_si_no_existe():
    r"""
    Si no existe la copia en %APPDATA%, la crea copiándola
    desde el dist\\ManteMoustache (o desde la carpeta local en desarrollo).
    """
    destino = get_db_path()
    if not os.path.isfile(destino):
        if getattr(sys, "frozen", False):
            origen = os.path.join(os.path.dirname(sys.executable), "mantenimiento.db")
        else:
            origen = os.path.join(os.path.dirname(__file__), "mantenimiento.db")
        try:
            shutil.copyfile(origen, destino)
        except Exception as e:
            print("Error copiando la BD a AppData:", e)
            

def main():
    # 1) Inicializar / copiar BD si hace falta
    inicializar_bd_si_no_existe()
    init_db()
    # 2) Crear las tablas 
    crear_tabla_ordenes_trabajo()
    crear_tabla_usuarios()
    crear_tabla_personal()
    # 3) Mostrar el splash, y al cerrarse lanzar el login/app
    mostrar_splash(lambda: mostrar_login(lanzar_app))
    # 4) Iniciar el bucle principal de Tkinter
    root.mainloop()
# ——————————————————————————————
#   CLASE TOOLTIP
# ——————————————————————————————
class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tipwindow = None
        widget.bind("<Enter>", self.show)
        widget.bind("<Leave>", self.hide)
    def show(self, event=None):
        
        if self.tipwindow or not self.text:
            return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 10
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(
            tw, text=self.text, justify=tk.LEFT,
            background="#ffffe0", relief=tk.SOLID, borderwidth=1,
            font=("Arial", 10, "normal")
        )
        label.pack(ipadx=4, ipady=2)
    def hide(self, event=None):
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()
class ToolTipButton(tk.Button):
    tooltip: ToolTip 

from ordenes_trabajo.ordenes_trabajo import mostrar_ordenes_trabajo
from splash import mostrar_splash
from usuarios.lista_usuarios import mostrar_lista_usuarios
from personal.lista_personal import mostrar_lista_personal
from marcar_tarjeta.entrada_salida import configurar_pagina_entrada_salida as mostrar_entrada_salida

DEBUG_FOR_ERROR_TEST = False
USUARIO_ACTUAL = {"usuario": "", "nombre": 
    "", "imagen": "", "rol": ""}

root = tk.Tk()
root.withdraw()

BUTTON_DEFAULT_BG = "#34495e"
BUTTON_ACTIVE_BG = "#90ee90"

# ==============================================
# MEJORA 2: CONFIGURACIÓN INICIAL DE PANTALLA
# ==============================================
def on_close():
    """Restaura la resolución original al cerrar la aplicación"""
    root.destroy()
# Funciones de sesión/flujo

def cerrar_sesion(_=None):
    """
    Oculta la ventana principal y vuelve al login.
    Antes limpia cualquier widget que hubiera para no duplicar al reabrir.
    """
    if messagebox.askyesno("Cerrar sesión", "¿Estás seguro que deseas cerrar sesión?"):
        # Limpiar datos de usuario
        USUARIO_ACTUAL.update({"usuario": "", "nombre": "", "imagen": "", "rol": ""})
        # Ocultar ventana
        root.withdraw()
        # Mostrar login de nuevo
        mostrar_login(lanzar_app)

def salir_app(_=None):
    """
    Sale de la aplicación por completo.
    """
    if messagebox.askyesno("Salir", "¿Deseás salir del sistema?"):
        on_close()
        sys.exit(0)

# Menú lateral con toggle y highlight

def construir_menu_lateral(root, main_frame):
    """Construye el menú lateral con toggle."""
    color_lateral = "#2c3e50"
    color_texto   = "white"

    # Frame del menú (sidebar)
    menu_frame = tk.Frame(root, bg=color_lateral, width=200)
    menu_frame.pack(side="left", fill="y")
    menu_frame.pack_propagate(False)

    # Frame del botón toggle (el “hamburger”)
    toggle_frame = tk.Frame(root, bg=color_lateral, width=20)
    toggle_frame.pack(side="left", fill="y")
    toggle_frame.pack_propagate(False)

    # Lista para exponer los botones si hace falta
    menu_buttons: list[tk.Button] = []

    # Estado del menú
    visible = True

    # Estado inicial del menú (declarado antes de la función)
    menu_visible = True

    # Función que alterna el menú (con 4 espacios de sangría)
    def toggle_menu():
        nonlocal menu_visible
        if menu_visible:
            # Ocultar menú
            menu_frame.pack_forget()
            toggle_btn.config(text="▶")
            toggle_btn.tooltip.text = "Mostrar menú"
        else:
            # Mostrar menú y reasignar orden de los frames
            menu_frame.pack(side="left", fill="y")
            toggle_frame.pack_forget()
            toggle_frame.pack(side="left", fill="y")
            toggle_btn.config(text="✕")
            toggle_btn.tooltip.text = "Ocultar menú"
        # Invertir el estado
        menu_visible = not menu_visible


    # Creación del botón toggle (también sangrado 4 espacios)
    toggle_btn = ToolTipButton(
    toggle_frame,
    text="✕",
    bg=BUTTON_DEFAULT_BG,
    fg=color_texto,
    bd=0,
    font=("Arial", 14),
    command=toggle_menu
)

    toggle_btn.pack(expand=True, fill="both")
    toggle_btn.tooltip = ToolTip(toggle_btn, "Ocultar menú")


    # --- Contenido del menú ---
    # Usuario
    frame_usr = ImageFrame(menu_frame, bg=color_lateral)
    frame_usr.pack(pady=(20, 10))
    ruta = USUARIO_ACTUAL.get("imagen") or "usuarios/imagenes/default_user.png"
    if os.path.isfile(ruta):
        img = Image.open(ruta).resize((180, 180))
        foto = ImageTk.PhotoImage(img)
        tk.Label(frame_usr, image=foto, bg=color_lateral).pack()
        frame_usr.image = foto
    else:
        tk.Label(frame_usr, text="Usuario", fg="white", bg=color_lateral).pack()
    tk.Label(
        frame_usr,
        text=f"{USUARIO_ACTUAL.get('nombre','')}\n({USUARIO_ACTUAL.get('rol','')})",
        fg="white", bg=color_lateral, font=("Arial",10,"bold"), wraplength=180
    ).pack(pady=5)

    # Contenedor de botones
    frame_btns = tk.Frame(menu_frame, bg=color_lateral)
    frame_btns.pack(fill="x", expand=True, pady=(20,10))

    def cargar_vista(func, btn):
        def _():
            try:
                for w in main_frame.winfo_children():
                    w.destroy()
                main_frame.configure(bg="#f0f0f0")
                if DEBUG_FOR_ERROR_TEST:
                    raise Exception(f"Error simulado en {func.__name__}")
                func(main_frame)
                # reseteo estilos
                for b in menu_buttons:
                    b.config(bg=BUTTON_DEFAULT_BG)
                btn.config(bg=BUTTON_ACTIVE_BG)
            except Exception as e:
                traceback.print_exc()
                messagebox.showerror("Error", str(e), parent=root)
        return _

    def boton_menu(parent, texto, vista_func, bold=False):
        font = ("Arial",12,"bold") if bold else ("Arial",12)
        btn = tk.Button(
            parent, text=texto, bg=BUTTON_DEFAULT_BG, fg=color_texto,
            font=font, relief="flat", padx=10, pady=8, width=18
        )
        menu_buttons.append(btn)
        # bind tras añadir a la lista para cerrar bien 'btn'
        btn.config(command=cargar_vista(vista_func, btn))
        btn.pack(pady=4)
        return btn

    # Botones principales
    boton_menu(
    frame_btns, 
    "Entrada/Salida", 
    lambda frame: mostrar_entrada_salida(frame, USUARIO_ACTUAL["rol"])
)
    boton_menu(frame_btns, "Órdenes de Trabajo", mostrar_ordenes_en_pestanas)
    if USUARIO_ACTUAL.get("rol") == "admin":
        boton_menu(frame_btns, "Gestión de Usuarios", mostrar_lista_usuarios)
        boton_menu(frame_btns, "Gestión de Personal", mostrar_lista_personal)


    # Botones de sesión
    frame_ses = tk.Frame(menu_frame, bg=color_lateral)
    frame_ses.pack(side="bottom", fill="x", pady=(0,10))
    boton_menu(frame_ses, "Cerrar Sesión", cerrar_sesion, bold=True)
    boton_menu(frame_ses, "Salir", salir_app, bold=True)

    # Para permitir que lanzar_app active el primero:
    return menu_buttons

# Lanzamiento

def lanzar_app():
    """
    Muestra la ventana principal en FULLSCREEN (sin barra de tareas),
    limpia cualquier widget previo y construye el único menú lateral.
    """
    # 1) Elimino todo lo que hubiera en root
    for w in root.winfo_children():
        w.destroy()


    
    # 3) Hago visible la ventana y la pongo fullscreen
    root.deiconify()
    root.title("Sistema de Mantenimiento Industrial")
    root.attributes("-fullscreen", True)

    # Permito salir del modo fullscreen con ESC (opcional)
    root.bind("<Escape>", lambda e: root.attributes("-fullscreen", False))

    # 4) Creo el frame principal (lado derecho) que contendrá el contenido
    main_frame = tk.Frame(root, bg="#f0f0f0")
    main_frame.pack(side="right", fill="both", expand=True)

    # 5) Construyo el menú lateral ÚNICO (lado izquierdo) con botones
    construir_menu_lateral(root, main_frame)

def mostrar_login(callback):
    win = tk.Toplevel()
    win.title("Inicio de Sesión")
    
    win.configure(bg="#0f223b")
    w, h = 450, 500
    x = (win.winfo_screenwidth() // 2) - (w // 2)
    y = (win.winfo_screenheight() // 2) - (h // 2)
    win.geometry(f"{w}x{h}+{x}+{y}")
    win.resizable(False, False)

    marco = tk.Frame(win, bg="#0f223b")
    marco.pack(padx=20, pady=20, expand=True)

    frame_img = tk.Frame(marco, width=200, height=200, bg="white",
                         highlightthickness=1, highlightbackground="#ccc")
    frame_img.pack(pady=(10,20)); frame_img.pack_propagate(False)
    lbl_img = tk.Label(frame_img, bg="white")
    lbl_img.pack(fill="both", expand=True)

    def actualizar_imagen(event=None):
        u = entry_user.get().strip()
        if not u:
            lbl_img.config(image="", text="")
            return

        # Usar la conexión centralizada que apunta a get_db_path()
        with conectar() as conn:
            r = conn.execute(
                "SELECT imagen FROM usuarios WHERE usuario = ?",
                (u,)
            ).fetchone()

        if r and r[0] and os.path.isfile(r[0]):
            try:
                # Mejor usar el filtro de alta calidad
                img = Image.open(r[0]).resize((200, 200), Image.Resampling.LANCZOS)
                tk_img = ImageTk.PhotoImage(img)
                lbl_img.config(image=tk_img, text="")
                lbl_img.image = tk_img # type: ignore
            except Exception:
                lbl_img.config(image="", text="Error al cargar")
        else:
            lbl_img.config(image="", text="")

    tk.Label(marco, text="Usuario", bg="#0f223b", fg="white", font=("Arial", 12)).pack()
    entry_user = tk.Entry(marco, font=("Arial", 12))
    entry_user.pack(pady=(0, 15))
    entry_user.bind("<KeyRelease>", actualizar_imagen)

    tk.Label(marco, text="Contraseña", bg="#0f223b", fg="white", font=("Arial", 12)).pack()
    entry_pass = tk.Entry(marco, show="*", font=("Arial", 12))
    entry_pass.pack(pady=(0, 20))

    def login(event=None):
        u = entry_user.get().strip()
        p = entry_pass.get().strip()
        with conectar() as conn:
            datos = conn.execute(
                "SELECT usuario, contraseña, rol, imagen, nombre "
                "FROM usuarios WHERE usuario = ? AND contraseña = ?",
                (u, p)
            ).fetchone()
        if datos:
            USUARIO_ACTUAL.update({
                "usuario": datos[0],
                "rol":     datos[2],
                "imagen":  datos[3] or "",
                "nombre":  datos[4] or datos[0]
            })
            win.destroy()
            callback()
        else:
            messagebox.showerror(
                "Error",
                "Usuario o contraseña incorrectos",
                parent=win
            )

    tk.Button(marco, text="Ingresar", font=("Arial", 12), bg="white", fg="#0f223b",
              width=15, command=login).pack()
    win.bind("<Return>", login)
    win.transient()
    win.grab_set()
    win.focus_force()

if __name__ == "__main__":
    main()