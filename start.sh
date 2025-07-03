#!/bin/bash

# AutoApply AI Startup Script
echo "🚀 Starting AutoApply AI..."

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Creating from template..."
    cp .env.example .env
    echo "📝 Please edit .env file with your API keys and configuration"
    echo "❌ Exiting. Please configure .env and run again."
    exit 1
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Create uploads directory if it doesn't exist
mkdir -p uploads

echo "📦 Building Docker containers..."
docker-compose build

echo "🗄️  Starting database and services..."
docker-compose up -d postgres redis

echo "⏳ Waiting for database to be ready..."
sleep 10

echo "🏗️  Running database migrations..."
docker-compose run --rm backend python -c "from backend.app.database import engine, Base; Base.metadata.create_all(bind=engine)"

echo "🌐 Starting all services..."
docker-compose up -d

echo "✅ AutoApply AI is starting up!"
echo ""
echo "🔗 Services:"
echo "   - API Documentation: http://localhost:8000/docs"
echo "   - Main API: http://localhost:8000"
echo "   - Flower (Celery Monitor): http://localhost:5555"
echo "   - pgAdmin (Database): http://localhost:5050"
echo ""
echo "📊 To monitor logs:"
echo "   docker-compose logs -f"
echo ""
echo "🛑 To stop all services:"
echo "   docker-compose down"
echo ""
echo "🧪 To test the system:"
echo "   docker-compose exec backend python -m backend.app.cli test-config" 