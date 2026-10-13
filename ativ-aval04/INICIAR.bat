@echo off
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" goto dependencias
py -3 -m venv .venv
if not errorlevel 1 goto dependencias
python -m venv .venv
if errorlevel 1 goto erro_python
:dependencias
".venv\Scripts\python.exe" -c "import flask, oracledb, requests, dotenv" >nul 2>&1
if not errorlevel 1 goto configurar
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto erro_dependencias
:configurar
if not exist ".env" copy ".env.example" ".env" >nul
echo EventTech - Sistema de Gestao de Eventos
echo Preencha ORACLE_USER e ORACLE_PASSWORD no arquivo .env para usar o banco.
echo Se a tabela ainda nao existe, execute script.sql no seu Oracle.
echo Abra http://127.0.0.1:5000 no navegador. CTRL+C encerra o servidor.
".venv\Scripts\python.exe" eventtech\App.py
pause
exit /b 0
:erro_python
echo Instale Python 3.10 ou mais recente em https://www.python.org/downloads/
echo Marque a opcao para adicionar Python ao PATH e tente novamente.
pause
exit /b 1
:erro_dependencias
echo Nao foi possivel instalar as bibliotecas. Confira sua internet e tente novamente.
pause
exit /b 1
