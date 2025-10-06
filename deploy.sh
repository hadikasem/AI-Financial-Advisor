#!/bin/bash

# Deployment Script for Risk Assessment App

set -e

echo "🚀 Starting Risk Assessment App Deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    print_status "Docker and Docker Compose are installed ✓"
}

# Check if Ollama is running
check_ollama() {
    if ! curl -s http://localhost:11434/api/tags > /dev/null; then
        print_warning "Ollama is not running. Starting Ollama..."
        
        # Try to start Ollama
        if command -v ollama &> /dev/null; then
            ollama serve &
            sleep 5
            
            # Pull the required model
            print_status "Pulling Ollama model: gpt-oss:20b"
            ollama pull gpt-oss:20b
        else
            print_error "Ollama is not installed. Please install Ollama first."
            print_status "Visit: https://ollama.ai/download"
            exit 1
        fi
    else
        print_status "Ollama is running ✓"
    fi
}

# Create environment files
setup_environment() {
    print_status "Setting up environment files..."
    
    # Backend environment
    if [ ! -f backend/.env ]; then
        cp backend/env_example.txt backend/.env
        print_status "Created backend/.env file"
    fi
    
    # Frontend environment
    if [ ! -f frontend/.env ]; then
        cat > frontend/.env << EOF
API_BASE_URL=http://localhost:5000/api
EOF
        print_status "Created frontend/.env file"
    fi
}

# Build and start services
start_services() {
    print_status "Building and starting services..."
    
    # Stop existing containers
    docker-compose down 2>/dev/null || true
    
    # Build and start services
    docker-compose up --build -d
    
    print_status "Services started successfully!"
}

# Wait for services to be ready
wait_for_services() {
    print_status "Waiting for services to be ready..."
    
    # Wait for database
    print_status "Waiting for database..."
    timeout=60
    while [ $timeout -gt 0 ]; do
        if docker-compose exec -T db pg_isready -U risk_agent_user -d risk_agent_db > /dev/null 2>&1; then
            print_status "Database is ready ✓"
            break
        fi
        sleep 2
        timeout=$((timeout - 2))
    done
    
    if [ $timeout -le 0 ]; then
        print_error "Database failed to start"
        exit 1
    fi
    
    # Wait for backend
    print_status "Waiting for backend API..."
    timeout=60
    while [ $timeout -gt 0 ]; do
        if curl -s http://localhost:5000/api/health > /dev/null 2>&1; then
            print_status "Backend API is ready ✓"
            break
        fi
        sleep 2
        timeout=$((timeout - 2))
    done
    
    if [ $timeout -le 0 ]; then
        print_error "Backend API failed to start"
        exit 1
    fi
    
    # Wait for frontend
    print_status "Waiting for frontend..."
    timeout=60
    while [ $timeout -gt 0 ]; do
        if curl -s http://localhost:8501/_stcore/health > /dev/null 2>&1; then
            print_status "Frontend is ready ✓"
            break
        fi
        sleep 2
        timeout=$((timeout - 2))
    done
    
    if [ $timeout -le 0 ]; then
        print_error "Frontend failed to start"
        exit 1
    fi
}

# Run database migrations
run_migrations() {
    print_status "Running database migrations..."
    
    # Run the migration script
    python3 scripts/migrate_data.py
    
    print_status "Database migrations completed ✓"
}

# Display service URLs
show_urls() {
    echo ""
    print_status "🎉 Deployment completed successfully!"
    echo ""
    echo "📱 Application URLs:"
    echo "   Frontend: http://localhost:8501"
    echo "   Backend API: http://localhost:5000"
    echo "   Database: localhost:5432"
    echo "   Ollama: http://localhost:11434"
    echo ""
    echo "🔧 Management Commands:"
    echo "   View logs: docker-compose logs -f"
    echo "   Stop services: docker-compose down"
    echo "   Restart services: docker-compose restart"
    echo "   Update services: docker-compose up --build -d"
    echo ""
    echo "📊 Test the application:"
    echo "   1. Open http://localhost:8501 in your browser"
    echo "   2. Register a new account"
    echo "   3. Complete the risk assessment"
    echo "   4. Create financial goals"
    echo "   5. Update progress and see recommendations"
    echo ""
}

# Main deployment function
main() {
    print_status "Starting Risk Assessment App deployment..."
    
    check_docker
    check_ollama
    setup_environment
    start_services
    wait_for_services
    run_migrations
    show_urls
    
    print_status "Deployment completed! 🎉"
}

# Handle script arguments
case "${1:-}" in
    "stop")
        print_status "Stopping services..."
        docker-compose down
        print_status "Services stopped ✓"
        ;;
    "restart")
        print_status "Restarting services..."
        docker-compose restart
        print_status "Services restarted ✓"
        ;;
    "logs")
        docker-compose logs -f
        ;;
    "status")
        docker-compose ps
        ;;
    "clean")
        print_status "Cleaning up..."
        docker-compose down -v
        docker system prune -f
        print_status "Cleanup completed ✓"
        ;;
    *)
        main
        ;;
esac
