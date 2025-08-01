import os
import sqlite3
from datetime import datetime, timedelta
from db_init import get_db_path

def conectar():
    """Establece conexión con la base de datos"""
    db = get_db_path()
    # Solo creamos la carpeta si dirname no está vacío
    carpeta = os.path.dirname(db)
    if carpeta:
        os.makedirs(carpeta, exist_ok=True)
    return sqlite3.connect(db, timeout=10)



def cargar_datos_ot(nro_ot):
    """Carga los datos de una Orden de Trabajo específica desde la BD."""
    with conectar() as conn:
        cur = conn.cursor()
        # Consulta principal para datos básicos + insumos + imágenes
        cur.execute(
            """
            SELECT 
                nro_ot, cliente, trabajo, observaciones,
                fecha_ingreso, fecha_iniciado, fecha_final,
                fecha_estimada, estado, responsable, prioridad,
                insumos, imagenes
            FROM ordenes_trabajo
            WHERE nro_ot = ?
            """,
            (nro_ot,)
        )
        row = cur.fetchone()
        if not row:
            return None

        datos = {
            'nro_ot':         row[0],
            'cliente':        row[1],
            'trabajo':        row[2],
            'observaciones':  row[3],
            'fecha_ingreso':  row[4],
            'fecha_iniciado': row[5],
            'fecha_final':    row[6],
            'fecha_estimada': row[7],
            'estado':         row[8],
            'responsable':    row[9],
            'prioridad':      row[10],
            'insumos':        row[11] or "",
            'imagenes':       [img.strip() for img in (row[12] or "").split(',') if img.strip()],
            'fotos':          [],
            'es_cliente':     bool(row[1] and row[1].strip())
        }
        return datos


def guardar_datos_ot(codigo, datos_actualizados):
    """Guarda los datos actualizados de la OT en la base de datos."""
    try:
        with conectar() as conn:
            cur = conn.cursor()
            # Actualizar ordenes_trabajo
            cur.execute(
                """UPDATE ordenes_trabajo SET
                    cliente=?, trabajo=?, observaciones=?,
                    fotos=?, fecha_ingreso=?, fecha_iniciado=?,
                    fecha_final=?, fecha_estimada=?, estado=?,
                    responsable=?, prioridad=?, imagenes=?
                WHERE nro_ot=?""",
                (
                    datos_actualizados.get('cliente'),
                    datos_actualizados.get('trabajo'),
                    datos_actualizados.get('observaciones'),
                    ",".join(datos_actualizados.get('fotos', [])),
                    datos_actualizados.get('fecha_ingreso'),
                    datos_actualizados.get('fecha_iniciado'),
                    datos_actualizados.get('fecha_final'),
                    datos_actualizados.get('fecha_estimada'),
                    datos_actualizados.get('estado'),
                    datos_actualizados.get('responsable'),
                    datos_actualizados.get('prioridad'),
                    ",".join(datos_actualizados.get('imagenes', [])),
                    codigo
                )
            )
        return True
    except Exception as e:
        print(f"Error al guardar datos de OT: {e}")
        return False
