# archivo: asistencia_gui.py
import os
import sqlite3
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
from tkcalendar import DateEntry
from db_init import get_db_path
import pandas as pd
from .horarios import abrir_ventana_gestion_horas


# ─── util ──────────────────────────────────────────────────────────────
def fecha_hoy_ddmmyyyy() -> str:
    return datetime.now().strftime("%d/%m/%Y")

def formatea_fecha_ddmmyyyy(txt: str) -> str:
    """
    Devuelve la fecha en formato dd/MM/yyyy,
    venga como 'YYYY-MM-DD', 'YYYY/MM/DD' o ya como 'dd/MM/yyyy'.
    """
    txt = txt.strip()
    if "-" in txt:
        try:
            return datetime.strptime(txt, "%Y-%m-%d").strftime("%d/%m/%Y")
        except ValueError:
            pass
    if txt.count("/") == 2 and len(txt) == 10:  # 31/07/2025
        return txt
    # último recurso: intenta con barra ISO => 2025/07/31
    try:
        return datetime.strptime(txt, "%Y/%m/%d").strftime("%d/%m/%Y")
    except ValueError:
        return txt
# ───────────────────────────────────────────────────────────────────────                                  # ya es dd/MM/yyyy

def conectar():
    db = get_db_path()
    os.makedirs(os.path.dirname(db), exist_ok=True)
    return sqlite3.connect(db, timeout=10)

def asegurar_tabla_asistencia():
    with conectar() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS asistencia_diaria (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre           TEXT    NOT NULL,
                fecha            TEXT    NOT NULL,
                hora_entrada     TEXT,
                hora_salida      TEXT,
                total_horas      REAL    DEFAULT 0,
                trabajo_asignado TEXT,
                hs_trabajo       REAL    DEFAULT 0
            )
        """)
        # Si la tabla ya existía sin esas columnas, las añadimos — ignoramos el error si ya existen
        for col_def in [
            ("trabajo_asignado", "TEXT"),
            ("hs_trabajo",     "REAL DEFAULT 0")
        ]:
            try:
                conn.execute(f"ALTER TABLE asistencia_diaria ADD COLUMN {col_def[0]} {col_def[1]}")
            except sqlite3.OperationalError:
                pass
            
def configurar_pagina_entrada_salida(frame_principal, rol_usuario_actual):
    asegurar_tabla_asistencia()
    # Limpiá todos los widgets existentes en el frame principal
    for w in frame_principal.winfo_children():
        w.destroy()
    frame_principal.configure(bg='#0f223b')

    clock = tk.Label(frame_principal, font=('Arial', 48), bg='#0f223b', fg='white')
    clock.pack(pady=10)

    def update_clock():
        if clock.winfo_exists():
            clock.config(text=datetime.now().strftime('%d/%m/%Y %H:%M:%S'))
            frame_principal.after(1000, update_clock)
    update_clock()

    tk.Label(frame_principal, text='Nombre completo:', font=('Arial', 18), bg='#0f223b', fg='white').pack()
    with conectar() as conn:
        nombres = [r[0] for r in conn.execute("SELECT DISTINCT nombre_completo FROM personal")]
    nombre_var = tk.StringVar()
    combo = ttk.Combobox(frame_principal, textvariable=nombre_var, values=nombres,
                         font=('Arial', 16), width=30, state='readonly')
    if nombres:
        combo.current(0)
    combo.pack(pady=10)

    # ========== SOLO PARA ADMIN ==========
    def exportar_excel():
        ventana = tk.Toplevel()
        ventana.title('Exportar Asistencia')
        ventana.grab_set()

        tk.Label(ventana, text='Fecha desde:', font=('Arial', 10, 'bold')).pack(anchor='w', padx=10, pady=(10, 0))
        de1 = DateEntry(ventana, date_pattern='dd/MM/yyyy', width=12)
        de1.pack(padx=10, pady=(0, 5))

        tk.Label(ventana, text='Fecha hasta:', font=('Arial', 10, 'bold')).pack(anchor='w', padx=10)
        de2 = DateEntry(ventana, date_pattern='dd/MM/yyyy', width=12)
        de2.pack(padx=10, pady=(0, 10))

        tk.Label(ventana, text='Nombre (o Todos):', font=('Arial', 10, 'bold')).pack(anchor='w', padx=10)
        with conectar() as conn:
            nombres = ['Todos'] + [r[0] for r in conn.execute("SELECT DISTINCT nombre FROM asistencia_diaria")]
        nombre_sel = tk.StringVar(value='Todos')
        cmb = ttk.Combobox(ventana, textvariable=nombre_sel, values=nombres, state='readonly', width=30)
        cmb.pack(padx=10, pady=(0, 10))

        abrir_var = tk.BooleanVar(value=True)
        tk.Checkbutton(ventana, text="Abrir archivo automáticamente", variable=abrir_var).pack(anchor='w', padx=10)

        def generar_excel():
            # --- rango de fechas en dd/MM/yyyy ---------------------------------
            d1_str = de1.get_date().strftime("%d/%m/%Y")
            d2_str = de2.get_date().strftime("%d/%m/%Y")

            # --- nombre a filtrar ---------------------------------------------
            nm = nombre_sel.get()

            # --- consulta ------------------------------------------------------
            q = """
                SELECT nombre, fecha, hora_entrada, hora_salida, total_horas
                  FROM asistencia_diaria
                 WHERE fecha BETWEEN ? AND ?
            """
            params = [d1_str, d2_str]
            if nm != 'Todos':
                q += " AND nombre = ?"
                params.append(nm)

            with conectar() as conn:
                rows = conn.execute(q, params).fetchall()

            # -------- agrupar y formatear --------------------------------------
            registros = {}
            for nombre, fecha_db, he, hs, th in rows:
                clave = (nombre, fecha_db)
                if clave not in registros:
                    registros[clave] = {"entrada": None, "salida": None, "total": 0}
                if he and registros[clave]["entrada"] is None:
                    registros[clave]["entrada"] = he[:5]     # HH:MM
                if hs:
                    registros[clave]["salida"] = hs[:5]      # HH:MM
                registros[clave]["total"] += float(th or 0)

            datos = []
            for (nombre, fecha_db), vals in registros.items():
                tot     = vals["total"]
                comunes = min(tot, 8)
                extras  = round(tot - comunes, 2)

                datos.append([
                    nombre,
                    formatea_fecha_ddmmyyyy(fecha_db),       # dd/MM/yyyy
                    vals["entrada"] or '',
                    vals["salida"]  or '',
                    round(tot, 2),
                    round(comunes, 2),
                    extras
                ])

            # --- DataFrame  + fila de totales ----------------------------------
            df = pd.DataFrame(
                datos,
                columns=[
                    'Nombre', 'Fecha', 'Hora entrada', 'Hora salida',
                    'Total horas', 'Hs comunes', 'Hs extras'
                ]
            )

            df.loc[len(df)] = [
                '', '', '', 'Totales',
                df['Total horas'].sum(),
                df['Hs comunes'].sum(),
                df['Hs extras'].sum()
            ]

            # --- Guardar --------------------------------------------------------
            fname_default = f"asistencia_{datetime.today().strftime('%d-%m-%Y')}.xlsx"
            fname = filedialog.asksaveasfilename(
                parent=ventana,
                initialfile=fname_default,
                defaultextension='.xlsx',
                filetypes=[('Excel', '*.xlsx')],
                title='Guardar como...'
            )
            if not fname:
                return

            try:
                with pd.ExcelWriter(fname, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name='Asistencia')
                    ws = writer.sheets['Asistencia']
                    from openpyxl.utils import get_column_letter
                    for i, col in enumerate(df.columns, 1):
                        max_len = max(df[col].astype(str).str.len().max(), len(col)) + 2
                        ws.column_dimensions[get_column_letter(i)].width = max_len
            except PermissionError:
                messagebox.showerror(
                    'Error al guardar',
                    f"No se pudo guardar el archivo:\n{fname}\n\n"
                    "Cierra el archivo si está abierto o elige otra ruta.",
                    parent=ventana
                )
                return

            messagebox.showinfo('Exportado', f'Archivo guardado:\n{fname}', parent=ventana)
            if abrir_var.get():
                try:
                    os.startfile(fname)
                except AttributeError:
                    subprocess.call(["open", fname])
            ventana.destroy()


        ttk.Button(ventana, text='Exportar a Excel', command=generar_excel).pack(pady=10)

    if rol_usuario_actual== "admin":
        ttk.Button(
            frame_principal,
            text="Editar Horas",
            command=lambda: abrir_ventana_gestion_horas(
                frame_principal.winfo_toplevel(),
                on_update_main=cargar_registros
            )
        ).pack(side="top", anchor="nw", padx=20, pady=5)

        btn_exportar_excel = ttk.Button(
            frame_principal,
            text="Exportar a Excel",
            command=exportar_excel
        )
        btn_exportar_excel.pack(side="top", anchor="ne", padx=20, pady=10)
    # Botones Entrada / Salida
    btn_frame = tk.Frame(frame_principal, bg='#0f223b')
    btn_frame.pack(pady=10)

    def actualizar_estado_ot_por_responsable(nombre, nuevo_estado, ot_especifica=None):
            """
            • Si nuevo_estado == 'Pausado'   ⇒ pausa TODAS las OTs “En proceso” del responsable.
            • Si nuevo_estado == 'En proceso'⇒ reanuda SOLO la OT indicada (ot_especifica) o,
              si es None, todas las OTs pausadas del responsable.

            Al reanudar se suma correctamente la pausa al campo tiempo_pausado.
            """
            now_dt  = datetime.now()
            now_str = now_dt.strftime('%d/%m/%Y %H:%M:%S')

            with conectar() as conn:
                cur = conn.cursor()

                # Selección de OTs afectadas
                query = """
                    SELECT nro_ot, fecha_pausada, tiempo_pausado, estado
                      FROM ordenes_trabajo
                     WHERE responsable LIKE ?
                       AND estado NOT IN ('Ingresada','Realizado')
                """
                params = [f"%{nombre}%"]
                if ot_especifica:
                    query += " AND nro_ot=?"
                    params.append(ot_especifica)

                for nro_ot, fecha_pausada_str, tiempo_prev, estado in cur.execute(query, params):

                    # ---------- PAUSAR ----------
                    if nuevo_estado == 'Pausado' and estado == 'En proceso':
                        total_seg = int(tiempo_prev or 0)
                        # si fecha_pausada estaba vacía, la fijamos ahora
                        cur.execute("""
                            UPDATE ordenes_trabajo
                               SET estado        = 'Pausado',
                                   fecha_pausada = ?,
                                   tiempo_pausado= ?
                             WHERE nro_ot = ?
                        """, (now_str, total_seg, nro_ot))

                    # ---------- REANUDAR ----------
                    elif nuevo_estado == 'En proceso' and estado == 'Pausado':
                        nuevos_seg = 0
                        if fecha_pausada_str:
                            try:
                                pausa_dt   = datetime.strptime(fecha_pausada_str, '%d/%m/%Y %H:%M:%S')
                                nuevos_seg = int((now_dt - pausa_dt).total_seconds())
                            except Exception:
                                pass

                        total_seg = int(tiempo_prev or 0) + nuevos_seg

                        cur.execute("""
                            UPDATE ordenes_trabajo
                               SET estado        = 'En proceso',
                                   fecha_pausada = NULL,
                                   tiempo_pausado= ?
                             WHERE nro_ot = ?
                        """, (total_seg, nro_ot))

                conn.commit()

    def cargar_registros():
        tree.delete(*tree.get_children())
        hoy = fecha_hoy_ddmmyyyy()            # ← dd/MM/yyyy

        with conectar() as conn:
            filas = conn.execute("""
                SELECT nombre, fecha, hora_entrada, hora_salida, total_horas
                  FROM asistencia_diaria
                 WHERE fecha = ?
                 ORDER BY nombre, id
            """, (hoy,)).fetchall()

        for nombre, fecha_db, he, hs, th in filas:
            disp_fecha = formatea_fecha_ddmmyyyy(fecha_db)  # dd/MM/yyyy
            hora_ent   = he[:5] if he else ''               # HH:MM
            hora_sal   = hs[:5] if hs else ''
            total      = f"{th:.2f}" if hs else ''

            tree.insert(
                '', 'end',
                values=(nombre, disp_fecha, hora_ent, hora_sal, total)
            )

    def registrar(tipo):
        # — helper para elegir OT si hay más de una pausada —
        def solicitar_ot_a_reanudar(ots):
            dialog = tk.Toplevel(frame_principal)
            dialog.title("Reanudar OT")
            dialog.transient(frame_principal.winfo_toplevel())
            dialog.grab_set()
            dialog.configure(bg='#0f223b')

            dialog.update_idletasks()
            sw, sh = dialog.winfo_screenwidth(), dialog.winfo_screenheight()
            width, height = 600, 300
            x = (sw - width) // 2
            y = (sh - height) // 2
            dialog.geometry(f"{width}x{height}+{x}+{y}")

            tk.Label(
                dialog,
                text="Seleccione la OT a reanudar",
                font=("Arial", 14, "bold"),
                bg='#0f223b',
                fg='white'
            ).pack(pady=(10, 5))

            cols = ("OT", "Trabajo", "Cliente")
            tv = ttk.Treeview(dialog, columns=cols, show="headings", height=min(len(ots), 8))
            for col in cols:
                tv.heading(col, text=col, anchor='center')
                tv.column(col, anchor='center', width=180 if col!="OT" else 80)
            for nro_ot, trabajo, cliente in ots:
                tv.insert("", "end", values=(nro_ot, trabajo, cliente))
            tv.pack(fill='both', expand=True, padx=10, pady=5)

            btn_frame = tk.Frame(dialog, bg='#0f223b')
            btn_frame.pack(pady=(5, 10))
            sel_var = tk.StringVar()

            def on_ok():
                sel = tv.selection()
                if sel:
                    sel_var.set(tv.item(sel[0])['values'][0])
                    dialog.destroy()
                else:
                    messagebox.showwarning("Atención", "Seleccione una OT", parent=dialog)

            ttk.Button(btn_frame, text="Reanudar",  command=on_ok).pack(side="left", padx=5)
            ttk.Button(btn_frame, text="Cancelar", command=dialog.destroy).pack(side="left", padx=5)

            dialog.wait_window()
            return sel_var.get()

        # — inicio de registrar() propiamente dicho —
        nom = nombre_var.get().strip()
        if not nom:
            messagebox.showwarning('Atención', 'Seleccione un nombre', parent=frame_principal)
            return

        now = datetime.now()
        fecha = now.strftime('%d/%m/%Y')
        hora_actual = now.strftime('%H:%M:%S')

        if tipo == 'Entrada':
            # 1) No permitir si hay CUALQUIER entrada pendiente (de cualquier fecha)
            with conectar() as conn:
                pendiente = conn.execute(
                    "SELECT fecha FROM asistencia_diaria "
                    "WHERE nombre=? AND (hora_salida IS NULL OR hora_salida='') "
                    "ORDER BY id LIMIT 1",
                    (nom,)
                ).fetchone()

            if pendiente:
                disp = formatea_fecha_ddmmyyyy(pendiente[0])
                messagebox.showwarning(
                    'Atención',
                    f'Tienes una entrada sin salida del día {disp}. '
                    'Marca la salida antes de ingresar una nueva entrada.',
                    parent=frame_principal
                )
                return



            # 2) Elegir trabajo_asignado de las OTs pausadas
            with conectar() as conn:
                pausadas = conn.execute(
                    "SELECT nro_ot, trabajo, cliente FROM ordenes_trabajo "
                    "WHERE responsable LIKE ? AND estado='Pausado'",
                    (f"%{nom}%",)
                ).fetchall()

            if not pausadas:
                trabajo_sel = None
            elif len(pausadas) == 1:
                trabajo_sel = pausadas[0][0]
            else:
                trabajo_sel = solicitar_ot_a_reanudar(pausadas)

            # 3) Insertar entrada + trabajo_asignado
            with conectar() as conn:
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO asistencia_diaria(
                        nombre, fecha, hora_entrada, trabajo_asignado
                    ) VALUES (?, ?, ?, ?)
                """, (nom, fecha, hora_actual, trabajo_sel))
                conn.commit()

            # 4) Reanudar la OT seleccionada (ajusta tiempo_pausado)
            if trabajo_sel:
                actualizar_estado_ot_por_responsable(nom, 'En proceso', trabajo_sel)

        else:  # Salida  ---------------------------------------------------
            with conectar() as conn:
                cur = conn.cursor()
                cur.execute("""
                    SELECT id, hora_entrada
                      FROM asistencia_diaria
                     WHERE nombre=? AND fecha=? AND hora_salida IS NULL
                  ORDER BY id DESC LIMIT 1
                """, (nom, fecha))
                fila = cur.fetchone()

                if not fila:
                    messagebox.showwarning(
                        'Atención',
                        'No hay entrada pendiente para marcar salida.',
                        parent=frame_principal
                    )
                    return

                registro_id, hora_entrada = fila

                # ---------- normalizar hora_entrada ----------
                hora_txt = hora_entrada.strip()

                if '.' in hora_txt:               # con microsegundos
                    hora_t = datetime.strptime(hora_txt, '%H:%M:%S.%f').time()
                else:                             # HH:MM:SS
                    hora_t = datetime.strptime(hora_txt, '%H:%M:%S').time()


                t0 = datetime.combine(now.date(), hora_t)
                total_hs = round((now - t0).total_seconds() / 3600, 2)

                hora_actual = now.strftime('%H:%M:%S')    # guardamos sin microseg.

                # actualizar hora_salida, total_horas y hs_trabajo
                cur.execute("""
                    UPDATE asistencia_diaria
                       SET hora_salida = ?,
                           total_horas = ?,
                           hs_trabajo  = ?
                     WHERE id = ?
                """, (hora_actual, total_hs, total_hs, registro_id))
                conn.commit()

            # actualizar estados de OTs en pausa → Pasa a 'Pausado'
            actualizar_estado_ot_por_responsable(nom, 'Pausado')


        messagebox.showinfo(
            'Registrado',
            f"{tipo} de {nom} a las {hora_actual}",
            parent=frame_principal
        )
        cargar_registros()



    tk.Button(btn_frame, text='Registrar Entrada', font=('Arial', 20), bg='#27ae60', fg='white',
              command=lambda: registrar('Entrada'), width=15).pack(side='left', padx=20)
    tk.Button(btn_frame, text='Registrar Salida', font=('Arial', 20), bg='#c0392b', fg='white',
              command=lambda: registrar('Salida'), width=15).pack(side='left', padx=20)

    # Tabla de registros
    tk.Label(frame_principal, text='Registros del día', font=('Arial', 24, 'bold'),
             bg='#0f223b', fg='white').pack(pady=(20, 10))
    cols = ('Nombre', 'Fecha', 'Hora de entrada', 'Hora de salida', 'Total de horas')
    tree = ttk.Treeview(frame_principal, columns=cols, show='headings', height=8)
    for c in cols:
        tree.heading(c, text=c)
        tree.column(c, anchor='center')
    tree.pack(fill='both', expand=True, padx=20, pady=(0, 20))
    cargar_registros()





# Para pruebas
if __name__ == '__main__':
    root = tk.Tk()
    root.title("Gestión de Asistencia")
    main = tk.Frame(root)
    main.pack(fill='both', expand=True)
    configurar_pagina_entrada_salida(main, rol_usuario_actual)
    root.mainloop()
