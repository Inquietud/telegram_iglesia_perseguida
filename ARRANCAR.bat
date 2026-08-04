@echo off
cd /d "%~dp0"
title Bot del canal - dejar esta ventana abierta

if not exist config.json (
  echo No hay config.json todavia. Ejecuta antes CONFIGURAR.bat
  echo.
  goto fin
)

where py >nul 2>&1
if %errorlevel%==0 goto usar_py
where python >nul 2>&1
if %errorlevel%==0 goto usar_python
goto sin_python

:usar_py
echo Bot en marcha. Deja esta ventana abierta. Ctrl+C para parar.
echo.
py -3 bot.py
goto fin

:usar_python
echo Bot en marcha. Deja esta ventana abierta. Ctrl+C para parar.
echo.
python bot.py
goto fin

:sin_python
echo No encuentro Python. Instalalo desde python.org marcando
echo la casilla "Add python.exe to PATH".

:fin
echo.
echo ------------------------------------------------------------
echo  El bot se ha detenido. Cierra la ventana con la X.
echo ------------------------------------------------------------
cmd /k
