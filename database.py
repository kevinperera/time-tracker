import sqlite3
from datetime import datetime

def init_db():
    conn = sqlite3.connect('time_tracker.db')
    c = conn.cursor()
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS time_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user TEXT NOT NULL,
            task TEXT NOT NULL,
            type TEXT NOT NULL,
            time_spent REAL NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def log_time(user, task, task_type, time_spent):
    conn = sqlite3.connect('time_tracker.db')
    c = conn.cursor()
    
    c.execute('''
        INSERT INTO time_logs (user, task, type, time_spent)
        VALUES (?, ?, ?, ?)
    ''', (user, task, task_type, time_spent))
    
    conn.commit()
    conn.close()

def get_time_logs():
    conn = sqlite3.connect('time_tracker.db')
    c = conn.cursor()
    
    c.execute('''
        SELECT user, task, type, time_spent, timestamp 
        FROM time_logs 
        ORDER BY timestamp DESC
    ''')
    
    logs = []
    for row in c.fetchall():
        logs.append({
            'user': row[0],
            'task': row[1],
            'type': row[2],
            'time_spent': row[3],
            'timestamp': row[4]
        })
    
    conn.close()
    return logs