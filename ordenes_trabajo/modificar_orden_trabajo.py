import os
import sys
import sqlite3
from datetime import datetime, timedelta
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from tkcalendar import DateEntry
import sqlite3
from db_init import get_db_path
from db_init import conectar, get_db_path

conn = sqlite3.connect(get_db_path())

# Configuración de paths
base_dir = os.path.dirname(__file__)
root_dir = os.path.abspath(os.path.join(base_dir, os.pardir))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

# Importar selectores modificados
from insumos.selector_insumos import mostrar_selector_insumos
from personal.selector_personal import mostrar_selector_responsables
from insumos.selector_herramientas import mostrar_selector_herramientas

def crear_campo(frame, label_text, valor=None, tipo='entry', ancho=30, alto=None):
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
        w = ttk.Combobox(frame, values=valor or [], state='readonly', width=ancho-2)
        if valor and isinstance(valor, str):
            w.set(valor)
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

def abrir_formulario_modificar_ot(datos_ot, actualizar_callback=None, parent=None):
    # Si se pasó solo el número de OT (string), cargar los datos desde la BD
    if isinstance(datos_ot, str):
        with conectar() as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM ordenes_trabajo WHERE nro_ot = ?",
                (datos_ot,)
            )
            fila = cur.fetchone()
            if not fila:
                messagebox.showerror("Error", f"No se encontró la OT {datos_ot}", parent=parent)
                return
            datos_ot = dict(fila)

    ventana = tk.Toplevel()
    ventana.title("Formulario OT - Versión Integrada")
    ventana.configure(bg="#f2f2f2")

    # Variables para control de tiempo
    tiempo_inicio = None
    tiempo_pausa_inicio = None
    tiempo_total_pausado = timedelta()

    # Centrar ventana
    window_width = 900
    window_height = 700
    screen_width = ventana.winfo_screenwidth()
    screen_height = ventana.winfo_screenheight()
    center_x = int(screen_width / 2 - window_width / 2)
    center_y = int(screen_height / 2 - window_height / 2)
    ventana.geometry(f"{window_width}x{window_height}+{center_x}+{center_y}")
    ventana.resizable(False, False)
    ventana.grab_set()

    # Estado dirty para cambios
    dirty = False
    def marcar_dirty(event=None):
        nonlocal dirty
        dirty = True

    # Resto del código del formulario aquí...
    # Por ejemplo: cargar campos, mostrar fecha_ingreso, fecha_iniciado, etc.


    def cargar_datos():
        with conectar() as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(
                "SELECT nro_ot, nro_op, cliente, trabajo, prioridad, observaciones, "
                "insumos, herramientas, responsable, estado, fecha "
                "FROM ordenes_trabajo WHERE nro_ot = ?",
                (datos_ot["nro_ot"],)
            )
            row = cur.fetchone()
            if not row:
                raise ValueError(f"No existe OT {datos_ot['nro_ot']}")

            datos = {
                'nro_ot':       row[0],
                'nro_op':       row[1],
                'cliente':      row[2],
                'trabajo':      row[3],
                'prioridad':    row[4],
                'observaciones':row[5],
                'insumos':      row[6],
                'herramientas': row[7],
                'responsable':  row[8],
                'estado':       row[9],
                'fecha':        row[10],
            }
            return datos

            
            # Procesamiento mejorado de insumos
            initial_insumos = {}
            for raw in (datos['insumos'] or "").split(","):
                raw = raw.strip()
                if not raw or "-" not in raw: 
                    continue
                    
                try:
                    # Formato esperado: "CODIGO - Descripción (CANTIDAD unidad)"
                    cod, resto = raw.split(" - ", 1)
                    _, cant = resto.rsplit("(", 1)
                    initial_insumos[cod.strip()] = {
                        'descripcion': resto.split(")")[0].strip(),
                        'cantidad': float(cant.strip(") ").split()[0]),
                        'unidad': cant.strip(") ").split()[1] if len(cant.strip(") ").split()) > 1 else "un"
                    }
                except Exception as e:
                    print(f"Error procesando insumo '{raw}': {e}")
                    continue
                    
            datos['insumos_dict'] = initial_insumos  # Nuevo campo estructurado
            
            datos['es_cliente'] = bool(datos['nro_op'] and datos['nro_op'].upper().startswith("OD"))
            if datos['es_cliente']:
                cur.execute(
                    "SELECT cliente,fecha_ingreso,fecha_iniciado,fecha_estimada,fecha_final,"
                    "tiempo_pausado,imagenes "
                    "FROM ordenes_trabajo WHERE codigo=?",
                    (datos['nro_op'],)
                )
                row2 = cur.fetchone() or [None]*7
                datos.update({
                    'cliente': row2[0],
                    'fecha_ingreso': row2[1],
                    'fecha_iniciado': row2[2],
                    'fecha_estimada': row2[3],
                    'fecha_final': row2[4],
                    'tiempo_pausado': float(row2[5] or 0) if row2[5] is not None else 0
                })
                if datos['fecha_iniciado']:
                    try:
                        nonlocal tiempo_inicio
                        tiempo_inicio = datetime.strptime(datos['fecha_iniciado'], '%Y-%m-%d %H:%M:%S')
                    except:
                        tiempo_inicio = None
                if datos['estado'] == 'Realizado' and datos['fecha_iniciado'] and datos['fecha_final']:
                    try:
                        inicio = datetime.strptime(datos['fecha_iniciado'], '%Y-%m-%d %H:%M:%S')
                        fin = datetime.strptime(datos['fecha_final'], '%Y-%m-%d %H:%M:%S')
                        pausado = timedelta(seconds=datos['tiempo_pausado'])
                        delta = (fin - inicio) - pausado
                        dias = delta.days
                        horas = delta.seconds // 3600
                        minutos = (delta.seconds % 3600) // 60
                        if dias > 0:
                            datos['tiempo_trabajo'] = f"{dias} días, {horas} horas"
                        else:
                            datos['tiempo_trabajo'] = f"{horas} horas, {minutos} minutos"
                    except Exception as e:
                        print(f"Error calculando tiempo de trabajo: {e}")
                        datos['tiempo_trabajo'] = "No calculado"
                imagenes_str = row2[6] or ""
                datos['imagenes'] = [img.strip() for img in imagenes_str.split(',') if img.strip()]
                datos['imagenes'] = [img for img in datos['imagenes'] if os.path.exists(img)]
            return datos

    datos = cargar_datos()
    
    # Flags de estado según datos cargados
    en_proceso = datos['estado'] == 'En proceso'
    finalizada = datos['estado'] == 'Realizado'
    pausado = datos['estado'] == 'Pausado'

    # Contenedor principal
    cont = tk.Frame(ventana, bg="#f2f2f2")
    cont.pack(padx=20, pady=10, fill="both", expand=True)

    # PANEL IZQUIERDO
    frame_izq = tk.Frame(cont, bg="#f2f2f2", width=380)
    frame_izq.pack(side="left", fill="y")

    entry_ot = crear_campo(frame_izq, 'N° OT', datos['nro_ot'], tipo='entry')
    entry_ot.config(state='disabled')

    combo_estado = crear_campo(frame_izq, 'Estado', datos['estado'], tipo='combobox')
    combo_estado['values'] = ['Pendiente', 'En proceso', 'Realizado', 'Cancelada']
    combo_estado.config(state='disabled')

    if datos['es_cliente']:
        combo_cli = crear_campo(frame_izq, 'Cliente', datos['cliente'], tipo='combobox')
        combo_cli['values'] = [datos['cliente']] + ["Cliente B", "Cliente C"]
        
        crear_campo(frame_izq, 'Fecha Ingreso', datos['fecha_ingreso'], tipo='date')
        
        e_start = crear_campo(frame_izq, 'Fecha Inicio', datos['fecha_iniciado'], tipo='entry')
        if datos['fecha_iniciado']:
            e_start.delete(0, tk.END)
            e_start.insert(0, datetime.strptime(datos['fecha_iniciado'], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y %H:%M'))
            e_start.config(state='disabled')
        
        e_est = crear_campo(frame_izq, 'Fecha Estimada', datos['fecha_estimada'], tipo='entry')
        if datos['fecha_final']:
            e_est.delete(0, tk.END)
            e_est.insert(0, datetime.strptime(datos['fecha_final'], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y %H:%M'))
            e_est.config(state='disabled')
            
            if finalizada and 'tiempo_trabajo' in datos:
                tk.Label(frame_izq, text="Tiempo de trabajo:", bg="#f2f2f2", font=("Arial",10,"bold")).pack(anchor='w', pady=(5,0))
                tiempo_entry = ttk.Entry(frame_izq, width=30)
                tiempo_entry.insert(0, datos['tiempo_trabajo'])
                tiempo_entry.config(state='readonly')
                tiempo_entry.pack(anchor='w', pady=(0,5))
    else:
        combo_eq = crear_campo(frame_izq, 'Equipo', datos['cliente'], tipo='combobox')
        combo_eq['values'] = ["EQ001", "EQ002", "EQ123"]

    combo_prio = crear_campo(frame_izq, 'Prioridad', datos['prioridad'], tipo='combobox')
    combo_prio['values'] = ['Alta', 'Media', 'Baja']

    # BOTONES IZQUIERDO
    frame_botones_izq = tk.Frame(frame_izq, bg="#f2f2f2")
    frame_botones_izq.pack(fill='x', pady=(20, 0))

    # Botón Guardar (siempre visible)
    btn_guardar = tk.Button(
        frame_botones_izq,
        text="Guardar",
        width=12,
        bg='#4CAF50',
        fg='white',
        command=lambda: [save(), messagebox.showinfo('Guardado', 'Cambios guardados correctamente', parent=ventana)]
    )
    btn_guardar.pack(pady=5)

    # Botones según estado
    if finalizada:
        pass
    elif en_proceso:
        btn_finalizar = tk.Button(
            frame_botones_izq,
            text="Finalizar Trabajo",
            width=15,
            bg='#4CAF50',
            fg='white',
            command=finalizar_trabajo
        )
        btn_finalizar.pack(pady=5)
    elif pausado:
        btn_iniciar = tk.Button(
            frame_botones_izq,
            text="Iniciar Trabajo",
            width=15,
            bg='#2196F3',
            fg='white',
            command=iniciar_trabajo
        )
        btn_iniciar.pack(pady=5)
    else:
        btn_iniciar = tk.Button(
            frame_botones_izq,
            text="Iniciar Trabajo",
            width=15,
            bg='#2196F3',
            fg='white',
            command=iniciar_trabajo
        )
        btn_iniciar.pack(pady=5)

    # PANEL DERECHO
    frame_der = tk.Frame(cont, bg="#f2f2f2")
    frame_der.pack(side="left", fill="both", expand=True, padx=10)

    # Operación y Observaciones
    tk.Label(frame_der, text="Trabajo a realizar:", bg="#f2f2f2", font=("Arial",10,"bold")).pack(anchor='w', pady=(5,0))
    text_op = tk.Text(frame_der, width=30, height=6, wrap='word')
    text_op.insert('1.0', datos['trabajo'] or '')
    text_op.pack(fill='x', pady=(0,10))
    text_op.bind('<Key>', marcar_dirty)

    tk.Label(frame_der, text="Observaciones:", bg="#f2f2f2", font=("Arial",10,"bold")).pack(anchor='w', pady=(5,0))
    text_obs = tk.Text(frame_der, width=30, height=6, wrap='word')
    text_obs.insert('1.0', datos['observaciones'] or '')
    text_obs.pack(fill='x', pady=(0,10))
    text_obs.bind('<Key>', marcar_dirty)

    # Listboxes con botones +
    frame_bot = tk.Frame(frame_der, bg="#f2f2f2")
    frame_bot.pack(anchor='w', fill='x', pady=(10,0))

    # Insumos
    frame_ins = tk.Frame(frame_bot, bg="#f2f2f2")
    frame_ins.pack(side='left', fill='both', expand=True, padx=5)
    hdr_ins = tk.Frame(frame_ins, bg="#f2f2f2"); hdr_ins.pack(fill='x')
    tk.Label(hdr_ins, text="Insumos:", bg="#f2f2f2", font=("Arial",10,"bold")).pack(side='left')
    btn_agregar_insumo = tk.Button(hdr_ins, text='+', width=2, bg='#3498db', fg='white',
             command=lambda: [mostrar_selector_insumos(ventana, listbox_ins), marcar_dirty()])
    btn_agregar_insumo.pack(side='left', padx=(5,0))
    listbox_ins = tk.Listbox(frame_ins, height=5)
    listbox_ins.pack(fill='both', expand=True, pady=(5,0))
    for insumo in (datos['insumos'] or '').split(','):
        if insumo.strip(): listbox_ins.insert(tk.END, insumo.strip())

    # Herramientas
    frame_herr = tk.Frame(frame_bot, bg="#f2f2f2")
    frame_herr.pack(side='left', fill='both', expand=True, padx=5)
    hdr_herr = tk.Frame(frame_herr, bg="#f2f2f2"); hdr_herr.pack(fill='x')
    tk.Label(hdr_herr, text="Herramientas:", bg="#f2f2f2", font=("Arial",10,"bold")).pack(side='left')
    btn_agregar_herr = tk.Button(hdr_herr, text='+', width=2, bg='#3498db', fg='white',
             command=lambda: [mostrar_selector_herramientas(ventana, listbox_herr), marcar_dirty()])
    btn_agregar_herr.pack(side='left', padx=(5,0))
    listbox_herr = tk.Listbox(frame_herr, height=5)
    listbox_herr.pack(fill='both', expand=True, pady=(5,0))
    for herr in (datos['herramientas'] or '').split(','):
        if herr.strip(): listbox_herr.insert(tk.END, herr.strip())

    # Responsables
    frame_res = tk.Frame(frame_bot, bg="#f2f2f2")
    frame_res.pack(side='left', fill='both', expand=True, padx=5)
    hdr_res = tk.Frame(frame_res, bg="#f2f2f2"); hdr_res.pack(fill='x')
    tk.Label(hdr_res, text="Responsables:", bg="#f2f2f2", font=("Arial",10,"bold")).pack(side='left')
    btn_agregar_resp = tk.Button(hdr_res, text='+', width=2, bg='#3498db', fg='white',
             command=lambda: [mostrar_selector_responsables(ventana, listbox_res), marcar_dirty()])
    btn_agregar_resp.pack(side='left', padx=(5,0))
    listbox_res = tk.Listbox(frame_res, height=5)
    listbox_res.pack(fill='both', expand=True, pady=(5,0))
    for resp in (datos['responsable'] or '').split(','):
        if resp.strip(): listbox_res.insert(tk.END, resp.strip())

    # Imágenes
    tk.Label(frame_der, text="Imágenes:", bg="#f2f2f2", font=("Arial",10,"bold")).pack(anchor='w', pady=(10,0))
    frame_imgs = tk.Frame(frame_der, bg="#f2f2f2")
    frame_imgs.pack(fill='x', pady=(0,10))
    
    img_labels = []
    img_photos = []
    
    def ampliar_imagen(img_path):
        if not img_path or not os.path.exists(img_path):
            return
        
        ventana_zoom = tk.Toplevel(ventana)
        ventana_zoom.title("Imagen ampliada")
        ventana_zoom.transient(ventana)
        ventana_zoom.grab_set()
        
        try:
            img = Image.open(img_path)
            img.thumbnail((800, 600))
            photo = ImageTk.PhotoImage(img)
            
            label = tk.Label(ventana_zoom, image=photo)
            label.image = photo
            label.pack()
            
            btn_cerrar = tk.Button(ventana_zoom, text="Cerrar", command=ventana_zoom.destroy)
            btn_cerrar.pack(pady=10)
        except Exception as e:
            tk.Label(ventana_zoom, text=f"Error al cargar imagen: {e}").pack()
            tk.Button(ventana_zoom, text="Cerrar", command=ventana_zoom.destroy).pack()

    for i in range(4):
        img_frame = tk.Frame(frame_imgs, bg="gray80", width=150, height=100, relief='ridge')
        img_frame.pack(side='left', padx=5, fill='both', expand=True)
        img_frame.pack_propagate(False)
        
        label = tk.Label(img_frame, bg="gray80", cursor="hand2")
        label.pack(fill='both', expand=True)
        
        if datos['es_cliente'] and i < len(datos['imagenes']):
            try:
                img_path = datos['imagenes'][i]
                if os.path.exists(img_path):
                    img = Image.open(img_path)
                    img.thumbnail((150, 100))
                    photo = ImageTk.PhotoImage(img)
                    
                    label.config(image=photo)
                    label.image = photo
                    img_photos.append(photo)
                    
                    label.bind('<Button-1>', lambda e, path=img_path: ampliar_imagen(path))
                else:
                    label.config(text=f"Imagen {i+1}\nNo encontrada", font=("Arial",8))
            except Exception as e:
                label.config(text=f"Imagen {i+1}\nError al cargar", font=("Arial",8))
        else:
            label.config(text=f"Imagen {i+1}\nNo disponible", font=("Arial",8))
        
        img_labels.append(label)

    def quitar_herramienta(event=None):
        if combo_estado.get() == "Realizada":
            return
            
        sel = listbox_herr.curselection()
        if sel and messagebox.askyesno("Confirmar", "¿Eliminar esta herramienta?", parent=ventana):
            listbox_herr.delete(sel[0])
            marcar_dirty()

    def quitar_responsable(event=None):
        if combo_estado.get() == "Realizada":
            return
            
        sel = listbox_res.curselection()
        if sel and messagebox.askyesno("Confirmar", "¿Eliminar este responsable?", parent=ventana):
            listbox_res.delete(sel[0])
            marcar_dirty()

    # Asignar eventos
    listbox_ins.bind('<Double-1>', devolver_insumo)
    listbox_ins.bind('<Delete>', devolver_insumo)
    listbox_herr.bind('<Double-1>', quitar_herramienta)
    listbox_herr.bind('<Delete>', quitar_herramienta)
    listbox_res.bind('<Double-1>', quitar_responsable)
    listbox_res.bind('<Delete>', quitar_responsable)

    def iniciar_trabajo():
        nonlocal tiempo_inicio, dirty
        # Si ya está finalizada, no dejamos continuar
        if datos['estado'] in ('Realizado',):
            ventana.lift()
            ventana.focus_force()
            messagebox.showwarning(
                "Estado Finalizado",
                "La orden ya está finalizada.",
                parent=ventana
            )
            return

        # Confirmación
        ventana.lift()
        ventana.focus_force()
        if not messagebox.askyesno(
            "Confirmar Inicio",
            "¿Desea iniciar el trabajo en esta orden?",
            parent=ventana
        ):
            return

        # Marcar inicio
        ahora = datetime.now()
        tiempo_inicio = ahora

        # Actualizar campo visual de fecha/hora de inicio
        if 'e_start' in locals():
            e_start.config(state='normal')
            e_start.delete(0, tk.END)
            e_start.insert(0, ahora.strftime('%d/%m/%Y %H:%M'))
            e_start.config(state='disabled')

        # Cambiar estado en el combobox
        combo_estado.set('En proceso')

        # Guardar en BD
        if save('En proceso', inicio=ahora):
            ventana.lift()
            ventana.focus_force()
            messagebox.showinfo(
                "Inicio Registrado",
                "El trabajo ha sido marcado como 'En proceso'.",
                parent=ventana
            )
            refrescar_formulario()


    def finalizar_trabajo():
        nonlocal tiempo_inicio
        if tiempo_inicio is None:
            messagebox.showerror('Error', 'No se ha registrado tiempo de inicio', parent=ventana)
            return
            
        save('Realizado')
        messagebox.showinfo('Finalizado', 'Trabajo completado', parent=ventana)
        refrescar_formulario()

    def refrescar_formulario():
        ventana.destroy()
        # Volver a cargar los datos actualizados desde la base de datos
        with conectar() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM ordenes_trabajo WHERE nro_ot = ?",
                (datos['nro_ot'],)
            )
            fila = cur.fetchone()
            if fila:
                columnas = [desc[0] for desc in cur.description]
                datos_actualizados = dict(zip(columnas, fila))
            else:
                messagebox.showerror(
                    "Error",
                    "No se pudo cargar la orden actualizada.",
                    parent=ventana
                )
                return

        abrir_formulario_modificar_ot(datos_actualizados, actualizar_callback)



    def save(estado=None, inicio=None):
        nonlocal tiempo_inicio, tiempo_total_pausado, dirty

        # 1) Recolectar datos del formulario
        cliente   = combo_cli.get() if datos['es_cliente'] else combo_eq.get()
        trabajo   = text_op.get('1.0','end-1c').strip()
        observac  = text_obs.get('1.0','end-1c').strip()
        prio      = combo_prio.get()
        insumos   = ",".join(listbox_ins.get(0, tk.END))
        herrs     = ",".join(listbox_herr.get(0, tk.END))
        respons   = ",".join(listbox_res.get(0, tk.END))
        estado_db = estado or combo_estado.get()
        ahora_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # 2) Conectar a la BD
        db_path = get_db_path()
        conn = sqlite3.connect(db_path)
        cur  = conn.cursor()

        # 3) UPDATE principal
        cur.execute("""
            UPDATE ordenes_trabajo SET
                cliente=?,
                trabajo=?,
                prioridad=?,
                observaciones=?,
                insumos=?,
                herramientas=?,
                responsable=?,
                estado=?,
                fecha=?
            WHERE nro_ot=?
        """, (
            cliente,
            trabajo,
            prio,
            observac,
            insumos,
            herrs,
            respons,
            estado_db,
            ahora_str,
            datos['nro_ot']
        ))

        # 4) Si es OT de cliente y pasaron inicio o finalización, actualizar esas columnas
        if datos['es_cliente']:
            if inicio:
                cur.execute("""
                    UPDATE ordenes_trabajo SET
                        fecha_iniciado=?, estado=?
                    WHERE nro_ot=?
                """, (
                    inicio.strftime('%Y-%m-%d %H:%M:%S'),
                    'En proceso',
                    datos['nro_ot']
                ))
            if estado == 'Realizado':
                fecha_final = datetime.now()
                segundos_p = tiempo_total_pausado.total_seconds()
                cur.execute("""
                    UPDATE ordenes_trabajo SET
                        fecha_final=?,
                        tiempo_pausado=?,
                        estado=?
                    WHERE nro_ot=?
                """, (
                    fecha_final.strftime('%Y-%m-%d %H:%M:%S'),
                    segundos_p,
                    'Realizado',
                    datos['nro_ot']
                ))

        # 5) Commit y limpieza
        conn.commit()
        conn.close()

        dirty = False
        if actualizar_callback:
            actualizar_callback()

    ventana.protocol("WM_DELETE_WINDOW", on_closing)

    # Botón SALIR
    btn_salir = tk.Button(
        ventana, 
        text='SALIR', 
        width=10,
        bg='#f44336',
        fg='white',
        font=('Arial', 10, 'bold'),
        command=on_closing
    )
    btn_salir.pack(side='bottom', pady=10)

    ventana.mainloop()