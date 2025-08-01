import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk
import os
import sqlite3
from db_init import get_db_path, conectar



def abrir_modificar_usuario(datos, actualizar_callback=None):
    user_id, usuario_actual, contrasena_actual, nombre_actual, rol_actual, imagen_path_actual = datos

    ventana = tk.Toplevel()
    ventana.title("Modificar Usuario")
    ventana.grab_set()

    for i in range(9):
        ventana.grid_rowconfigure(i, pad=5)
    ventana.grid_columnconfigure(0, pad=5)
    ventana.grid_columnconfigure(1, pad=5)

    tk.Label(ventana, text="Usuario:").grid(row=0, column=0, sticky="e")
    entry_usuario = tk.Entry(ventana, state="disabled")
    entry_usuario.grid(row=0, column=1, sticky="w")
    entry_usuario.insert(0, usuario_actual)

    tk.Label(ventana, text="Nombre:").grid(row=1, column=0, sticky="e")
    entry_nombre = tk.Entry(ventana)
    entry_nombre.grid(row=1, column=1, sticky="w")
    entry_nombre.insert(0, nombre_actual)

    tk.Label(ventana, text="Contraseña:").grid(row=2, column=0, sticky="e")
    entry_contrasena = tk.Entry(ventana, show="*")
    entry_contrasena.grid(row=2, column=1, sticky="w")
    entry_contrasena.insert(0, contrasena_actual)

    tk.Label(ventana, text="Repetir Contraseña:").grid(row=3, column=0, sticky="e")
    entry_repetir = tk.Entry(ventana, show="*")
    entry_repetir.grid(row=3, column=1, sticky="w")
    entry_repetir.insert(0, contrasena_actual)

    tk.Label(ventana, text="Rol:").grid(row=4, column=0, sticky="e")
    combo_rol = ttk.Combobox(ventana, values=["admin", "supervisor", "operario"], state="readonly")
    combo_rol.grid(row=4, column=1, sticky="w")
    combo_rol.set(rol_actual)

    tk.Label(ventana, text="Imagen:").grid(row=5, column=0, sticky="e")
    label_imagen = tk.Label(ventana)
    label_imagen.grid(row=5, column=1, sticky="w")

    imagen_var = tk.StringVar(value=imagen_path_actual if imagen_path_actual else "")

    def cargar_imagen(ruta):
        try:
            img = Image.open(ruta).resize((150, 150))
            imagen_tk = ImageTk.PhotoImage(img)
            label_imagen.configure(image=imagen_tk, text="")
            label_imagen.image = imagen_tk
        except:
            label_imagen.configure(text="No se pudo cargar la imagen", image="")

    if imagen_path_actual and os.path.isfile(imagen_path_actual):
        cargar_imagen(imagen_path_actual)
    else:
        label_imagen.configure(text="Sin imagen", image="")

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
        nuevo_nombre = entry_nombre.get().strip()
        contrasena = entry_contrasena.get().strip()
        repetir = entry_repetir.get().strip()
        nuevo_rol = combo_rol.get().strip()
        imagen_origen = imagen_var.get().strip()

        if not nuevo_nombre or not contrasena:
            messagebox.showerror("Error", "Nombre y Contraseña son obligatorios.", parent=ventana)
            return

        if contrasena != repetir:
            messagebox.showerror("Error", "Las contraseñas no coinciden.", parent=ventana)
            return

        ruta_final = imagen_path_actual
        if imagen_origen != imagen_path_actual and imagen_origen:
            try:
                carpeta_destino = os.path.join("usuarios", "imagenes")
                os.makedirs(carpeta_destino, exist_ok=True)
                ext = os.path.splitext(imagen_origen)[1].lower()
                ruta_final = os.path.join(carpeta_destino, f"{usuario_actual}{ext}")
                with open(imagen_origen, "rb") as origen, open(ruta_final, "wb") as destino:
                    destino.write(origen.read())
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo copiar la imagen:\n{e}", parent=ventana)
                return

        try:
            conn = conectar()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE usuarios 
                SET nombre = ?, contraseña = ?, rol = ?, imagen = ?
                WHERE id = ?
            """, (nuevo_nombre, contrasena, nuevo_rol, ruta_final, user_id))
            conn.commit()
            conn.close()

            messagebox.showinfo("Éxito", "Usuario modificado correctamente.", parent=ventana)
            ventana.destroy()
            if actualizar_callback:
                actualizar_callback()

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo modificar el usuario:\n{e}", parent=ventana)

    tk.Button(ventana, text="Guardar", command=guardar)\
        .grid(row=7, column=1, sticky="e", pady=10)

    def eliminar_usuario():
        confirmar = messagebox.askyesno("Eliminar", "¿Eliminar este usuario?", parent=ventana)
        if not confirmar:
            return
        try:
            conn = conectar()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM usuarios WHERE id = ?", (user_id,))
            conn.commit()
            conn.close()
            messagebox.showinfo("Eliminado", "Usuario eliminado correctamente.", parent=ventana)
            ventana.destroy()
            if actualizar_callback:
                actualizar_callback()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo eliminar el usuario:\n{e}", parent=ventana)

    tk.Button(ventana, text="Eliminar Usuario", command=eliminar_usuario, bg="red", fg="white")\
        .grid(row=8, column=1, sticky="e", pady=5)

    ventana.mainloop()
