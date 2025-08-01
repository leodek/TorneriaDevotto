# -*- mode: python ; coding: utf-8 -*-
import os
block_cipher = None

# Usa el directorio actual (desde donde ejecutas 'pyinstaller main.spec')
project_root = os.getcwd()

# ─── Datas: splash y carpeta de imágenes ─────────────────────────────────
datas = [
    (os.path.join(project_root, "splash.png"), "."),
]
img_dir = os.path.join(project_root, "usuarios", "imagenes")
for root, _, files in os.walk(img_dir):
    for fname in files:
        if fname.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
            src = os.path.join(root, fname)
            dest = os.path.relpath(root, project_root)
            datas.append((src, dest))

# ─── Analysis ─────────────────────────────────────────────────────────────
a = Analysis(
    ["main.py"],            # tu script principal
    pathex=[project_root],
    binaries=[],            # añade aquí DLLs si necesitas
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)

# ─── PYZ ───────────────────────────────────────────────────────────────────
pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher,
)

# ─── EXE ───────────────────────────────────────────────────────────────────
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,             # incluye las librerías nativas
    a.zipfiles,
    a.datas,                # splash + usuarios/imagenes
    name="ManteMoustache",
    icon=os.path.join(project_root, "icono.ico"),
    debug=False,
    strip=False,
    upx=True,
    console=False,          # oculta la consola
)

# ─── COLLECT ───────────────────────────────────────────────────────────────
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name="ManteMoustache",
)
