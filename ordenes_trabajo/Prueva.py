import tkinter as tk
from tkinter import ttk
from tkcalendar import DateEntry
from datetime import datetime, date

def crear_campo(frame, label_text, valor=None, tipo='entry', ancho=30, alto=None):
    tk.Label(frame, text=f"{label_text}:", bg="#f2f2f2", font=("Arial",10,"bold")).pack(anchor='w', pady=(5,0))
    if tipo == 'entry':
        w = ttk.Entry(frame, width=ancho)
        if valor is not None: w.insert(0, valor)
    elif tipo == 'text':
        w = tk.Text(frame, width=ancho, height=alto or 4, wrap='word')
        if valor is not None: w.insert('1.0', valor)
    elif tipo == 'combobox':
        w = ttk.Combobox(frame, values=valor or [], state='readonly', width=ancho-2)
        if valor and isinstance(valor, str): w.set(valor)
    elif tipo == 'date':
        w = DateEntry(frame, date_pattern='dd/MM/yyyy', width=ancho-3)
        if valor:
            try:
                d = datetime.strptime(valor, '%Y-%m-%d').date()
                w.set_date(d)
            except:
                pass
    w.pack(anchor='w', pady=(0,5))
    return w

def prueba_ui_v7_adjust():
    root = tk.Tk()
    root.title("Prueba Formulario V7 Ajustado")
    root.configure(bg="#f2f2f2")
    root.geometry("900x650")

    cont = tk.Frame(root, bg="#f2f2f2")
    cont.pack(padx=20, pady=10, fill="both", expand=True)

    # Panel izquierdo
    frame_izq = tk.Frame(cont, bg="#f2f2f2", width=380)
    frame_izq.pack(side="left", fill="y")

    datos = {
        'nro_ot': 'OT001','estado': 'Pendiente','es_cliente': True,
        'cliente': 'Cliente A','codigo_equipo': 'EQ123',
        'fecha_ingreso': date.today().strftime('%Y-%m-%d'),
        'fecha_iniciado': None,'fecha_estimada': date.today().strftime('%Y-%m-%d'),
        'prioridad': 'Media',
    }

    crear_campo(frame_izq, 'N° OT', datos['nro_ot'], tipo='entry').config(state='disabled')
    combo_estado = crear_campo(frame_izq, 'Estado', datos['estado'], tipo='combobox')
    combo_estado['values'] = ['Pendiente','En proceso','Realizado','Cancelada']
    combo_estado.config(state='disabled')

    if datos['es_cliente']:
        crear_campo(frame_izq, 'Cliente', datos['cliente'], tipo='combobox').config(values=[datos['cliente'], 'Otro Cliente'])
        crear_campo(frame_izq, 'Fecha Ingreso', datos['fecha_ingreso'], tipo='date')
        e_start = crear_campo(frame_izq, 'Fecha Inicio', datos['fecha_iniciado'], tipo='entry')
        e_start.delete(0, tk.END)
        e_est = crear_campo(frame_izq, 'Fecha Estimada', datos['fecha_estimada'], tipo='entry')
        e_est.delete(0, tk.END)
        e_est.insert(0, datetime.strptime(datos['fecha_estimada'], '%Y-%m-%d').strftime('%d/%m/%Y'))
    else:
        combo_eq = crear_campo(frame_izq, 'Equipo', datos['codigo_equipo'], tipo='combobox')
        combo_eq.config(values=[datos['codigo_equipo'], 'EQ999'])
        crear_campo(frame_izq, 'Fecha Realización', datos['fecha_ingreso'], tipo='date')

    combo_prio = crear_campo(frame_izq, 'Prioridad', datos['prioridad'], tipo='combobox')
    combo_prio.config(values=['Alta','Media','Baja'])

    # Botones en panel izquierdo: Guardar e Iniciar arriba de listboxes
    frame_acc = tk.Frame(frame_izq, bg="#f2f2f2")
    frame_acc.pack(fill='x', pady=(20,0))
    tk.Button(frame_acc, text="Guardar", width=12).pack(side='left', padx=(0,5))
    tk.Button(frame_acc, text="Iniciar Trabajo", width=15, bg='#2196F3', fg='white').pack(side='left')

    # Panel derecho
    frame_der = tk.Frame(cont, bg="#f2f2f2")
    frame_der.pack(side="left", fill="both", expand=True, padx=10)

    # Operación y Observaciones arriba
    tk.Label(frame_der, text="Operación a realizar:", bg="#f2f2f2", font=("Arial",10,"bold")).pack(anchor='w', pady=(5,0))
    tk.Text(frame_der, width=30, height=6, wrap='word').pack(fill='x', pady=(0,10))
    tk.Label(frame_der, text="Observaciones:", bg="#f2f2f2", font=("Arial",10,"bold")).pack(anchor='w', pady=(5,0))
    tk.Text(frame_der, width=30, height=6, wrap='word').pack(fill='x', pady=(0,10))

    # Listboxes con botones +
    frame_bot = tk.Frame(frame_der, bg="#f2f2f2")
    frame_bot.pack(anchor='w', fill='x', pady=(10,0))
    for label_text in ("Insumos","Herramientas","Responsables"):
        sub = tk.Frame(frame_bot, bg="#f2f2f2")
        sub.pack(side='left', fill='both', expand=True, padx=5)
        hdr = tk.Frame(sub, bg="#f2f2f2"); hdr.pack(fill='x')
        tk.Label(hdr, text=f"{label_text}:", bg="#f2f2f2", font=("Arial",10,"bold")).pack(side='left')
        tk.Button(hdr, text='+', width=2, bg='#3498db', fg='white').pack(side='left', padx=(5,0))
        tk.Listbox(sub, height=5).pack(fill='both', expand=True, pady=(5,0))

    # Imágenes debajo de listboxes
    tk.Label(frame_der, text="Imágenes:", bg="#f2f2f2", font=("Arial",10,"bold")).pack(anchor='w', pady=(10,0))
    frame_imgs = tk.Frame(frame_der, bg="#f2f2f2")
    frame_imgs.pack(fill='x', pady=(0,10))
    for i in range(4):
        tk.Label(frame_imgs, text=f"Img {i+1}", bg="gray80", width=20, height=8, relief='ridge').pack(side='left', padx=5)

    # Botón Salir abajo a la derecha
    footer = tk.Frame(root, bg="#f2f2f2")
    footer.pack(fill='x', side='bottom', pady=10, padx=10)
    tk.Button(footer, text="Salir", width=12, bg='#f44336', fg='white', command=root.destroy).pack(side='right')

    root.mainloop()

if __name__ == "__main__":
    prueba_ui_v7_adjust()
