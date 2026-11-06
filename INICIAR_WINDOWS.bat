@echo off
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel% equ 0 (
  py -3 iniciar.py
) else (
  python iniciar.py
)
echo.
echo Se o Python nao foi encontrado, instale Python 3.10 ou superior.
echo Consulte LEIA_PRIMEIRO.txt nesta pasta.
pause
