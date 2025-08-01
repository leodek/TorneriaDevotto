import os, sys, sqlite3, json

def get_db_path():
    """
    Devuelve la ruta absoluta a mantenimiento.db.
    - En modo .exe (sys.frozen = True) => %APPDATA%\\ManteMoustache\\mantenimiento.db
    - En modo desarrollador => carpeta actual
    """
    if getattr(sys, "frozen", False):
        base_dir = os.path.join(os.environ["APPDATA"], "ManteMoustache")
    else:
        # Carpeta del script (ProyectoDevotto)
        base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, "mantenimiento.db")


def export_table(table_name, output_file, columns):
    conn = sqlite3.connect(get_db_path())
    cur = conn.cursor()
    cur.execute(f"SELECT {','.join(columns)} FROM {table_name}")
    rows = cur.fetchall()
    data = [dict(zip(columns, row)) for row in rows]
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    conn.close()

if __name__ == '__main__':
    export_table(
        'asistencia_diaria',
        'docs/data/entrada_salida.json',
        ['nombre','fecha','hora_entrada','hora_salida','total_horas']
    )
    export_table(
        'ordenes_trabajo',
        'docs/data/ordenes_trabajo.json',
        ['id','nro_ot','cliente','trabajo','fecha_ingreso','insumos','responsable',
         'observaciones','estado','prioridad','herramientas','fecha_estimada',
         'tiempo_pausado','fecha_pausada','tiempo_trabajo','fecha_iniciado',
         'fecha_final','imagenes','fotos']
    )
