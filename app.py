from flask import Flask, render_template, request, jsonify
from database import init_db, log_time, get_time_logs
import json
from datetime import datetime

app = Flask(__name__)

# Initialize database
init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/log_time', methods=['POST'])
def log_time_route():
    try:
        data = request.get_json()
        user = data.get('user')
        task = data.get('task')
        task_type = data.get('type')
        time_spent = data.get('time_spent')
        
        if not all([user, task, task_type, time_spent]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        log_time(user, task, task_type, time_spent)
        return jsonify({'message': 'Time logged successfully'}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/get_logs', methods=['GET'])
def get_logs_route():
    try:
        logs = get_time_logs()
        return jsonify({'logs': logs}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)