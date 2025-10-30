#!/bin/bash
# deploy.sh - Simple deployment script for User Counter Service

set -e

# Configuration
SERVICE_NAME="user-counter"
SERVICE_PORT="8080"
SERVICE_HOST="0.0.0.0"
INSTALL_DIR="/opt/user-counter"
SERVICE_USER="www-data"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_requirements() {
    print_status "Checking requirements..."
    
    if ! command -v python3 &> /dev/null; then
        print_error "Python3 is required but not installed"
        exit 1
    fi
    
    if ! command -v pip3 &> /dev/null; then
        print_error "pip3 is required but not installed"
        exit 1
    fi
    
    print_status "Requirements check passed"
}

install_service() {
    print_status "Installing User Counter Service..."
    
    # Create installation directory
    sudo mkdir -p $INSTALL_DIR
    
    # Copy files
    sudo cp user_counter_service.py $INSTALL_DIR/
    sudo cp requirements.txt $INSTALL_DIR/ 2>/dev/null || echo "flask" | sudo tee $INSTALL_DIR/requirements.txt
    
    # Create virtual environment
    sudo python3 -m venv $INSTALL_DIR/.venv
    
    # Install dependencies
    sudo $INSTALL_DIR/.venv/bin/pip install -r $INSTALL_DIR/requirements.txt
    
    # Set permissions
    if id "$SERVICE_USER" &>/dev/null; then
        sudo chown -R $SERVICE_USER:$SERVICE_USER $INSTALL_DIR
    else
        print_warning "User $SERVICE_USER not found, keeping current ownership"
    fi
    
    print_status "Service installed to $INSTALL_DIR"
}

create_systemd_service() {
    print_status "Creating systemd service..."
    
    sudo tee /etc/systemd/system/$SERVICE_NAME.service > /dev/null <<EOF
[Unit]
Description=User Counter Service
After=network.target

[Service]
Type=exec
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$INSTALL_DIR
Environment=PATH=$INSTALL_DIR/.venv/bin
ExecStart=$INSTALL_DIR/.venv/bin/python user_counter_service.py --host $SERVICE_HOST --port $SERVICE_PORT
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

    sudo systemctl daemon-reload
    sudo systemctl enable $SERVICE_NAME
    
    print_status "Systemd service created"
}

start_service() {
    print_status "Starting service..."
    
    sudo systemctl start $SERVICE_NAME
    sleep 2
    
    if sudo systemctl is-active --quiet $SERVICE_NAME; then
        print_status "Service started successfully"
        sudo systemctl status $SERVICE_NAME --no-pager
    else
        print_error "Failed to start service"
        sudo journalctl -u $SERVICE_NAME --no-pager -n 20
        exit 1
    fi
}

test_service() {
    print_status "Testing service..."
    
    # Wait for service to be ready
    sleep 3
    
    # Test health endpoint
    if response=$(curl -s -X POST http://localhost:$SERVICE_PORT/health 2>/dev/null); then
        if echo "$response" | grep -q "healthy"; then
            print_status "Service test passed: $response"
        else
            print_warning "Service responded but may have issues: $response"
        fi
    else
        print_error "Service test failed - cannot reach http://localhost:$SERVICE_PORT/health"
        print_error "Check if the service is running and port is accessible"
    fi
}

configure_firewall() {
    if command -v ufw &> /dev/null; then
        print_status "Configuring firewall..."
        sudo ufw allow $SERVICE_PORT/tcp
        print_status "Firewall configured to allow port $SERVICE_PORT"
    else
        print_warning "UFW not found, please manually configure firewall to allow port $SERVICE_PORT"
    fi
}

show_usage() {
    print_status "Service deployed successfully!"
    echo ""
    echo "Service Information:"
    echo "  - Service: $SERVICE_NAME"
    echo "  - Port: $SERVICE_PORT"
    echo "  - Installation: $INSTALL_DIR"
    echo ""
    echo "Usage from other computers:"
    echo "  curl -X POST http://$(hostname -I | awk '{print $1}'):$SERVICE_PORT/health"
    echo "  curl -X POST http://namaz-sw.qawqa.link:$SERVICE_PORT/health"
    echo ""
    echo "Management commands:"
    echo "  sudo systemctl start $SERVICE_NAME"
    echo "  sudo systemctl stop $SERVICE_NAME"
    echo "  sudo systemctl restart $SERVICE_NAME"
    echo "  sudo systemctl status $SERVICE_NAME"
    echo "  sudo journalctl -u $SERVICE_NAME -f"
}

# Main deployment flow
main() {
    print_status "Starting deployment of User Counter Service..."
    
    check_requirements
    install_service
    create_systemd_service
    start_service
    test_service
    configure_firewall
    show_usage
}

# Handle command line arguments
case "${1:-deploy}" in
    "deploy")
        main
        ;;
    "start")
        sudo systemctl start $SERVICE_NAME
        ;;
    "stop")
        sudo systemctl stop $SERVICE_NAME
        ;;
    "restart")
        sudo systemctl restart $SERVICE_NAME
        ;;
    "status")
        sudo systemctl status $SERVICE_NAME
        ;;
    "logs")
        sudo journalctl -u $SERVICE_NAME -f
        ;;
    "test")
        test_service
        ;;
    "uninstall")
        print_status "Uninstalling service..."
        sudo systemctl stop $SERVICE_NAME 2>/dev/null || true
        sudo systemctl disable $SERVICE_NAME 2>/dev/null || true
        sudo rm -f /etc/systemd/system/$SERVICE_NAME.service
        sudo systemctl daemon-reload
        sudo rm -rf $INSTALL_DIR
        print_status "Service uninstalled"
        ;;
    *)
        echo "Usage: $0 {deploy|start|stop|restart|status|logs|test|uninstall}"
        echo ""
        echo "Commands:"
        echo "  deploy    - Full deployment (default)"
        echo "  start     - Start the service"
        echo "  stop      - Stop the service"
        echo "  restart   - Restart the service"
        echo "  status    - Show service status"
        echo "  logs      - Show service logs (follow)"
        echo "  test      - Test the service"
        echo "  uninstall - Remove the service completely"
        exit 1
        ;;
esac