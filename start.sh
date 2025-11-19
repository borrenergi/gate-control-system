#!/bin/bash

# Grindstyrning - Quick Start Script

echo "🚪 Grindstyrning - Startar systemet..."
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env fil saknas!"
    echo "Kopierar .env.example till .env..."
    cp .env.example .env
    echo ""
    echo "📝 Redigera .env och fyll i dina uppgifter:"
    echo "   nano .env"
    echo ""
    echo "Kör sedan: ./start.sh igen"
    exit 1
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker är inte installerat"
    echo "Installera med: curl -fsSL https://get.docker.com | sh"
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose är inte installerat"
    exit 1
fi

# Create necessary directories
mkdir -p logs config templates

echo "🐳 Startar Docker containers..."
docker-compose up -d

echo ""
echo "✅ Systemet är igång!"
echo ""
echo "📊 Webbgränssnitt: http://localhost:5000"
echo "🔐 Standard login: admin / admin123"
echo ""
echo "📋 Visa loggar:    docker-compose logs -f"
echo "🛑 Stoppa:         docker-compose down"
echo ""
echo "📖 Läs SETUP_GUIDE.md för fullständig installation"
echo ""
