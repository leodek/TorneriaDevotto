# File: ot_ui_elements.py
import tkinter as tk
from tkinter import ttk
from tkcalendar import DateEntry
from datetime import datetime # Necesario para parsear fechas si se usa el tipo 'date'
import sqlite3
from db_init import get_db_path


def crear_campo(frame, label_text, valor=None, tipo='entry', ancho=30, alto=None):
    """
    Crea un label y un widget de entrada (Entry, Text, Combobox, DateEntry)
    dentro de un frame dado.
    """
    tk.Label(frame, text=f"{label_text}:", bg="#f2f2f2", font=("Arial",10,"bold")).pack(anchor='w', pady=(5,0))
    if tipo == 'entry':
        w = ttk.Entry(frame, width=ancho)
        if valor is not None:
            w.insert(0, valor)
    elif tipo == 'text':
        w = tk.Text(frame, width=ancho, height=alto or 4, wrap='word')
        if valor is not None:
            w.insert('1.0', valor)
    elif tipo == 'combobox':
        # Asegurarse de que valor sea una lista para values
        values_list = valor if isinstance(valor, list) else ([valor] if valor is not None else [])
        w = ttk.Combobox(frame, values=values_list, state='readonly', width=ancho-2)
        if valor and isinstance(valor, str): # Si el valor inicial es una cadena, establecerlo
             w.set(valor)
    elif tipo == 'date':
        w = DateEntry(frame, date_pattern='dd/MM/yyyy', width=ancho-3)
        if valor:
            try:
                # Intentar establecer la fecha si el valor es una cadena de fecha válida
                d = datetime.strptime(valor, '%Y-%m-%d').date()
                w.set_date(d)
            except (ValueError, TypeError):
                # Manejar casos donde el valor no es una fecha válida
                pass # O podrías establecer una fecha por defecto o dejarla vacía
    w.pack(anchor='w', pady=(0,5))
    return w

# Puedes agregar otras funciones genéricas de UI aquí si las tienes o las creas en el futuro.
# Por ejemplo:
# def crear_boton(frame, text, command, bg, fg, font, width):
#     btn = tk.Button(frame, text=text, command=command, bg=bg, fg=fg, font=font, width=width)
#     btn.pack(pady=5)
#     return btn

