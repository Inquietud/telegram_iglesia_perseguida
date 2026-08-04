@echo off
cd /d "%~dp0"
title Configurar canal de Telegram

echo Buscando Python...
echo.

where py >nul 2>&1
if %errorlevel%==0 goto usar_py

where python >nul 2>&1
if %errorlevel%==0 goto usar_python

where python3 >nul 2>&1
if %errorlevel%==0 goto usar_python3

goto sin_python

:usar_py
echo Encontrado: py
py -3 configurar.py
goto fin

:usar_python
echo Encontrado: python
python configurar.py
goto fin

:usar_python3
echo Encontrado: python3
python3 configurar.py
goto fin

:sin_python
echo ============================================================
echo  NO HAY PYTHON INSTALADO EN ESTE ORDENADOR
echo ============================================================
echo.
echo  1. Ve a https://www.python.org/downloads/
echo  2. Descarga la version para Windows y ejecutala
echo  3. IMPORTANTE: en la primera pantalla del instalador marca
echo     la casilla de abajo "Add python.exe to PATH"
echo  4. Termina la instalacion, cierra esta ventana y vuelve a
echo     hacer doble clic en CONFIGURAR.bat
echo.

:fin
echo.
echo ------------------------------------------------------------
echo  Esta ventana no se cerrara sola. Cierrala con la X.
echo  Si ha salido algun error, copialo o hazle una foto.
echo ------------------------------------------------------------
cmd /k
