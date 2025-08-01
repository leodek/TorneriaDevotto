import tkinter as tk
from tkinter import ttk
from ordenes_trabajo.ordenes_trabajo import mostrar_ordenes_trabajo
from ordenes_trabajo.Ot_2semanas import mostrar_proximas_ot as mostrar_ordenes_una_semana

class AutoRefreshNotebook(ttk.Notebook):
    """Notebook que solo refresca al cambiar realmente de pestaña."""
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.tab_handlers = {}
        self._last_tab = None
        self.bind("<<NotebookTabChanged>>", self._on_tab_changed)

    def add_tab(self, frame, text, update_func):
        """Añade la pestaña y registra su función."""
        self.add(frame, text=text)
        self.tab_handlers[text] = (frame, update_func)

    def _on_tab_changed(self, _):
        tab_text = self.tab(self.select(), "text")
        # si es la misma que antes, no hacemos nada
        if tab_text == self._last_tab:
            return
        self._last_tab = tab_text

        frame, update_func = self.tab_handlers[tab_text]
        # limpiamos y refrescamos
        for w in frame.winfo_children():
            w.destroy()
        update_func(frame)


def mostrar_ordenes_en_pestanas(frame_principal):
    # limpiamos contenedor
    for w in frame_principal.winfo_children():
        w.destroy()
    frame_principal.configure(bg="white")

    # Creamos el notebook
    notebook = AutoRefreshNotebook(frame_principal)

    # Pestaña 1: lista completa
    pestaña_todas = tk.Frame(notebook, bg="white")
    notebook.add_tab(pestaña_todas, "Lista de Trabajos", mostrar_ordenes_trabajo)

    # Pestaña 2: próximas
    pestaña_prox = tk.Frame(notebook, bg="white")
    notebook.add_tab(pestaña_prox, "Tarjetas de Trabajo", mostrar_ordenes_una_semana)

    notebook.pack(fill="both", expand=True, padx=10, pady=10)

    # Cargamos solo la primera (evitamos doble)
    mostrar_ordenes_trabajo(pestaña_todas)
    notebook._last_tab = "Lista de Trabajos"
