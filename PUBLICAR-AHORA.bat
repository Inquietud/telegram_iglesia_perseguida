@echo off
cd /d "%~dp0"
title Publicar ahora

echo Sincronizando con GitHub...
git pull --rebase
if errorlevel 1 (
  echo.
  echo No he podido sincronizar. Resuelvelo antes de seguir:
  echo    git status
  goto fin
)

echo.
echo Procesando tus botones y buscando noticias...
echo.

where py >nul 2>&1
if %errorlevel%==0 (py -3 bot.py --una-vez) else (python bot.py --una-vez)

echo.
echo Guardando el estado en GitHub...
git add estado.json traducciones.json
git commit -m "estado (publicado a mano)" >nul 2>&1
git push

:fin
echo.
echo ------------------------------------------------------------
echo  Listo. Cierra la ventana con la X.
echo ------------------------------------------------------------
cmd /k
