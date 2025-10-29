document.getElementById('timeForm').addEventListener('submit', function(e) {
    e.preventDefault();
    
    const formData = {
        user: document.getElementById('user').value,
        task: document.getElementById('task').value,
        type: document.getElementById('type').value,
        time_spent: parseFloat(document.getElementById('time_spent').value)
    };
    
    fetch('/log_time', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showMessage(data.error, 'error');
        } else {
            showMessage(data.message, 'success');
            document.getElementById('timeForm').reset();
            loadLogs(); // Refresh logs after successful submission
        }
    })
    .catch(error => {
        showMessage('Error logging time: ' + error, 'error');
    });
});

function loadLogs() {
    fetch('/get_logs')
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                showMessage(data.error, 'error');
            } else {
                displayLogs(data.logs);
            }
        })
        .catch(error => {
            showMessage('Error loading logs: ' + error, 'error');
        });
}

function displayLogs(logs) {
    const container = document.getElementById('logsContainer');
    
    if (logs.length === 0) {
        container.innerHTML = '<p>No time logs found.</p>';
        return;
    }
    
    container.innerHTML = logs.map(log => `
        <div class="log-entry ${log.type}">
            <strong>${log.user}</strong> (${log.type})<br>
            Task: ${log.task}<br>
            Time: ${log.time_spent} hours<br>
            <small>${new Date(log.timestamp).toLocaleString()}</small>
        </div>
    `).join('');
}

function showMessage(message, type) {
    // Remove existing messages
    const existingMessage = document.querySelector('.message');
    if (existingMessage) {
        existingMessage.remove();
    }
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;
    messageDiv.textContent = message;
    
    document.querySelector('.form-section').appendChild(messageDiv);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (messageDiv.parentNode) {
            messageDiv.remove();
        }
    }, 5000);
}

// Load logs when page loads
document.addEventListener('DOMContentLoaded', loadLogs);