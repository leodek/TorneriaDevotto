# File: ot_form_logic.py
import os
import sys
import sqlite3 # Aunque la mayoría de DB va a ot_data_manager, sqlite3 se usa en cargar_datos localmente
from datetime import datetime, timedelta
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from tkcalendar import DateEntry
import sys
import os
base_dir = os.path.dirname(__file__)
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)
try:
    from .ot_data_manager import cargar_datos_ot, guardar_datos_ot
except ImportError:
    from ordenes_trabajo.ot_data_manager import cargar_datos_ot, guardar_datos_ot
from db_init import conectar
from typing import cast
from datetime import datetime, timedelta




# Configuración de paths (puede ser necesario si los módulos están en diferentes directorios)
# Asegúrate de que la ruta base sea correcta para importar los otros módulos
base_dir = os.path.dirname(__file__)
root_dir = os.path.abspath(os.path.join(base_dir, os.pardir))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

try:
    from .ot_ui_elements import crear_campo
except ImportError:
    from ot_ui_elements import crear_campo
from personal.selector_personal import mostrar_selector_responsables

def sumar_tiempo_pausado(nro_ot: str, segundos_pausa: int):
    """
    Añade los segundos de pausa al campo tiempo_pausado de la orden.
    """
    with conectar() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT tiempo_pausado FROM ordenes_trabajo WHERE nro_ot = ?",
            (nro_ot,)
        )
        fila = cur.fetchone()
        actuales = int(fila[0] or 0)
        cur.execute(
            "UPDATE ordenes_trabajo SET tiempo_pausado = ? WHERE nro_ot = ?",
            (actuales + segundos_pausa, nro_ot)
        )
        conn.commit()

def sumar_tiempo_trabajo(nro_ot: str, segundos_trabajo: int):
    """
    Añade los segundos de trabajo efectivo al campo tiempo_trabajo de la orden.
    """
    with conectar() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT tiempo_trabajo FROM ordenes_trabajo WHERE nro_ot = ?",
            (nro_ot,)
        )
        fila = cur.fetchone()
        actuales = int(fila[0] or 0)
        cur.execute(
            "UPDATE ordenes_trabajo SET tiempo_trabajo = ? WHERE nro_ot = ?",
            (actuales + segundos_trabajo, nro_ot)
        )
        conn.commit()


def abrir_formulario_modificar_ot(nro_ot, parent=None, actualizar_callback=None):
    """
    Abre el formulario para modificar una orden de trabajo existente.
    Carga datos usando ot_data_manager y construye la UI usando ot_ui_elements.
    """
    # Cargar datos usando el nuevo módulo
    datos = cargar_datos_ot(nro_ot)

    if not datos:
        messagebox.showerror("Error", f"No se encontró la orden de trabajo {nro_ot}", parent=parent)
        return # Salir si la OT no existe
    
    # --- Definir las flags de estado INMEDIATAMENTE después de cargar los datos ---
    en_proceso = datos['estado'] == 'En proceso'
    finalizada = datos['estado'] == 'Realizado'
    pausado = datos['estado'] == 'Pausado'
    # -----------------------------------------------------------------------------


    ventana = tk.Toplevel(parent) # Usar parent para que la ventana sea modal si se abre desde otra
    ventana.title(f"Modificar Orden de Trabajo {nro_ot}")
    ventana.configure(bg="#f2f2f2")

    # Variables para control de tiempo
    tiempo_inicio = None
    if datos.get('fecha_iniciado'):
        try:
            tiempo_inicio = datetime.strptime(datos['fecha_iniciado'], '%d/%m/%Y %H:%M:%S')
        except:
            tiempo_inicio = None

    tiempo_pausa_inicio = None
    if datos.get('fecha_pausada'):
        try:
            tiempo_pausa_inicio = datetime.strptime(datos['fecha_pausada'], '%d/%m/%Y %H:%M:%S')
        except:
            tiempo_pausa_inicio = None

    tiempo_total_pausado = timedelta(seconds=int(datos.get('tiempo_pausado', 0)))



    # Ajustar tamaño y posición: centrado horizontal, lo más arriba posible
    window_width = 700
    window_height = 750

    # Obtener ancho de pantalla (si no hay parent) o ancho del padre
    if parent:
        screen_width = parent.winfo_width()
    else:
        screen_width = ventana.winfo_screenwidth()

    # Calcular X para centrar
    center_x = (screen_width - window_width) // 2
    # Fijar Y en el borde superior
    top_y = 0

    ventana.geometry(f"{window_width}x{window_height}+{center_x}+{top_y}")


    ventana.resizable(False, False)
    ventana.grab_set() # Hacer la ventana modal

    # Estado dirty para cambios
    dirty = False
    def marcar_dirty(event=None):
        nonlocal dirty
        dirty = True

    # --- Funciones de control de OT (Definidas aquí para interactuar con la UI local) ---
    def refrescar_formulario():
        """Cierra la ventana actual y abre una nueva para refrescar."""
        ventana.destroy()
        # Llamar a la función principal para reabrir el formulario con datos actualizados
        abrir_formulario_modificar_ot(nro_ot, parent=parent, actualizar_callback=actualizar_callback)


    def save(estado_a_guardar=None, inicio_a_guardar=None, pause_start_time=None):
        nonlocal tiempo_inicio, tiempo_total_pausado, dirty

        # 1) Registrar pausa si aplica
        if pause_start_time is not None:
            tiempo_total_pausado += datetime.now() - pause_start_time
            fecha_pausa = pause_start_time.strftime('%d/%m/%Y %H:%M:%S')
            with conectar() as conn:
                conn.execute(
                    "UPDATE ordenes_trabajo SET fecha_pausada = ? WHERE nro_ot = ?",
                    (fecha_pausa, datos['nro_ot'])
                )   

       # 2) Recolectar datos del formulario
        cliente      = combo_cli.get().strip() if datos['es_cliente'] else combo_eq.get().strip() # type: ignore
        trabajo      = text_op.get('1.0', 'end-1c').strip()
        observac     = text_obs.get('1.0', 'end-1c').strip()
        prio         = combo_prio.get() # type: ignore
        insumos      = text_insumos.get('1.0', 'end-1c').strip()

        # Responsables: obtenemos índices válidos en lugar de tk.END
        last_index = listbox_res.size() - 1
        if last_index >= 0:
            lista_responsables = listbox_res.get(0, last_index)
        else:
            lista_responsables = ()
        respons      = ",".join(lista_responsables)

        estado_actual = estado_a_guardar if estado_a_guardar else combo_estado.get() # type: ignore


        # 3) Mantener la fecha de ingreso original
        fecha_ingreso_original = datos.get('fecha_ingreso')

        # 4) Ejecutar UPDATE sin sobrescribir fecha_ingreso
        with conectar() as conn:
            cur = conn.cursor()
            cur.execute("""
                UPDATE ordenes_trabajo SET
                    cliente=?,
                    trabajo=?,
                    prioridad=?,
                    observaciones=?,
                    insumos=?,
                    responsable=?,
                    estado=?,
                    fecha_ingreso=?
                WHERE nro_ot=?
            """, (
                cliente,
                trabajo,
                prio,
                observac,
                insumos,
                respons,
                estado_actual,
                fecha_ingreso_original,
                datos['nro_ot']
            ))
            conn.commit()

        # 5) Limpiar flag de cambios y refrescar si corresponde
        dirty = False
        if actualizar_callback:
            actualizar_callback()
        return True
    
        # ————————————————
    # Nuevo: guardar y refrescar ventana
    def guardar_y_refrescar():
        """Guarda los datos y, si todo fue bien, recarga el formulario."""
        correcto = save()
        if correcto:
            refrescar_formulario()
    

    def iniciar_trabajo():
        """
        Pone la OT en estado «En proceso».
        • Valida que todos los responsables tengan una ENTRADA sin salida en asistencia_diaria.
        • Si alguno no la tiene, pide confirmación antes de continuar.
        • Registra la fecha de inicio y refresca el formulario.
        """
        nonlocal tiempo_inicio, dirty

        # ─── 0) Validar responsables ─────────────────────────────────────
        def responsables_actuales() -> list[str]:
            return [
                listbox_res.get(i).strip()
                for i in range(listbox_res.size())
                if listbox_res.get(i).strip()
            ]

        faltantes: list[str] = []
        with conectar() as conn:
            cur = conn.cursor()
            for resp in responsables_actuales():
                existe = cur.execute(
                    """
                    SELECT 1
                      FROM asistencia_diaria
                     WHERE nombre = ?
                       AND (hora_salida IS NULL OR hora_salida = '')
                    LIMIT 1
                    """,
                    (resp,),
                ).fetchone()
                if not existe:
                    faltantes.append(resp)

        if faltantes:
            if not messagebox.askyesno(
                "Responsables sin entrada",
                "Los siguientes responsables NO registraron su ENTRADA:\n\n"
                + "\n".join(faltantes)
                + "\n\n¿Desea iniciar el trabajo de todas formas?",
                parent=ventana,
            ):
                return  # Cancela el inicio

        # ─── 1) Verificar estado actual ──────────────────────────────────
        if datos["estado"] in ("Realizado",):
            messagebox.showwarning(
                "Estado Finalizado",
                "La orden ya está finalizada.",
                parent=ventana,
            )
            return

        # ─── 2) Cambiar a «En proceso» ───────────────────────────────────
        ahora = datetime.now()
        if save("En proceso", inicio_a_guardar=ahora):
            try:
                with conectar() as conn:
                    conn.execute(
                        "UPDATE ordenes_trabajo "
                        "SET fecha_iniciado = ? "
                        "WHERE nro_ot = ?",
                        (ahora.strftime("%d/%m/%Y %H:%M:%S"), datos["nro_ot"]),
                    )
                    conn.commit()
            except Exception as e:
                messagebox.showerror(
                    "Error BD",
                    f"No se pudo guardar fecha de inicio:\n{e}",
                    parent=ventana,
                )
                return

            messagebox.showinfo(
                "Inicio Registrado",
                "El trabajo ha sido marcado como 'En proceso'.",
                parent=ventana,
            )

            # ─── 3) Refrescar la ventana ────────────────────────────────
            refrescar_formulario()


    def finalizar_trabajo():
        nonlocal tiempo_inicio, tiempo_pausa_inicio
        """Cambia el estado a 'Realizado', registra fecha_final, acumula pausa y trabajo, y refresca UI."""
        if datos['estado'] == 'Realizado':
            messagebox.showwarning("Estado Finalizado", "La orden ya está finalizada.", parent=ventana)
            return
        if datos['estado'] == 'Pendiente':
            messagebox.showwarning("Estado Pendiente", "La orden aún no ha sido iniciada.", parent=ventana)
            return

        ahora = datetime.now()

        # Si estaba pausado, acumulo la pausa hasta ahora
        if datos['estado'] == 'Pausado' and tiempo_pausa_inicio is not None:
            pausa_actual = ahora - tiempo_pausa_inicio
            segundos_pausa = int(pausa_actual.total_seconds())
            sumar_tiempo_pausado(datos['nro_ot'], segundos_pausa)
            tiempo_pausa_inicio = None

        if not messagebox.askyesno(
            "Confirmar Finalización",
            "¿Desea finalizar el trabajo en esta orden?",
            parent=ventana
        ):
            return

        # guardo nuevo estado y refresco
        if save('Realizado'):
            try:
                with conectar() as conn:
                    conn.execute(
                        "UPDATE ordenes_trabajo SET fecha_final = ? WHERE nro_ot = ?",
                        (ahora.strftime("%d/%m/%Y %H:%M:%S"), datos['nro_ot'])
                    )
            except Exception as e:
                messagebox.showerror("Error BD", f"No se pudo guardar fecha final: {e}", parent=ventana)

            # calculo y sumo tiempo trabajado
            if tiempo_inicio:
                with conectar() as conn:
                    cur = conn.cursor()
                    cur.execute(
                        "SELECT tiempo_pausado FROM ordenes_trabajo WHERE nro_ot = ?",
                        (datos['nro_ot'],)
                    )
                    segs_p = cur.fetchone()[0] or 0
                total_pausado = timedelta(seconds=int(segs_p))
                neto = ahora - tiempo_inicio - total_pausado
                segundos_trabajo = int(neto.total_seconds())
                sumar_tiempo_trabajo(datos['nro_ot'], segundos_trabajo)

                h, resto = divmod(segundos_trabajo, 3600)
                m, s    = divmod(resto, 60)
                tiempo_str = f"{h:02d}:{m:02d}:{s:02d}"
                messagebox.showinfo(
                    "Trabajo Finalizado",
                    f"Orden marcada como 'Realizado'.\nTiempo de trabajo: {tiempo_str}",
                    parent=ventana
                )
            else:
                messagebox.showinfo(
                    "Trabajo Finalizado",
                    "Orden marcada como 'Realizado',\npero no había fecha de inicio registrada.",
                    parent=ventana
                )

            refrescar_formulario()

    def pausar_trabajo():
        nonlocal tiempo_pausa_inicio
        """Pausa una OT en curso, guarda fecha_pausada en BD y refresca UI."""
        if datos['estado'] != 'En proceso':
            messagebox.showwarning(
                "Estado Incorrecto",
                "Solo se puede pausar una orden 'En proceso'.",
                parent=ventana
            )
            return

        if messagebox.askyesno(
            "Confirmar Pausa",
            "¿Desea pausar el trabajo en esta orden?",
            parent=ventana
        ):
            ahora = datetime.now()
            # guardamos localmente cuándo empezó la pausa
            tiempo_pausa_inicio = ahora
            fecha_pausa_str = ahora.strftime('%d/%m/%Y %H:%M:%S')

            try:
                with conectar() as conn:
                    # actualizamos fecha_pausada y dejamos tiempo_pausado intacto
                    conn.execute(
                        "UPDATE ordenes_trabajo "
                        "SET fecha_pausada = ? "
                        "WHERE nro_ot = ?",
                        (fecha_pausa_str, datos['nro_ot'])
                    )
            except Exception as e:
                messagebox.showerror("Error BD", f"No se pudo guardar fecha de pausa: {e}", parent=ventana)
                return

            messagebox.showinfo("Trabajo Pausado", "El trabajo ha sido pausado.", parent=ventana)
            refrescar_formulario()


    def reanudar_trabajo():
        """
        Pasa la OT de «Pausado» a «En proceso».
        • Valida que todos los responsables tengan una ENTRADA sin salida en asistencia_diaria.
        • Si alguno no la tiene, pide confirmación antes de continuar.
        • Actualiza fecha_pausada / tiempo_pausado y refresca la UI.
        """
        nonlocal tiempo_pausa_inicio, tiempo_total_pausado

        # ─── 0) Validar responsables ─────────────────────────────────────
        def responsables_actuales() -> list[str]:
            return [
                listbox_res.get(i).strip()
                for i in range(listbox_res.size())
                if listbox_res.get(i).strip()
            ]

        faltantes: list[str] = []
        with conectar() as conn:
            cur = conn.cursor()
            for resp in responsables_actuales():
                existe = cur.execute(
                    """
                    SELECT 1
                      FROM asistencia_diaria
                     WHERE nombre = ?
                       AND (hora_salida IS NULL OR hora_salida = '')
                    LIMIT 1
                    """,
                    (resp,),
                ).fetchone()
                if not existe:
                    faltantes.append(resp)

        if faltantes:
            if not messagebox.askyesno(
                "Responsables sin entrada",
                "Los siguientes responsables NO registraron su ENTRADA:\n\n"
                + "\n".join(faltantes)
                + "\n\n¿Desea reanudar el trabajo de todas formas?",
                parent=ventana,
            ):
                return  # Cancela la reanudación

        # ─── 1) Comprobaciones de estado ─────────────────────────────────
        if datos["estado"] != "Pausado":
            messagebox.showwarning(
                "Estado Incorrecto",
                "Solo se puede reanudar una orden en estado 'Pausado'.",
                parent=ventana,
            )
            return

        if not messagebox.askyesno(
            "Confirmar Reanudar",
            "¿Desea reanudar el trabajo en esta orden?",
            parent=ventana,
        ):
            return

        ahora = datetime.now()

        # ─── 2) Obtener fecha_pausada original ───────────────────────────
        with conectar() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT fecha_pausada FROM ordenes_trabajo WHERE nro_ot = ?",
                (datos["nro_ot"],),
            )
            fila = cur.fetchone()
        if not fila or not fila[0]:
            messagebox.showerror(
                "Error",
                "No hay fecha de pausa en la base de datos.",
                parent=ventana,
            )
            return

        fecha_pausada_dt = datetime.strptime(fila[0], "%d/%m/%Y %H:%M:%S")

        # ─── 3) Calcular y acumular pausa ────────────────────────────────
        segundos_pausa = int((ahora - fecha_pausada_dt).total_seconds())
        sumar_tiempo_pausado(datos["nro_ot"], segundos_pausa)

        # ─── 4) Actualizar estado ────────────────────────────────────────
        try:
            with conectar() as conn:
                conn.execute(
                    """
                    UPDATE ordenes_trabajo
                       SET estado = 'En proceso',
                           fecha_pausada = NULL
                     WHERE nro_ot = ?
                    """,
                    (datos["nro_ot"],),
                )
        except Exception as e:
            messagebox.showerror(
                "Error BD", f"No se pudo reanudar la orden:\n{e}", parent=ventana
            )
            return

        tiempo_pausa_inicio = None

        messagebox.showinfo(
            "Trabajo Reanudado",
            "El trabajo ha sido reanudado.",
            parent=ventana,
        )

        # ─── 5) Refrescar la ventana ─────────────────────────────────────
        refrescar_formulario()


    def on_closing():
        nonlocal dirty

        changed = []

        if text_op.get('1.0', 'end-1c').strip() != datos.get('trabajo', ''):
            changed.append("Trabajo")
        if text_obs.get('1.0', 'end-1c').strip() != datos.get('observaciones', ''):
            changed.append("Observaciones")
        if combo_prio.get() != datos.get('prioridad', ''): # type: ignore
            changed.append("Prioridad")

        # Cliente/Equipo
        if combo_cli is not None:
            current_cli = combo_cli.get().strip() # type: ignore
        elif combo_eq is not None:
            current_cli = combo_eq.get().strip() # type: ignore
        else:
            current_cli = ''
        if current_cli != datos.get('cliente', ''):
            changed.append("Cliente/Equipo")

        if text_insumos.get('1.0', 'end-1c').strip() != datos.get('insumos', ''):
            changed.append("Insumos")

        # Responsables (igual que en save)
        last_idx = listbox_res.size() - 1
        items = listbox_res.get(0, last_idx) if last_idx >= 0 else ()
        curr_resp = sorted(i.strip() for i in items if i.strip())
        init_resp = sorted(i.strip() for i in (datos.get('responsable','') or '').split(',') if i.strip())
        if curr_resp != init_resp:
            changed.append("Responsables")

        if changed and not messagebox.askyesno(
            "Salir sin guardar",
            f"Hay cambios en: {', '.join(changed)}.\n¿Salir sin guardar?",
            parent=ventana
        ):
            return

        ventana.destroy()



    # Conectar este manejador al evento de cerrar ventana ("X")
    ventana.protocol("WM_DELETE_WINDOW", on_closing)


    def quitar_responsable(event=None): # type: ignore
        """Quita un responsable del Listbox."""
        if datos['estado'] == "Realizado":
            messagebox.showwarning("Orden Finalizada", "No se pueden quitar responsables en una orden finalizada.", parent=ventana)
            return

        sel = listbox_res.curselection()
        if sel and messagebox.askyesno("Confirmar", "¿Eliminar este responsable de la lista?", parent=ventana):
            listbox_res.delete(sel[0])
            marcar_dirty()

    # --- Construcción de la UI ---
    # Contenedor principal
    cont = tk.Frame(ventana, bg="#f2f2f2")
    cont.pack(padx=20, pady=10, fill="both", expand=True)

    # PANEL IZQUIERDO
    frame_izq = tk.Frame(cont, bg="#f2f2f2", width=380)
    frame_izq.pack(side="left", fill="y")

    # Usar crear_campo del nuevo módulo
    entry_ot = crear_campo(frame_izq, 'N° OT', datos['nro_ot'], tipo='entry')
    entry_ot.config(state='disabled')

    combo_estado = crear_campo(frame_izq, 'Estado', datos['estado'], tipo='combobox')
    combo_estado['values'] = ['Pendiente', 'En proceso', 'Realizado', 'Cancelada']
    combo_estado.config(state='disabled') # El estado se cambia con los botones de acción

    # Inicializar combo_cli y combo_eq a None
    combo_cli = None
    combo_eq = None

    if datos['es_cliente']:
        combo_cli = crear_campo(frame_izq, 'Cliente', datos['cliente'], tipo='combobox')
        # Puedes cargar la lista completa de clientes si es necesario, por ahora solo el cliente actual
        # combo_cli['values'] = cargar_lista_clientes() # Ejemplo si tuvieras esa función
        combo_cli.config(state='readonly') # type: ignore # O 'normal' si quieres que se pueda cambiar

        crear_campo(frame_izq, 'Fecha Ingreso', datos.get('fecha_ingreso'), tipo='date') # Usar .get para evitar KeyError

        # Definir e_start aquí si es_cliente es True
        # Mostrar fecha y hora si está disponible
        fecha_inicio_str = datos.get('fecha_iniciado')
        if fecha_inicio_str:
                try:
                        fecha_inicio_str = datetime.strptime(fecha_inicio_str, '%d/%m/%Y %H:%M:%S').strftime('%d/%m/%Y %H:%M')
                except:
                        pass  # Mantener la cadena original si falla el formato

        e_start = crear_campo(frame_izq, 'Fecha Inicio', fecha_inicio_str, tipo='entry')
        e_start.config(state='disabled')  # No editable directamente


        # Mostrar fecha estimada/final
        fecha_final_str = datos.get('fecha_final')
        fecha_estimada_str = datos.get('fecha_estimada')

        if fecha_final_str: # Si está finalizada, mostrar fecha final
             try:
                 fecha_final_str = datetime.strptime(fecha_final_str, '%d/%m/%Y %H:%M:%S').strftime('%d/%m/%Y %H:%M')
             except:
                 pass
             crear_campo(frame_izq, 'Fecha Final', fecha_final_str, tipo='entry').config(state='disabled')
        elif fecha_estimada_str: # Si no está finalizada, mostrar fecha estimada
             crear_campo(frame_izq, 'Fecha Estimada', fecha_estimada_str, tipo='date') # Usar tipo date para editar

        # Mostrar tiempo de trabajo si está finalizada
        if finalizada and 'tiempo_trabajo' in datos:
            tk.Label(frame_izq, text="Tiempo de trabajo:", bg="#f2f2f2", font=("Arial",10,"bold")).pack(anchor='w', pady=(5,0))
            tiempo_entry = ttk.Entry(frame_izq, width=30)
            tiempo_entry.insert(0, datos['tiempo_trabajo'])
            tiempo_entry.config(state='readonly')
            tiempo_entry.pack(anchor='w', pady=(0,5))

    else: # Si no es cliente, es una OT interna con código de equipo
        combo_eq = crear_campo(frame_izq, 'Equipo', datos['cliente'], tipo='combobox')
        # Puedes cargar la lista completa de equipos si es necesario
        # combo_eq['values'] = cargar_lista_equipos() # Ejemplo
        combo_eq.config(state='readonly') # type: ignore # O 'normal' si quieres que se pueda cambiar
        # Asegurarse de que e_start esté definido incluso si es_cliente es False, como None
        e_start = None


    combo_prio = crear_campo(frame_izq, 'Prioridad', datos['prioridad'], tipo='combobox')
    combo_prio['values'] = ['Alta', 'Media', 'Baja']
    combo_prio.bind('<<ComboboxSelected>>', marcar_dirty) # Marcar dirty al cambiar prioridad


    # BOTONES IZQUIERDO
    frame_botones_izq = tk.Frame(frame_izq, bg="#f2f2f2")
    frame_botones_izq.pack(fill='x', pady=(20, 0))

    def eliminar_orden():
        if not messagebox.askyesno(
            "Confirmar eliminación",
            "¿Desea eliminar esta orden de trabajo?",
            parent=ventana
        ):
            return

        try:
            with conectar() as conn:
                conn.execute(
                    "DELETE FROM ordenes_trabajo WHERE nro_ot = ?",
                    (datos['nro_ot'],)
                )
            messagebox.showinfo(
                "Eliminada",
                "Orden eliminada correctamente",
                parent=ventana
            )
            # Refrescar lista si es necesario
            if actualizar_callback:
                try:
                    actualizar_callback()
                except Exception as e:
                    messagebox.showerror(
                        "Error al refrescar lista",
                        f"No se pudo actualizar la lista:\n{e}",
                        parent=ventana
                    )
            ventana.destroy()

        except Exception as e:
            messagebox.showerror(
                "Error",
                f"No se pudo eliminar la orden: {e}",
                parent=ventana
            )


            # Refrescar la lista en la ventana principal
            if actualizar_callback:
                try:
                    actualizar_callback()
                except Exception as e:
                    messagebox.showerror(
                        "Error al refrescar lista",
                        f"No se pudo actualizar la lista:\n{e}",
                        parent=ventana
                    )

            # Cerrar sólo el Toplevel de detalle
            ventana.destroy()

        except Exception as e: # type: ignore
            messagebox.showerror(
                "Error",
                f"No se pudo eliminar la orden: {e}",
                parent=ventana
            )

    def mostrar_resumen():
        # 1) Traer datos de la OT
        try:
            with conectar() as conn:
                cur = conn.cursor()
                cur.execute(
                    "SELECT fecha_iniciado, fecha_pausada, tiempo_pausado, fecha_final, estado "
                    "FROM ordenes_trabajo WHERE nro_ot = ?",
                    (datos['nro_ot'],)
                )
                fila = cur.fetchone()
        except Exception as e:
            messagebox.showerror("Error BD", f"No se pudo obtener el resumen: {e}", parent=ventana)
            return

        if not fila:
            messagebox.showerror("Error", f"OT {datos['nro_ot']} no encontrada", parent=ventana)
            return

        fecha_ini_str, fecha_pau_str, segs_p, fecha_fin_str, estado = fila
        try:
            inicio_dt = datetime.strptime(fecha_ini_str, "%d/%m/%Y %H:%M:%S")
        except:
            messagebox.showerror("Error formato", "Fecha de inicio inválida", parent=ventana)
            return

        # 2) Buscar última salida manual en asistencia_diaria
        salida_dt = None
        try:
            with conectar() as conn2:
                row = conn2.execute(
                    "SELECT fecha, hora_salida "
                    "FROM asistencia_diaria "
                    "WHERE trabajo_asignado = ? AND hora_salida IS NOT NULL "
                    "ORDER BY fecha || ' ' || hora_salida DESC "
                    "LIMIT 1",
                    (datos['nro_ot'],)
                ).fetchone()
            if row and row[1]:
                salida_dt = datetime.strptime(f"{row[0]} {row[1]}", "%Y-%m-%d %H:%M:%S")
        except:
            pass

        now = datetime.now()

        # 3) Determinar fin_dt y calcular pausas
        if salida_dt:
            fin_dt = salida_dt
            pausas = timedelta(seconds=int(segs_p or 0))
            if estado == "Pausado" and fecha_pau_str:
                try:
                    pause_dt = datetime.strptime(fecha_pau_str, "%d/%m/%Y %H:%M:%S")
                    pausas += (salida_dt - pause_dt)
                except:
                    pass
            pau_fmt = fecha_pau_str or "-"
        else:
            if estado == "En proceso":
                fin_dt = now
                pausas = timedelta(seconds=int(segs_p or 0))
                pau_fmt = fecha_pau_str or "-"
            elif estado == "Pausado":
                try:
                    pause_dt = datetime.strptime(fecha_pau_str, "%d/%m/%Y %H:%M:%S")
                    pausas = timedelta(seconds=int(segs_p or 0)) + (now - pause_dt)
                    pau_fmt = now.strftime("%d/%m/%Y %H:%M:%S")
                    fin_dt = now
                except:
                    messagebox.showerror("Error formato", "Fecha de pausa inválida", parent=ventana)
                    return
            else:
                try:
                    fin_dt = datetime.strptime(fecha_fin_str, "%d/%m/%Y %H:%M:%S")
                except:
                    messagebox.showerror("Error formato", "Fecha de cierre inválida", parent=ventana)
                    return
                pausas = timedelta(seconds=int(segs_p or 0))
                pau_fmt = fecha_pau_str or "-"

        # 4) Calcular neto y formatear
        total = fin_dt - inicio_dt
        neto  = total - pausas
        segs  = int(neto.total_seconds())
        h, r  = divmod(segs, 3600)
        m, s  = divmod(r, 60)
        tiempo_str = f"{h:02d}:{m:02d}:{s:02d}"
        inicio_fmt = inicio_dt.strftime("%d/%m/%Y %H:%M:%S")
        fin_fmt    = fin_dt.strftime("%d/%m/%Y %H:%M:%S")

        # 5) Mostrar diálogo final
        texto = (
            f"        Estado:            {estado}\n"
            f"        Fecha Inicio:      {inicio_fmt}\n"
            f"        Fecha Pausada:     {pau_fmt}\n"
            f"        Fecha Cierre:      {fin_fmt}\n"
            f"        Tiempo Pausado:    {pausas}\n"
            f"        Tiempo de Trabajo: {tiempo_str}"
        )

        top = tk.Toplevel(ventana)
        top.title("Resumen de la OT")
        top.transient(ventana)

        # Configuración de tamaño y posición
        top.minsize(300, 250)
        top.geometry("400x250")
        sw, sh = top.winfo_screenwidth(), top.winfo_screenheight()
        x = (sw // 2) - (400 // 2)
        y = (sh // 2) - (250 // 2)
        top.geometry(f"+{x}+{y}")

        # Contenido del diálogo
        tk.Label(top, text="Resumen de tiempos", font=("Arial", 14, "bold"))\
            .pack(pady=10)
        tk.Label(top, text=texto, justify="left", font=("Arial", 11))\
            .pack(padx=20, pady=10, anchor="w")
        tk.Button(top, text="Cerrar", command=top.destroy).pack(pady=(0,20))

        top.grab_set()

    def agregar_imagenes():
        nonlocal imgs, img_index
        seleccion = fd.askopenfilenames(
            title="Seleccionar imágenes",
            initialdir=os.path.expanduser("~"),                # abre en tu home
            filetypes=[
                ("Archivos de imagen", "*.jpg *.jpeg *.png *.gif *.bmp"),
                ("Todos los archivos", "*.*")
            ],
            parent=ventana
        )
        if not seleccion:
            return

        imgs.extend(seleccion)
        # guardo en BD usando la conexión centralizada
        with conectar() as conn:
            conn.execute(
                "UPDATE ordenes_trabajo SET imagenes = ? WHERE nro_ot = ?",
                (",".join(imgs), datos['nro_ot'])
            )
        img_index = len(imgs) - len(seleccion)
        show_current()



    def eliminar_imagen():
        nonlocal imgs, img_index
        if not imgs:
            return
        imgs.pop(img_index)
        # Guardo en BD usando la conexión centralizada
        with conectar() as conn:
            conn.execute(
                "UPDATE ordenes_trabajo SET imagenes = ? WHERE nro_ot = ?",
                (",".join(imgs), datos['nro_ot'])
            )
        img_index = max(0, min(img_index, len(imgs)-1))
        show_current()


    # botón Resumen
    tk.Button(
        frame_botones_izq,
        text="Resumen",
        width=15,
        bg="#95a5a6",
        fg="white",
        command=mostrar_resumen
    ).pack(pady=5)


    # Botón Guardar (siempre visible)
    btn_guardar = tk.Button(
        frame_botones_izq,
        text="Guardar",
        width=12,
        bg='#4CAF50',
        fg='white',
        command=lambda: guardar_y_refrescar() # Llamar a save sin cambiar estado
    )
    btn_guardar.pack(pady=5)

    # BOTONES SEGÚN ESTADO
    if finalizada:
        # … (igual que antes)
        pass

    elif en_proceso:
        btn_pausar = tk.Button(
            frame_botones_izq,
            text="Pausar Trabajo",
            width=15,
            bg='#FFC107',
            fg='black',
            command=lambda: (
                save('Ingresada'),
                messagebox.showinfo("Estado Actualizado", "La orden ahora está en estado 'Ingresada'."),
                refrescar_formulario()
            )
        )
        btn_pausar.pack(pady=5)


        btn_finalizar = tk.Button(
            frame_botones_izq, text="Finalizar Trabajo", width=15,
            bg='#4CAF50', fg='white', command=finalizar_trabajo
        )
        btn_finalizar.pack(pady=5)

    elif pausado:
        btn_reanudar = tk.Button(
            frame_botones_izq, text="Reanudar Trabajo", width=15,
            bg='#2196F3', fg='white', command=reanudar_trabajo
        )
        btn_reanudar.pack(pady=5)

        btn_finalizar = tk.Button(
            frame_botones_izq, text="Finalizar Trabajo", width=15,
            bg='#4CAF50', fg='white', command=finalizar_trabajo
        )
        btn_finalizar.pack(pady=5)

    # <-- aquí añadimos "Ingresada" junto a "Pendiente" -->
    elif datos['estado'] in ('Pendiente', 'Ingresada'):
        btn_iniciar = tk.Button(
            frame_botones_izq, text="Iniciar Trabajo", width=15,
            bg='#2196F3', fg='white', command=iniciar_trabajo
        )
        btn_iniciar.pack(pady=5)

    # Botón Eliminar (siempre visible)
    btn_guardar = tk.Button(
        frame_botones_izq,
        text="Eliminar trabajo",
        width=12,
        bg="#FF0011",
        fg='black',
        command=eliminar_orden
    )
    btn_guardar.pack(pady=5)
    
    # Botón Salir (siempre visible)
    btn_salir = tk.Button(
        frame_botones_izq,
        text="SALIR",
        width=12,
        bg="#FF0011",
        fg='black',
    command=on_closing # Llama a la función on_closing al hacer clic
    )
    btn_salir.pack(pady=5)
    
        # ———— Imágenes: mover botones al panel izquierdo ————
    # Botón Añadir imagen
    btn_add_img = tk.Button(
        frame_botones_izq,
        text='+ Añadir imagen',
        width=12,
        bg="#929292",
        fg='black',
        command=agregar_imagenes
    )
    btn_add_img.pack(pady=5)

    # Botón Eliminar imagen actual
    btn_del_img = tk.Button(
        frame_botones_izq,
        text='– Eliminar actual',
        width=12,
        bg="#929292",
        fg='black',
        command=eliminar_imagen
    )
    btn_del_img.pack(pady=5)




        # Si es Cancelada, no mostrar botones de acción


    # PANEL DERECHO
    frame_der = tk.Frame(cont, bg="#f2f2f2")
    frame_der.pack(side="left", fill="both", expand=True, padx=10)

    # Trabajo y Observaciones
    tk.Label(frame_der, text="Trabajo a realizar:", bg="#f2f2f2", font=("Arial",10,"bold")).pack(anchor='w', pady=(5,0))
    text_op = tk.Text(frame_der, width=30, height=6, wrap='word')
    text_op.delete('1.0', tk.END)  # Asegura que el widget esté vacío antes de insertar texto

    trabajo_texto = datos.get('trabajo')
    if trabajo_texto is None:
        trabajo_texto = ""  # evita insertar None, debe ser string

    text_op.insert('1.0', trabajo_texto)  # Inserta el texto de trabajo
    text_op.pack(fill='x', pady=(0,10))
    text_op.bind('<Key>', marcar_dirty)


    tk.Label(frame_der, text="Observaciones:", bg="#f2f2f2", font=("Arial",10,"bold")).pack(anchor='w', pady=(5,0))
    text_obs = tk.Text(frame_der, width=30, height=6, wrap='word')
    text_obs.insert('1.0', datos.get('observaciones', '')) # Usar .get para evitar KeyError
    text_obs.pack(fill='x', pady=(0,10))
    text_obs.bind('<Key>', marcar_dirty)

        # Listboxes/Treeviews con botones +
    frame_bot = tk.Frame(frame_der, bg="#f2f2f2")
    frame_bot.pack(anchor='w', fill='x', pady=(10,0))

    # ——————————————————————————————————————————————————————————————
    # Sustituir sección de Insumos por un Text widget
    # ——————————————————————————————————————————————————————————————
    tk.Label(frame_der, text="Insumos:", bg="#f2f2f2", font=("Arial",10,"bold")).pack(anchor='w', pady=(10,0))
    text_insumos = tk.Text(frame_der, width=40, height=4, wrap='word')
    text_insumos.insert('1.0', datos.get('insumos', ''))
    text_insumos.pack(fill='x', pady=(0,10))
    text_insumos.bind('<Key>', marcar_dirty)
    
    # Responsables (Listbox)
    frame_res = tk.Frame(frame_bot, bg="#f2f2f2")
    frame_res.pack(side='left', fill='both', expand=True, padx=5)
    hdr_res = tk.Frame(frame_res, bg="#f2f2f2"); hdr_res.pack(fill='x')
    tk.Label(hdr_res, text="Responsables:", bg="#f2f2f2", font=("Arial",10,"bold")).pack(side='left')
    btn_agregar_resp = tk.Button(
        hdr_res, text='+', width=2, bg='#3498db', fg='white',
        command=lambda: (mostrar_selector_responsables(listbox_res), marcar_dirty())
    )
    btn_agregar_resp.pack(side='left', padx=(5,0))

    listbox_res = tk.Listbox(frame_res, height=5)
    listbox_res.pack(fill='both', expand=True, pady=(5,0))

    # Insertar solo el nombre, extrayéndolo si viene con "ID - Nombre"
    # Responsables (solo nombre)
    for resp in (datos.get('responsable', '') or '').split(','):
        resp = resp.strip()
        if not resp:
            continue
        # si viene "código - nombre - sector - cargo"
        if ' - ' in resp:
            parts = [p.strip() for p in resp.split(' - ')]
            nombre = parts[1]  # segundo elemento = nombre
        # si viene "código, nombre, sector, cargo"
        elif ',' in resp:
            parts = [p.strip() for p in resp.split(',')]
            nombre = parts[1]  # segundo elemento = nombre
        else:
            nombre = resp
        listbox_res.insert(tk.END, nombre)



    # Imágenes

    img_labels = []
    img_photos = []

    def ampliar_imagen(img_path):
        if not img_path or not os.path.exists(img_path):
            return

        # Creamos una Toplevel hija de 'ventana'
        ventana_zoom = tk.Toplevel(ventana)
        ventana_zoom.title("Imagen ampliada")
        ventana_zoom.transient(ventana)

        # Interceptamos la 'X' de la ventana para que no propague el cierre
        def cerrar_zoom():
            ventana_zoom.grab_release()
            ventana_zoom.destroy()

        ventana_zoom.protocol("WM_DELETE_WINDOW", cerrar_zoom)

        # Esto hace que solo reciba eventos la ventana de zoom
        ventana_zoom.grab_set()

        try:
            img = Image.open(img_path)
            img.thumbnail((800, 600))
            photo = ImageTk.PhotoImage(img)

            lbl = tk.Label(ventana_zoom, image=photo)
            lbl.image = photo # type: ignore
            lbl.pack(padx=10, pady=10)
        except Exception as e:
            tk.Label(ventana_zoom, text=f"Error al cargar imagen:\n{e}", fg="red").pack(padx=10, pady=10)

        # Botón Cerrar que llama a nuestra función de cierre
        tk.Button(ventana_zoom, text="Cerrar", command=cerrar_zoom).pack(pady=(0,10))

    import tkinter.filedialog as fd

    # … dentro de abrir_formulario_modificar_ot …

    # ——————————————————————————————————————————————————————————————
    # Imágenes con navegación de 1 en 1 + botones + / –
    # ——————————————————————————————————————————————————————————————
    import tkinter.filedialog as fd

    # 1) Cargo la lista inicial
    raw = datos.get('imagenes', [])
    if isinstance(raw, list):
        imgs = raw
    else:
        imgs = [p.strip() for p in raw.split(',') if p.strip()]
    img_index = 0

    # 2) Defino primero las funciones que usan imgs e img_index
    def show_current():
        nonlocal img_index
        if not imgs:
            lbl_img.config(text="No imágenes", image='')
            lbl_ctr.config(text='')
            return

        path = imgs[img_index]
        if os.path.exists(path):
            try:
                im = Image.open(path)
                # Asegurarnos de que tkinter haya calculado el tamaño real
                frame_imgs.update_idletasks()
                w = frame_imgs.winfo_width() - 4
                h = frame_imgs.winfo_height() - 30

                # Si aún no hay tamaño válido, reintentar tras 100 ms
                if w <= 0 or h <= 0:
                    frame_imgs.after(100, show_current)
                    return

                # Redimensionar con LANCZOS
                im.thumbnail((w, h), Image.Resampling.LANCZOS)
                ph = ImageTk.PhotoImage(im)
                lbl_img.config(image=ph, text='')
                lbl_img.image = ph # type: ignore
            except Exception as e:
                lbl_img.config(text=f"Error al cargar imagen:\n{e}", image='')
        else:
            lbl_img.config(text="¡Archivo no existe!", image='')

        lbl_ctr.config(text=f"{img_index+1}/{len(imgs)}")


    def prev_image():
        nonlocal img_index
        if img_index > 0:
            img_index -= 1
            show_current()

    def next_image():
        nonlocal img_index
        if img_index + 1 < len(imgs):
            img_index += 1
            show_current()
            
    # 3) Ahora creo los widgets
    tk.Label(frame_der, text="Imágenes:", bg="#f2f2f2", font=("Arial",10,"bold")).pack(anchor='w', pady=(10,0))
    frame_imgs = tk.Frame(frame_der, bg="#f2f2f2", height=250)
    frame_imgs.pack(fill='both', pady=(0,10), expand=True)

    lbl_img = tk.Label(frame_imgs, bg="gray80")
    lbl_img.pack(fill='both', expand=True)
    lbl_img.bind("<Double-Button-1>", lambda e: ampliar_imagen(imgs[img_index] if imgs else None))

    lbl_ctr = tk.Label(frame_imgs, bg="#f2f2f2")
    lbl_ctr.place(relx=0.5, rely=0.95, anchor='s')

    # Navegación ← →
    nav = tk.Frame(frame_imgs, bg="#f2f2f2")
    nav.place(relx=0.5, rely=0.02, anchor='n')
    tk.Button(nav, text='←', command=prev_image).pack(side='left', padx=5)
    tk.Button(nav, text='→', command=next_image).pack(side='left', padx=5)


    # 4) Refrescar al redimensionar
    frame_imgs.bind("<Configure>", lambda e: show_current())

    # 5) Mostrar por primera vez
    show_current()


    # Carga inicial
    show_current()

    def quitar_responsable(event=None):
        """Quita un responsable del Listbox."""
        if datos['estado'] == "Realizado":
            messagebox.showwarning("Orden Finalizada", "No se pueden quitar responsables en una orden finalizada.", parent=ventana)
            return

        sel = listbox_res.curselection()
        if sel and messagebox.askyesno("Confirmar", "¿Eliminar este responsable de la lista?", parent=ventana):
            listbox_res.delete(sel[0])
            marcar_dirty()
    listbox_res.bind('<Double-1>', quitar_responsable)
    listbox_res.bind('<Delete>', quitar_responsable)