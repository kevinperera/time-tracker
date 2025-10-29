// Global variables
let currentUserRole = '';
let developers = [];

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

async function initializeApp() {
    await loadDevelopers();
    await loadRecords();
    
    // Set up event listeners
    const createRecordForm = document.getElementById('createRecordForm');
    if (createRecordForm) {
        createRecordForm.addEventListener('submit', handleCreateRecord);
    }
    
    const statusFilter = document.getElementById('statusFilter');
    if (statusFilter) {
        statusFilter.addEventListener('change', loadRecords);
    }
    
    // Set up modal
    setupModal();
}

// Setup modal functionality
function setupModal() {
    const modal = document.getElementById('editModal');
    const closeBtn = document.querySelector('.close');
    
    if (closeBtn) {
        closeBtn.addEventListener('click', () => {
            modal.style.display = 'none';
        });
    }
    
    window.addEventListener('click', (event) => {
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    });
}

// Load developers for assignee dropdown
async function loadDevelopers() {
    try {
        const response = await fetch('/records');
        const data = await response.json();
        currentUserRole = data.user_role;
        
        // Get developers list from users API (you might need to create this endpoint)
        const devSelect = document.getElementById('developer_assignee');
        if (devSelect) {
            // For now, we'll populate from existing records
            // In a real app, you'd have a separate users endpoint
            devSelect.innerHTML = '<option value="">Select Developer</option>';
            // This would be populated from a proper users endpoint
        }
    } catch (error) {
        console.error('Error loading developers:', error);
        showMessage('Error loading developers', 'error');
    }
}

// Load and display records
async function loadRecords() {
    try {
        const statusFilter = document.getElementById('statusFilter')?.value || '';
        let url = '/records';
        if (statusFilter) {
            url += `?status=${encodeURIComponent(statusFilter)}`;
        }
        
        const response = await fetch(url);
        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        displayRecords(data.records, data.user_role);
    } catch (error) {
        console.error('Error loading records:', error);
        showMessage('Error loading records: ' + error.message, 'error');
    }
}

// Display records in the container
function displayRecords(records, userRole) {
    const container = document.getElementById('recordsContainer');
    
    if (!records || records.length === 0) {
        container.innerHTML = '<div class="no-records">No records found.</div>';
        return;
    }
    
    container.innerHTML = records.map(record => createRecordCard(record, userRole)).join('');
    
    // Add event listeners to action buttons
    addRecordEventListeners();
}

// Create HTML for a record card
function createRecordCard(record, userRole) {
    const canEdit = userRole === 'admin' || userRole === 'lead';
    const isAssignedDeveloper = record.developer_assignee && record.developer_assignee === sessionStorage.getItem('username');
    const canChangeStatus = isAssignedDeveloper || canEdit;
    
    return `
        <div class="record-card ${record.eta_warning ? 'warning' : ''}" data-record-id="${record.id}">
            <div class="record-header">
                <div class="record-title">${escapeHtml(record.task)}</div>
                <div class="record-status-container">
                    <span class="record-status status-${record.status.toLowerCase().replace(' ', '')}">
                        ${record.status}
                    </span>
                    ${record.eta_warning ? '<span class="eta-warning">ETA SOON</span>' : ''}
                </div>
            </div>
            
            <div class="record-details">
                <div class="record-detail">
                    <strong>Book ID:</strong> ${escapeHtml(record.book_id)}
                </div>
                <div class="record-detail">
                    <strong>Created:</strong> ${formatDate(record.created_date)} by ${escapeHtml(record.created_by)}
                </div>
                <div class="record-detail">
                    <strong>Developer:</strong> ${record.developer_assignee ? escapeHtml(record.developer_assignee) : 'Not assigned'}
                </div>
                <div class="record-detail">
                    <strong>Page Count:</strong> ${record.page_count || 'N/A'}
                </div>
                <div class="record-detail">
                    <strong>OCR:</strong> ${record.ocr ? record.ocr.charAt(0).toUpperCase() + record.ocr.slice(1) : 'N/A'}
                </div>
                <div class="record-detail">
                    <strong>ETA:</strong> ${record.eta ? formatDate(record.eta) : 'Not set'}
                </div>
                ${record.published_date ? `
                <div class="record-detail">
                    <strong>Published:</strong> ${formatDate(record.published_date)}
                </div>
                ` : ''}
            </div>
            
            ${record.status === 'In Progress' || record.status === 'TODO' ? `
            <div class="time-tracker">
                <div class="time-info">
                    <strong>Time Spent:</strong> <span id="time-${record.id}">Loading...</span> hours
                </div>
                ${record.status === 'In Progress' ? `
                <div class="progress-bar">
                    <div class="progress-fill" id="progress-${record.id}" style="width: 0%"></div>
                </div>
                ` : ''}
            </div>
            ` : ''}
            
            <div class="record-actions">
                ${canChangeStatus ? `
                <select class="status-select" data-record-id="${record.id}">
                    <option value="Backlog" ${record.status === 'Backlog' ? 'selected' : ''}>Backlog</option>
                    <option value="TODO" ${record.status === 'TODO' ? 'selected' : ''}>TODO</option>
                    <option value="In Progress" ${record.status === 'In Progress' ? 'selected' : ''}>In Progress</option>
                    <option value="In Review" ${record.status === 'In Review' ? 'selected' : ''}>In Review</option>
                    <option value="Published" ${record.status === 'Published' ? 'selected' : ''}>Published</option>
                </select>
                ` : `
                <span>Status: ${record.status}</span>
                `}
                
                ${canEdit ? `
                <button class="edit-btn" data-record-id="${record.id}">Edit</button>
                ` : ''}
                
                ${isAssignedDeveloper && record.status === 'In Progress' ? `
                <button class="stop-timer-btn" data-record-id="${record.id}">Stop Work</button>
                ` : ''}
            </div>
        </div>
    `;
}

// Add event listeners to record action buttons
function addRecordEventListeners() {
    // Status change handlers
    document.querySelectorAll('.status-select').forEach(select => {
        select.addEventListener('change', handleStatusChange);
    });
    
    // Edit button handlers
    document.querySelectorAll('.edit-btn').forEach(btn => {
        btn.addEventListener('click', handleEditRecord);
    });
    
    // Stop timer button handlers
    document.querySelectorAll('.stop-timer-btn').forEach(btn => {
        btn.addEventListener('click', handleStopTimer);
    });
    
    // Load time data for relevant records
    loadTimeDataForRecords();
}

// Handle status change
async function handleStatusChange(event) {
    const recordId = event.target.dataset.recordId;
    const newStatus = event.target.value;
    
    try {
        const response = await fetch(`/records/${recordId}/update`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ status: newStatus })
        });
        
        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        showMessage('Status updated successfully', 'success');
        await loadRecords(); // Reload to show updated status
        
    } catch (error) {
        console.error('Error updating status:', error);
        showMessage('Error updating status: ' + error.message, 'error');
        await loadRecords(); // Reload to reset select
    }
}

// Handle create record form submission
async function handleCreateRecord(event) {
    event.preventDefault();
    
    const formData = {
        task: document.getElementById('task').value,
        book_id: document.getElementById('book_id').value,
        developer_assignee: document.getElementById('developer_assignee').value || null,
        page_count: document.getElementById('page_count').value ? parseInt(document.getElementById('page_count').value) : null,
        ocr: document.getElementById('ocr').value || null,
        eta: document.getElementById('eta').value || null
    };
    
    try {
        const response = await fetch('/records/create', {
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
        
        showMessage('Record created successfully', 'success');
        document.getElementById('createRecordForm').reset();
        await loadRecords();
        
    } catch (error) {
        console.error('Error creating record:', error);
        showMessage('Error creating record: ' + error.message, 'error');
    }
}

// Handle edit record
async function handleEditRecord(event) {
    const recordId = event.target.dataset.recordId;
    
    try {
        const response = await fetch(`/records/${recordId}`);
        const record = await response.json();
        
        if (record.error) {
            throw new Error(record.error);
        }
        
        openEditModal(record);
        
    } catch (error) {
        console.error('Error loading record for edit:', error);
        showMessage('Error loading record: ' + error.message, 'error');
    }
}

// Open edit modal with record data
function openEditModal(record) {
    const modal = document.getElementById('editModal');
    const form = document.getElementById('editRecordForm');
    
    // Populate form with record data
    document.getElementById('editRecordId').value = record.id;
    // You would populate other form fields here
    
    modal.style.display = 'block';
}

// Handle stop timer
async function handleStopTimer(event) {
    const recordId = event.target.dataset.recordId;
    
    try {
        const response = await fetch(`/records/${recordId}/update`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ status: 'In Review' })
        });
        
        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        showMessage('Work stopped and status updated to In Review', 'success');
        await loadRecords();
        
    } catch (error) {
        console.error('Error stopping timer:', error);
        showMessage('Error stopping work: ' + error.message, 'error');
    }
}

// Load time data for records
async function loadTimeDataForRecords() {
    const records = document.querySelectorAll('.record-card');
    
    for (const recordCard of records) {
        const recordId = recordCard.dataset.recordId;
        const record = await getRecordTime(recordId);
        
        if (record) {
            const timeElement = document.getElementById(`time-${recordId}`);
            const progressElement = document.getElementById(`progress-${recordId}`);
            
            if (timeElement) {
                timeElement.textContent = record.time_spent.toFixed(2);
            }
            
            // Simulate progress bar (you might want to implement actual progress logic)
            if (progressElement) {
                const progress = Math.min((record.time_spent / 8) * 100, 100); // Assuming 8 hours max
                progressElement.style.width = `${progress}%`;
            }
        }
    }
}

// Get time data for a specific record
async function getRecordTime(recordId) {
    try {
        const response = await fetch(`/records/${recordId}/time`);
        return await response.json();
    } catch (error) {
        console.error('Error fetching time data:', error);
        return null;
    }
}

// Export CSV
async function exportCSV() {
    try {
        const startDate = prompt('Enter start date (YYYY-MM-DD) or leave empty for all:');
        const endDate = prompt('Enter end date (YYYY-MM-DD) or leave empty for all:');
        
        let url = '/export/csv';
        const params = new URLSearchParams();
        
        if (startDate) params.append('start_date', startDate);
        if (endDate) params.append('end_date', endDate);
        
        if (params.toString()) {
            url += '?' + params.toString();
        }
        
        window.open(url, '_blank');
        
    } catch (error) {
        console.error('Error exporting CSV:', error);
        showMessage('Error exporting CSV: ' + error.message, 'error');
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
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (messageDiv.parentNode) {
            messageDiv.remove();
        }
    }, 5000);
}

function formatDate(dateString) {
    if (!dateString) return 'N/A';
    
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
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

// Countdown timer functionality (for ETA warnings)
function updateCountdowns() {
    document.querySelectorAll('.record-card').forEach(card => {
        const etaElement = card.querySelector('[data-eta]');
        if (etaElement) {
            const eta = new Date(etaElement.dataset.eta);
            const now = new Date();
            const diffTime = eta - now;
            const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
            
            if (diffDays <= 2) {
                card.classList.add('warning');
            }
        }
    });
}

// Initialize countdown updates
setInterval(updateCountdowns, 60000); // Update every minute