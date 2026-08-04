@echo off
cd /d "%~dp0"
title Diagnostico
echo Recogiendo informacion... espera unos segundos.

(
echo ===== DIAGNOSTICO =====
echo Fecha: %date% %time%
echo Carpeta: %cd%
echo.
echo --- where py ---
where py 2>&1
echo --- py -3 --version ---
py -3 --version 2>&1
echo.
echo --- where python ---
where python 2>&1
echo --- python --version ---
python --version 2>&1
echo.
echo --- pip ---
py -3 -m pip --version 2>&1
python -m pip --version 2>&1
echo.
echo --- modulos ---
py -3 -c "import requests, feedparser; print('requests y feedparser OK')" 2>&1
python -c "import requests, feedparser; print('requests y feedparser OK')" 2>&1
echo.
echo --- ficheros en la carpeta ---
dir /b
echo.
echo --- existe config.json? ---
if exist config.json (echo SI) else (echo NO)
) > diagnostico.txt 2>&1

echo.
echo Hecho. Se ha creado el fichero diagnostico.txt en esta carpeta.
echo Dile a Claude que lo lea.
echo.
cmd /k
