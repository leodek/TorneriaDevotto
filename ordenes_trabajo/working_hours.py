# working_hours.py

import sqlite3
from datetime import datetime, timedelta
from typing import Optional

from db_init import get_db_path

def conectar() -> sqlite3.Connection:
    db = get_db_path()
    return sqlite3.connect(db, timeout=10)

def _safe_parse(ts: str) -> datetime:
    """
    Acepta 'YYYY-MM-DD HH:MM:SS' o 'YYYY-MM-DD HH:MM' y normaliza a datetime.
    """
    if len(ts) == 16:  # "YYYY-MM-DD HH:MM"
        ts += ":00"
    return datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")

def recalc_asistencia(registro_id: int) -> None:
    """
    Recalcula total_horas y hs_trabajo descontando pausa_segmento de esa fila.
    """
    with conectar() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT fecha, hora_entrada, hora_salida, pausa_segmento
              FROM asistencia_diaria
             WHERE id = ?
        """, (registro_id,))
        fila = cur.fetchone()
        if not fila:
            return
        fecha, he, hs, segs_pausa = fila
        if not he or not hs:
            return

        # Parseo
        dt_ent = _safe_parse(f"{fecha} {he}" if " " not in he else he)
        dt_sal = _safe_parse(f"{fecha} {hs}" if " " not in hs else hs)
        if dt_sal <= dt_ent:
            dt_sal += timedelta(days=1)

        # Cálculo neto
        dur = dt_sal - dt_ent
        bruto = dur.total_seconds()
        neto = max(bruto - (segs_pausa or 0), 0)
        neto_hs = round(neto / 3600.0, 2)

        # Guardar
        cur.execute("""
            UPDATE asistencia_diaria
               SET total_horas = ?, hs_trabajo = ?
             WHERE id = ?
        """, (neto_hs, neto_hs, registro_id))
        conn.commit()

def update_entrada(registro_id: int, nuevo_ts: str) -> None:
    """
    Actualiza hora_entrada y recalcula horas.
    nuevo_ts: 'HH:MM' o 'YYYY-MM-DD HH:MM[:SS]'.
    """
    with conectar() as conn:
        cur = conn.cursor()
        cur.execute("SELECT fecha FROM asistencia_diaria WHERE id = ?", (registro_id,))
        fecha = cur.fetchone()[0]
        # normalizar
        ts_full = (
            f"{fecha} {nuevo_ts}" 
            if len(nuevo_ts) > 5 else 
            f"{fecha} {nuevo_ts}:00"
        )
        cur.execute("UPDATE asistencia_diaria SET hora_entrada = ? WHERE id = ?",
                    (ts_full, registro_id))
        conn.commit()
    recalc_asistencia(registro_id)

def update_salida(registro_id: int, nuevo_ts: str) -> None:
    """
    Actualiza hora_salida y recalcula horas.
    """
    with conectar() as conn:
        cur = conn.cursor()
        cur.execute("SELECT fecha FROM asistencia_diaria WHERE id = ?", (registro_id,))
        fecha = cur.fetchone()[0]
        ts_full = (
            f"{fecha} {nuevo_ts}" 
            if len(nuevo_ts) > 5 else 
            f"{fecha} {nuevo_ts}:00"
        )
        cur.execute("UPDATE asistencia_diaria SET hora_salida = ? WHERE id = ?",
                    (ts_full, registro_id))
        conn.commit()
    recalc_asistencia(registro_id)

def calcular_horas_por_persona(
    nombre: str,
    fecha_desde: Optional[str] = None,
    fecha_hasta: Optional[str] = None
) -> float:
    """
    Suma hs_trabajo para un nombre dado, opcionalmente entre dos fechas.
    Agrega el tramo abierto hasta ahora.
    """
    with conectar() as conn:
        cur = conn.cursor()
        sql = "SELECT COALESCE(SUM(hs_trabajo),0) FROM asistencia_diaria WHERE nombre=?"
        params = [nombre]
        if fecha_desde:
            sql += " AND fecha>=?"
            params.append(fecha_desde)
        if fecha_hasta:
            sql += " AND fecha<=?"
            params.append(fecha_hasta)
        cur.execute(sql, params)
        total = cur.fetchone()[0] or 0.0

        # sesión abierta
        cur.execute("""
            SELECT fecha, hora_entrada, pausa_segmento
              FROM asistencia_diaria
             WHERE nombre=? AND hora_salida IS NULL
             ORDER BY id DESC LIMIT 1
        """, (nombre,))
        row = cur.fetchone()
        if row:
            fecha, he, segs_p = row
            dt_ent = _safe_parse(f"{fecha} {he}" if " " not in he else he)
            secs = max((datetime.now() - dt_ent).total_seconds() - (segs_p or 0), 0)
            total += secs / 3600.0

    return round(total, 2)

def calcular_horas_por_ot(
    nro_ot: str,
    fecha_desde: Optional[str] = None,
    fecha_hasta: Optional[str] = None
) -> float:
    """
    Suma hs_trabajo de una OT, opcionalmente entre dos fechas,
    e incluye segmento abierto.
    """
    with conectar() as conn:
        cur = conn.cursor()
        sql = """
            SELECT COALESCE(SUM(hs_trabajo),0) 
              FROM asistencia_diaria 
             WHERE trabajo_asignado=?
               AND hora_salida IS NOT NULL
        """
        params = [nro_ot]
        if fecha_desde:
            sql += " AND fecha>=?"
            params.append(fecha_desde)
        if fecha_hasta:
            sql += " AND fecha<=?"
            params.append(fecha_hasta)
        cur.execute(sql, params)
        total = cur.fetchone()[0] or 0.0

        # segmento abierto
        cur.execute("""
            SELECT fecha, hora_entrada, pausa_segmento
              FROM asistencia_diaria
             WHERE trabajo_asignado=? AND hora_salida IS NULL
             ORDER BY id DESC LIMIT 1
        """, (nro_ot,))
        row = cur.fetchone()
        if row:
            fecha, he, segs_p = row
            dt_ent = _safe_parse(f"{fecha} {he}" if " " not in he else he)
            secs = max((datetime.now() - dt_ent).total_seconds() - (segs_p or 0), 0)
            total += secs / 3600.0

    return round(total, 2)
