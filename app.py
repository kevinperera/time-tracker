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
            if request.headers.get('Content-Type') == 'application/json':
                return jsonify({'error': 'Authentication required'}), 401
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Role-based access control
def role_required(roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'username' not in session:
                if request.headers.get('Content-Type') == 'application/json':
                    return jsonify({'error': 'Authentication required'}), 401
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
    try:
        users = get_users()
        return jsonify({'users': users})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/create_user', methods=['POST'])
@login_required
@role_required(['admin'])
def create_user_route():
    try:
        username = request.json.get('username')
        password = request.json.get('password')
        role = request.json.get('role')
        
        if not username or not password or not role:
            return jsonify({'error': 'Username, password, and role are required'}), 400
        
        if create_user(username, password, role):
            return jsonify({'message': 'User created successfully'})
        else:
            return jsonify({'error': 'Username already exists'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/change_password', methods=['POST'])
@login_required
@role_required(['admin'])
def change_password_route():
    try:
        username = request.json.get('username')
        new_password = request.json.get('new_password')
        
        if not username or not new_password:
            return jsonify({'error': 'Username and new password are required'}), 400
        
        change_password(username, new_password)
        return jsonify({'message': 'Password changed successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/update_user', methods=['POST'])
@login_required
@role_required(['admin'])
def update_user_route():
    try:
        old_username = request.json.get('old_username')
        new_username = request.json.get('new_username')
        new_role = request.json.get('new_role')
        
        if not old_username or not new_username or not new_role:
            return jsonify({'error': 'All fields are required'}), 400
        
        if update_user(old_username, new_username, new_role):
            return jsonify({'message': 'User updated successfully'})
        else:
            return jsonify({'error': 'Failed to update user'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/delete_user', methods=['POST'])
@login_required
@role_required(['admin'])
def delete_user_route():
    try:
        username = request.json.get('username')
        
        if not username:
            return jsonify({'error': 'Username is required'}), 400
        
        if username == 'admin':
            return jsonify({'error': 'Cannot delete admin user'}), 400
        
        if delete_user(username):
            return jsonify({'message': 'User deleted successfully'})
        else:
            return jsonify({'error': 'Failed to delete user'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Records Management
@app.route('/records')
@login_required
def get_records_route():
    try:
        status_filter = request.args.get('status', '')
        search_query = request.args.get('search', '')
        assigned_to_me = request.args.get('assigned_to_me', 'false').lower() == 'true'
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        offset = (page - 1) * limit
        
        user_role = session['role']
        username = session['username']
        
        # If assigned_to_me is true, filter by current user
        if assigned_to_me and user_role == 'developer':
            developer_filter = username
        else:
            developer_filter = None
        
        records = get_records(
            user_role=user_role, 
            username=username, 
            status=status_filter, 
            search=search_query,
            developer_filter=developer_filter,
            limit=limit,
            offset=offset
        )
        
        total_records = get_records_count(
            user_role=user_role,
            username=username,
            status=status_filter,
            search=search_query,
            developer_filter=developer_filter
        )
        
        # Add time tracking data for each record
        for record in records:
            # Add ETA warning
            if record['eta']:
                try:
                    eta_date = datetime.strptime(record['eta'], '%Y-%m-%d')
                    days_until_eta = (eta_date - datetime.now()).days
                    record['eta_warning'] = days_until_eta <= 2
                except ValueError:
                    record['eta_warning'] = False
            else:
                record['eta_warning'] = False
            
            # Calculate current time for active statuses and add to total
            current_todo_time = record['total_todo_time']
            current_in_progress_time = record['total_in_progress_time']
            current_in_review_time = record['total_in_review_time']
            current_review_failed_time = record['total_review_failed_time']
            
            # Add current active time if status is TODO
            if record['status'] == 'TODO' and record['todo_start_time']:
                current_todo_time += calculate_time_spent(record['todo_start_time'])
            
            # Add current active time if status is In Progress
            if record['status'] == 'In Progress' and record['in_progress_start_time']:
                current_in_progress_time += calculate_time_spent(record['in_progress_start_time'])
            
            # Add current active time if status is In Review
            if record['status'] == 'In Review' and record['in_review_start_time']:
                current_in_review_time += calculate_time_spent(record['in_review_start_time'])
            
            # Add current active time if status is Review failed - In Progress
            if record['status'] == 'Review failed - In Progress' and record['review_failed_start_time']:
                current_review_failed_time += calculate_time_spent(record['review_failed_start_time'])
            
            # Convert to hours and minutes
            record['time_todo_hours'] = int(current_todo_time)
            record['time_todo_minutes'] = int((current_todo_time - record['time_todo_hours']) * 60)
            record['time_in_progress_hours'] = int(current_in_progress_time)
            record['time_in_progress_minutes'] = int((current_in_progress_time - record['time_in_progress_hours']) * 60)
            record['time_in_review_hours'] = int(current_in_review_time)
            record['time_in_review_minutes'] = int((current_in_review_time - record['time_in_review_hours']) * 60)
            record['time_review_failed_hours'] = int(current_review_failed_time)
            record['time_review_failed_minutes'] = int((current_review_failed_time - record['time_review_failed_hours']) * 60)
            
            record['time_todo'] = current_todo_time
            record['time_in_progress'] = current_in_progress_time
            record['time_in_review'] = current_in_review_time
            record['time_review_failed'] = current_review_failed_time
            
            # Add tracking indicators
            record['is_todo_tracking'] = record['status'] == 'TODO' and record['todo_start_time'] is not None
            record['is_in_progress_tracking'] = record['status'] == 'In Progress' and record['in_progress_start_time'] is not None
            record['is_in_review_tracking'] = record['status'] == 'In Review' and record['in_review_start_time'] is not None
            record['is_review_failed_tracking'] = record['status'] == 'Review failed - In Progress' and record['review_failed_start_time'] is not None
        
        return jsonify({
            'records': records, 
            'user_role': user_role,
            'total_records': total_records,
            'current_page': page,
            'total_pages': (total_records + limit - 1) // limit
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/records/create', methods=['POST'])
@login_required
@role_required(['admin', 'lead'])
def create_record_route():
    try:
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
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/records/<int:record_id>')
@login_required
def get_record_route(record_id):
    try:
        record = get_record_by_id(record_id)
        if not record:
            return jsonify({'error': 'Record not found'}), 404
        
        # Check if user has permission to view this record
        user_role = session['role']
        username = session['username']
        
        if user_role == 'developer' and record['developer_assignee'] != username:
            return jsonify({'error': 'Access denied'}), 403
        
        return jsonify(record)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/records/<int:record_id>/update', methods=['POST'])
@login_required
def update_record_route(record_id):
    try:
        data = request.json
        
        # Check if user has permission to edit this record
        record = get_record_by_id(record_id)
        if not record:
            return jsonify({'error': 'Record not found'}), 404
        
        user_role = session['role']
        username = session['username']
        
        # Developers cannot update records (only status through separate endpoint)
        if user_role == 'developer':
            return jsonify({'error': 'Access denied - Developers cannot edit records'}), 403
        
        # Admin and Lead can update all fields
        if user_role in ['admin', 'lead']:
            update_record(record_id, **data)
            return jsonify({'message': 'Record updated successfully'})
        
        return jsonify({'error': 'Access denied'}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/records/<int:record_id>/status', methods=['POST'])
@login_required
def update_record_status_route(record_id):
    try:
        data = request.json
        new_status = data.get('status')
        
        if not new_status:
            return jsonify({'error': 'Status is required'}), 400
        
        # Check if user has permission to update status
        record = get_record_by_id(record_id)
        if not record:
            return jsonify({'error': 'Record not found'}), 404
        
        user_role = session['role']
        username = session['username']
        
        print(f"DEBUG: User {username} (role: {user_role}) trying to update record {record_id} status to {new_status}")
        print(f"DEBUG: Record developer: {record.get('developer_assignee')}")
        
        # Developers can update status of their assigned records
        if user_role == 'developer':
            # Check if developer is assigned to this record
            if record.get('developer_assignee') == username:
                # Developers can only change to: In Progress, In Review, Review failed - In Progress, On-Hold, Published
                allowed_statuses = ['In Progress', 'In Review', 'Review failed - In Progress', 'On-Hold', 'Published']
                if new_status not in allowed_statuses:
                    return jsonify({'error': f'Developers can only set status to: {", ".join(allowed_statuses)}'}), 403
                
                print(f"DEBUG: Developer {username} is assigned to record, updating status to {new_status}")
                update_record(record_id, status=new_status)
                return jsonify({'message': 'Status updated successfully'})
            else:
                print(f"DEBUG: Developer {username} is NOT assigned to record {record_id}")
                return jsonify({'error': 'Access denied - You can only update status of your assigned records'}), 403
        
        # Admin and Lead can update status of any record
        if user_role in ['admin', 'lead']:
            update_record(record_id, status=new_status)
            return jsonify({'message': 'Status updated successfully'})
        
        return jsonify({'error': 'Access denied'}), 403
    except Exception as e:
        print(f"DEBUG: Error in status update: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/records/<int:record_id>/delete', methods=['POST'])
@login_required
@role_required(['admin', 'lead'])
def delete_record_route(record_id):
    try:
        if delete_record(record_id):
            return jsonify({'message': 'Record deleted successfully'})
        else:
            return jsonify({'error': 'Failed to delete record'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/records/<int:record_id>/time')
@login_required
def get_record_time_route(record_id):
    try:
        record = get_record_by_id(record_id)
        if not record:
            return jsonify({'error': 'Record not found'}), 404
        
        # Calculate current times including active session
        time_todo = record['total_todo_time']
        time_in_progress = record['total_in_progress_time']
        time_in_review = record['total_in_review_time']
        time_review_failed = record['total_review_failed_time']
        
        if record['status'] == 'TODO' and record['todo_start_time']:
            time_todo += calculate_time_spent(record['todo_start_time'])
        elif record['status'] == 'In Progress' and record['in_progress_start_time']:
            time_in_progress += calculate_time_spent(record['in_progress_start_time'])
        elif record['status'] == 'In Review' and record['in_review_start_time']:
            time_in_review += calculate_time_spent(record['in_review_start_time'])
        elif record['status'] == 'Review failed - In Progress' and record['review_failed_start_time']:
            time_review_failed += calculate_time_spent(record['review_failed_start_time'])
        
        total_time = time_todo + time_in_progress + time_in_review + time_review_failed
        
        return jsonify({
            'time_todo': time_todo,
            'time_in_progress': time_in_progress,
            'time_in_review': time_in_review,
            'time_review_failed': time_review_failed,
            'total_time': total_time
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/developers')
@login_required
def get_developers_route():
    try:
        developers = get_users(role='developer')
        return jsonify({'developers': developers})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/export/csv')
@login_required
@role_required(['admin'])
def export_csv():
    try:
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
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    if request.headers.get('Content-Type') == 'application/json':
        return jsonify({'error': 'Resource not found'}), 404
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    if request.headers.get('Content-Type') == 'application/json':
        return jsonify({'error': 'Internal server error'}), 500
    return render_template('500.html'), 500



@app.route('/workload')
@login_required
@role_required(['admin', 'lead'])
def workload_dashboard():
    return render_template('workload.html', 
                         username=session['username'], 
                         role=session['role'])

@app.route('/api/workload')
@login_required
@role_required(['admin', 'lead'])
def api_get_workload():
    try:
        date = request.args.get('date')
        developer = request.args.get('developer')
        
        if not date:
            date = datetime.now().strftime('%Y-%m-%d')
        
        workload_data = get_developer_workload(date, developer)
        activities = get_developer_daily_activities(date, developer)
        
        return jsonify({
            'workload': workload_data,
            'activities': activities,
            'date': date,
            'developer': developer
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/developers/workload')
@login_required
@role_required(['admin', 'lead'])
def api_get_developers_for_workload():
    try:
        developers = get_users(role='developer')
        return jsonify({'developers': developers})
    except Exception as e:
        return jsonify({'error': str(e)}), 500



if __name__ == '__main__':
    app.run(debug=True)