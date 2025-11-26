@echo off
REM DisectVal Windows Executable Builder
REM This script builds 3 executables and places them in the repository root:
REM   - Setup.exe: Dependency installation and setup
REM   - Dev.exe: Developer mode (requires dev credentials)
REM   - UserVersion.exe: Standard user version

echo ============================================
echo   DisectVal Executable Builder
echo ============================================
echo.

REM Install dependencies if needed
echo Installing PyInstaller...
pip install pyinstaller>=6.0.0

REM Build using the spec file
echo.
echo Building executables...
pyinstaller DisectVal.spec --noconfirm

REM Copy the executables to root (outside folders)
echo.
echo Copying executables to repository root...

if exist "dist\Setup.exe" (
    copy "dist\Setup.exe" "Setup.exe"
    echo   [OK] Setup.exe
) else (
    echo   [FAIL] Setup.exe not created
)

if exist "dist\Dev.exe" (
    copy "dist\Dev.exe" "Dev.exe"
    echo   [OK] Dev.exe
) else (
    echo   [FAIL] Dev.exe not created
)

if exist "dist\UserVersion.exe" (
    copy "dist\UserVersion.exe" "UserVersion.exe"
    echo   [OK] UserVersion.exe
) else (
    echo   [FAIL] UserVersion.exe not created
)

echo.
echo ============================================
if exist "Setup.exe" if exist "Dev.exe" if exist "UserVersion.exe" (
    echo   Build Complete!
    echo   Executables are in the repository root.
) else (
    echo   Build had errors. Check above for details.
)
echo ============================================
echo.
pause
