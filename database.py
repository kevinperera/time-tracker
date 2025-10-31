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
            todo_start_time DATETIME,
            in_progress_start_time DATETIME,
            total_todo_time REAL DEFAULT 0,
            total_in_progress_time REAL DEFAULT 0,
            FOREIGN KEY (developer_assignee) REFERENCES users (username),
            FOREIGN KEY (created_by) REFERENCES users (username)
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
    
    # Add new columns if they don't exist
    c.execute("PRAGMA table_info(records)")
    columns = [column[1] for column in c.fetchall()]
    
    if 'todo_start_time' not in columns:
        c.execute("ALTER TABLE records ADD COLUMN todo_start_time DATETIME")
        print("Added todo_start_time column")
    
    if 'in_progress_start_time' not in columns:
        c.execute("ALTER TABLE records ADD COLUMN in_progress_start_time DATETIME")
        print("Added in_progress_start_time column")
    
    if 'total_todo_time' not in columns:
        c.execute("ALTER TABLE records ADD COLUMN total_todo_time REAL DEFAULT 0")
        print("Added total_todo_time column")
    
    if 'total_in_progress_time' not in columns:
        c.execute("ALTER TABLE records ADD COLUMN total_in_progress_time REAL DEFAULT 0")
        print("Added total_in_progress_time column")
    
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
        c.execute("SELECT username, role, created_at FROM users WHERE role = ? ORDER BY username", (role,))
    else:
        c.execute("SELECT username, role, created_at FROM users ORDER BY username")
    
    users = [{'username': row[0], 'role': row[1], 'created_at': row[2]} for row in c.fetchall()]
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
    
    # Get current record data before update
    c.execute("SELECT status, todo_start_time, in_progress_start_time, total_todo_time, total_in_progress_time FROM records WHERE id = ?", (record_id,))
    current_record = c.fetchone()
    if current_record:
        current_status, current_todo_start, current_in_progress_start, current_total_todo, current_total_in_progress = current_record
    else:
        current_status, current_todo_start, current_in_progress_start, current_total_todo, current_total_in_progress = None, None, None, 0, 0
    
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
    
    # Handle status changes and time tracking
    if status is not None and status != current_status:
        updates.append("status = ?")
        params.append(status)
        
        now = datetime.now()
        
        # Handle TODO status time tracking
        if status == 'TODO':
            # Start TODO timer if not already started
            if not current_todo_start:
                updates.append("todo_start_time = ?")
                params.append(now)
        elif current_status == 'TODO' and current_todo_start:
            # Stop TODO timer and add to total
            todo_time_spent = calculate_time_spent(current_todo_start)
            updates.append("total_todo_time = total_todo_time + ?")
            params.append(todo_time_spent)
            updates.append("todo_start_time = NULL")
        
        # Handle In Progress status time tracking
        if status == 'In Progress':
            # Start In Progress timer if not already started
            if not current_in_progress_start:
                updates.append("in_progress_start_time = ?")
                params.append(now)
        elif current_status == 'In Progress' and current_in_progress_start:
            # Stop In Progress timer and add to total
            in_progress_time_spent = calculate_time_spent(current_in_progress_start)
            updates.append("total_in_progress_time = total_in_progress_time + ?")
            params.append(in_progress_time_spent)
            updates.append("in_progress_start_time = NULL")
        
        if status == 'Published':
            updates.append("published_date = ?")
            params.append(now.strftime('%Y-%m-%d %H:%M:%S'))
    
    if updates:
        query = f"UPDATE records SET {', '.join(updates)} WHERE id = ?"
        params.append(record_id)
        c.execute(query, params)
    
    conn.commit()
    conn.close()

def get_records(user_role=None, username=None, status=None, search=None, limit=20, offset=0):
    conn = sqlite3.connect('time_tracker.db')
    c = conn.cursor()
    
    query = """
        SELECT r.*, u.role as created_by_role 
        FROM records r 
        JOIN users u ON r.created_by = u.username
    """
    params = []
    conditions = []
    
    if user_role == 'developer' and username:
        conditions.append("(r.developer_assignee = ? OR r.developer_assignee IS NULL)")
        params.append(username)
    
    if status:
        conditions.append("r.status = ?")
        params.append(status)
    
    if search:
        conditions.append("(r.task LIKE ? OR r.book_id LIKE ? OR r.developer_assignee LIKE ?)")
        params.extend([f'%{search}%', f'%{search}%', f'%{search}%'])
    
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    
    query += " ORDER BY r.created_date DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    
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
            'todo_start_time': row[11],
            'in_progress_start_time': row[12],
            'total_todo_time': row[13] or 0,
            'total_in_progress_time': row[14] or 0,
            'created_by_role': row[15]
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
            'published_date': row[10],
            'todo_start_time': row[11],
            'in_progress_start_time': row[12],
            'total_todo_time': row[13] or 0,
            'total_in_progress_time': row[14] or 0
        }
    else:
        record = None
    
    conn.close()
    return record

def calculate_time_spent(start_time):
    """Calculate time spent from start time to now"""
    if not start_time:
        return 0
    
    if isinstance(start_time, str):
        try:
            start_time = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            try:
                start_time = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S.%f')
            except ValueError:
                return 0
    
    current_time = datetime.now()
    time_spent = (current_time - start_time).total_seconds() / 3600  # Convert to hours
    return round(time_spent, 2)

def delete_record(record_id):
    conn = sqlite3.connect('time_tracker.db')
    c = conn.cursor()
    
    try:
        c.execute("DELETE FROM records WHERE id = ?", (record_id,))
        conn.commit()
        success = True
    except sqlite3.Error:
        success = False
    finally:
        conn.close()
    
    return success

def get_records_count(user_role=None, username=None, status=None, search=None):
    conn = sqlite3.connect('time_tracker.db')
    c = conn.cursor()
    
    query = "SELECT COUNT(*) FROM records r JOIN users u ON r.created_by = u.username"
    params = []
    conditions = []
    
    if user_role == 'developer' and username:
        conditions.append("(r.developer_assignee = ? OR r.developer_assignee IS NULL)")
        params.append(username)
    
    if status:
        conditions.append("r.status = ?")
        params.append(status)
    
    if search:
        conditions.append("(r.task LIKE ? OR r.book_id LIKE ? OR r.developer_assignee LIKE ?)")
        params.extend([f'%{search}%', f'%{search}%', f'%{search}%'])
    
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    
    c.execute(query, params)
    count = c.fetchone()[0]
    conn.close()
    return count