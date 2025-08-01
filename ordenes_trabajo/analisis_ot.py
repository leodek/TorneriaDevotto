import tkinter as tk
from tkinter import ttk
import sqlite3
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import re

def mostrar_analisis_ot(frame):
    """
    Dentro de `frame` crea un Combobox con 8 opciones de gráficos y un área
    donde se dibujan los gráficos de análisis de órdenes de trabajo.
    """
    # — Selección de gráfica —
    sel_frame = ttk.Frame(frame)
    sel_frame.pack(fill="x", pady=10, padx=10)

    opciones = [
        "Distribución de OTs por Estado",
        "Distribución por Prioridad",
        "Tipo de Orden de Trabajo",
        "Carga de Trabajo por Equipo",
        "Uso de Insumos - Top 10",
        "Uso de Herramientas - Top 10",
        "Distribución por Responsable",
        "Top Operaciones Realizadas"
    ]
    combo = ttk.Combobox(sel_frame, values=opciones, state="readonly", width=32)
    combo.pack(side="left", padx=(0,10))
    combo.current(0)

    # — Área de dibujo —
    graf_frame = tk.Frame(frame, bg="white")
    graf_frame.pack(fill="both", expand=True, padx=10, pady=(0,10))

    # — Funciones de cada gráfico —
    def graf_estado(parent):
        conn = sqlite3.connect("mantenimiento.db")
        cur = conn.cursor()
        cur.execute("SELECT estado, COUNT(*) FROM ordenes_trabajo GROUP BY estado")
        data = cur.fetchall()
        conn.close()

        labels, vals = zip(*data) if data else (["Sin datos"], [1])
        fig, ax = plt.subplots()
        bars = ax.bar(labels, vals)
        ax.set_title("Distribución de OTs por Estado")
        ax.set_ylabel("Cantidad")
        ax.bar_label(bars, rotation=90, label_type='center')

        canvas = FigureCanvasTkAgg(fig, parent)
        canvas.get_tk_widget().pack(fill="both", expand=True)
        canvas.draw()
        plt.close(fig)

    def graf_prioridad(parent):
        conn = sqlite3.connect("mantenimiento.db")
        cur = conn.cursor()
        cur.execute("SELECT prioridad, COUNT(*) FROM ordenes_trabajo GROUP BY prioridad")
        data = cur.fetchall()
        conn.close()

        labels, vals = zip(*data) if data else ([], [])
        fig, ax = plt.subplots()
        bars = ax.bar(labels, vals)
        ax.set_title("Distribución por Prioridad")
        ax.set_ylabel("Cantidad")
        ax.bar_label(bars, rotation=90, label_type='center')
        if labels:
            plt.setp(ax.get_xticklabels(), rotation=45, ha='right')

        canvas = FigureCanvasTkAgg(fig, parent)
        canvas.get_tk_widget().pack(fill="both", expand=True)
        canvas.draw()
        plt.close(fig)

    def graf_tipo_ot(parent):
        conn = sqlite3.connect("mantenimiento.db")
        cur = conn.cursor()
        cur.execute("SELECT nro_op FROM ordenes_trabajo")
        data = [row[0] or "" for row in cur.fetchall()]
        conn.close()

        preventivo = sum(1 for op in data if op.upper().startswith("OP"))
        diarias    = sum(1 for op in data if op.upper().startswith("OD"))
        sizes = [preventivo, diarias]
        labels = [
            f"Mantenimiento Preventivo\n{preventivo} OTs",
            f"Órdenes Diarias\n{diarias} OTs"
        ]

        fig, ax = plt.subplots()
        wedges = ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
        ax.set_title("Tipo de Orden de Trabajo", pad=20)

        canvas = FigureCanvasTkAgg(fig, parent)
        canvas.get_tk_widget().pack(fill="both", expand=True)
        canvas.draw()
        plt.close(fig)

    def graf_carga_equipo(parent):
        conn = sqlite3.connect("mantenimiento.db")
        cur = conn.cursor()
        cur.execute("SELECT codigo_equipo, COUNT(*) FROM ordenes_trabajo GROUP BY codigo_equipo")
        data = cur.fetchall()
        conn.close()

        labels, vals = zip(*sorted(data, key=lambda x: x[1], reverse=True)) if data else ([], [])
        fig, ax = plt.subplots()
        bars = ax.bar(labels, vals)
        ax.set_title("Carga de Trabajo por Equipo")
        ax.set_ylabel("Cantidad")
        ax.bar_label(bars, rotation=90, label_type='center')
        if labels:
            plt.setp(ax.get_xticklabels(), rotation=45, ha='right')

        canvas = FigureCanvasTkAgg(fig, parent)
        canvas.get_tk_widget().pack(fill="both", expand=True)
        canvas.draw()
        plt.close(fig)

    def graf_insumos(parent):
        conn = sqlite3.connect("mantenimiento.db")
        cur = conn.cursor()
        cur.execute("SELECT insumos FROM ordenes_trabajo WHERE insumos IS NOT NULL")
        raws = [row[0] for row in cur.fetchall()]
        conn.close()

        conteo = {}
        for raw in raws:
            for item in raw.split(","):
                m = re.match(r"^(.*?)\s*\(Cant:\s*([\d\.]+)", item.strip())
                if m:
                    nm, qt = m.group(1).strip(), float(m.group(2))
                    conteo[nm] = conteo.get(nm, 0) + qt
                else:
                    nm = item.split("(")[0].strip()
                    conteo[nm] = conteo.get(nm, 0) + 1

        top10 = sorted(conteo.items(), key=lambda x: x[1], reverse=True)[:10]
        labels, vals = zip(*top10) if top10 else ([], [])
        fig, ax = plt.subplots()
        bars = ax.bar(labels, vals)
        ax.set_title("Uso de Insumos - Top 10")
        ax.set_ylabel("Cantidad")
        ax.bar_label(bars, rotation=90, label_type='center')
        if labels:
            plt.setp(ax.get_xticklabels(), rotation=45, ha='right')

        canvas = FigureCanvasTkAgg(fig, parent)
        canvas.get_tk_widget().pack(fill="both", expand=True)
        canvas.draw()
        plt.close(fig)

    def graf_herramientas(parent):
        conn = sqlite3.connect("mantenimiento.db")
        cur = conn.cursor()
        cur.execute("SELECT herramientas FROM ordenes_trabajo WHERE herramientas IS NOT NULL")
        raws = [row[0] for row in cur.fetchall()]
        conn.close()

        conteo = {}
        for raw in raws:
            for item in raw.split(","):
                nm = item.strip()
                conteo[nm] = conteo.get(nm, 0) + 1

        top10 = sorted(conteo.items(), key=lambda x: x[1], reverse=True)[:10]
        labels, vals = zip(*top10) if top10 else ([], [])
        fig, ax = plt.subplots()
        bars = ax.bar(labels, vals)
        ax.set_title("Uso de Herramientas - Top 10")
        ax.set_ylabel("Veces Usada")
        ax.bar_label(bars, rotation=90, label_type='center')
        if labels:
            plt.setp(ax.get_xticklabels(), rotation=45, ha='right')

        canvas = FigureCanvasTkAgg(fig, parent)
        canvas.get_tk_widget().pack(fill="both", expand=True)
        canvas.draw()
        plt.close(fig)

    def graf_responsable(parent):
        conn = sqlite3.connect("mantenimiento.db")
        cur = conn.cursor()
        cur.execute("SELECT responsable, COUNT(*) FROM ordenes_trabajo GROUP BY responsable")
        data = cur.fetchall()
        conn.close()

        labels, vals = zip(*data) if data else ([], [])
        fig, ax = plt.subplots()
        bars = ax.bar(labels, vals)
        ax.set_title("Distribución por Responsable")
        ax.set_ylabel("Cantidad")
        ax.bar_label(bars, rotation=90, label_type='center')
        if labels:
            plt.setp(ax.get_xticklabels(), rotation=45, ha='right')

        canvas = FigureCanvasTkAgg(fig, parent)
        canvas.get_tk_widget().pack(fill="both", expand=True)
        canvas.draw()
        plt.close(fig)

    def graf_operaciones(parent):
        conn = sqlite3.connect("mantenimiento.db")
        cur = conn.cursor()
        cur.execute("SELECT operacion, COUNT(*) FROM ordenes_trabajo GROUP BY operacion")
        data = cur.fetchall()
        conn.close()

        labels, vals = zip(*data) if data else ([], [])
        fig, ax = plt.subplots()
        bars = ax.bar(labels, vals)
        ax.set_title("Top Operaciones Realizadas")
        ax.set_ylabel("Cantidad")
        ax.bar_label(bars, rotation=90, label_type='center')
        if labels:
            plt.setp(ax.get_xticklabels(), rotation=45, ha='right')

        canvas = FigureCanvasTkAgg(fig, parent)
        canvas.get_tk_widget().pack(fill="both", expand=True)
        canvas.draw()
        plt.close(fig)

    # — Mapeo y callback —
    graph_funcs = {
        opciones[0]: graf_estado,
        opciones[1]: graf_prioridad,
        opciones[2]: graf_tipo_ot,
        opciones[3]: graf_carga_equipo,
        opciones[4]: graf_insumos,
        opciones[5]: graf_herramientas,
        opciones[6]: graf_responsable,
        opciones[7]: graf_operaciones,
    }

    def on_change(event=None):
        for w in graf_frame.winfo_children():
            w.destroy()
        fn = graph_funcs.get(combo.get())
        if fn:
            fn(graf_frame)

    combo.bind("<<ComboboxSelected>>", on_change)
    on_change()
