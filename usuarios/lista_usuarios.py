import tkinter as tk
from tkinter import ttk
import sqlite3
from usuarios.agregar_usuario import abrir_formulario_agregar
from usuarios.modificar_usuario import abrir_modificar_usuario
import sqlite3
from db_init import get_db_path, conectar



def mostrar_lista_usuarios(frame):
    for widget in frame.winfo_children():
        widget.destroy()

    frame.configure(bg="white")

    tk.Label(frame, text="LISTA DE USUARIOS", font=("Arial", 22, "bold"),
             bg="white", fg="#2c3e50").pack(pady=(20, 10))

    frame_filtros = tk.Frame(frame, bg="white")
    frame_filtros.pack(fill=tk.X, padx=10, pady=10)

    tk.Label(frame_filtros, text="Usuario:", bg="white").grid(row=0, column=0, padx=5)
    entry_usuario = tk.Entry(frame_filtros)
    entry_usuario.grid(row=0, column=1, padx=5)

    tk.Label(frame_filtros, text="Nombre:", bg="white").grid(row=0, column=2, padx=5)
    entry_nombre = tk.Entry(frame_filtros)
    entry_nombre.grid(row=0, column=3, padx=5)

    tk.Label(frame_filtros, text="Rol:", bg="white").grid(row=0, column=4, padx=5)
    combo_rol = ttk.Combobox(frame_filtros, values=["", "admin", "supervisor", "operario"], state="readonly", width=15)
    combo_rol.grid(row=0, column=5, padx=5)
    combo_rol.set("")

    def buscar_usuarios():
        usuario = entry_usuario.get().strip()
        nombre = entry_nombre.get().strip()
        rol = combo_rol.get().strip()

        query = "SELECT id, usuario, contraseña, nombre, rol, imagen FROM usuarios WHERE 1=1"
        params = []

        if usuario:
            query += " AND usuario LIKE ?"
            params.append(f"%{usuario}%")
        if nombre:
            query += " AND nombre LIKE ?"
            params.append(f"%{nombre}%")
        if rol:
            query += " AND rol = ?"
            params.append(rol)

        conn = conectar()
        cur = conn.cursor()
        cur.execute(query, tuple(params))
        resultados = cur.fetchall()
        conn.close()

        tree.delete(*tree.get_children())
        for fila in resultados:
            tree.insert("", tk.END, values=fila)

    tk.Button(frame_filtros, text="Buscar", command=buscar_usuarios,
              bg="#3498db", fg="white", width=12).grid(row=0, column=6, padx=10)

    tk.Button(frame_filtros, text="Nuevo Usuario",
              command=lambda: abrir_formulario_agregar(actualizar_callback=buscar_usuarios),
              bg="#2ecc71", fg="white", width=15).grid(row=0, column=7, padx=10)

    frame_tabla = tk.Frame(frame)
    frame_tabla.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

    columnas = ("id", "usuario", "contraseña", "nombre", "rol", "imagen")
    tree = ttk.Treeview(frame_tabla, columns=columnas, show="headings")
    for col in columnas:
        tree.heading(col, text=col.capitalize())
        tree.column(col, anchor="center", width=120)
    tree.pack(fill=tk.BOTH, expand=True)

    def on_doble_click(event):
        item = tree.selection()
        if item:
            valores = tree.item(item[0], "values")
            abrir_modificar_usuario(valores, actualizar_callback=buscar_usuarios)

    tree.bind("<Double-1>", on_doble_click)
    buscar_usuarios()
