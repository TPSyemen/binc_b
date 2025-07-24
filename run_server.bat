@echo off
echo Starting E-Commerce Hub Platform...
echo.

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed or not in PATH
    echo Please install Python 3.8+ and add it to your PATH
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install requirements
echo Installing requirements...
pip install -r requirements.txt

REM Apply migrations
echo Applying database migrations...
python manage.py makemigrations
python manage.py migrate

REM Create superuser if needed (optional)
echo.
echo To create a superuser account, run: python manage.py createsuperuser
echo.

REM Start the development server
echo Starting Django development server...
echo.
echo The server will be available at: http://127.0.0.1:8000
echo Press Ctrl+C to stop the server
echo.
python manage.py runserver 0.0.0.0:8000

pause
