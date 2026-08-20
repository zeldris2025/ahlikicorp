@echo off
setlocal enabledelayedexpansion

echo 🚀 Ah Liki Investment Corporation - Setup Script
echo ==================================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found. Please install Python 3.11+
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo ✅ Using %PYTHON_VERSION%
echo.

REM Install requirements
echo 📦 Installing dependencies...
pip install --upgrade pip
pip install -r requirements.txt

echo.
echo 🗄️  Running migrations...
python manage.py migrate

echo.
echo 🌱 Seeding initial data...
python manage.py seed_data

echo.
echo ✅ Setup complete!
echo.
echo 📝 Demo Credentials:
echo    Admin:    admin@example.com / AdminPass123!
echo    Finance:  finance@example.com / FinancePass123!
echo    Customer: customer@example.com / CustomerPass123!
echo.
echo 🚀 To start development server:
echo    python manage.py runserver
echo.
echo 🌐 Then visit: http://localhost:8000
echo.
pause
