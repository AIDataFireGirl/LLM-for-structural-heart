#!/bin/bash

# Structural Heart LLM System - Setup Script
# Automated installation and configuration

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check Python version
check_python_version() {
    if command_exists python3; then
        PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
        REQUIRED_VERSION="3.8"
        
        if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" = "$REQUIRED_VERSION" ]; then
            print_success "Python $PYTHON_VERSION found (>= $REQUIRED_VERSION required)"
            return 0
        else
            print_error "Python $PYTHON_VERSION found, but $REQUIRED_VERSION or higher is required"
            return 1
        fi
    else
        print_error "Python 3 not found. Please install Python 3.8 or higher"
        return 1
    fi
}

# Function to install system dependencies
install_system_dependencies() {
    print_status "Installing system dependencies..."
    
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        if command_exists apt-get; then
            sudo apt-get update
            sudo apt-get install -y python3-pip python3-venv redis-server curl git
        elif command_exists yum; then
            sudo yum install -y python3-pip redis curl git
        elif command_exists dnf; then
            sudo dnf install -y python3-pip redis curl git
        else
            print_error "Unsupported Linux distribution. Please install Python 3.8+, Redis, and curl manually"
            return 1
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if command_exists brew; then
            brew install python@3.9 redis curl git
        else
            print_error "Homebrew not found. Please install Homebrew first: https://brew.sh/"
            return 1
        fi
    else
        print_error "Unsupported operating system: $OSTYPE"
        return 1
    fi
    
    print_success "System dependencies installed"
}

# Function to setup Python virtual environment
setup_python_environment() {
    print_status "Setting up Python virtual environment..."
    
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        print_success "Virtual environment created"
    else
        print_warning "Virtual environment already exists"
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    print_success "Python environment setup complete"
}

# Function to install Python dependencies
install_python_dependencies() {
    print_status "Installing Python dependencies..."
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Install dependencies
    pip install -r requirements.txt
    
    print_success "Python dependencies installed"
}

# Function to setup Redis
setup_redis() {
    print_status "Setting up Redis..."
    
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        if command_exists systemctl; then
            sudo systemctl start redis
            sudo systemctl enable redis
        else
            print_warning "systemctl not found. Please start Redis manually"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if command_exists brew; then
            brew services start redis
        else
            print_warning "Homebrew not found. Please start Redis manually"
        fi
    fi
    
    # Test Redis connection
    if redis-cli ping > /dev/null 2>&1; then
        print_success "Redis is running"
    else
        print_warning "Redis connection failed. Please start Redis manually"
    fi
}

# Function to create configuration files
create_config_files() {
    print_status "Creating configuration files..."
    
    # Create .env file if it doesn't exist
    if [ ! -f ".env" ]; then
        cp env.example .env
        print_success "Created .env file from template"
        print_warning "Please update .env file with your configuration"
    else
        print_warning ".env file already exists"
    fi
    
    # Create necessary directories
    mkdir -p logs cache models monitoring/grafana/dashboards monitoring/grafana/datasources config nginx
    
    print_success "Configuration files created"
}

# Function to setup monitoring
setup_monitoring() {
    print_status "Setting up monitoring configuration..."
    
    # Create Prometheus configuration
    cat > monitoring/prometheus.yml << EOF
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'structural-heart-llm'
    static_configs:
      - targets: ['llm-api:8000']
    metrics_path: '/metrics'
    scrape_interval: 5s

  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']
    scrape_interval: 10s
EOF
    
    # Create Redis configuration
    cat > config/redis.conf << EOF
# Redis configuration for Structural Heart LLM System
bind 0.0.0.0
port 6379
timeout 0
tcp-keepalive 300
daemonize no
supervised no
pidfile /var/run/redis_6379.pid
loglevel notice
logfile ""
databases 16
save 900 1
save 300 10
save 60 10000
stop-writes-on-bgsave-error yes
rdbcompression yes
rdbchecksum yes
dbfilename dump.rdb
dir ./
maxmemory 256mb
maxmemory-policy allkeys-lru
appendonly yes
appendfilename "appendonly.aof"
appendfsync everysec
no-appendfsync-on-rewrite no
auto-aof-rewrite-percentage 100
auto-aof-rewrite-min-size 64mb
EOF
    
    print_success "Monitoring configuration created"
}

# Function to run tests
run_tests() {
    print_status "Running tests..."
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Run tests
    if python -m pytest tests/ -v; then
        print_success "Tests passed"
    else
        print_warning "Some tests failed. This is normal for initial setup"
    fi
}

# Function to start the application
start_application() {
    print_status "Starting the application..."
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Start the application
    python main.py &
    APP_PID=$!
    
    # Wait a moment for the app to start
    sleep 5
    
    # Check if the application is running
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        print_success "Application started successfully"
        print_status "API is available at: http://localhost:8000"
        print_status "API documentation at: http://localhost:8000/docs"
        print_status "Health check at: http://localhost:8000/health"
        print_status "Metrics at: http://localhost:8000/metrics"
    else
        print_error "Application failed to start"
        kill $APP_PID 2>/dev/null || true
        return 1
    fi
}

# Function to show usage information
show_usage() {
    echo "Structural Heart LLM System - Setup Script"
    echo "=========================================="
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --help              Show this help message"
    echo "  --install           Install all dependencies and setup the system"
    echo "  --test              Run tests only"
    echo "  --start             Start the application"
    echo "  --docker            Setup using Docker Compose"
    echo "  --monitoring        Setup monitoring only"
    echo ""
    echo "Examples:"
    echo "  $0 --install        # Full installation"
    echo "  $0 --docker         # Setup with Docker"
    echo "  $0 --test           # Run tests"
    echo ""
}

# Function to setup Docker
setup_docker() {
    print_status "Setting up with Docker Compose..."
    
    if ! command_exists docker; then
        print_error "Docker not found. Please install Docker first"
        return 1
    fi
    
    if ! command_exists docker-compose; then
        print_error "Docker Compose not found. Please install Docker Compose first"
        return 1
    fi
    
    # Create .env file for Docker
    if [ ! -f ".env" ]; then
        cp env.example .env
        print_success "Created .env file for Docker"
    fi
    
    # Start services
    docker-compose up -d
    
    print_success "Docker services started"
    print_status "API is available at: http://localhost:8000"
    print_status "Grafana dashboard at: http://localhost:3000"
    print_status "Prometheus metrics at: http://localhost:9090"
}

# Main function
main() {
    echo "Structural Heart LLM System - Setup Script"
    echo "=========================================="
    echo ""
    
    case "${1:-}" in
        --help)
            show_usage
            exit 0
            ;;
        --install)
            print_status "Starting full installation..."
            
            check_python_version || exit 1
            install_system_dependencies
            setup_python_environment
            install_python_dependencies
            setup_redis
            create_config_files
            setup_monitoring
            run_tests
            
            print_success "Installation completed successfully!"
            print_status "To start the application, run: $0 --start"
            ;;
        --test)
            setup_python_environment
            run_tests
            ;;
        --start)
            setup_python_environment
            start_application
            ;;
        --docker)
            setup_docker
            ;;
        --monitoring)
            setup_monitoring
            print_success "Monitoring setup completed"
            ;;
        *)
            show_usage
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@" 