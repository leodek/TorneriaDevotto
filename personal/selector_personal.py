import tkinter as tk
from tkinter import messagebox
import sqlite3
from db_init import get_db_path
import sqlite3
from db_init import conectar



def mostrar_selector_responsables(dest_widget):
    """
    Muestra un diálogo con una lista de nombres de personal.
    Al pulsar OK inserta el nombre seleccionado en `dest_widget`,
    que puede ser un Listbox o un Text (deshabilitado).
    """
    parent = dest_widget.winfo_toplevel()
    ventana = tk.Toplevel(parent)
    ventana.title("Seleccionar Responsable")
    ventana.configure(bg="white")
    ventana.resizable(False, False)
    ventana.grab_set()

    # Centrar ventana pequeña
    w, h = 300, 300
    sw, sh = ventana.winfo_screenwidth(), ventana.winfo_screenheight()
    x = (sw - w) // 2
    y = (sh - h) // 2
    ventana.geometry(f"{w}x{h}+{x}+{y}")

    # Lista de nombres
    listbox = tk.Listbox(ventana, selectmode=tk.SINGLE)
    listbox.pack(fill="both", expand=True, padx=10, pady=(10, 0))

    # Cargar nombres desde la tabla personal
    try:
        with conectar() as conn:
            cur = conn.cursor()
            cur.execute("SELECT nombre_completo FROM personal")
            for (nombre,) in cur.fetchall():
                listbox.insert(tk.END, nombre)
    except Exception as e:
        messagebox.showerror("Error BD", f"No se pudo cargar el personal:\n{e}", parent=ventana)
        ventana.destroy()
        return

    # Botones
    frame_btn = tk.Frame(ventana, bg="white")
    frame_btn.pack(fill="x", pady=10)

    def on_ok():
        sel = listbox.curselection()
        if not sel:
            messagebox.showwarning("Sin selección", "Por favor selecciona un nombre.", parent=ventana)
            return
        nombre = listbox.get(sel[0])

        # Insertar en Listbox destino
        if isinstance(dest_widget, tk.Listbox):
            if nombre not in dest_widget.get(0, tk.END):
                dest_widget.insert(tk.END, nombre)
        # Insertar en Text destino
        elif isinstance(dest_widget, tk.Text):
            dest_widget.config(state="normal")
            contenido = dest_widget.get("1.0", "end").splitlines()
            if nombre not in contenido:
                dest_widget.insert("end", nombre + "\n")
            dest_widget.config(state="disabled")

        ventana.destroy()

    tk.Button(frame_btn, text="OK", width=10, command=on_ok).pack(side="left", padx=10)
    tk.Button(frame_btn, text="Cancelar", width=10, command=ventana.destroy).pack(side="right", padx=10)
