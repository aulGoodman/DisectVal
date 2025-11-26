@echo off
REM DisectVal Windows Executable Builder
REM This script builds DisectVal.exe and places it in the repository root

echo Building DisectVal.exe...

REM Install dependencies if needed
pip install pyinstaller>=6.0.0

REM Build using the spec file
pyinstaller DisectVal.spec --noconfirm

REM Copy the executable to root (outside folders)
if exist "dist\DisectVal.exe" (
    copy "dist\DisectVal.exe" "DisectVal.exe"
    echo.
    echo Build complete! DisectVal.exe has been created in the repository root.
    echo You can now run DisectVal.exe directly.
) else (
    echo.
    echo Error: Build failed. DisectVal.exe was not created.
    exit /b 1
)

echo.
pause
