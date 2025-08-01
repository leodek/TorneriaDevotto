import os
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
from datetime import datetime, date, timedelta
from PIL import Image, ImageTk
from ordenes_trabajo.ot_form_logic import abrir_formulario_modificar_ot as modificar_ot
from ordenes_trabajo.agregar_orden_diaria import agregar_orden_trabajo
from db_init import get_db_path, conectar




# ─────────────────────────────
#  CONFIGURACIÓN
# ─────────────────────────────

POLL_MS = 5000
NUM_COLUMNS = 4
CARD_WIDTH = 600  # Ancho aumentado para mejor visualización
CARD_HEIGHT = 450  # Altura proporcional
CARD_PADX = 10    # Espaciado horizontal entre tarjetas
CARD_PADY = 10    # Espaciado vertical entre tarjetas
PRIORITY_COL = {"Alta": "#e74c3c", "Media": "#f39c12", "Baja": "#f1c40f"}

def parse_date(s: str) -> date | None:
    core = s.strip().split()[0].split("T")[0] if s else ""
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d/%m/%Y", "%d-%m-%Y"):
        try: 
            return datetime.strptime(core, fmt).date()
        except ValueError: 
            continue
    return None

def mostrar_proximas_ot(frame: tk.Frame) -> None:
    # ─────────────────────────────
    #  LIMPIEZA Y FILTROS
    # ─────────────────────────────
    for w in frame.winfo_children(): 
        w.destroy()
    frame.configure(bg="white")
    
    # Obtener valores únicos de la BD
    with conectar() as con:
        cur = con.cursor()
        cur.execute("SELECT DISTINCT prioridad FROM ordenes_trabajo")
        prioridades = [r[0] for r in cur.fetchall() if r[0]]
        cur.execute("SELECT DISTINCT estado FROM ordenes_trabajo")
        estados       = [r[0] for r in cur.fetchall() if r[0]]
        cur.execute("SELECT DISTINCT responsable FROM ordenes_trabajo")
        responsables  = [r[0] for r in cur.fetchall() if r[0]]
        cur.execute("SELECT DISTINCT cliente FROM ordenes_trabajo")
        clientes      = [r[0] for r in cur.fetchall() if r[0]]
        cur.execute("SELECT DISTINCT fecha_ingreso FROM ordenes_trabajo")
        fechas        = sorted({parse_date(r[0]) for r in cur.fetchall() if parse_date(r[0])})


    # Barra de filtros
    bar = tk.Frame(frame, bg="white")
    bar.pack(fill="x", padx=20, pady=10)

    # Auxiliar para crear combobox + label + bindings
    def make_combo(parent, label_text, var, values):
        tk.Label(parent, text=label_text, font=("Arial",11,"bold"), bg="white")\
            .pack(side="left", padx=(0,5))
        combo = ttk.Combobox(parent, textvariable=var, values=values,
                             width=12, state="readonly")
        combo.pack(side="left", padx=5)
        combo.bind("<Delete>",    lambda e, v=var: (v.set(""), refrescar(False)))
        combo.bind("<BackSpace>", lambda e, v=var: (v.set(""), refrescar(False)))
        combo.bind("<<ComboboxSelected>>", lambda e: refrescar(False))
        return combo

    prio_var = tk.StringVar()
    cb_prio  = make_combo(bar, "Prioridad:",   prio_var,    prioridades)

    est_var = tk.StringVar()
    cb_est   = make_combo(bar, "Estado:",       est_var,     estados)

    resp_var = tk.StringVar()
    cb_resp  = make_combo(bar, "Responsable:",  resp_var,    responsables)

    cli_var  = tk.StringVar()
    cb_cli   = make_combo(bar, "Cliente:",      cli_var,     clientes)

    fecha_var = tk.StringVar()
    fecha_vals = [d.strftime("%d/%m/%Y") for d in fechas]
    cb_fecha = make_combo(bar, "Fecha:",        fecha_var,   fecha_vals)
    
    # Botón Limpiar filtros
    tk.Button(
        bar,
        text="Limpiar filtros",
        font=("Arial", 10),
        bg="#e74c3c",
        fg="white",
        command=lambda: (
            prio_var.set(""),
            est_var.set(""),
            resp_var.set(""),
            cli_var.set(""),
            fecha_var.set(""),
            refrescar(False)
        )
    ).pack(side="right", padx=(0, 5))

    tk.Button(bar, text="🔄", width=3, command=lambda: refrescar(True))\
        .pack(side="right")

    for combo, var in ((cb_prio, prio_var), (cb_est, est_var)):
        combo.bind("<<ComboboxSelected>>", lambda e: refrescar(False))
        combo.bind("<Delete>", lambda e, v=var: (v.set(""), refrescar(False)))
        combo.bind("<BackSpace>", lambda e, v=var: (v.set(""), refrescar(False)))

    # ─────────────────────────────
    #  ÁREA SCROLL
    # ─────────────────────────────
    cont = tk.Frame(frame, bg="white")
    cont.pack(fill="both", expand=True, padx=20, pady=10)
    
    canvas = tk.Canvas(cont, bg="white", highlightthickness=0)
    sb = ttk.Scrollbar(cont, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=sb.set)
    
    sb.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)

    inner = tk.Frame(canvas, bg="white")
    canvas.create_window((0, 0), window=inner, anchor="nw")
    inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    
    for c in range(NUM_COLUMNS): 
        inner.columnconfigure(c, weight=1, uniform="cards")

    filas = []
    last_mtime = os.path.getmtime(get_db_path())

    # ─────────────────────────────
    #  CARGA DE DATOS
    # ─────────────────────────────
    def load_data():
        nonlocal filas
        with conectar() as con:
            cur = con.cursor()
            cur.execute("""
                SELECT id, nro_ot, cliente, trabajo, fecha_ingreso, insumos,
                       responsable, observaciones, estado, prioridad, fecha_estimada,
                       fecha_iniciado, tiempo_trabajo, tiempo_pausado, imagenes
                  FROM ordenes_trabajo
            """)
            raw = cur.fetchall()
        hoy = date.today()
        inicio = hoy - timedelta(days=15)
        fin    = hoy + timedelta(days=15)

        filas.clear()
        estados = set()

        for (_id, ot, cli, trab, f_txt, ins, resp, obs,
             est, prio, f_est, f_ini, t_t, t_p, imgs) in raw:
            fd = parse_date(f_txt)
            # solo incluyo si fd está entre hace 15 días y dentro de 15 días
            if fd and inicio <= fd <= fin:
                filas.append({
                    "nro_ot": ot,
                    "cliente": cli,
                    "trabajo": trab,
                    "fecha_ingreso": fd.strftime("%d/%m/%Y"),
                    "insumos": ins,
                    "responsable": resp,
                    "observaciones": obs,
                    "estado": est,
                    "prioridad": prio,
                    "fecha_estimada": f_est,
                    "fecha_iniciado": f_ini,
                    "tiempo_trabajo": t_t,
                    "tiempo_pausado": t_p,
                    "imagenes": imgs or ""
                })
                estados.add(est or "-")

        # Actualiza los valores del combo de estados si está vacío
        if not cb_est["values"]:
            cb_est["values"] = sorted(estados)
    # ─────────────────────────────
    #  DIÁLOGO DETALLE
    # ─────────────────────────────
    def ver_detalle(item):
        try:
            with conectar() as conn:
                cur = conn.cursor()
                cur.execute(
                    "SELECT fecha_iniciado, fecha_pausada, tiempo_pausado, fecha_final, estado "
                    "FROM ordenes_trabajo WHERE nro_ot = ?",
                    (item["nro_ot"],)
                )
                fila = cur.fetchone()
        except Exception as e:
            messagebox.showerror("Error BD", f"No se pudo obtener datos: {e}", parent=frame)
            return
        if not fila:
            messagebox.showerror("Error", f"OT {item['nro_ot']} no encontrada", parent=frame)
            return

        fecha_ini_str, fecha_pau_str, segs_p, fecha_fin_str, estado = fila
        now = datetime.now()

        # Parsear fechas de inicio y pausa
        try:
            inicio_dt = datetime.strptime(fecha_ini_str, "%d/%m/%Y %H:%M:%S")
        except:
            inicio_dt = None
        try:
            pause_dt = datetime.strptime(fecha_pau_str or "", "%d/%m/%Y %H:%M:%S")
        except:
            pause_dt = None
        segs_prev = int(segs_p or 0)

        # Calcular dinámicamente pausas y trabajo
        total_pausas = timedelta(0)
        trabajo_td   = timedelta(0)

        if estado == "Pausado" and inicio_dt and pause_dt:
            trabajo_td = (pause_dt - inicio_dt) - timedelta(seconds=segs_prev)
            total_pausas = timedelta(seconds=segs_prev) + (now - pause_dt)
        elif estado == "En proceso" and inicio_dt:
            trabajo_td   = (now - inicio_dt) - timedelta(seconds=segs_prev)
            total_pausas = timedelta(seconds=segs_prev)
        elif inicio_dt:
            try:
                fin_dt = datetime.strptime(fecha_fin_str or "", "%d/%m/%Y %H:%M:%S")
            except:
                fin_dt = now
            trabajo_td   = (fin_dt - inicio_dt) - timedelta(seconds=segs_prev)
            total_pausas = timedelta(seconds=segs_prev)
        elif inicio_dt:
            # OT ya finalizada
            try:
                fin_dt = datetime.strptime(fecha_fin_str or "", "%d/%m/%Y %H:%M:%S")
            except:
                fin_dt = now
            trabajo_td   = (fin_dt - inicio_dt) - timedelta(seconds=segs_prev)
            total_pausas = timedelta(seconds=segs_prev)

        # Función de formateo a hh:mm:ss
        def fmt(td: timedelta) -> str:
            secs = int(td.total_seconds())
            h, rem = divmod(secs, 3600)
            m, s   = divmod(rem, 60)
            return f"{h:02d}:{m:02d}:{s:02d}"

        trabajo_fmt = fmt(trabajo_td)
        pausa_fmt   = fmt(total_pausas)


        # ————— Línea original: construcción del diálogo —————
        dlg = tk.Toplevel(frame)
        dlg.title(f"Detalle OT {item['nro_ot']}")
        
        sw, sh = dlg.winfo_screenwidth(), dlg.winfo_screenheight()
        ww, hh = int(sw * 0.6), int(sh * 0.6)
        dlg.geometry(f"{ww}x{hh}+{(sw-ww)//2}+{(sh-hh)//2}")
        dlg.grab_set()

        # División horizontal
        left = tk.Frame(dlg, width=ww//2, bg="white")
        left.pack(side="left", fill="both")
        
        right = tk.Frame(dlg, width=ww//2, bg="white")
        right.pack(side="right", fill="both", expand=True)

        # Imagen con contador
        imgs = [p.strip() for p in item["imagenes"].split(",") if p.strip()]
        idx = 0
        
        lbl_img = tk.Label(left, bg="white")
        lbl_img.pack(expand=True, padx=20, pady=20)
        
        lbl_ctr = tk.Label(left, bg="white")
        lbl_ctr.pack()

        def show_img():
            nonlocal idx
            total = len(imgs)
            if total == 0:
                lbl_img.config(text="No imágenes", image="")
                lbl_ctr.config(text="")
                return
            
            path = imgs[idx]
            if os.path.exists(path):
                im = Image.open(path)
                im.thumbnail((ww//2-40, hh//2))
                ph = ImageTk.PhotoImage(im)
                lbl_img.config(image=ph)
                lbl_img.image = ph
            else:
                lbl_img.config(text="Archivo no existe", image="")
            lbl_ctr.config(text=f"Foto {idx+1}/{total}")

        def prev(): 
            nonlocal idx
            idx = (idx-1) % max(len(imgs), 1)
            show_img()
        
        def nxt():  
            nonlocal idx
            idx = (idx+1) % max(len(imgs), 1)
            show_img()

        nav = tk.Frame(left, bg="white")
        nav.pack(pady=5)
        
        tk.Button(nav, text="←", command=prev).pack(side="left", padx=10)
        tk.Button(nav, text="→", command=nxt).pack(side="left", padx=10)
        show_img()

        # Campos info, usando los cálculos actualizados
        campos = [
            ("OT",             item["nro_ot"]),
            ("Cliente",        item["cliente"]),
            ("Trabajo",        item["trabajo"]),
            ("Fecha de Ingreso",  item["fecha_ingreso"]),
            ("Fecha Estimada", item["fecha_estimada"]),
            ("Fecha de Inicio", item["fecha_iniciado"]),
            ("Tiempo de Trabajo", trabajo_fmt),
            ("Tiempo Pausado", pausa_fmt),
            ("Estado",         estado),
            ("Prioridad",      item["prioridad"]),
            ("Responsable",    item["responsable"]),
            ("Insumos",        item["insumos"]),
            ("Observaciones",  item["observaciones"]),
        ]

        for label, val in campos:
            row = tk.Frame(right, bg="white")
            row.pack(fill="x", pady=3, padx=10)
            tk.Label(row, text=f"{label}:", font=("Arial",11,"bold"), bg="white")\
                .pack(side="left")
            tk.Label(row, text=val or "-", font=("Arial",11), bg="white")\
                .pack(side="left", padx=8)

        # Botón Cerrar
        pie = tk.Frame(right, bg="white")
        pie.pack(pady=15)
        tk.Button(pie, text="Cerrar", bg="#e74c3c", fg="white",
                 command=dlg.destroy)\
            .pack(side="left", padx=10)

        dlg.grab_set()



    # ─────────────────────────────
    #  DIBUJAR TARJETAS
    # ─────────────────────────────
    def draw(items):
        # Limpiar el contenedor
        for wgt in inner.winfo_children():
            wgt.destroy()
        
        # Mostrar mensaje si no hay items
        if not items:
            tk.Label(inner, text="No hay órdenes para mostrar.", 
                     font=("Arial", 14), bg="white")\
              .grid(row=0, column=0, columnspan=NUM_COLUMNS, pady=20)
            return

        # Calcular ancho dinámico basado en el contenedor
        container_width = frame.winfo_width() - 40  # Restar padding
        card_width = max(CARD_WIDTH, (container_width // NUM_COLUMNS) - (2 * CARD_PADX))
        card_height = CARD_HEIGHT
        
        # Crear las tarjetas
        for idx, itm in enumerate(items):
            row, col = divmod(idx, NUM_COLUMNS)
            
            # Frame de la tarjeta
            card = tk.Frame(inner, bg="white", bd=1, relief="solid", 
                            cursor="hand2", highlightthickness=1,
                            highlightbackground="#e0e0e0")
            card.grid(row=row, column=col, padx=CARD_PADX, pady=CARD_PADY, sticky="nsew")
            card.config(width=card_width, height=card_height)
            card.grid_propagate(False)
            
            # Cabecera
            header = tk.Frame(card, bg="white")
            header.pack(fill="x", pady=(8, 0), padx=8)
            
            tk.Label(header, text=f"{itm['nro_ot']}", 
                     font=("Arial", 10, "bold"), bg="white")\
              .pack(side="left")
            
            col_bg = PRIORITY_COL.get(itm["prioridad"], "#cccccc")
            tk.Label(header, text=itm["prioridad"], 
                     font=("Arial", 9, "bold"), bg=col_bg, fg="white",
                     padx=5, pady=2)\
              .pack(side="right")

            # Contenido
            content = tk.Frame(card, bg="white")
            content.pack(fill="both", expand=True, padx=8, pady=4)
            
            # Cliente
            tk.Label(content, text=f"Cliente: {itm['cliente']}", 
                     font=("Arial", 9), bg="white", anchor="w")\
              .pack(fill="x", pady=(0, 4))
            
            # Responsable
            tk.Label(content, text=f"Responsable: {itm['responsable']}", 
                     font=("Arial", 9), bg="white", anchor="w")\
              .pack(fill="x", pady=(0, 4))

            # Estado (NUEVO, MISMO ESTILO)
            tk.Label(content, text=f"Estado: {itm['estado']}", 
                     font=("Arial", 9), bg="white", anchor="w")\
              .pack(fill="x", pady=(0, 4))

            # Trabajo
            short = (itm['trabajo'][:40] + "…") if len(itm['trabajo']) > 40 else itm['trabajo']
            tk.Label(content, text=f"Trabajo: {short}", 
                     font=("Arial", 9), bg="white", anchor="w", 
                     wraplength=card_width-20)\
              .pack(fill="x", pady=(0, 6))

            # Fecha
            tk.Label(content, text=f"Ingreso: {itm['fecha_ingreso']}", 
                     font=("Arial", 8), bg="white", anchor="w")\
              .pack(fill="x")


            # Botón
            footer = tk.Frame(card, bg="white")
            footer.pack(side="bottom", fill="x", pady=(0, 6))
            
            tk.Button(footer, text="Ver Detalle", font=("Arial", 9),
                     command=lambda it=itm: ver_detalle(it))\
              .pack(pady=2)

        # Ajustar scroll
        canvas.configure(scrollregion=canvas.bbox("all"))

    # ─────────────────────────────
    #  REFRESCAR Y WATCHER
    # ─────────────────────────────
    def refrescar(force):
            if force:
                load_data()
            filtrado = filas
            if prio_var.get():
                filtrado = [f for f in filtrado if f["prioridad"] == prio_var.get()]
            if est_var.get():
                filtrado = [f for f in filtrado if f["estado"] == est_var.get()]
            if resp_var.get():
                filtrado = [f for f in filtrado if resp_var.get().lower() in (f["responsable"] or "").lower()]
            if cli_var.get():
                filtrado = [f for f in filtrado if cli_var.get().lower() in (f["cliente"] or "").lower()]
            if fecha_var.get():
                filtrado = [f for f in filtrado if f["fecha_ingreso"] == fecha_var.get()]
            draw(filtrado)


    def watch():
        nonlocal last_mtime
        if not frame.winfo_exists(): 
            return
        
        mt = os.path.getmtime(get_db_path())
        if mt != last_mtime:
            last_mtime = mt
            refrescar(False)
        
        frame.after(POLL_MS, watch)

    # ─────────────────────────────
    #  INICIO
    # ─────────────────────────────
    load_data()
    refrescar(True)
    frame.after(POLL_MS, watch)