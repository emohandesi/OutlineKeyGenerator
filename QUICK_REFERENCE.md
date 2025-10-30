# Quick Reference - User Counter Service Deployment

## On Your Server (namaz-sw.qawqa.link)

### 1. Quick Development Deploy
```bash
# Start the service quickly
python3 user_counter_service.py --host 0.0.0.0 --port 8080
```

### 2. Production Deploy (Automated)
```bash
# Use the deployment script
sudo ./deploy.sh

# Manual commands if needed
sudo ./deploy.sh deploy    # Full deployment
sudo ./deploy.sh start     # Start service
sudo ./deploy.sh stop      # Stop service
sudo ./deploy.sh status    # Check status
sudo ./deploy.sh logs      # View logs
```

### 3. Manual Production Deploy
```bash
# Install dependencies
pip install flask gunicorn

# Run with Gunicorn
gunicorn -w 4 -b 0.0.0.0:8080 user_counter_service:app

# Or as daemon
gunicorn -w 4 -b 0.0.0.0:8080 --daemon user_counter_service:app
```

## From Other Computers

### Testing the Service
```bash
# Replace namaz-sw.qawqa.link with your actual server address

# Health check (creates user tracking)
curl -X POST http://namaz-sw.qawqa.link:8080/health

# With cookie persistence (recommended)
curl -X POST http://namaz-sw.qawqa.link:8080/health -c cookies.txt -b cookies.txt

# Keepalive endpoint
curl -X POST http://namaz-sw.qawqa.link:8080/keepalive

# Get statistics
curl http://namaz-sw.qawqa.link:8080/stats

# Pretty formatted statistics
curl -s http://namaz-sw.qawqa.link:8080/stats | python3 -m json.tool
```

### Python Client Example
```python
import requests

# Create session for cookie persistence
session = requests.Session()

# Health check
response = session.post('http://namaz-sw.qawqa.link:8080/health')
print(response.json())

# Get stats
stats = session.get('http://namaz-sw.qawqa.link:8080/stats')
print(stats.json())
```

### JavaScript (Browser)
```javascript
// Health check
fetch('http://namaz-sw.qawqa.link:8080/health', {
    method: 'POST',
    credentials: 'include'
})
.then(r => r.json())
.then(data => console.log(data));
```

## Service Management

```bash
# Check if service is running
sudo systemctl status user-counter

# Start/Stop/Restart
sudo systemctl start user-counter
sudo systemctl stop user-counter
sudo systemctl restart user-counter

# View logs
sudo journalctl -u user-counter -f

# Check what's using port 8080
sudo lsof -i :8080

# Kill process on port 8080
sudo kill -9 $(sudo lsof -t -i:8080)
```

## Firewall & Security

```bash
# Allow port through firewall
sudo ufw allow 8080/tcp

# Check firewall status
sudo ufw status

# For production, consider setting up nginx reverse proxy
# and SSL certificate with Let's Encrypt
```

## Troubleshooting

### Common Issues:
1. **Connection refused**: Service not running or wrong port
2. **Permission denied**: Check file permissions and user
3. **Port in use**: Another service using port 8080
4. **Database locked**: Multiple instances running

### Quick Fixes:
```bash
# Check service status
./deploy.sh status

# Restart service
./deploy.sh restart

# View recent logs
./deploy.sh logs | tail -20

# Test service locally
curl -X POST http://localhost:8080/health
```

## Expected Responses

### First Request (New User):
```json
{
  "status": "healthy",
  "new_client": true,
  "daily_active_users": 1,
  "monthly_active_users": 1
}
```

### Subsequent Requests (Returning User):
```json
{
  "status": "healthy",
  "new_client": false,
  "daily_active_users": 1,
  "monthly_active_users": 1
}
```

### Statistics Response:
```json
{
  "success": true,
  "data": {
    "daily_active_users": 5,
    "monthly_active_users": 42,
    "total_unique_users": 128,
    "daily_breakdown": [
      {"date": "2025-10-30", "users": 5}
    ]
  }
}
```