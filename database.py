import sqlite3
from datetime import datetime
import hashlib

def init_db():
    conn = sqlite3.connect('time_tracker.db')
    c = conn.cursor()
    
    # Users table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('admin', 'lead', 'developer')),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Records table
    c.execute('''
        CREATE TABLE IF NOT EXISTS records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task TEXT NOT NULL,
            book_id TEXT NOT NULL,
            developer_assignee TEXT,
            page_count INTEGER,
            ocr TEXT CHECK(ocr IN ('yes', 'no')),
            eta DATE,
            status TEXT NOT NULL CHECK(status IN ('Backlog', 'TODO', 'In Progress', 'In Review', 'Published')),
            created_by TEXT NOT NULL,
            created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            published_date DATETIME,
            FOREIGN KEY (developer_assignee) REFERENCES users (username),
            FOREIGN KEY (created_by) REFERENCES users (username)
        )
    ''')
    
    # Time tracking table
    c.execute('''
        CREATE TABLE IF NOT EXISTS time_tracking (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            record_id INTEGER NOT NULL,
            developer_username TEXT NOT NULL,
            status_from TEXT NOT NULL,
            status_to TEXT NOT NULL,
            start_time DATETIME NOT NULL,
            end_time DATETIME,
            time_spent REAL,
            FOREIGN KEY (record_id) REFERENCES records (id),
            FOREIGN KEY (developer_username) REFERENCES users (username)
        )
    ''')
    
    # Insert default admin user if not exists
    c.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'")
    if c.fetchone()[0] == 0:
        admin_password = hashlib.sha256('admin123'.encode()).hexdigest()
        c.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            ('admin', admin_password, 'admin')
        )
    
    conn.commit()
    conn.close()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_user(username, password):
    conn = sqlite3.connect('time_tracker.db')
    c = conn.cursor()
    
    hashed_password = hash_password(password)
    c.execute(
        "SELECT username, role FROM users WHERE username = ? AND password = ?",
        (username, hashed_password)
    )
    
    user = c.fetchone()
    conn.close()
    
    if user:
        return {'username': user[0], 'role': user[1]}
    return None

def get_users(role=None):
    conn = sqlite3.connect('time_tracker.db')
    c = conn.cursor()
    
    if role:
        c.execute("SELECT username, role FROM users WHERE role = ? ORDER BY username", (role,))
    else:
        c.execute("SELECT username, role FROM users ORDER BY username")
    
    users = [{'username': row[0], 'role': row[1]} for row in c.fetchall()]
    conn.close()
    return users

def create_user(username, password, role):
    conn = sqlite3.connect('time_tracker.db')
    c = conn.cursor()
    
    try:
        hashed_password = hash_password(password)
        c.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            (username, hashed_password, role)
        )
        conn.commit()
        success = True
    except sqlite3.IntegrityError:
        success = False
    finally:
        conn.close()
    
    return success

def change_password(username, new_password):
    conn = sqlite3.connect('time_tracker.db')
    c = conn.cursor()
    
    hashed_password = hash_password(new_password)
    c.execute(
        "UPDATE users SET password = ? WHERE username = ?",
        (hashed_password, username)
    )
    
    conn.commit()
    conn.close()

def create_record(task, book_id, created_by, developer_assignee=None, page_count=None, ocr=None, eta=None):
    conn = sqlite3.connect('time_tracker.db')
    c = conn.cursor()
    
    c.execute('''
        INSERT INTO records (task, book_id, developer_assignee, page_count, ocr, eta, status, created_by)
        VALUES (?, ?, ?, ?, ?, ?, 'Backlog', ?)
    ''', (task, book_id, developer_assignee, page_count, ocr, eta, created_by))
    
    record_id = c.lastrowid
    conn.commit()
    conn.close()
    return record_id

def update_record(record_id, task=None, book_id=None, developer_assignee=None, page_count=None, ocr=None, eta=None, status=None):
    conn = sqlite3.connect('time_tracker.db')
    c = conn.cursor()
    
    updates = []
    params = []
    
    if task is not None:
        updates.append("task = ?")
        params.append(task)
    if book_id is not None:
        updates.append("book_id = ?")
        params.append(book_id)
    if developer_assignee is not None:
        updates.append("developer_assignee = ?")
        params.append(developer_assignee)
    if page_count is not None:
        updates.append("page_count = ?")
        params.append(page_count)
    if ocr is not None:
        updates.append("ocr = ?")
        params.append(ocr)
    if eta is not None:
        updates.append("eta = ?")
        params.append(eta)
    if status is not None:
        updates.append("status = ?")
        params.append(status)
        if status == 'Published':
            updates.append("published_date = ?")
            params.append(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    
    if updates:
        query = f"UPDATE records SET {', '.join(updates)} WHERE id = ?"
        params.append(record_id)
        c.execute(query, params)
        conn.commit()
    
    conn.close()

def get_records(user_role=None, username=None, status=None):
    conn = sqlite3.connect('time_tracker.db')
    c = conn.cursor()
    
    query = """
        SELECT r.*, u.role as created_by_role 
        FROM records r 
        JOIN users u ON r.created_by = u.username
    """
    params = []
    
    if user_role == 'developer' and username:
        query += " WHERE r.developer_assignee = ?"
        params.append(username)
    elif status:
        query += " WHERE r.status = ?"
        params.append(status)
    
    query += " ORDER BY r.created_date DESC"
    
    c.execute(query, params)
    records = []
    for row in c.fetchall():
        records.append({
            'id': row[0],
            'task': row[1],
            'book_id': row[2],
            'developer_assignee': row[3],
            'page_count': row[4],
            'ocr': row[5],
            'eta': row[6],
            'status': row[7],
            'created_by': row[8],
            'created_date': row[9],
            'published_date': row[10],
            'created_by_role': row[11]
        })
    
    conn.close()
    return records

def get_record_by_id(record_id):
    conn = sqlite3.connect('time_tracker.db')
    c = conn.cursor()
    
    c.execute("SELECT * FROM records WHERE id = ?", (record_id,))
    row = c.fetchone()
    
    if row:
        record = {
            'id': row[0],
            'task': row[1],
            'book_id': row[2],
            'developer_assignee': row[3],
            'page_count': row[4],
            'ocr': row[5],
            'eta': row[6],
            'status': row[7],
            'created_by': row[8],
            'created_date': row[9],
            'published_date': row[10]
        }
    else:
        record = None
    
    conn.close()
    return record

def log_time_tracking(record_id, developer_username, status_from, status_to):
    conn = sqlite3.connect('time_tracker.db')
    c = conn.cursor()
    
    # End previous active session for this record and developer
    c.execute('''
        UPDATE time_tracking 
        SET end_time = ?, time_spent = ROUND((JULIANDAY(?) - JULIANDAY(start_time)) * 24, 2)
        WHERE record_id = ? AND developer_username = ? AND end_time IS NULL
    ''', (datetime.now(), datetime.now(), record_id, developer_username))
    
    # Start new session if moving to In Progress
    if status_to == 'In Progress':
        c.execute('''
            INSERT INTO time_tracking (record_id, developer_username, status_from, status_to, start_time)
            VALUES (?, ?, ?, ?, ?)
        ''', (record_id, developer_username, status_from, status_to, datetime.now()))
    
    conn.commit()
    conn.close()

def get_time_spent(record_id, developer_username):
    conn = sqlite3.connect('time_tracker.db')
    c = conn.cursor()
    
    c.execute('''
        SELECT SUM(time_spent) 
        FROM time_tracking 
        WHERE record_id = ? AND developer_username = ? AND time_spent IS NOT NULL
    ''', (record_id, developer_username))
    
    result = c.fetchone()
    total_time = result[0] if result[0] else 0
    conn.close()
    return total_time

def update_user(old_username, new_username, new_role):
    conn = sqlite3.connect('time_tracker.db')
    c = conn.cursor()
    
    try:
        c.execute(
            "UPDATE users SET username = ?, role = ? WHERE username = ?",
            (new_username, new_role, old_username)
        )
        
        # Also update any records that reference this user
        c.execute(
            "UPDATE records SET developer_assignee = ? WHERE developer_assignee = ?",
            (new_username, old_username)
        )
        
        c.execute(
            "UPDATE records SET created_by = ? WHERE created_by = ?",
            (new_username, old_username)
        )
        
        conn.commit()
        success = True
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        success = False
    finally:
        conn.close()
    
    return success

def delete_user(username):
    conn = sqlite3.connect('time_tracker.db')
    c = conn.cursor()
    
    try:
        # Check if user has any records
        c.execute("SELECT COUNT(*) FROM records WHERE created_by = ? OR developer_assignee = ?", 
                 (username, username))
        record_count = c.fetchone()[0]
        
        if record_count > 0:
            # Instead of deleting, you might want to disable the user
            # For now, we'll return False to prevent deletion of users with records
            return False
        
        c.execute("DELETE FROM users WHERE username = ?", (username,))
        conn.commit()
        success = True
    except sqlite3.Error:
        success = False
    finally:
        conn.close()
    
    return success

def delete_record(record_id):
    conn = sqlite3.connect('time_tracker.db')
    c = conn.cursor()
    
    try:
        # First delete related time tracking records
        c.execute("DELETE FROM time_tracking WHERE record_id = ?", (record_id,))
        # Then delete the record
        c.execute("DELETE FROM records WHERE id = ?", (record_id,))
        conn.commit()
        success = True
    except sqlite3.Error:
        success = False
    finally:
        conn.close()
    
    return success