import tkinter as tk
from tkinter import messagebox
import sqlite3
import sqlite3
from db_init import get_db_path
from db_init import conectar

def abrir_formulario_modificar_personal(datos, actualizar_callback=None):
    ventana = tk.Toplevel()
    ventana.title("Modificar Personal")
    ventana.grab_set()
    ventana.configure(bg="white")
    ventana.resizable(False, False)

    # Centrar ventana
    ancho_ventana = 400
    alto_ventana = 400
    pantalla_ancho = ventana.winfo_screenwidth()
    pantalla_alto = ventana.winfo_screenheight()
    x = (pantalla_ancho // 2) - (ancho_ventana // 2)
    y = (pantalla_alto // 2) - (alto_ventana // 2)
    ventana.geometry(f"{ancho_ventana}x{alto_ventana}+{x}+{y}")

    tk.Label(ventana, text="MODIFICAR PERSONAL", font=("Arial", 14, "bold"),
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
        entrada.insert(0, datos.get(campo, ""))
        entradas[campo] = entrada

        # El campo de número de operario no se puede modificar (clave primaria)
        if campo == "numero_operario":
            entrada.config(state="readonly")

    def modificar_personal():
        actualizados = {}
        for campo, entrada in entradas.items():
            valor = entrada.get()
           # Solo aplicamos strip() a campos que no son numéricos
            if campo != "telefono":
                valor = valor.strip()
            actualizados[campo] = valor


        if not all([actualizados["nombre_completo"], actualizados["cargo"], actualizados["sector"]]):
            messagebox.showwarning("Campos requeridos", "Por favor completá todos los campos obligatorios.", parent=ventana)
            return

        try:
            conn = conectar()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE personal
                SET nombre_completo = ?, cargo = ?, sector = ?, telefono = ?
                WHERE numero_operario = ?
            """, (
                actualizados["nombre_completo"],
                actualizados["cargo"],
                actualizados["sector"],
                actualizados["telefono"],
                actualizados["numero_operario"]
            ))
            conn.commit()
            conn.close()
            messagebox.showinfo("Éxito", "Datos actualizados correctamente.", parent=ventana)
            ventana.destroy()
            if actualizar_callback:
                actualizar_callback()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo actualizar:\n{e}", parent=ventana)

    def eliminar_personal():
        if not messagebox.askyesno("Eliminar", "¿Estás seguro de eliminar este registro?", parent=ventana):
            return

        try:
            conn = conectar()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM personal WHERE numero_operario = ?", (datos["numero_operario"],))
            conn.commit()
            conn.close()
            messagebox.showinfo("Eliminado", "Registro eliminado correctamente.", parent=ventana)
            ventana.destroy()
            if actualizar_callback:
                actualizar_callback()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo eliminar:\n{e}", parent=ventana)

    btn_frame = tk.Frame(ventana, bg="white")
    btn_frame.pack(pady=10)

    tk.Button(btn_frame, text="Modificar", width=12, bg="#2980b9", fg="white", command=modificar_personal).pack(side="left", padx=10)
    tk.Button(btn_frame, text="Eliminar", width=12, bg="#c0392b", fg="white", command=eliminar_personal).pack(side="left", padx=10)
