#!/usr/bin/env python3
"""
User Counter Service

A Flask-based service that tracks unique users through cookies.
Handles POST requests and counts daily and monthly active users.
"""

import os
import json
import uuid
import sqlite3
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, make_response
import threading
from contextlib import contextmanager

app = Flask(__name__)

# Configuration
DATABASE_PATH = 'user_tracking.db'
COOKIE_NAME = 'client_id'
COOKIE_MAX_AGE = 365 * 24 * 60 * 60  # 1 year in seconds

# Thread lock for database operations
db_lock = threading.Lock()


class UserTracker:
    def __init__(self, db_path=DATABASE_PATH):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Initialize the SQLite database with required tables."""
        with self.get_db() as conn:
            conn.executescript('''
                CREATE TABLE IF NOT EXISTS user_activity (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_id TEXT NOT NULL,
                    timestamp DATETIME NOT NULL,
                    date_only DATE NOT NULL,
                    UNIQUE(client_id, date_only)
                );

                CREATE INDEX IF NOT EXISTS idx_client_id ON user_activity(client_id);
                CREATE INDEX IF NOT EXISTS idx_date ON user_activity(date_only);
                CREATE INDEX IF NOT EXISTS idx_timestamp ON user_activity(timestamp);
            ''')

    @contextmanager
    def get_db(self):
        """Get database connection with proper locking."""
        with db_lock:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            try:
                yield conn
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()

    def track_user_activity(self, client_id):
        """Track user activity for the given client ID."""
        now = datetime.now()
        date_only = now.date()
        
        try:
            with self.get_db() as conn:
                # Insert or ignore if already exists for today
                conn.execute('''
                    INSERT OR IGNORE INTO user_activity 
                    (client_id, timestamp, date_only) 
                    VALUES (?, ?, ?)
                ''', (client_id, now, date_only))
                
                # Update timestamp if user already visited today
                conn.execute('''
                    UPDATE user_activity 
                    SET timestamp = ? 
                    WHERE client_id = ? AND date_only = ?
                ''', (now, client_id, date_only))
                
        except sqlite3.Error as e:
            app.logger.error(f"Database error in track_user_activity: {e}")

    def get_active_users(self):
        """Get daily and monthly active user counts."""
        today = datetime.now().date()
        month_ago = today - timedelta(days=30)
        
        try:
            with self.get_db() as conn:
                # Daily active users
                daily_result = conn.execute('''
                    SELECT COUNT(DISTINCT client_id) as count
                    FROM user_activity 
                    WHERE date_only = ?
                ''', (today,)).fetchone()
                
                # Monthly active users
                monthly_result = conn.execute('''
                    SELECT COUNT(DISTINCT client_id) as count
                    FROM user_activity 
                    WHERE date_only >= ?
                ''', (month_ago,)).fetchone()
                
                return {
                    'daily_active_users': daily_result['count'] if daily_result else 0,
                    'monthly_active_users': monthly_result['count'] if monthly_result else 0
                }
        except sqlite3.Error as e:
            app.logger.error(f"Database error in get_active_users: {e}")
            return {
                'daily_active_users': 0,
                'monthly_active_users': 0
            }

    def cleanup_old_data(self, days_to_keep=90):
        """Clean up old user activity data."""
        cutoff_date = datetime.now().date() - timedelta(days=days_to_keep)
        
        try:
            with self.get_db() as conn:
                result = conn.execute('''
                    DELETE FROM user_activity 
                    WHERE date_only < ?
                ''', (cutoff_date,))
                
                deleted_count = result.rowcount
                app.logger.info(f"Cleaned up {deleted_count} old records")
                return deleted_count
        except sqlite3.Error as e:
            app.logger.error(f"Database error in cleanup_old_data: {e}")
            return 0

    def get_user_stats(self):
        """Get detailed user statistics."""
        try:
            with self.get_db() as conn:
                # Total unique users
                total_result = conn.execute('''
                    SELECT COUNT(DISTINCT client_id) as count
                    FROM user_activity
                ''').fetchone()
                
                # Users by day (last 7 days)
                week_ago = datetime.now().date() - timedelta(days=7)
                daily_stats = conn.execute('''
                    SELECT date_only, COUNT(DISTINCT client_id) as count
                    FROM user_activity 
                    WHERE date_only >= ?
                    GROUP BY date_only
                    ORDER BY date_only DESC
                ''', (week_ago,)).fetchall()
                
                return {
                    'total_unique_users': total_result['count'] if total_result else 0,
                    'daily_breakdown': [
                        {
                            'date': str(row['date_only']),
                            'users': row['count']
                        } for row in daily_stats
                    ]
                }
        except sqlite3.Error as e:
            app.logger.error(f"Database error in get_user_stats: {e}")
            return {
                'total_unique_users': 0,
                'daily_breakdown': []
            }


# Initialize tracker
tracker = UserTracker()


@app.route('/health', methods=['POST'])
def health_check():
    """Health check endpoint that tracks unique clients"""
    if request.method != 'POST':
        return jsonify({'error': 'Method not allowed'}), 405

    # Get or create client ID from cookie
    client_id = request.cookies.get(COOKIE_NAME)
    
    # Create response
    response_data = {'status': 'healthy'}
    
    if not client_id:
        # Generate new client ID if none exists
        client_id = str(uuid.uuid4())
        response_data['new_client'] = True
    else:
        response_data['new_client'] = False

    # Track user activity
    tracker.track_user_activity(client_id)

    # Add active user counts to response
    user_counts = tracker.get_active_users()
    response_data.update(user_counts)

    # Create response with cookie
    response = make_response(jsonify(response_data))
    
    if response_data['new_client']:
        response.set_cookie(
            COOKIE_NAME,
            client_id,
            max_age=COOKIE_MAX_AGE,
            httponly=True,
            samesite='Lax',
            secure=False  # Set to True in production with HTTPS
        )

    return response


@app.route('/keepalive', methods=['POST'])
def keepalive():
    """Alternative endpoint name for keepalive requests"""
    return health_check()


@app.route('/stats', methods=['GET'])
def get_stats():
    """Get detailed user statistics (admin endpoint)"""
    try:
        stats = tracker.get_user_stats()
        active_users = tracker.get_active_users()
        
        return jsonify({
            'success': True,
            'data': {
                **stats,
                **active_users,
                'timestamp': datetime.now().isoformat()
            }
        })
    except Exception as e:
        app.logger.error(f"Error in get_stats: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/cleanup', methods=['POST'])
def cleanup_data():
    """Clean up old user data (admin endpoint)"""
    try:
        days_to_keep = request.json.get('days_to_keep', 90) if request.json else 90
        deleted_count = tracker.cleanup_old_data(days_to_keep)
        
        return jsonify({
            'success': True,
            'message': f'Cleaned up {deleted_count} old records',
            'deleted_count': deleted_count
        })
    except Exception as e:
        app.logger.error(f"Error in cleanup_data: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='User Counter Service')
    parser.add_argument('--host', default='127.0.0.1', help='Host to bind to')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    print(f"Starting User Counter Service on {args.host}:{args.port}")
    print(f"Database: {DATABASE_PATH}")
    print("Available endpoints:")
    print("  POST /health - Health check with user tracking")
    print("  POST /keepalive - Alternative keepalive endpoint")
    print("  GET /stats - Get user statistics")
    print("  POST /cleanup - Clean up old data")
    
    app.run(host=args.host, port=args.port, debug=args.debug)