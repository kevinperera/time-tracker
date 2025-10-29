// Admin Users Management JavaScript
document.addEventListener('DOMContentLoaded', function() {
    loadUsers();
    
    const createUserForm = document.getElementById('createUserForm');
    if (createUserForm) {
        createUserForm.addEventListener('submit', handleCreateUser);
    }
});

// Load all users
async function loadUsers() {
    try {
        const response = await fetch('/admin/users');
        // This endpoint would need to be created to return users list
        const users = await response.json();
        displayUsers(users);
    } catch (error) {
        console.error('Error loading users:', error);
        showMessage('Error loading users', 'error');
    }
}

// Display users in the container
function displayUsers(users) {
    const container = document.getElementById('usersContainer');
    
    if (!users || users.length === 0) {
        container.innerHTML = '<div class="no-users">No users found.</div>';
        return;
    }
    
    container.innerHTML = users.map(user => `
        <div class="user-card">
            <div class="user-info">
                <strong>Username:</strong> ${escapeHtml(user.username)}<br>
                <strong>Role:</strong> ${escapeHtml(user.role)}<br>
                <strong>Created:</strong> ${formatDate(user.created_at)}
            </div>
            <div class="user-actions">
                <button onclick="changePassword('${escapeHtml(user.username)}')" 
                        class="change-password-btn"
                        ${user.role === 'admin' ? 'disabled' : ''}>
                    Change Password
                </button>
            </div>
        </div>
    `).join('');
}

// Handle create user form submission
async function handleCreateUser(event) {
    event.preventDefault();
    
    const formData = {
        username: document.getElementById('new_username').value,
        password: document.getElementById('new_password').value,
        role: document.getElementById('new_role').value
    };
    
    try {
        const response = await fetch('/admin/create_user', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
        });
        
        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        showMessage('User created successfully', 'success');
        document.getElementById('createUserForm').reset();
        await loadUsers();
        
    } catch (error) {
        console.error('Error creating user:', error);
        showMessage('Error creating user: ' + error.message, 'error');
    }
}

// Change user password
async function changePassword(username) {
    const newPassword = prompt(`Enter new password for ${username}:`);
    
    if (!newPassword) {
        return;
    }
    
    if (newPassword.length < 3) {
        alert('Password must be at least 3 characters long');
        return;
    }
    
    try {
        const response = await fetch('/admin/change_password', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                username: username,
                new_password: newPassword
            })
        });
        
        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        showMessage(`Password changed successfully for ${username}`, 'success');
        
    } catch (error) {
        console.error('Error changing password:', error);
        showMessage('Error changing password: ' + error.message, 'error');
    }
}

// Utility functions (same as main script.js)
function showMessage(message, type) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;
    messageDiv.textContent = message;
    
    document.querySelector('.container').insertBefore(messageDiv, document.querySelector('.container').firstChild);
    
    setTimeout(() => {
        if (messageDiv.parentNode) {
            messageDiv.remove();
        }
    }, 5000);
}

function formatDate(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString();
}

function escapeHtml(unsafe) {
    if (!unsafe) return '';
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}