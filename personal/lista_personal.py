import tkinter as tk
from tkinter import ttk
import sqlite3
from personal.agregar_personal import abrir_formulario_agregar_personal
from personal.modificar_personal import abrir_formulario_modificar_personal
from db_init import get_db_path, conectar




def mostrar_lista_personal(frame):
    for widget in frame.winfo_children():
        widget.destroy()

    frame.configure(bg="white")
    frame.columnconfigure(0, weight=1)

    tk.Label(frame, text="GESTIÓN DE PERSONAL", font=("Arial", 20, "bold"),
             bg="white", fg="#2c3e50").grid(row=0, column=0, sticky="w", padx=20, pady=(20, 10))

    # === Fila de checkbox y botón de ingreso ===
    fila_superior = tk.Frame(frame, bg="white")
    fila_superior.grid(row=1, column=0, sticky="ew", padx=20)
    fila_superior.columnconfigure(0, weight=1)

    mostrar_filtros_var = tk.BooleanVar(value=False)

    def toggle_filtros():
        if mostrar_filtros_var.get():
            contenedor_filtros.grid()
        else:
            contenedor_filtros.grid_remove()

    tk.Checkbutton(fila_superior, text="Mostrar filtros", variable=mostrar_filtros_var,
                   command=toggle_filtros, bg="white").grid(row=0, column=0, sticky="w")

    tk.Button(fila_superior, text="INGRESAR PERSONAL", bg="#27ae60", fg="white",
          font=("Arial", 10, "bold"), width=25,
          command=lambda: abrir_formulario_agregar_personal(actualizar_callback=cargar_datos)).grid(row=0, column=1, sticky="e")


    # === Contenedor que limita el ancho del recuadro de filtros ===
    contenedor_filtros = tk.Frame(frame, bg="white", width=800)
    contenedor_filtros.grid_propagate(False)
    contenedor_filtros.grid(row=2, column=0, sticky="n", padx=20)
    contenedor_filtros.grid_remove()  # oculto al inicio

    filtro_frame = tk.LabelFrame(contenedor_filtros, text="FILTROS DE BÚSQUEDA", bg="white",
                                 font=("Arial", 10, "bold"), labelanchor="nw", padx=10, pady=10)
    filtro_frame.pack(anchor="n")

    filtros_contenido_frame = tk.Frame(filtro_frame, bg="white")
    filtros_contenido_frame.grid(row=0, column=0, padx=10, pady=10)

    campos = [
        ("numero_operario", "Nº Operario"),
        ("nombre_completo", "Nombre completo"),
        ("cargo", "Cargo"),
        ("sector", "Sector"),
        ("telefono", "Teléfono"),
    ]

    variables = {}

    def borrar_y_actualizar(event, var, widget):
        var.set("")
        if isinstance(widget, ttk.Combobox):
            widget.set("")
        else:
            widget.delete(0, tk.END)
        cargar_datos()

    for i, (campo, etiqueta) in enumerate(campos):
        tk.Label(filtros_contenido_frame, text=etiqueta + ":", bg="white").grid(row=i, column=0, padx=5, pady=5, sticky="e")
        var = tk.StringVar()
        variables[campo] = var
        entry = tk.Entry(filtros_contenido_frame, textvariable=var, width=30, relief="solid", bd=1)
        entry.grid(row=i, column=1, padx=5)
        entry.bind("<KeyRelease>", lambda e: cargar_datos())
        for tecla in ("<Delete>", "<BackSpace>"):
            entry.bind(tecla, lambda e, v=var, w=entry: borrar_y_actualizar(e, v, w))

    tk.Button(filtros_contenido_frame, text="Buscar", command=lambda: cargar_datos(),
              bg="#2980b9", fg="white", width=12).grid(row=0, column=2, padx=10)
    tk.Button(filtros_contenido_frame, text="Limpiar", command=lambda: limpiar_filtros(),
              bg="#e74c3c", fg="white", width=12).grid(row=1, column=2, padx=10)

    # === Tabla de resultados ===
    columnas = [campo for campo, _ in campos]
    tree_frame = tk.Frame(frame, bg="white")
    tree_frame.grid(row=3, column=0, sticky="nsew", padx=20, pady=(0, 10))
    frame.rowconfigure(3, weight=1)

    tree_scroll = tk.Scrollbar(tree_frame)
    tree_scroll.pack(side="right", fill="y")

    tree = ttk.Treeview(tree_frame, columns=columnas, show="headings", yscrollcommand=tree_scroll.set, height=16)
    tree_scroll.config(command=tree.yview)

    for col in columnas:
        ancho = 150 if col == "nombre_completo" else 100
        tree.heading(col, text=col.replace("_", " ").upper())
        tree.column(col, width=ancho, anchor="center")

    tree.pack(fill="both", expand=True)
    
    def doble_click(event):
        item = tree.selection()
        if item:
          valores = tree.item(item[0])["values"]
          datos = dict(zip(columnas, valores))
          abrir_formulario_modificar_personal(datos, actualizar_callback=cargar_datos)

    tree.bind("<Double-1>", doble_click)

    
    def cargar_datos():
        tree.delete(*tree.get_children())
        conn = conectar()
        cursor = conn.cursor()
        query = "SELECT numero_operario, nombre_completo, cargo, sector, telefono FROM personal WHERE 1=1"
        params = []

        for campo, var in variables.items():
            if var.get():
                query += f" AND {campo} LIKE ?"
                params.append(f"%{var.get()}%")

        cursor.execute(query, params)
        for row in cursor.fetchall():
            tree.insert("", tk.END, values=row)
        conn.close()

    def limpiar_filtros():
        for var in variables.values():
            var.set("")
        cargar_datos()

    cargar_datos()
