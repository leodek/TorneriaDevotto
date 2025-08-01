import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk
import os
import sqlite3
from db_init import get_db_path, conectar


def abrir_formulario_agregar(actualizar_callback=None):
    ventana = tk.Toplevel()
    ventana.title("Agregar Nuevo Usuario")
    ventana.grab_set()

    # Centrar ventana
    ancho, alto = 300, 400
    pantalla_ancho = ventana.winfo_screenwidth()
    pantalla_alto = ventana.winfo_screenheight()
    x = int((pantalla_ancho / 2) - (ancho / 2))
    y = int((pantalla_alto / 2) - (alto / 2))
    ventana.geometry(f"{ancho}x{alto}+{x}+{y}")

    for i in range(9):
        ventana.grid_rowconfigure(i, pad=5)
    ventana.grid_columnconfigure(0, pad=5)
    ventana.grid_columnconfigure(1, pad=5)

    # Usuario
    tk.Label(ventana, text="Usuario:").grid(row=0, column=0, sticky="e")
    entry_usuario = tk.Entry(ventana)
    entry_usuario.grid(row=0, column=1, sticky="w")

    # Nombre
    tk.Label(ventana, text="Nombre:").grid(row=1, column=0, sticky="e")
    entry_nombre = tk.Entry(ventana)
    entry_nombre.grid(row=1, column=1, sticky="w")

    # Contraseña
    tk.Label(ventana, text="Contraseña:").grid(row=2, column=0, sticky="e")
    entry_contrasena = tk.Entry(ventana, show="*")
    entry_contrasena.grid(row=2, column=1, sticky="w")

    # Repetir Contraseña
    tk.Label(ventana, text="Repetir Contraseña:").grid(row=3, column=0, sticky="e")
    entry_repetir = tk.Entry(ventana, show="*")
    entry_repetir.grid(row=3, column=1, sticky="w")

    # Rol
    tk.Label(ventana, text="Rol:").grid(row=4, column=0, sticky="e")
    combo_rol = ttk.Combobox(ventana, values=["admin", "supervisor", "operario"], state="readonly")
    combo_rol.grid(row=4, column=1, sticky="w")
    combo_rol.set("operario")

    # Imagen
    tk.Label(ventana, text="Imagen:").grid(row=5, column=0, sticky="e")
    label_imagen = tk.Label(ventana, text="Sin imagen")
    label_imagen.grid(row=5, column=1, sticky="w")

    imagen_var = tk.StringVar(value="")

    def cargar_imagen(ruta):
        try:
            img = Image.open(ruta)
            img = img.resize((150, 150))
            imagen_tk = ImageTk.PhotoImage(img)
            label_imagen.configure(image=imagen_tk, text="")
            label_imagen.image = imagen_tk
        except Exception:
            label_imagen.configure(text="No se pudo cargar la imagen", image="")

    def seleccionar_imagen():
        ruta = filedialog.askopenfilename(
            title="Seleccionar imagen",
            filetypes=[("Archivos de imagen", "*.png;*.jpg;*.jpeg;*.gif")]
        )
        if ruta:
            imagen_var.set(ruta)
            cargar_imagen(ruta)

    tk.Button(ventana, text="Seleccionar imagen", command=seleccionar_imagen)\
        .grid(row=6, column=1, sticky="w")

    def guardar():
        usuario = entry_usuario.get().strip()
        nombre = entry_nombre.get().strip()
        contrasena = entry_contrasena.get().strip()
        repetir = entry_repetir.get().strip()
        rol = combo_rol.get().strip()
        imagen_origen = imagen_var.get().strip()

        if not usuario or not nombre or not contrasena or not rol:
            messagebox.showerror("Error", "Todos los campos son obligatorios.", parent=ventana)
            return

        if contrasena != repetir:
            messagebox.showerror("Error", "Las contraseñas no coinciden.", parent=ventana)
            return

        # Procesar imagen
        ruta_destino = ""
        if imagen_origen:
            try:
                carpeta_destino = os.path.join("usuarios", "imagenes")
                os.makedirs(carpeta_destino, exist_ok=True)
                ext = os.path.splitext(imagen_origen)[1].lower()
                ruta_destino = os.path.join(carpeta_destino, f"{usuario}{ext}")
                with open(imagen_origen, "rb") as origen, open(ruta_destino, "wb") as destino:
                    destino.write(origen.read())
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo copiar la imagen:\n{e}", parent=ventana)
                return

        try:
            conn = conectar()
            cursor = conn.cursor()
            query = """
                INSERT INTO usuarios (usuario, nombre, contraseña, rol, imagen)
                VALUES (?, ?, ?, ?, ?)
            """
            cursor.execute(query, (usuario, nombre, contrasena, rol, ruta_destino))
            conn.commit()
            conn.close()

            messagebox.showinfo("Éxito", "Usuario agregado con éxito.", parent=ventana)
            ventana.destroy()

            if actualizar_callback:
                actualizar_callback()

        except Exception as e:
            messagebox.showerror("Error", f"Error al agregar el usuario:\n{e}", parent=ventana)

    tk.Button(ventana, text="Guardar", command=guardar)\
        .grid(row=7, column=1, sticky="e", pady=10)

    ventana.mainloop()
