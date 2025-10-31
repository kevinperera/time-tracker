from flask import Blueprint, render_template, request, jsonify, session
from database import get_records, get_users, get_record_by_id
from datetime import datetime, timedelta
import json

tracking_bp = Blueprint('tracking', __name__)

@tracking_bp.route('/trackingpy')
def tracking_dashboard():
    if 'username' not in session:
        return redirect('/login')
    
    if session.get('role') not in ['admin', 'lead']:
        return "Access denied", 403
    
    return render_template('trackingpy.html', 
                         username=session['username'], 
                         role=session['role'])

@tracking_bp.route('/api/trackingpy/developer-stats')
def developer_stats():
    if 'username' not in session or session.get('role') not in ['admin', 'lead']:
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        # Get all developers
        developers = get_users(role='developer')
        developer_stats = []
        
        # Get date range filters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        for developer in developers:
            # Get all records for this developer
            records = get_records(developer_filter=developer['username'])
            
            developer_data = {
                'username': developer['username'],
                'total_records': len(records),
                'total_todo_time': 0,
                'total_in_progress_time': 0,
                'records_by_status': {
                    'Backlog': 0,
                    'TODO': 0,
                    'In Progress': 0,
                    'In Review': 0,
                    'Published': 0
                }
            }
            
            # Calculate time and status counts
            for record in records:
                # Apply date filter if provided
                if start_date and end_date:
                    record_date = datetime.strptime(record['created_date'].split()[0], '%Y-%m-%d')
                    filter_start = datetime.strptime(start_date, '%Y-%m-%d')
                    filter_end = datetime.strptime(end_date, '%Y-%m-%d')
                    
                    if not (filter_start <= record_date <= filter_end):
                        continue
                
                # Add to status count
                developer_data['records_by_status'][record['status']] += 1
                
                # Add time tracking
                developer_data['total_todo_time'] += record.get('time_todo', 0)
                developer_data['total_in_progress_time'] += record.get('time_in_progress', 0)
            
            developer_stats.append(developer_data)
        
        return jsonify({'developers': developer_stats})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@tracking_bp.route('/api/trackingpy/status-overview')
def status_overview():
    if 'username' not in session or session.get('role') not in ['admin', 'lead']:
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        # Get all records
        records = get_records()
        
        # Get date range filters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        status_counts = {
            'Backlog': 0,
            'TODO': 0,
            'In Progress': 0,
            'In Review': 0,
            'Published': 0
        }
        
        total_time_todo = 0
        total_time_in_progress = 0
        
        for record in records:
            # Apply date filter if provided
            if start_date and end_date:
                record_date = datetime.strptime(record['created_date'].split()[0], '%Y-%m-%d')
                filter_start = datetime.strptime(start_date, '%Y-%m-%d')
                filter_end = datetime.strptime(end_date, '%Y-%m-%d')
                
                if not (filter_start <= record_date <= filter_end):
                    continue
            
            # Add to status count
            status_counts[record['status']] += 1
            
            # Add time tracking
            total_time_todo += record.get('time_todo', 0)
            total_time_in_progress += record.get('time_in_progress', 0)
        
        # Prepare data for charts
        chart_data = {
            'status_counts': status_counts,
            'total_time_todo': total_time_todo,
            'total_time_in_progress': total_time_in_progress,
            'status_labels': list(status_counts.keys()),
            'status_values': list(status_counts.values()),
            'time_labels': ['TODO Time', 'In Progress Time'],
            'time_values': [total_time_todo, total_time_in_progress]
        }
        
        return jsonify(chart_data)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@tracking_bp.route('/api/trackingpy/developer-records')
def developer_records():
    if 'username' not in session or session.get('role') not in ['admin', 'lead']:
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        developer_username = request.args.get('developer')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if not developer_username:
            return jsonify({'error': 'Developer username is required'}), 400
        
        # Get records for specific developer
        records = get_records(developer_filter=developer_username)
        
        developer_records_data = []
        
        for record in records:
            # Apply date filter if provided
            if start_date and end_date:
                record_date = datetime.strptime(record['created_date'].split()[0], '%Y-%m-%d')
                filter_start = datetime.strptime(start_date, '%Y-%m-%d')
                filter_end = datetime.strptime(end_date, '%Y-%m-%d')
                
                if not (filter_start <= record_date <= filter_end):
                    continue
            
            record_data = {
                'id': record['id'],
                'task': record['task'],
                'book_id': record['book_id'],
                'status': record['status'],
                'created_date': record['created_date'],
                'time_todo': record.get('time_todo', 0),
                'time_in_progress': record.get('time_in_progress', 0),
                'eta': record.get('eta'),
                'page_count': record.get('page_count'),
                'ocr': record.get('ocr')
            }
            
            developer_records_data.append(record_data)
        
        return jsonify({'records': developer_records_data})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500