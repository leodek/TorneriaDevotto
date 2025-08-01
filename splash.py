# splash.py
import os
import sys
import tkinter as tk
from PIL import Image, ImageTk

def mostrar_splash(callback, duracion=2000):
    # Ventana sin bordes
    splash = tk.Toplevel()
    splash.overrideredirect(True)

    # --- aquí cambiamos ---
    if getattr(sys, "frozen", False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(__file__)
    img_path = os.path.join(base, "splash.png")
    # -----------------------

    if not os.path.isfile(img_path):
        raise FileNotFoundError(f"No se encontró la imagen de splash: {img_path}")

    img = Image.open(img_path)
    ancho, alto = img.size

    # Centrar en pantalla
    sw = splash.winfo_screenwidth()
    sh = splash.winfo_screenheight()
    x = (sw - ancho) // 2
    y = (sh - alto) // 2
    splash.geometry(f"{ancho}x{alto}+{x}+{y}")

    # Mostrar la imagen y mantener la referencia
    photo = ImageTk.PhotoImage(img)
    label = tk.Label(splash, image=photo)
    label.pack(fill="both", expand=True)
    splash.image = photo

    # Cerrar y continuar tras 'duracion' milisegundos
    splash.after(duracion, lambda: _close_and_continue(splash, callback))

def _close_and_continue(splash, callback):
    splash.destroy()
    callback()
