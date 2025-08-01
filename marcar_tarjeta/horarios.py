# Corrección completa de abrir_ventana_gestion_horas con parser flexible y Combobox que desaparece

import os
import sqlite3
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
from db_init import get_db_path
import re

# ─── utilidades de fecha ──────────────────────────────────────────────
def fecha_hoy_ddmmyyyy() -> str:
    return datetime.now().strftime("%d/%m/%Y")

def formatea_fecha_ddmmyyyy(txt: str) -> str:
    """
    Devuelve la fecha en dd/MM/yyyy venga como:
    • 'YYYY-MM-DD', 'YYYY/MM/DD' o ya 'dd/MM/yyyy'
    """
    txt = txt.strip()
    if "-" in txt:
        try:
            return datetime.strptime(txt, "%Y-%m-%d").strftime("%d/%m/%Y")
        except ValueError:
            pass
    if txt.count("/") == 2 and len(txt) == 10:
        return txt
    try:
        return datetime.strptime(txt, "%Y/%m/%d").strftime("%d/%m/%Y")
    except ValueError:
        return txt
# ──────────────────────────────────────────────────────────────────────


def conectar():
    db = get_db_path()
    os.makedirs(os.path.dirname(db), exist_ok=True)
    return sqlite3.connect(db, timeout=10)

def abrir_ventana_gestion_horas(parent, on_update_main=None):
    win = tk.Toplevel(parent)
    win.title("Gestión de Horas")
    win.configure(bg="#f2f2f2")
    win.resizable(False, False)
    W, H = 800, 500
    sw, sh = win.winfo_screenwidth(), win.winfo_screenheight()
    win.geometry(f"{W}x{H}+{(sw-W)//2}+{(sh-H)//2}")
    win.grab_set()

    # — filtros —
    fframe = tk.Frame(win, bg="#f2f2f2")
    fframe.pack(fill="x", pady=10, padx=10)
    tk.Label(fframe, text="Responsable:", bg="#f2f2f2").grid(row=0, column=0, sticky="w")
    with conectar() as c:
        pers = [r[0] for r in c.execute("SELECT DISTINCT nombre_completo FROM personal")]
    nom_var = tk.StringVar(value=pers[0] if pers else "")
    cb_pers = ttk.Combobox(fframe, textvariable=nom_var, values=pers, state="readonly", width=20)
    cb_pers.grid(row=0, column=1, padx=5)

    tk.Label(fframe, text="Desde:", bg="#f2f2f2").grid(row=0, column=2, sticky="w", padx=(20,0))
    d1 = DateEntry(fframe, date_pattern="dd/MM/yyyy", width=12)
    d1.set_date(datetime.now().date())   # Día de hoy por defecto
    d1.grid(row=0, column=3, padx=5)

    tk.Label(fframe, text="Hasta:", bg="#f2f2f2").grid(row=0, column=4, sticky="w", padx=(20,0))
    d2 = DateEntry(fframe, date_pattern="dd/MM/yyyy", width=12)
    d2.set_date(datetime.now().date())   # Día de hoy por defecto
    d2.grid(row=0, column=5, padx=5)

    editor = None

    def safe_parse(t):
        if " " in t:
            t = t.split(" ", 1)[1]
        for fmt in ("%H:%M:%S", "%H:%M"):
            try:
                return datetime.strptime(t, fmt)
            except ValueError:
                continue
        raise ValueError(f"Formato de hora inválido: {t}")

    def auto_filtrar(*_):
        nonlocal editor
        if editor:
            editor.destroy()
            editor = None
        cargar_datos()

    cb_pers.bind("<<ComboboxSelected>>", auto_filtrar)
    d1.bind("<<DateEntrySelected>>", auto_filtrar)
    d2.bind("<<DateEntrySelected>>", auto_filtrar)

    # — tabla (sin Trabajo y Hs Trabajo) —
    cols = ("Fecha","Entrada","Salida","Horas","Hs comunes","Hs extras")
    tree = ttk.Treeview(
        win,
        columns=cols,
        show="headings",
        height=18,
        style="Ges.Treeview"
    )
    for c in cols:
        tree.heading(c, text=c)
        tree.column(c, anchor="center", width=110)
    tree.pack(fill="both", expand=True, padx=10)

    # — totales —
    tframe = tk.Frame(win, bg="#f2f2f2")
    tframe.pack(fill="x", padx=10, pady=(0,10))
    lbl_tot = tk.Label(
        tframe,
        text="Totales →  Horas: 0.00   Comunes: 0.00   Extras: 0.00",
        bg="#f2f2f2",
        font=("Arial",10,"bold")
    )
    lbl_tot.pack(anchor="e")

    def on_dblclk(event):
        nonlocal editor
        region = tree.identify("region", event.x, event.y)
        if region != "cell": return
        item = tree.identify_row(event.y)
        col  = tree.identify_column(event.x)
        ci = int(col.replace("#","")) - 1
        if ci not in (1,2): return   # sólo editar Entrada o Salida

        vals = list(tree.item(item, "values"))
        fecha, ent_act, sal_act = vals[0], vals[1], vals[2]

        if ci == 2 and not ent_act:
            messagebox.showwarning(
                "Edición no permitida",
                "Primero debe definir una Entrada antes de la Salida.",
                parent=win
            )
            return

        def validate_hhmm(P):
            return re.fullmatch(r"\d{0,2}:?\d{0,2}", P) is not None

        x0, y0, w0, h0 = tree.bbox(item, col)
        orig = vals[ci]
        editor = tk.Entry(tree,
                          font=("Arial", 12),
                          validate="key",
                          validatecommand=(win.register(validate_hhmm), "%P"))
        editor.place(x=x0, y=y0, width=w0, height=h0)
        editor.insert(0, orig)
        editor.focus()

        def save_cb(e=None):
            nonlocal editor
            if editor is None:
                return
            nv = editor.get()
            if not re.fullmatch(r"\d{2}:\d{2}", nv):
                messagebox.showerror("Formato inválido", "Use HH:MM", parent=win)
                if editor:
                    editor.focus_set()
                return

            fecha_item = datetime.strptime(fecha, "%d/%m/%Y").date()
            dt_new = datetime.combine(fecha_item, datetime.strptime(nv, "%H:%M").time())
            dt_limit = datetime.now() if fecha_item == datetime.now().date() else datetime.combine(fecha_item, datetime.max.time())
            if dt_new > dt_limit:
                messagebox.showerror("Hora inválida", "No se puede ingresar una hora a futuro.", parent=win)
                if editor:
                    editor.focus_set()
                return

            with conectar() as conn:
                cur = conn.cursor()

                # No permitir entrada si hay otra pendiente (en cualquier fecha)
                if ci == 1:  # Entrada
                    nm = nom_var.get()
                    cur.execute("""
                        SELECT id, fecha FROM asistencia_diaria
                        WHERE nombre=? AND (hora_entrada IS NOT NULL AND (hora_salida IS NULL OR hora_salida=''))
                          AND id <> ?
                    """, (nm, int(item)))
                    pendiente = cur.execute("""
                        SELECT id, fecha
                          FROM asistencia_diaria
                         WHERE nombre=? AND hora_entrada IS NOT NULL
                           AND (hora_salida IS NULL OR hora_salida='')
                           AND id <> ?
                    """, (nm, int(item))).fetchone()
                    if pendiente:
                        messagebox.showerror(
                            "Entrada pendiente",
                            f"Ya existe una entrada sin salida para el día "
                            f"{formatea_fecha_ddmmyyyy(pendiente[1])}.",
                            parent=win
                        )
                        ...

                        if editor:
                            editor.focus_set()
                        return

                # ── Actualiza entrada o salida ───────────────────────
                campo      = "hora_entrada" if ci == 1 else "hora_salida"
                val_iso    = f"{nv}:00"            # guarda HH:MM:SS
                registro_id = int(item)

                conn.execute(
                    f"UPDATE asistencia_diaria SET {campo} = ? WHERE id = ?",
                    (val_iso, registro_id)
                )


                # Si es salida: completar salidas pendientes anteriores (sin salida)
                if ci == 2:
                    nm = nom_var.get()
                    cur.execute("""
                        SELECT id, fecha FROM asistencia_diaria
                        WHERE nombre=? AND (hora_entrada IS NOT NULL AND (hora_salida IS NULL OR hora_salida=''))
                          AND id <> ?
                        ORDER BY fecha, id
                    """, (nm, int(item)))
                    faltantes = cur.fetchall()
                    for row in faltantes:
                        conn.execute(
                            "UPDATE asistencia_diaria SET hora_salida=? WHERE id=?",
                            (val_iso, row[0])
                        )

                    # Si OT asociada está en proceso, pasar a Pausado
                    cur.execute("""
                        SELECT trabajo_asignado FROM asistencia_diaria WHERE id=?
                    """, (registro_id,))
                    ot_rel = cur.fetchone()
                    if ot_rel and ot_rel[0]:
                        cur2 = conn.cursor()
                        cur2.execute(
                            "SELECT estado FROM ordenes_trabajo WHERE nro_ot=?",
                            (ot_rel[0],)
                        )
                        estado_ot = cur2.fetchone()
                        if estado_ot and estado_ot[0] == "En proceso":
                            conn.execute(
                                "UPDATE ordenes_trabajo SET estado='Pausado' WHERE nro_ot=?",
                                (ot_rel[0],)
                            )
                # Recalcular total_horas
                cur.execute("SELECT hora_entrada, hora_salida FROM asistencia_diaria WHERE id=?", (registro_id,))
                he_full, hs_full = cur.fetchone()
                total = 0.0
                if he_full and hs_full:
                    try:
                        t0 = safe_parse(he_full)
                        t1 = safe_parse(hs_full)
                        if t1 <= t0:
                            t1 += timedelta(days=1)
                        total = round((t1 - t0).seconds / 3600, 2)
                    except Exception:
                        total = 0.0
                conn.execute("""
                    UPDATE asistencia_diaria
                    SET total_horas=?
                    WHERE id=?
                """, (total, registro_id))
                conn.commit()

            cargar_datos()
            if editor:
                editor.destroy()
                editor = None
            tree.focus_set()
            if on_update_main:
                on_update_main()

        def focus_out_cb(e=None):
            nonlocal editor
            if editor:
                editor.destroy()
                editor = None
            tree.focus_set()

        editor.bind("<Return>", save_cb)
        editor.bind("<FocusOut>", focus_out_cb)



    tree.bind("<Double-1>", on_dblclk)

    def cargar_datos():
        tree.delete(*tree.get_children())

        nm       = nom_var.get()
        d1_str   = d1.get_date().strftime("%d/%m/%Y")   # dd/MM/yyyy
        d2_str   = d2.get_date().strftime("%d/%m/%Y")

        with conectar() as conn:
            filas = conn.execute("""
                SELECT id, fecha, hora_entrada, hora_salida, total_horas
                  FROM asistencia_diaria
                 WHERE nombre=? AND fecha BETWEEN ? AND ?
                 ORDER BY fecha, id
            """, (nm, d1_str, d2_str)).fetchall()

        for id_, fecha_db, he, hs, th in filas:
            disp_fecha = formatea_fecha_ddmmyyyy(fecha_db)   # dd/MM/yyyy

            entrada = he[:5] if he else ''   # HH:MM
            salida  = hs[:5] if hs else ''   # HH:MM
            horas   = th or 0.0
            comunes = min(horas, 8)
            extras  = max(horas - 8, 0)

            tree.insert(
                "", "end", iid=str(id_),
                values=(
                    disp_fecha, entrada, salida,
                    f"{horas:.2f}", f"{comunes:.2f}", f"{extras:.2f}"
                )
            )

        recalcular_totales()

    def recalcular_fila(item):
        v = tree.item(item, "values")
        ent, sal = v[1], v[2]
        if sal:
            dt0 = safe_parse(ent)
            dt1 = safe_parse(sal)
            if dt1 <= dt0: dt1 += timedelta(days=1)
            diff_h = (dt1 - dt0).seconds / 3600.0
            comunes = min(diff_h, 8)
            extras  = max(diff_h - 8, 0)
        else:
            diff_h = comunes = extras = 0.0

        tree.set(item, 3, f"{diff_h:.2f}")
        tree.set(item, 4, f"{comunes:.2f}")
        tree.set(item, 5, f"{extras:.2f}")

    def recalcular_totales():
        tot = sum(float(tree.set(i,3)) for i in tree.get_children())
        tc  = sum(float(tree.set(i,4)) for i in tree.get_children())
        te  = sum(float(tree.set(i,5)) for i in tree.get_children())
        lbl_tot.config(text=f"Totales →  Horas: {tot:.2f}   Comunes: {tc:.2f}   Extras: {te:.2f}")

    cargar_datos()
    win.mainloop()
