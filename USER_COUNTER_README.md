# User Counter Service

A Flask-based web service that tracks unique users through cookies and provides daily/monthly active user statistics.

## Features

- **Cookie-based tracking**: Automatically assigns unique client IDs via cookies
- **Daily & Monthly metrics**: Tracks daily active users (DAU) and monthly active users (MAU)
- **SQLite database**: Persistent storage with thread-safe operations
- **Multiple endpoints**: Health check, keepalive, statistics, and cleanup
- **Data cleanup**: Automatic cleanup of old user activity data

## Installation

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the service:
   ```bash
   python3 user_counter_service.py [--host HOST] [--port PORT] [--debug]
   ```

## Endpoints

### POST /health
Health check endpoint that tracks unique clients.

**Request:**
```bash
curl -X POST http://localhost:5000/health
```

**Response:**
```json
{
  "status": "healthy",
  "new_client": true,
  "daily_active_users": 1,
  "monthly_active_users": 1
}
```

### POST /keepalive
Alternative endpoint with same functionality as /health.

### GET /stats
Get detailed user statistics (admin endpoint).

**Response:**
```json
{
  "success": true,
  "data": {
    "daily_active_users": 5,
    "monthly_active_users": 142,
    "total_unique_users": 500,
    "daily_breakdown": [
      {"date": "2025-10-29", "users": 5},
      {"date": "2025-10-28", "users": 8}
    ],
    "timestamp": "2025-10-29T22:15:47.616859"
  }
}
```

### POST /cleanup
Clean up old user activity data (admin endpoint).

**Request:**
```bash
curl -X POST http://localhost:5000/cleanup \
  -H "Content-Type: application/json" \
  -d '{"days_to_keep": 90}'
```

## Cookie Details

- **Name**: `client_id`
- **Duration**: 1 year
- **Properties**: HttpOnly, SameSite=Lax
- **Auto-generated**: UUID4 format for new clients

## Database Schema

The service uses SQLite with the following table:

```sql
CREATE TABLE user_activity (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id TEXT NOT NULL,
    timestamp DATETIME NOT NULL,
    date_only DATE NOT NULL,
    UNIQUE(client_id, date_only)
);
```

## Example Usage

```python
import requests

# First request (new client)
response = requests.post('http://localhost:5000/health')
print(response.json())
# {"status": "healthy", "new_client": true, "daily_active_users": 1, "monthly_active_users": 1}

# Subsequent requests (returning client with cookie)
response = requests.post('http://localhost:5000/health')
print(response.json())
# {"status": "healthy", "new_client": false, "daily_active_users": 1, "monthly_active_users": 1}

# Get statistics
stats = requests.get('http://localhost:5000/stats')
print(stats.json())
```

## Production Deployment

For production use:

1. Use a proper WSGI server (gunicorn, uwsgi)
2. Set `secure=True` for cookies (HTTPS only)
3. Configure proper logging
4. Set up database backups
5. Monitor disk space for SQLite database

Example with gunicorn:
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 user_counter_service:app
```