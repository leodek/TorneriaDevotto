import tkinter as tk
from tkinter import messagebox
import sqlite3

from db_init import get_db_path, conectar



def abrir_formulario_agregar_personal(actualizar_callback=None):
    ventana = tk.Toplevel()
    ventana.title("Agregar Personal")
    ventana.grab_set()
    ventana.configure(bg="white")
    ventana.resizable(False, False)

    # Centramos la ventana
    ancho_ventana = 400
    alto_ventana = 400
    pantalla_ancho = ventana.winfo_screenwidth()
    pantalla_alto = ventana.winfo_screenheight()
    x = (pantalla_ancho // 2) - (ancho_ventana // 2)
    y = (pantalla_alto // 2) - (alto_ventana // 2)
    ventana.geometry(f"{ancho_ventana}x{alto_ventana}+{x}+{y}")
  
    tk.Label(ventana, text="AGREGAR NUEVO PERSONAL", font=("Arial", 14, "bold"),
             bg="white", fg="#2c3e50").pack(pady=10)

    campos = [
        ("numero_operario", "Número de operario"),
        ("nombre_completo", "Nombre completo"),
        ("cargo", "Cargo"),
        ("sector", "Sector"),
        ("telefono", "Teléfono"),
    ]

    entradas = {}

    contenedor = tk.Frame(ventana, bg="white")
    contenedor.pack(pady=10)

    for i, (campo, etiqueta) in enumerate(campos):
        tk.Label(contenedor, text=etiqueta + ":", bg="white", anchor="w").grid(row=i, column=0, sticky="e", padx=5, pady=5)
        entrada = tk.Entry(contenedor, width=30)
        entrada.grid(row=i, column=1, padx=5, pady=5)
        entradas[campo] = entrada

    def agregar_personal():
        datos = {campo: entrada.get().strip() for campo, entrada in entradas.items()}

        if not all([datos["numero_operario"], datos["nombre_completo"], datos["cargo"], datos["sector"]]):
            messagebox.showwarning("Campos obligatorios", "Por favor completá todos los campos obligatorios (sin dejar en blanco).", parent=ventana)
            return

        try:
            conn = conectar()

            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO personal (numero_operario, nombre_completo, cargo, sector, telefono)
                VALUES (?, ?, ?, ?, ?)
            """, (
                datos["numero_operario"],
                datos["nombre_completo"],
                datos["cargo"],
                datos["sector"],
                datos["telefono"]
            ))
            conn.commit()
            conn.close()

            messagebox.showinfo("Éxito", "Personal agregado correctamente.", parent=ventana)
            ventana.destroy()

            if actualizar_callback:
                actualizar_callback()

        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "El número de operario ya existe.", parent=ventana)

        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error al guardar:\n{e}", parent=ventana)

    # Botones
    btn_frame = tk.Frame(ventana, bg="white")
    btn_frame.pack(pady=10)

    tk.Button(btn_frame, text="Agregar", width=12, bg="#27ae60", fg="white", command=agregar_personal).pack(side="left", padx=10)
    tk.Button(btn_frame, text="Cancelar", width=12, bg="#e74c3c", fg="white", command=ventana.destroy).pack(side="left", padx=10)
