#!/bin/bash

echo "Starting E-Commerce Hub Platform..."
echo

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed or not in PATH"
    echo "Please install Python 3.8+ and add it to your PATH"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install requirements
echo "Installing requirements..."
pip install -r requirements.txt

# Apply migrations
echo "Applying database migrations..."
python manage.py makemigrations
python manage.py migrate

# Create superuser if needed (optional)
echo
echo "To create a superuser account, run: python manage.py createsuperuser"
echo

# Start the development server
echo "Starting Django development server..."
echo
echo "The server will be available at: http://127.0.0.1:8000"
echo "Press Ctrl+C to stop the server"
echo
python manage.py runserver 0.0.0.0:8000
