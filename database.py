import sqlite3
from datetime import datetime, date
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
        CREATE TABLE IF NOT EXISTS records_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task TEXT NOT NULL,
            book_id TEXT NOT NULL,
            developer_assignee TEXT,
            page_count INTEGER,
            ocr TEXT CHECK(ocr IN ('yes', 'no')),
            eta DATE,
            status TEXT NOT NULL CHECK(status IN ('Backlog', 'TODO', 'In Progress', 'In Review', 'Published', 'On-Hold', 'Review failed - In Progress')),
            created_by TEXT NOT NULL,
            created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            published_date DATETIME,
            todo_start_time DATETIME,
            in_progress_start_time DATETIME,
            in_review_start_time DATETIME,
            review_failed_start_time DATETIME,
            FOREIGN KEY (developer_assignee) REFERENCES users (username),
            FOREIGN KEY (created_by) REFERENCES users (username)
        )
    ''')
    
    # Time tracking table - NEW: Separate table for daily time tracking
    c.execute('''
        CREATE TABLE IF NOT EXISTS record_time_tracking (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            record_id INTEGER NOT NULL,
            status TEXT NOT NULL,
            start_time DATETIME NOT NULL,
            end_time DATETIME,
            time_spent REAL DEFAULT 0,
            tracking_date DATE NOT NULL,
            FOREIGN KEY (record_id) REFERENCES records (id)
        )
    ''')
    
    # Check if old records table exists and migrate data
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='records'")
    if c.fetchone():
        print("Migrating data from old records table to new one...")
        # Copy data from old table to new table
        c.execute('''
            INSERT INTO records_new 
            (id, task, book_id, developer_assignee, page_count, ocr, eta, status, 
             created_by, created_date, published_date, todo_start_time, in_progress_start_time)
            SELECT 
            id, task, book_id, developer_assignee, page_count, ocr, eta, status,
            created_by, created_date, published_date, todo_start_time, in_progress_start_time
            FROM records
        ''')
        # Drop old table
        c.execute("DROP TABLE records")
        # Rename new table
        c.execute("ALTER TABLE records_new RENAME TO records")
        print("Data migration completed successfully")
    
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
    
    if 'in_review_start_time' not in columns:
        c.execute("ALTER TABLE records ADD COLUMN in_review_start_time DATETIME")
        print("Added in_review_start_time column")
    
    if 'review_failed_start_time' not in columns:
        c.execute("ALTER TABLE records ADD COLUMN review_failed_start_time DATETIME")
        print("Added review_failed_start_time column")
    
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
    c.execute("""SELECT status, todo_start_time, in_progress_start_time, in_review_start_time, 
                review_failed_start_time FROM records WHERE id = ?""", (record_id,))
    current_record = c.fetchone()
    if current_record:
        current_status, current_todo_start, current_in_progress_start, current_in_review_start, current_review_failed_start = current_record
    else:
        current_status, current_todo_start, current_in_progress_start, current_in_review_start, current_review_failed_start = (None, None, None, None, None)
    
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
        today = now.date()
        
        # Stop previous status timer and record time
        if current_status in ['TODO', 'In Progress', 'In Review', 'Review failed - In Progress']:
            start_time_field = f"{current_status.lower().replace(' ', '_').replace('-', '_')}_start_time"
            current_start_time = None
            
            if current_status == 'TODO':
                current_start_time = current_todo_start
            elif current_status == 'In Progress':
                current_start_time = current_in_progress_start
            elif current_status == 'In Review':
                current_start_time = current_in_review_start
            elif current_status == 'Review failed - In Progress':
                current_start_time = current_review_failed_start
            
            if current_start_time:
                # Calculate time spent and store in time tracking table
                time_spent = calculate_time_spent(current_start_time)
                
                # Insert into time tracking table with date
                c.execute('''
                    INSERT INTO record_time_tracking 
                    (record_id, status, start_time, end_time, time_spent, tracking_date)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (record_id, current_status, current_start_time, now, time_spent, today))
                
                # Clear the start time
                updates.append(f"{start_time_field} = NULL")
        
        # Start new status timer
        if status in ['TODO', 'In Progress', 'In Review', 'Review failed - In Progress']:
            start_time_field = f"{status.lower().replace(' ', '_').replace('-', '_')}_start_time"
            updates.append(f"{start_time_field} = ?")
            params.append(now)
        
        if status == 'Published':
            updates.append("published_date = ?")
            params.append(now.strftime('%Y-%m-%d %H:%M:%S'))
    
    if updates:
        query = f"UPDATE records SET {', '.join(updates)} WHERE id = ?"
        params.append(record_id)
        c.execute(query, params)
    
    conn.commit()
    conn.close()

def get_records(user_role=None, username=None, status=None, search=None, developer_filter=None, limit=20, offset=0):
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
    
    # Add developer filter for "Assigned to Me"
    if developer_filter:
        conditions.append("r.developer_assignee = ?")
        params.append(developer_filter)
    
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
            'in_review_start_time': row[13],
            'review_failed_start_time': row[14],
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
            'in_review_start_time': row[13],
            'review_failed_start_time': row[14]
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
        # Delete time tracking records first
        c.execute("DELETE FROM record_time_tracking WHERE record_id = ?", (record_id,))
        # Delete the record
        c.execute("DELETE FROM records WHERE id = ?", (record_id,))
        conn.commit()
        success = True
    except sqlite3.Error:
        success = False
    finally:
        conn.close()
    
    return success

def get_records_count(user_role=None, username=None, status=None, search=None, developer_filter=None):
    conn = sqlite3.connect('time_tracker.db')
    c = conn.cursor()
    
    query = "SELECT COUNT(*) FROM records r JOIN users u ON r.created_by = u.username"
    params = []
    conditions = []
    
    if user_role == 'developer' and username:
        conditions.append("(r.developer_assignee = ? OR r.developer_assignee IS NULL)")
        params.append(username)
    
    # Add developer filter for "Assigned to Me"
    if developer_filter:
        conditions.append("r.developer_assignee = ?")
        params.append(developer_filter)
    
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

# NEW FUNCTIONS FOR WORKLOAD TRACKING

def get_developer_workload(date=None, developer_username=None):
    """
    Get workload data for developers for a specific date
    Returns time spent by each developer on each status for the given date
    """
    conn = sqlite3.connect('time_tracker.db')
    c = conn.cursor()
    
    # Default to today if no date provided
    if not date:
        date = datetime.now().strftime('%Y-%m-%d')
    
    # Build query based on parameters
    query = """
        SELECT 
            r.developer_assignee,
            rtt.status,
            SUM(rtt.time_spent) as total_time,
            COUNT(DISTINCT rtt.record_id) as record_count
        FROM record_time_tracking rtt
        JOIN records r ON rtt.record_id = r.id
        WHERE r.developer_assignee IS NOT NULL
        AND rtt.tracking_date = ?
    """
    params = [date]
    
    if developer_username:
        query += " AND r.developer_assignee = ?"
        params.append(developer_username)
    
    query += """
        GROUP BY r.developer_assignee, rtt.status
        ORDER BY r.developer_assignee, rtt.status
    """
    
    c.execute(query, params)
    results = c.fetchall()
    
    # Process results into a structured format
    workload_data = {}
    for row in results:
        developer, status, total_time, record_count = row
        if developer not in workload_data:
            workload_data[developer] = {
                'todo_time': 0,
                'in_progress_time': 0,
                'in_review_time': 0,
                'review_failed_time': 0,
                'total_time': 0,
                'record_count': 0,
                'status_breakdown': {}
            }
        
        workload_data[developer]['status_breakdown'][status] = {
            'time': total_time,
            'record_count': record_count
        }
        
        # Add to specific status totals
        if status == 'TODO':
            workload_data[developer]['todo_time'] += total_time
        elif status == 'In Progress':
            workload_data[developer]['in_progress_time'] += total_time
        elif status == 'In Review':
            workload_data[developer]['in_review_time'] += total_time
        elif status == 'Review failed - In Progress':
            workload_data[developer]['review_failed_time'] += total_time
        
        workload_data[developer]['total_time'] += total_time
        workload_data[developer]['record_count'] += record_count
    
    conn.close()
    return workload_data

def get_developer_daily_activities(date=None, developer_username=None):
    """
    Get detailed daily activities for developers
    """
    conn = sqlite3.connect('time_tracker.db')
    c = conn.cursor()
    
    if not date:
        date = datetime.now().strftime('%Y-%m-%d')
    
    query = """
        SELECT 
            r.id,
            r.task,
            r.book_id,
            r.developer_assignee,
            rtt.status,
            rtt.time_spent,
            rtt.start_time,
            rtt.end_time,
            r.created_date
        FROM record_time_tracking rtt
        JOIN records r ON rtt.record_id = r.id
        WHERE r.developer_assignee IS NOT NULL
        AND rtt.tracking_date = ?
    """
    params = [date]
    
    if developer_username:
        query += " AND r.developer_assignee = ?"
        params.append(developer_username)
    
    query += " ORDER BY r.developer_assignee, rtt.start_time"
    
    c.execute(query, params)
    results = c.fetchall()
    
    # Group by record and status to get totals per record per status
    record_activities = {}
    
    for row in results:
        record_id, task, book_id, developer, status, time_spent, start_time, end_time, created_date = row
        
        if record_id not in record_activities:
            record_activities[record_id] = {
                'id': record_id,
                'task': task,
                'book_id': book_id,
                'developer_assignee': developer,
                'created_date': created_date,
                'todo_time': 0,
                'in_progress_time': 0,
                'in_review_time': 0,
                'review_failed_time': 0,
                'total_time': 0,
                'activities': []
            }
        
        # Add time to appropriate status
        if status == 'TODO':
            record_activities[record_id]['todo_time'] += time_spent
        elif status == 'In Progress':
            record_activities[record_id]['in_progress_time'] += time_spent
        elif status == 'In Review':
            record_activities[record_id]['in_review_time'] += time_spent
        elif status == 'Review failed - In Progress':
            record_activities[record_id]['review_failed_time'] += time_spent
        
        record_activities[record_id]['total_time'] += time_spent
        
        # Add individual activity
        record_activities[record_id]['activities'].append({
            'status': status,
            'time_spent': time_spent,
            'start_time': start_time,
            'end_time': end_time
        })
    
    # Convert to list
    activities = list(record_activities.values())
    
    conn.close()
    return activities