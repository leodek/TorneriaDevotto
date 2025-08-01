import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import shutil
from datetime import date, datetime
from tkcalendar import DateEntry
import sqlite3
import sqlite3
import os
import sqlite3
from db_init import get_db_path

def conectar():
    """Función de conexión a la base de datos usando la ruta segura de get_db_path()"""
    db = get_db_path()
    os.makedirs(os.path.dirname(db), exist_ok=True)
    return sqlite3.connect(db, timeout=10)


def agregar_orden_trabajo(actualizar_callback=None):
    ventana = tk.Toplevel()
    ventana.title("Nueva Orden de Trabajo")
    ventana.configure(bg="white")

    # Centrar ventana
    w, h = 850, 600
    sw, sh = ventana.winfo_screenwidth(), ventana.winfo_screenheight()
    ventana.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    campos = {}
    imagen_paths = []

    # Título
    tk.Label(ventana, text="NUEVA ORDEN DE TRABAJO",
             font=("Arial",18,"bold"), bg="white").place(x=250, y=10)

    # --- Cliente (Entry + Listbox para autocompletar) ---
    tk.Label(ventana, text="CLIENTE:", font=("Arial",10,"bold"), bg="white").place(x=20, y=100)
    ent_cliente = tk.Entry(ventana, width=24, bd=1, relief="solid")
    ent_cliente.place(x=120, y=98)
    campos["cliente"] = ent_cliente

    # Carga inicial de clientes
    conn = conectar()
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT cliente FROM ordenes_trabajo")
    original_clientes = [r[0] for r in cur.fetchall()]
    conn.close()

    # Listbox de sugerencias
    listbox_cliente = tk.Listbox(ventana, width=24, height=5)
    listbox_cliente.place(x=120, y=120)
    listbox_cliente.place_forget()

    def on_keyrelease_cliente(event):
        texto = ent_cliente.get().lower()
        filtrados = [c for c in original_clientes if texto in c.lower()] if texto else original_clientes
        listbox_cliente.delete(0, tk.END)
        for c in filtrados:
            listbox_cliente.insert(tk.END, c)
        listbox_cliente.place(x=120, y=120) if filtrados else listbox_cliente.place_forget()

    def on_listbox_select(event):
        if listbox_cliente.curselection():
            ent_cliente.delete(0, tk.END)
            ent_cliente.insert(0, listbox_cliente.get(listbox_cliente.curselection()[0]))
            listbox_cliente.place_forget()

    ventana.bind('<Button-1>', lambda e: listbox_cliente.place_forget() if e.widget not in (ent_cliente, listbox_cliente) else None)
    ent_cliente.bind('<KeyRelease>', on_keyrelease_cliente)
    listbox_cliente.bind('<<ListboxSelect>>', on_listbox_select)

    # --- Sección de imágenes ---
    img_frame = tk.Frame(ventana, bg="white")
    img_frame.place(x=580, y=50, width=260, height=200)

    imagen_paths = []
    img_index = 0

    canvas = tk.Canvas(img_frame, width=200, height=140, bg="white", highlightthickness=1, highlightbackground="black")
    canvas.grid(row=0, column=1, padx=2, pady=5)

    count_lbl = tk.Label(img_frame, text="0/8 fotos", bg="white", font=("Arial",9))
    count_lbl.grid(row=1, column=0, columnspan=3, pady=(0,5))

    def mostrar_imagen():
        nonlocal img_index
        total = len(imagen_paths)
        count_lbl.config(text=f"{total}/8 fotos")
        canvas.delete("all")
        
        if total == 0:
            btn_prev.config(state="disabled")
            btn_next.config(state="disabled")
            canvas.create_text(100, 70, text="No hay imágenes", fill="gray")
            return
            
        img_index = max(0, min(img_index, total-1))
        try:
            img = Image.open(imagen_paths[img_index]).resize((200,140), Image.Resampling.LANCZOS)
            tk_img = ImageTk.PhotoImage(img)
            canvas.image = tk_img
            canvas.create_image(0, 0, anchor="nw", image=tk_img)
        except Exception as e:
            canvas.create_text(100, 70, text="Error al cargar", fill="red")
        
        btn_prev.config(state="normal" if img_index>0 else "disabled")
        btn_next.config(state="normal" if img_index<total-1 else "disabled")

    def cambiar_imagen(delta):
        nonlocal img_index
        img_index += delta
        mostrar_imagen()

    def sel_imgs():
        nonlocal img_index
        if len(imagen_paths) >= 8:
            messagebox.showwarning(
                "Límite alcanzado",
                "Ya hay 8 fotos. Elimina una antes de agregar más.",
                parent=ventana
            )
            return
            
        files = filedialog.askopenfilenames(filetypes=[("Imágenes","*.jpg;*.jpeg;*.png")], parent=ventana)
        if not files:
            return
            
        os.makedirs("fotos_ordenes", exist_ok=True)
        disponibles = 8 - len(imagen_paths)
        for f in files[:disponibles]:
            nombre_archivo = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{os.path.basename(f)}"
            dst = os.path.join("fotos_ordenes", nombre_archivo)
            shutil.copy(f, dst)
            imagen_paths.append(dst)
            
        img_index = len(imagen_paths)-1
        mostrar_imagen()

    def eliminar_imagen():
        nonlocal img_index
        if not imagen_paths:
            return
            
        try:
            os.remove(imagen_paths[img_index])
            del imagen_paths[img_index]
            img_index = min(img_index, len(imagen_paths)-1)
            mostrar_imagen()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo eliminar la imagen: {e}", parent=ventana)

    # Botones de imágenes
    btn_prev = tk.Button(img_frame, text='←', width=2, command=lambda: cambiar_imagen(-1))
    btn_prev.grid(row=0, column=0, padx=2, pady=5)

    btn_next = tk.Button(img_frame, text='→', width=2, command=lambda: cambiar_imagen(1))
    btn_next.grid(row=0, column=2, padx=2, pady=5)

    btn_frame = tk.Frame(ventana, bg="white")
    btn_frame.place(x=610, y=200)
    tk.Button(btn_frame, text="+", width=2, bg="lime", command=sel_imgs).pack(side="left", padx=2)
    tk.Button(btn_frame, text="-", width=2, bg="red", command=eliminar_imagen).pack(side="left", padx=2)

    mostrar_imagen()

    # --- Campos del formulario ---
    # Trabajo a realizar (antes "Operación a realizar")
    tk.Label(ventana, text="TRABAJO A REALIZAR:", font=("Arial",10,"bold"), bg="white").place(x=20, y=140)
    txt_trabajo = tk.Text(ventana, width=40, height=4, bd=1, relief="solid")
    txt_trabajo.place(x=20, y=160)
    campos["trabajo"] = txt_trabajo

    # Observaciones
    tk.Label(ventana, text="OBSERVACIONES:", font=("Arial",10,"bold"), bg="white").place(x=20, y=260)
    txt_obs = tk.Text(ventana, width=40, height=4, bd=1, relief="solid")
    txt_obs.place(x=20, y=280)
    campos["observaciones"] = txt_obs

    # Responsable
    tk.Label(ventana, text="RESPONSABLE:", font=("Arial",10,"bold"), bg="white").place(x=380, y=260)
    list_resp = tk.Listbox(ventana, width=25, height=4, bd=1, relief="solid")
    list_resp.place(x=380, y=280)
    
    def on_resp_double(event):
        if list_resp.curselection() and messagebox.askyesno("Eliminar responsable", f"¿Eliminar «{list_resp.get(list_resp.curselection()[0])}»?"):
            list_resp.delete(list_resp.curselection()[0], parent=ventana)
    
    list_resp.bind("<Double-1>", on_resp_double)

    def add_resp():
        sel_win = tk.Toplevel(ventana)
        sel_win.title("Seleccionar Responsable")
        sel_win.configure(bg="white")
        sel_win.geometry("300x400+{}+{}".format(ventana.winfo_rootx()+590, ventana.winfo_rooty()+280))

        tk.Label(sel_win, text="Elige un responsable:", font=("Arial",12,"bold"), bg="white").pack(pady=(10,0))

        list_personal = tk.Listbox(sel_win, width=40, height=15)
        list_personal.pack(padx=10, pady=10, fill="both", expand=True)

        conn = conectar()
        cur = conn.cursor()
        cur.execute("SELECT nombre_completo FROM personal")
        for nombre in cur.fetchall():
            list_personal.insert(tk.END, nombre[0])
        conn.close()

        def confirmar():
            if list_personal.curselection():
                list_resp.insert(tk.END, list_personal.get(list_personal.curselection()[0]))
                sel_win.destroy()
        
        ttk.Button(sel_win, text="Seleccionar", command=confirmar).pack(pady=(0,10))
        list_personal.bind("<Double-1>", lambda e: confirmar())

    tk.Button(ventana, text="+", width=2, bg="#3498db", fg="white", command=add_resp).place(x=535, y=280)

    # Fecha de ingreso
    hoy = date.today().strftime("%d/%m/%Y")
    tk.Label(ventana, text="FECHA INGRESO:", font=("Arial",10,"bold"), bg="white").place(x=20, y=360)
    ent_fecha = tk.Entry(ventana, width=18, bd=1, relief="solid")
    ent_fecha.insert(0, hoy)
    ent_fecha.config(state="readonly")
    ent_fecha.place(x=140, y=358)
    campos["fecha_ingreso"] = hoy

    # Fecha estimada
    tk.Label(ventana, text="FECHA ESTIMADA DE FINALIZACIÓN:", font=("Arial",10,"bold"), bg="white").place(x=20, y=400)
    date_est = DateEntry(ventana, width=18, date_pattern='dd/MM/yyyy')
    date_est.place(x=260, y=398)
    date_est.delete(0, tk.END)
    campos["fecha_estimada"] = date_est

    # Prioridad
    tk.Label(ventana, text="PRIORIDAD:", font=("Arial",10,"bold"), bg="white").place(x=400, y=400)
    combo_prio = ttk.Combobox(ventana, width=18, state="readonly", values=["Alta","Media","Baja"])
    combo_prio.place(x=480, y=398)
    campos["prioridad"] = combo_prio

    # --- Función para guardar ---
    def guardar():
        # Validación
        if not campos["cliente"].get().strip():
            messagebox.showerror("Error", "Debe indicar un cliente" ,parent=ventana)
            return
        if not campos["trabajo"].get("1.0", "end").strip():
            messagebox.showerror("Error", "Debe describir el trabajo a realizar",parent=ventana)
            return
        if not campos["prioridad"].get():
            messagebox.showerror("Error", "Debe seleccionar una prioridad", parent=ventana)
            return

        # Preparar datos
        datos = {
            "cliente": campos["cliente"].get().strip(),
            "trabajo": campos["trabajo"].get("1.0", "end").strip(),
            "observaciones": campos["observaciones"].get("1.0", "end").strip(),
            "fecha_ingreso": campos["fecha_ingreso"],
            "fecha_estimada": campos["fecha_estimada"].get_date().strftime('%Y-%m-%d') if campos["fecha_estimada"].get() else "",
            "prioridad": campos["prioridad"].get(),
            "responsable": ",".join(list_resp.get(0, tk.END)),
            "imagenes": ",".join(imagen_paths) if imagen_paths else ""
        }

        conn = None
        try:
            conn = conectar()
            cur = conn.cursor()
            
            # Generar número de OT
            cur.execute("SELECT MAX(CAST(SUBSTR(nro_ot,3) AS INTEGER)) FROM ordenes_trabajo")
            maxn = cur.fetchone()[0] or 0
            nro_ot = f"OT{maxn+1:03d}"
            
            # Insertar en ordenes_trabajo
            cur.execute("""INSERT INTO ordenes_trabajo
                (nro_ot, cliente, trabajo, fecha_ingreso, responsable, 
                 observaciones, estado, prioridad, fecha_estimada, imagenes)
                VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", (
                nro_ot, 
                datos["cliente"], 
                datos["trabajo"], 
                datos["fecha_ingreso"], 
                datos["responsable"],
                datos["observaciones"], 
                "Ingresada", 
                datos["prioridad"], 
                datos["fecha_estimada"],
                datos["imagenes"]
            ))

            conn.commit()
            
            if actualizar_callback:
                actualizar_callback()
                
            messagebox.showinfo("Éxito", f"Orden de trabajo {nro_ot} creada correctamente", parent=ventana)
            ventana.destroy()
            
        except Exception as e:
            if conn:
                conn.rollback()
            messagebox.showerror("Error", f"No se pudo guardar: {str(e)}", parent=ventana)
            
            # Limpiar imágenes si hubo error
            for img in imagen_paths:
                try:
                    if os.path.exists(img):
                        os.remove(img)
                except:
                    pass
        finally:
            if conn:
                conn.close()

    tk.Button(ventana, text="GUARDAR", bg="lime green", fg="black",
             font=("Arial",10,"bold"), width=12, command=guardar).place(x=330, y=500)

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    agregar_orden_trabajo()
    root.mainloop()