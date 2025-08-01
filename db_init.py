# db_init.py
import os, sys, sqlite3
from datetime import datetime
from collections import defaultdict
import tkinter.messagebox as mb

# ───────────────────────────── rutas y conexión ────────────────────────────
def get_db_path() -> str:
    """Devuelve la ruta del archivo mantenimiento.db (AppData en .exe, carpeta del proyecto en desarrollo)."""
    if getattr(sys, "frozen", False):
        appdata = os.getenv("APPDATA", os.path.expanduser("~"))
        carpeta = os.path.join(appdata, "ManteMoustache")
        os.makedirs(carpeta, exist_ok=True)
        return os.path.join(carpeta, "mantenimiento.db")
    else:
        return os.path.join(os.path.dirname(__file__), "mantenimiento.db")

def conectar():
    db = get_db_path()
    os.makedirs(os.path.dirname(db), exist_ok=True)
    return sqlite3.connect(db, timeout=10)

# ───────────────── MIGRAR asistencia → asistencia_diaria ──────────────────
def _migrar_asistencia_si_corresponde(conn: sqlite3.Connection) -> None:
    """
    • Corre una sola vez: únicamente cuando la tabla asistencia_diaria aún no existe.
    • Empareja cada Entrada con la primera Salida posterior del mismo día/persona.
    • Genera varias filas por día si hay múltiples pares Entrada/Salida.
    • Guarda fecha dd/mm/yyyy y horas HH:MM:SS (sin microsegundos).
    """
    cur = conn.cursor()

    # 0) Si la tabla nueva ya existe → salir
    if cur.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='asistencia_diaria'"
    ).fetchone():
        return

    # 1) Verificar que la tabla vieja exista y tenga datos
    if not cur.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='asistencia'"
    ).fetchone():
        return
    if cur.execute("SELECT COUNT(*) FROM asistencia").fetchone()[0] == 0:
        return

    # 2) Crear la tabla destino
    cur.execute("""
        CREATE TABLE asistencia_diaria (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre         TEXT NOT NULL,
            fecha          TEXT NOT NULL,   -- dd/mm/yyyy
            hora_entrada   TEXT,
            hora_salida    TEXT,
            total_horas    REAL DEFAULT 0
        )
    """)

    # 3) Leer y agrupar eventos
    eventos = defaultdict(list)  # (nombre, fecha) → [(tipo, fecha_hora), …]
    for nombre, tipo, fh in cur.execute("""
        SELECT nombre, lower(tipo), fecha_hora
          FROM asistencia
      ORDER BY nombre, fecha_hora
    """):
        fecha_ddmmyyyy = datetime.fromisoformat(fh).strftime("%d/%m/%Y")
        eventos[(nombre, fecha_ddmmyyyy)].append((tipo, fh))

    inserciones = []

    # 4) Emparejar Entrada–Salida
    for (nombre, fecha), lista in eventos.items():
        lista.sort(key=lambda x: x[1])
        i = 0
        while i < len(lista):
            tipo_i, fh_i = lista[i]

            if not tipo_i.startswith("entrada"):
                i += 1
                continue  # Salida sin entrada previa

            hora_ent = fh_i[11:].split('.')[0]       # HH:MM:SS
            hora_sal = None
            total_h  = 0.0

            j = i + 1
            while j < len(lista):
                tipo_j, fh_j = lista[j]
                if tipo_j.startswith("salida"):
                    hora_sal = fh_j[11:].split('.')[0]
                    t0 = datetime.fromisoformat(fh_i)
                    t1 = datetime.fromisoformat(fh_j)
                    total_h = round((t1 - t0).total_seconds() / 3600, 2)
                    break
                j += 1

            inserciones.append((nombre, fecha, hora_ent, hora_sal, total_h))
            i = j + 1 if hora_sal else i + 1

    # 5) Insertar
    cur.executemany("""
        INSERT INTO asistencia_diaria
              (nombre, fecha, hora_entrada, hora_salida, total_horas)
        VALUES (?,?,?,?,?)
    """, inserciones)
    conn.commit()

    # 6) Aviso (solo esta vez)
    if inserciones:
        try:
            mb.showinfo(
                "Migración completada",
                f"Se migraron {len(inserciones)} pares Entrada/Salida a asistencia_diaria.\n"
                "Este mensaje aparecerá solo una vez."
            )
        except Exception:
            print(f"[INFO] Migración asistencia → asistencia_diaria: {len(inserciones)} filas.")

# ───────────────────────────── creación de tablas ───────────────────────────
def init_db():
    with conectar() as conn:
        cur = conn.cursor()

        # 1) Intentar migrar – si asistencia_diaria no existe, la crea y migra
        _migrar_asistencia_si_corresponde(conn)

        # 2) Asegurar el resto de las tablas
        cur.execute("""
        CREATE TABLE IF NOT EXISTS ordenes_trabajo(
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            nro_ot           TEXT,
            cliente          TEXT,
            trabajo          TEXT,
            fecha_ingreso    TEXT,
            insumos          TEXT,
            responsable      TEXT,
            observaciones    TEXT,
            estado           TEXT,
            prioridad        TEXT,
            herramientas     TEXT,
            fecha_estimada   TEXT,
            tiempo_pausado   INTEGER,
            fecha_pausada    INTEGER,
            tiempo_trabajo   INTEGER,
            fecha_iniciado   INTEGER,
            fecha_final      INTEGER,
            imagenes         INTEGER,
            fotos            INTEGER
        )""")

        cur.execute("""
        CREATE TABLE IF NOT EXISTS usuarios(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT UNIQUE NOT NULL,
            nombre TEXT NOT NULL,
            contraseña TEXT NOT NULL,
            imagen TEXT,
            rol TEXT
        )""")

        cur.execute("""
        INSERT OR IGNORE INTO usuarios(id, usuario, nombre, contraseña, imagen, rol) VALUES
          (1,'admin','Administrador','admin123','usuarios/imagenes/admin.png','admin'),
          (2,'nico.devoto','Nicolás','nico123','usuarios/imagenes/Nico.devoto.png','supervisor')
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS personal(
            numero_operario TEXT PRIMARY KEY,
            nombre_completo TEXT NOT NULL,
            cargo           TEXT NOT NULL,
            sector          TEXT NOT NULL,
            telefono        TEXT
        )""")

        conn.commit()
