# migrar_asistencia.py
import sqlite3
from datetime import datetime
from collections import defaultdict
from db_init import get_db_path   # usa tu función centralizada

def migrar_asistencia():
    db = get_db_path()
    conn = sqlite3.connect(db, timeout=10)
    cur  = conn.cursor()

    # 1) Asegurarse de que asistencia_diaria exista
    cur.execute("""
        CREATE TABLE IF NOT EXISTS asistencia_diaria (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre       TEXT NOT NULL,
            fecha        TEXT NOT NULL,          -- YYYY-MM-DD
            hora_entrada TEXT,                   -- HH:MM:SS
            hora_salida  TEXT,
            total_horas  REAL DEFAULT 0
        )
    """)

    # 2) Leer todos los registros antiguos ordenados por persona y hora
    cur.execute("""
        SELECT nombre, tipo, fecha_hora
          FROM asistencia
      ORDER BY nombre, fecha_hora
    """)
    registros = cur.fetchall()

    # 3) Organizar los eventos por (persona, fecha)
    eventos = defaultdict(list)
    for nombre, tipo, fecha_hora in registros:
        fecha = fecha_hora[:10]          # 'YYYY-MM-DD'
        eventos[(nombre, fecha)].append((tipo.lower(), fecha_hora))

    inserciones = []

    # 4) Emparejar Entrada → Salida para cada día/persona
    for (nombre, fecha), lista in eventos.items():
        # ordenar por timestamp, por si llegaran desordenados
        lista.sort(key=lambda x: x[1])

        i = 0
        while i < len(lista):
            tipo, fh_entrada = lista[i]
            if tipo.startswith("entrada"):
                hora_ent = fh_entrada[11:]          # 'HH:MM:SS'
                hora_sal = None
                tot_h    = 0.0

                # buscar la salida siguiente
                for j in range(i + 1, len(lista)):
                    tipo2, fh_salida = lista[j]
                    if tipo2.startswith("salida"):
                        hora_sal = fh_salida[11:]
                        t0 = datetime.fromisoformat(fh_entrada)
                        t1 = datetime.fromisoformat(fh_salida)
                        tot_h = round((t1 - t0).total_seconds() / 3600, 2)
                        i = j        # saltar hasta la salida emparejada
                        break

                inserciones.append((nombre, fecha, hora_ent, hora_sal, tot_h))
            i += 1

    # 5) Insertar – evita duplicar si ya existe ese par exacto
    cur.executemany("""
        INSERT INTO asistencia_diaria (nombre, fecha, hora_entrada, hora_salida, total_horas)
        SELECT ?,?,?,?,?
        WHERE NOT EXISTS (
            SELECT 1 FROM asistencia_diaria
             WHERE nombre=? AND fecha=? AND hora_entrada=? AND
                   COALESCE(hora_salida,'') = COALESCE(?, '')
        )
    """, [row + row for row in inserciones])     # row duplicado para el WHERE

    conn.commit()
    print(f"► Migración completada: {len(inserciones)} registros procesados.")
    conn.close()

if __name__ == "__main__":
    migrar_asistencia()
