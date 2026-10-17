@echo off
cd /d "%~dp0"
if not exist "venv\Scripts\python.exe" (echo [HOLD] Missing venv & exit /b 2)
venv\Scripts\python.exe -c "import os,sys; sys.exit(0 if os.environ.get('QSB_SOLANA_PRIVATE_KEY') else 3)"
if errorlevel 1 (echo [HOLD] Native runtime needs signing credential in current process; no secret is stored & exit /b 3)
echo [ORACLE155] Starting native executor; existing transaction gates remain authoritative
venv\Scripts\python.exe -m qseries_v2.oracle_execution.solana_atomic_executor.runtime --seconds 90
