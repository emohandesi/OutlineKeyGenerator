# Deployment Guide for User Counter Service

## Server Deployment on namaz-sw.qawqa.link

### 1. Basic Deployment (Development/Testing)

#### Quick Start:
```bash
# On your server (namaz-sw.qawqa.link)
cd /path/to/your/project
python3 user_counter_service.py --host 0.0.0.0 --port 8080
```

#### Access from other computers:
```bash
# From any computer
curl -X POST http://namaz-sw.qawqa.link:8080/health
curl -X POST http://namaz-sw.qawqa.link:8080/keepalive
curl http://namaz-sw.qawqa.link:8080/stats
```

### 2. Production Deployment with Gunicorn

#### Install Gunicorn:
```bash
pip install gunicorn
```

#### Run with Gunicorn:
```bash
# Basic production setup
gunicorn -w 4 -b 0.0.0.0:8080 user_counter_service:app

# With more options
gunicorn \
  --workers 4 \
  --bind 0.0.0.0:8080 \
  --timeout 30 \
  --keep-alive 5 \
  --max-requests 1000 \
  --max-requests-jitter 100 \
  --access-logfile /var/log/user-counter/access.log \
  --error-logfile /var/log/user-counter/error.log \
  --log-level info \
  --daemon \
  user_counter_service:app
```

### 3. Systemd Service (Recommended for Production)

Create a systemd service file:

#### /etc/systemd/system/user-counter.service
```ini
[Unit]
Description=User Counter Service
After=network.target

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=/opt/user-counter
Environment=PATH=/opt/user-counter/.venv/bin
ExecStart=/opt/user-counter/.venv/bin/gunicorn --workers 4 --bind 0.0.0.0:8080 user_counter_service:app
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

#### Enable and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable user-counter
sudo systemctl start user-counter
sudo systemctl status user-counter
```

### 4. Nginx Reverse Proxy (Optional but Recommended)

#### /etc/nginx/sites-available/user-counter
```nginx
server {
    listen 80;
    server_name namaz-sw.qawqa.link;

    location /api/user-counter/ {
        proxy_pass http://127.0.0.1:8080/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

#### Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/user-counter /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 5. Firewall Configuration

```bash
# Allow the port through firewall
sudo ufw allow 8080/tcp

# Or if using nginx reverse proxy
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
```

## Usage Examples from Remote Computers

### 1. Direct API Calls

#### Using curl:
```bash
# Health check (creates new user if no cookie)
curl -X POST http://namaz-sw.qawqa.link:8080/health

# With cookie persistence
curl -X POST http://namaz-sw.qawqa.link:8080/health -c cookies.txt -b cookies.txt

# Get statistics
curl http://namaz-sw.qawqa.link:8080/stats
```

#### Using Python requests:
```python
import requests

# Create a session to maintain cookies
session = requests.Session()

# First request (new user)
response = session.post('http://namaz-sw.qawqa.link:8080/health')
print(response.json())

# Subsequent requests (same user due to cookie)
response = session.post('http://namaz-sw.qawqa.link:8080/health')
print(response.json())

# Get statistics
stats = session.get('http://namaz-sw.qawqa.link:8080/stats')
print(stats.json())
```

#### Using JavaScript (browser):
```javascript
// Health check
fetch('http://namaz-sw.qawqa.link:8080/health', {
    method: 'POST',
    credentials: 'include'  // Include cookies
})
.then(response => response.json())
.then(data => console.log(data));

// Get statistics
fetch('http://namaz-sw.qawqa.link:8080/stats', {
    credentials: 'include'
})
.then(response => response.json())
.then(data => console.log(data));
```

### 2. If Using Nginx Reverse Proxy

```bash
# URLs would be:
curl -X POST http://namaz-sw.qawqa.link/api/user-counter/health
curl http://namaz-sw.qawqa.link/api/user-counter/stats
```

## Security Considerations

### 1. HTTPS Setup (Recommended)

Install SSL certificate (Let's Encrypt example):
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d namaz-sw.qawqa.link
```

Update your service to use secure cookies by modifying the code:
```python
# In user_counter_service.py, change:
secure=True  # Enable for HTTPS
```

### 2. Rate Limiting

Add rate limiting to nginx:
```nginx
http {
    limit_req_zone $remote_addr zone=api:10m rate=10r/s;
    
    server {
        location /api/user-counter/ {
            limit_req zone=api burst=20 nodelay;
            # ... rest of proxy config
        }
    }
}
```

## Monitoring and Maintenance

### 1. Log Monitoring
```bash
# Check service logs
sudo journalctl -u user-counter -f

# Check nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### 2. Database Backup
```bash
# Create backup script
#!/bin/bash
cp /opt/user-counter/user_tracking.db /backup/user_tracking_$(date +%Y%m%d_%H%M%S).db
```

### 3. Health Check Script
```bash
#!/bin/bash
# health_check.sh
RESPONSE=$(curl -s -X POST http://localhost:8080/health)
if [[ $? -eq 0 ]] && [[ $RESPONSE == *"healthy"* ]]; then
    echo "Service is healthy"
    exit 0
else
    echo "Service is down"
    exit 1
fi
```

## Troubleshooting

### Common Issues:

1. **Port already in use:**
   ```bash
   sudo lsof -i :8080
   sudo kill -9 <PID>
   ```

2. **Permission denied:**
   ```bash
   sudo chown -R www-data:www-data /opt/user-counter
   ```

3. **Database locked:**
   ```bash
   # Check for zombie processes
   ps aux | grep user_counter
   ```

4. **Service won't start:**
   ```bash
   # Check logs
   sudo journalctl -u user-counter --no-pager
   ```

## Quick Commands Summary

```bash
# Start development server
python3 user_counter_service.py --host 0.0.0.0 --port 8080

# Start production server
gunicorn -w 4 -b 0.0.0.0:8080 user_counter_service:app

# Test from remote
curl -X POST http://namaz-sw.qawqa.link:8080/health

# Check service status
sudo systemctl status user-counter

# View logs
sudo journalctl -u user-counter -f
```