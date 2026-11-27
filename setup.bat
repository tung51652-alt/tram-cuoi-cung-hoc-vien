@echo off
rem Cai dat moi truong va mo game TRAM CUOI CUNG (Windows).
rem   Bam dup file nay, hoac chay: setup.bat            -> cai (lan dau) roi mo game
rem                                setup.bat --chi-cai  -> chi cai, khong mo game
rem Chay lai bao nhieu lan cung duoc.
setlocal
cd /d "%~dp0"
echo == TRAM CUOI CUNG: chuan bi moi truong ==

set "PY="
where py >nul 2>nul && set "PY=py -3"
if not defined PY where python >nul 2>nul && set "PY=python"
if not defined PY (
    echo Khong tim thay Python. Hay cai Python 3.10+ tu python.org ^(nho tick "Add python.exe to PATH"^).
    goto :loi
)

%PY% -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)"
if errorlevel 1 (
    echo Can Python 3.10 tro len.
    goto :loi
)

if not exist ".venv\Scripts\python.exe" (
    echo [1/3] Tao moi truong .venv ...
    %PY% -m venv .venv
    if errorlevel 1 goto :loi
) else (
    echo [1/3] Da co .venv
)

echo [2/3] Cai thu vien ^(can Internet o lan dau^) ...
".venv\Scripts\python.exe" -m pip install --disable-pip-version-check -q -r requirements.txt
if errorlevel 1 (
    echo Cai thu vien that bai. Kiem tra mang roi chay lai setup.bat
    goto :loi
)

if "%~1"=="--chi-cai" (
    echo [3/3] Da cai xong. Lan sau bam dup setup.bat de mo game.
    goto :het
)

echo [3/3] Mo game ...
".venv\Scripts\python.exe" main.py %*
goto :het

:loi
echo.
echo Co loi. Doc dong thong bao o tren, sua roi chay lai.
pause
exit /b 1

:het
endlocal
