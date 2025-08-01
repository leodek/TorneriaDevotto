import sqlite3
import tkinter as tk

# Asegúrate de ajustar la ruta a tu módulo si es necesario
from modificar_orden_trabajo import abrir_formulario_modificar_ot  

def cargar_datos_ot(nro_ot: str) -> dict:
    """Lee una orden de trabajo de la BD y la devuelve como dict."""
    with sqlite3.connect("mantenimiento.db") as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT nro_ot, fecha, codigo_equipo, operacion, prioridad,
                   observaciones, estado, insumos, herramientas, responsable
            FROM ordenes_trabajo
            WHERE nro_ot = ?
        """, (nro_ot,))
        row = cur.fetchone()
    if not row:
        raise ValueError(f"No existe la orden '{nro_ot}'")
    return {
        "nro_ot":           row[0],
        "fecha":            row[1],
        "codigo_equipo":    row[2],
        "operacion":        row[3],
        "prioridad":        row[4],
        "observaciones":    row[5],
        "estado":           row[6],
        "insumos":          row[7] or "",
        "herramientas":     row[8] or "",
        "responsable":      row[9] or ""
    }

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()

    try:
        datos = cargar_datos_ot("OT007")
    except ValueError as e:
        tk.messagebox.showerror("Error", str(e))
        root.destroy()
    else:
        abrir_formulario_modificar_ot(datos)
        root.mainloop()
