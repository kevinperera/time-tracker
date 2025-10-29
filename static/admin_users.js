// Admin Users Management JavaScript
document.addEventListener('DOMContentLoaded', function() {
    const createUserForm = document.getElementById('createUserForm');
    const editUserForm = document.getElementById('editUserForm');
    
    if (createUserForm) {
        createUserForm.addEventListener('submit', handleCreateUser);
    }
    
    if (editUserForm) {
        editUserForm.addEventListener('submit', handleEditUser);
    }
});

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
        // Reload the page to show the new user
        setTimeout(() => {
            window.location.reload();
        }, 1000);
        
    } catch (error) {
        console.error('Error creating user:', error);
        showMessage('Error creating user: ' + error.message, 'error');
    }
}

// Handle edit user form submission
async function handleEditUser(event) {
    event.preventDefault();
    
    const formData = {
        old_username: document.getElementById('editOldUsername').value,
        new_username: document.getElementById('editUsername').value,
        new_role: document.getElementById('editRole').value
    };
    
    try {
        const response = await fetch('/admin/update_user', {
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
        
        showMessage('User updated successfully', 'success');
        closeEditModal();
        // Reload the page to show updated users
        setTimeout(() => {
            window.location.reload();
        }, 1000);
        
    } catch (error) {
        console.error('Error updating user:', error);
        showMessage('Error updating user: ' + error.message, 'error');
    }
}

// Edit user
function editUser(username, role) {
    document.getElementById('editOldUsername').value = username;
    document.getElementById('editUsername').value = username;
    document.getElementById('editRole').value = role;
    
    document.getElementById('editUserModal').style.display = 'block';
}

// Close edit modal
function closeEditModal() {
    document.getElementById('editUserModal').style.display = 'none';
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

// Delete user
async function deleteUser(username) {
    if (!confirm(`Are you sure you want to delete user "${username}"? This action cannot be undone.`)) {
        return;
    }
    
    try {
        const response = await fetch('/admin/delete_user', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                username: username
            })
        });
        
        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        showMessage(`User ${username} deleted successfully`, 'success');
        // Reload the page to reflect changes
        setTimeout(() => {
            window.location.reload();
        }, 1000);
        
    } catch (error) {
        console.error('Error deleting user:', error);
        showMessage('Error deleting user: ' + error.message, 'error');
    }
}

// Utility functions
function showMessage(message, type) {
    // Remove existing messages
    const existingMessage = document.querySelector('.message');
    if (existingMessage) {
        existingMessage.remove();
    }
    
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