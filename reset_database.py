#!/usr/bin/env python3
import os
import sqlite3

def reset_database():
    # Remove the existing database file
    if os.path.exists('time_tracker.db'):
        os.remove('time_tracker.db')
        print("Removed existing database file")
    
    # Reinitialize the database
    from database import init_db
    init_db()
    print("Database reinitialized successfully")
    
    # Add some test data
    conn = sqlite3.connect('time_tracker.db')
    c = conn.cursor()
    
    # Add test users
    import hashlib
    c.execute(
        "INSERT OR IGNORE INTO users (username, password, role) VALUES (?, ?, ?)",
        ('admin', hashlib.sha256('admin123'.encode()).hexdigest(), 'admin')
    )
    c.execute(
        "INSERT OR IGNORE INTO users (username, password, role) VALUES (?, ?, ?)",
        ('lead1', hashlib.sha256('lead123'.encode()).hexdigest(), 'lead')
    )
    c.execute(
        "INSERT OR IGNORE INTO users (username, password, role) VALUES (?, ?, ?)",
        ('dev1', hashlib.sha256('dev123'.encode()).hexdigest(), 'developer')
    )
    
    # Add test records
    c.execute('''
        INSERT OR IGNORE INTO records (task, book_id, developer_assignee, page_count, ocr, eta, status, created_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', ('Test Task 1', 'BOOK001', 'dev1', 100, 'yes', '2024-12-31', 'TODO', 'lead1'))
    
    c.execute('''
        INSERT OR IGNORE INTO records (task, book_id, developer_assignee, page_count, ocr, eta, status, created_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', ('Test Task 2', 'BOOK002', None, 50, 'no', None, 'Backlog', 'admin'))
    
    conn.commit()
    conn.close()
    print("Test data added successfully")

if __name__ == '__main__':
    reset_database()