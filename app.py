from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from database import *
from functools import wraps
import csv
from io import StringIO
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this in production!

# Initialize database
init_db()

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Role-based access control
def role_required(roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'username' not in session:
                return redirect(url_for('login'))
            if session.get('role') not in roles:
                return jsonify({'error': 'Access denied'}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = verify_user(username, password)
        if user:
            session['username'] = user['username']
            session['role'] = user['role']
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error='Invalid credentials')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', 
                         username=session['username'], 
                         role=session['role'])

# User Management (Admin only)
@app.route('/admin/users')
@login_required
@role_required(['admin'])
def admin_users():
    users = get_users()
    return render_template('admin_users.html', users=users, username=session['username'], role=session['role'])

@app.route('/api/users')
@login_required
@role_required(['admin'])
def api_get_users():
    users = get_users()
    return jsonify({'users': users})

@app.route('/admin/create_user', methods=['POST'])
@login_required
@role_required(['admin'])
def create_user_route():
    username = request.json.get('username')
    password = request.json.get('password')
    role = request.json.get('role')
    
    if not username or not password or not role:
        return jsonify({'error': 'Username, password, and role are required'}), 400
    
    if create_user(username, password, role):
        return jsonify({'message': 'User created successfully'})
    else:
        return jsonify({'error': 'Username already exists'}), 400

@app.route('/admin/change_password', methods=['POST'])
@login_required
@role_required(['admin'])
def change_password_route():
    username = request.json.get('username')
    new_password = request.json.get('new_password')
    
    if not username or not new_password:
        return jsonify({'error': 'Username and new password are required'}), 400
    
    change_password(username, new_password)
    return jsonify({'message': 'Password changed successfully'})

@app.route('/admin/update_user', methods=['POST'])
@login_required
@role_required(['admin'])
def update_user_route():
    old_username = request.json.get('old_username')
    new_username = request.json.get('new_username')
    new_role = request.json.get('new_role')
    
    if not old_username or not new_username or not new_role:
        return jsonify({'error': 'All fields are required'}), 400
    
    if update_user(old_username, new_username, new_role):
        return jsonify({'message': 'User updated successfully'})
    else:
        return jsonify({'error': 'Failed to update user'}), 400

@app.route('/admin/delete_user', methods=['POST'])
@login_required
@role_required(['admin'])
def delete_user_route():
    username = request.json.get('username')
    
    if not username:
        return jsonify({'error': 'Username is required'}), 400
    
    if username == 'admin':
        return jsonify({'error': 'Cannot delete admin user'}), 400
    
    if delete_user(username):
        return jsonify({'message': 'User deleted successfully'})
    else:
        return jsonify({'error': 'Failed to delete user'}), 400

# Records Management
@app.route('/records')
@login_required
def get_records_route():
    records = get_records(user_role=session['role'], username=session['username'])
    
    # Add ETA warning for records
    for record in records:
        if record['eta']:
            try:
                eta_date = datetime.strptime(record['eta'], '%Y-%m-%d')
                days_until_eta = (eta_date - datetime.now()).days
                record['eta_warning'] = days_until_eta <= 2
            except ValueError:
                record['eta_warning'] = False
        else:
            record['eta_warning'] = False
    
    return jsonify({'records': records, 'user_role': session['role']})

@app.route('/records/create', methods=['POST'])
@login_required
@role_required(['admin', 'lead'])
def create_record_route():
    task = request.json.get('task')
    book_id = request.json.get('book_id')
    developer_assignee = request.json.get('developer_assignee')
    page_count = request.json.get('page_count')
    ocr = request.json.get('ocr')
    eta = request.json.get('eta')
    
    if not task or not book_id:
        return jsonify({'error': 'Task and Book ID are required'}), 400
    
    record_id = create_record(task, book_id, session['username'], developer_assignee, page_count, ocr, eta)
    return jsonify({'message': 'Record created successfully', 'record_id': record_id})

@app.route('/records/<int:record_id>/update', methods=['POST'])
@login_required
def update_record_route(record_id):
    data = request.json
    
    # Developers can only update status
    if session['role'] == 'developer':
        if 'status' in data:
            record = get_record_by_id(record_id)
            if record and record['developer_assignee'] == session['username']:
                log_time_tracking(record_id, session['username'], record['status'], data['status'])
                update_record(record_id, status=data['status'])
                return jsonify({'message': 'Status updated successfully'})
        return jsonify({'error': 'Access denied'}), 403
    
    # Admin and Lead can update all fields
    update_record(record_id, **data)
    return jsonify({'message': 'Record updated successfully'})

@app.route('/records/<int:record_id>')
@login_required
def get_record_route(record_id):
    record = get_record_by_id(record_id)
    if not record:
        return jsonify({'error': 'Record not found'}), 404
    return jsonify(record)

@app.route('/records/<int:record_id>/time')
@login_required
def get_record_time_route(record_id):
    record = get_record_by_id(record_id)
    if not record:
        return jsonify({'error': 'Record not found'}), 404
    
    time_spent = get_time_spent(record_id, record['developer_assignee']) if record['developer_assignee'] else 0
    return jsonify({'time_spent': time_spent})

@app.route('/export/csv')
@login_required
@role_required(['admin'])
def export_csv():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # This would need to be implemented based on your date filtering needs
    records = get_records()
    
    output = StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['ID', 'Task', 'Book ID', 'Developer', 'Page Count', 'OCR', 'ETA', 'Status', 'Created By', 'Created Date', 'Published Date'])
    
    # Write data
    for record in records:
        writer.writerow([
            record['id'],
            record['task'],
            record['book_id'],
            record['developer_assignee'] or '',
            record['page_count'] or '',
            record['ocr'] or '',
            record['eta'] or '',
            record['status'],
            record['created_by'],
            record['created_date'],
            record['published_date'] or ''
        ])
    
    output.seek(0)
    return output.getvalue(), 200, {
        'Content-Type': 'text/csv',
        'Content-Disposition': 'attachment; filename=records_export.csv'
    }

if __name__ == '__main__':
    app.run(debug=True)