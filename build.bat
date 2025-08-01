@echo off
echo ================================
echo 🧑‍💻 Compilando MiAppMantenimiento...
echo ================================

REM Limpiar builds anteriores
rmdir /s /q build
rmdir /s /q dist
del /q MiAppMantenimiento.spec

REM Ejecutar PyInstaller
pyinstaller ^
  --noconsole ^
  --onefile ^
  --name "MiAppMantenimiento" ^
  --icon=usuarios\imagenes\default_user.ico ^
  --add-data "mantenimiento.db;." ^
  --add-data "usuarios\imagenes;usuarios\imagenes" ^
  --add-data "db;db" ^
  --add-data "equipos;equipos" ^
  --add-data "ordenes;ordenes" ^
  --add-data "ordenes_trabajo;ordenes_trabajo" ^
  --add-data "personal;personal" ^
  --add-data "usuarios;usuarios" ^
  --add-data "insumos;insumos" ^
  --add-data "marcar_tarjeta;marcar_tarjeta" ^
  --hidden-import=tkinter ^
  main.py

echo ================================
echo ✅ Compilación completada.
echo 📁 Tu archivo está en: dist\MiAppMantenimiento.exe
pause
