@echo off
REM Activate the virtual environment
call .\.venv\Scripts\activate

REM Set necessary variables
SET PYTHON=.venv\Scripts\python.exe
SET NUITKA=%PYTHON% -m nuitka
SET OUTPUT_DIR=dist
SET APP_NAME=NGAGE.exe
SET ASSETS_DIR=assets
SET VERSION=0.1.0

REM Ensure output directory exists
IF NOT EXIST %OUTPUT_DIR% (
    mkdir %OUTPUT_DIR%
)

REM Compile the Python script using Nuitka
echo Compiling script with Nuitka...
%NUITKA% --standalone --onefile^
    --lto=auto^
    --follow-imports^
    --show-progress^
    --enable-plugin=tk-inter^
    --windows-icon-from-ico=%ASSETS_DIR%\favicon.ico^
    --output-filename=%APP_NAME%^
    --company-name=NTTIndonesia^
    --product-name=NGAGE^
    --file-version=%VERSION%^
    --product-version=%VERSION%^
    --include-data-dir=%ASSETS_DIR%=assets^
    --output-dir=%OUTPUT_DIR%^
    --windows-console-mode=disable^
    app.py

IF %ERRORLEVEL% NEQ 0 (
    echo Compilation failed!
    exit /b %ERRORLEVEL%
)

REM Compress the compiled executable using UPX
IF EXIST %OUTPUT_DIR%\%APP_NAME% (
    echo Compressing executable with UPX...
    upx --best --lzma -v %OUTPUT_DIR%\%APP_NAME%

    IF %ERRORLEVEL% NEQ 0 (
        echo UPX compression failed!
        exit /b %ERRORLEVEL%
    )
) ELSE (
    echo Executable not found, skipping UPX compression.
)

echo Compilation and compression finished.
pause
