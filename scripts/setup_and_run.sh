#!/bin/bash

# AptiFy Module 2 Setup & Run Script

echo "🚀 Starting AptiFy Module 2 Setup..."

# Ensure we are in the project root
cd "$(dirname "$0")/.."

echo "📦 Making migrations for 'assignments' app..."
python3 manage.py makemigrations assignments

echo "📦 Making migrations for 'analysis' app..."
python3 manage.py makemigrations analysis

echo "🔄 Applying migrations..."
python3 manage.py migrate

echo "✅ Setup complete."
echo "🌍 Starting Development Server..."
echo "👉 Open http://127.0.0.1:8000/assignments/ in your browser."

python3 manage.py runserver
