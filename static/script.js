// Global variables
let currentUserRole = '';
let currentUsername = '';
let developers = [];
let currentRecordId = null;
let currentPage = 1;
const recordsPerPage = 20;
let totalRecords = 0;
let totalPages = 1;
let currentSearch = '';
let currentStatusFilter = '';
let isLoading = false;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, initializing app...');
    
    // Get current username from the page
    const userElement = document.querySelector('.user-name');
    if (userElement) {
        currentUsername = userElement.textContent.trim();
    }
    
    // Get current role from the page
    const roleElement = document.querySelector('.user-role');
    if (roleElement) {
        currentUserRole = roleElement.textContent.trim().toLowerCase();
    }
    
    console.log('Current user:', currentUsername, 'Role:', currentUserRole);
    
    initializeApp();
});

async function initializeApp() {
    console.log('Initializing app...');
    await loadDevelopers();
    await loadRecords();
    
    // Set up event listeners
    setupEventListeners();
    
    // Set up modals
    setupModals();
}

// Setup all event listeners
function setupEventListeners() {
    console.log('Setting up event listeners...');
    
    const createRecordForm = document.getElementById('createRecordForm');
    if (createRecordForm) {
        console.log('Create record form found, adding listener');
        createRecordForm.addEventListener('submit', handleCreateRecord);
    } else {
        console.log('Create record form NOT found');
    }
    
    const statusFilter = document.getElementById('statusFilter');
    if (statusFilter) {
        statusFilter.addEventListener('change', handleFilterChange);
    }
    
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('input', debounce(handleSearch, 500));
    }
    
    const editRecordForm = document.getElementById('editRecordForm');
    if (editRecordForm) {
        editRecordForm.addEventListener('submit', handleEditRecordSubmit);
    }
    
    const deleteRecordBtn = document.getElementById('deleteRecordBtn');
    if (deleteRecordBtn) {
        deleteRecordBtn.addEventListener('click', handleDeleteRecord);
    }
}

// Setup modal functionality
function setupModals() {
    console.log('Setting up modals...');
    
    // Create Record Modal
    const createModal = document.getElementById('createRecordModal');
    if (createModal) {
        const createCloseBtn = createModal.querySelector('.close');
        if (createCloseBtn) {
            createCloseBtn.addEventListener('click', closeCreateRecordModal);
        }
    }
    
    // Edit Record Modal
    const editModal = document.getElementById('editRecordModal');
    if (editModal) {
        const editCloseBtn = editModal.querySelector('.close');
        if (editCloseBtn) {
            editCloseBtn.addEventListener('click', closeEditRecordModal);
        }
    }
    
    // Close modals when clicking outside
    window.addEventListener('click', (event) => {
        const createModal = document.getElementById('createRecordModal');
        const editModal = document.getElementById('editRecordModal');
        
        if (event.target === createModal) {
            closeCreateRecordModal();
        }
        if (event.target === editModal) {
            closeEditRecordModal();
        }
    });
}

// Open Create Record Modal
function openCreateRecordModal() {
    console.log('Opening create record modal...');
    const modal = document.getElementById('createRecordModal');
    if (modal) {
        modal.style.display = 'block';
        console.log('Modal displayed');
        
        // Reset form
        const form = document.getElementById('createRecordForm');
        if (form) {
            form.reset();
        }
        
        // Ensure developers are loaded
        loadDevelopers();
    } else {
        console.log('Create record modal not found');
    }
}

// Close Create Record Modal
function closeCreateRecordModal() {
    const modal = document.getElementById('createRecordModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

// Debounce function for search
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Load developers for assignee dropdown
async function loadDevelopers() {
    try {
        console.log('Loading developers...');
        const response = await fetch('/api/developers');
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        developers = data.developers;
        console.log('Developers loaded:', developers);
        
        // Populate developer dropdowns
        const devSelects = [
            document.getElementById('createDeveloperAssignee'),
            document.getElementById('editDeveloperAssignee')
        ];
        
        devSelects.forEach(select => {
            if (select) {
                select.innerHTML = '<option value="">Select Developer</option>';
                developers.forEach(dev => {
                    const option = document.createElement('option');
                    option.value = dev.username;
                    option.textContent = dev.username;
                    select.appendChild(option);
                });
            }
        });
        
    } catch (error) {
        console.error('Error loading developers:', error);
        showMessage('Error loading developers: ' + error.message, 'error');
    }
}

// Load and display records
async function loadRecords(page = 1) {
    if (isLoading) {
        console.log('Already loading records, skipping...');
        return;
    }
    
    try {
        isLoading = true;
        currentPage = page;
        const statusFilter = document.getElementById('statusFilter')?.value || '';
        const searchQuery = document.getElementById('searchInput')?.value || '';
        
        currentStatusFilter = statusFilter;
        currentSearch = searchQuery;
        
        let url = `/records?page=${page}&limit=${recordsPerPage}`;
        if (statusFilter) {
            url += `&status=${encodeURIComponent(statusFilter)}`;
        }
        if (searchQuery) {
            url += `&search=${encodeURIComponent(searchQuery)}`;
        }
        
        console.log('Loading records from:', url);
        
        const response = await fetch(url);
        
        if (!response.ok) {
            if (response.status === 401) {
                window.location.href = '/login';
                return;
            }
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        console.log('Records loaded successfully:', data.records?.length || 0, 'records');
        
        if (data.records && data.records.length > 0) {
            displayRecords(data.records, data.user_role);
        } else {
            displayRecords([], data.user_role);
        }
        
        displayPagination();
        
    } catch (error) {
        console.error('Error loading records:', error);
        const container = document.getElementById('recordsContainer');
        if (container) {
            container.innerHTML = `
                <div class="error-message">
                    Error loading records: ${error.message}
                    <br><br>
                    <button onclick="location.reload()">Reload Page</button>
                </div>
            `;
        }
    } finally {
        isLoading = false;
    }
}

// Handle search input
function handleSearch() {
    currentPage = 1;
    loadRecords(1);
}

// Handle filter change
function handleFilterChange() {
    currentPage = 1;
    loadRecords(1);
}

// Display pagination
function displayPagination() {
    const container = document.getElementById('paginationContainer');
    if (!container) return;
    
    if (totalPages <= 1) {
        container.innerHTML = '';
        return;
    }
    
    let paginationHTML = '';
    
    // Previous button
    paginationHTML += `<button onclick="loadRecords(${currentPage - 1})" ${currentPage === 1 ? 'disabled' : ''}>Previous</button>`;
    
    // Page numbers
    const startPage = Math.max(1, currentPage - 2);
    const endPage = Math.min(totalPages, currentPage + 2);
    
    for (let i = startPage; i <= endPage; i++) {
        if (i === currentPage) {
            paginationHTML += `<button class="filter-active" disabled>${i}</button>`;
        } else {
            paginationHTML += `<button onclick="loadRecords(${i})">${i}</button>`;
        }
    }
    
    // Next button
    paginationHTML += `<button onclick="loadRecords(${currentPage + 1})" ${currentPage === totalPages ? 'disabled' : ''}>Next</button>`;
    
    // Page info
    paginationHTML += `<div class="pagination-info">Page ${currentPage} of ${totalPages} (${totalRecords} total records)</div>`;
    
    container.innerHTML = paginationHTML;
}

// Display records in the container
function displayRecords(records, userRole) {
    const container = document.getElementById('recordsContainer');
    if (!container) return;
    
    if (!records || records.length === 0) {
        container.innerHTML = `
            <div class="no-records">
                <h3>No records found</h3>
                <p>Try adjusting your search or filter criteria</p>
            </div>
        `;
        return;
    }
    
    console.log('Displaying', records.length, 'records for role:', userRole);
    
    container.innerHTML = records.map(record => createRecordCard(record, userRole)).join('');
    
    // Add event listeners to action buttons
    addRecordEventListeners();
}

// Create HTML for a record card
function createRecordCard(record, userRole) {
    const canEdit = userRole === 'admin' || userRole === 'lead';
    const isAssignedDeveloper = record.developer_assignee && record.developer_assignee === currentUsername;
    const canChangeStatus = (isAssignedDeveloper && userRole === 'developer') || canEdit;
    
    // Calculate progress percentages based on accumulated time
    const todoProgress = Math.min((record.time_todo / 24) * 100, 100);
    const inProgressProgress = Math.min((record.time_in_progress / 48) * 100, 100);
    
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
            
            <!-- Enhanced Time Tracking -->
            <div class="time-tracking-details">
                ${record.time_todo > 0 || record.status === 'TODO' ? `
                <div class="time-metric todo">
                    <div class="time-metric-header">
                        <div class="time-metric-label">
                            <span class="status-indicator"></span>
                            Time in TODO
                        </div>
                        <button class="refresh-btn" onclick="refreshRecordTime(${record.id})">
                            🔄 Refresh
                        </button>
                    </div>
                    <div class="time-metric-value">${record.time_todo.toFixed(2)} hours</div>
                    ${record.status === 'TODO' ? `
                    <div class="progress-container">
                        <div class="progress-header">
                            <div class="progress-label">Progress</div>
                            <div class="progress-percentage">${todoProgress.toFixed(1)}%</div>
                        </div>
                        <div class="progress-bar">
                            <div class="progress-fill todo" style="width: ${todoProgress}%"></div>
                        </div>
                    </div>
                    ` : ''}
                    <div class="time-details">Accumulated time spent in TODO status</div>
                </div>
                ` : ''}
                
                ${record.time_in_progress > 0 || record.status === 'In Progress' ? `
                <div class="time-metric in-progress">
                    <div class="time-metric-header">
                        <div class="time-metric-label">
                            <span class="status-indicator"></span>
                            Time in In Progress
                        </div>
                        <button class="refresh-btn" onclick="refreshRecordTime(${record.id})">
                            🔄 Refresh
                        </button>
                    </div>
                    <div class="time-metric-value">${record.time_in_progress.toFixed(2)} hours</div>
                    ${record.status === 'In Progress' ? `
                    <div class="progress-container">
                        <div class="progress-header">
                            <div class="progress-label">Progress</div>
                            <div class="progress-percentage">${inProgressProgress.toFixed(1)}%</div>
                        </div>
                        <div class="progress-bar">
                            <div class="progress-fill in-progress" style="width: ${inProgressProgress}%"></div>
                        </div>
                    </div>
                    ` : ''}
                    <div class="time-details">Accumulated time spent in In Progress status</div>
                </div>
                ` : ''}
            </div>
            
            <div class="record-actions">
                ${canChangeStatus ? `
                <select class="status-select" data-record-id="${record.id}">
                    ${userRole === 'developer' ? 
                        `
                        <option value="Backlog" disabled ${record.status === 'Backlog' ? 'selected' : ''}>Backlog</option>
                        <option value="TODO" disabled ${record.status === 'TODO' ? 'selected' : ''}>TODO</option>
                        <option value="In Progress" ${record.status === 'In Progress' ? 'selected' : ''}>In Progress</option>
                        <option value="In Review" ${record.status === 'In Review' ? 'selected' : ''}>In Review</option>
                        <option value="Published" ${record.status === 'Published' ? 'selected' : ''}>Published</option>
                        ` 
                        : 
                        `
                        <option value="Backlog" ${record.status === 'Backlog' ? 'selected' : ''}>Backlog</option>
                        <option value="TODO" ${record.status === 'TODO' ? 'selected' : ''}>TODO</option>
                        <option value="In Progress" ${record.status === 'In Progress' ? 'selected' : ''}>In Progress</option>
                        <option value="In Review" ${record.status === 'In Review' ? 'selected' : ''}>In Review</option>
                        <option value="Published" ${record.status === 'Published' ? 'selected' : ''}>Published</option>
                        `
                    }
                </select>
                ` : `
                <span class="status-text">Status: ${record.status}</span>
                `}
                
                ${canEdit ? `
                <button class="edit-btn" data-record-id="${record.id}">Edit</button>
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
}

// Handle status change
async function handleStatusChange(event) {
    const recordId = event.target.dataset.recordId;
    const newStatus = event.target.value;
    
    try {
        const response = await fetch(`/records/${recordId}/status`, {
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
        await loadRecords(currentPage);
        
    } catch (error) {
        console.error('Error updating status:', error);
        showMessage('Error updating status: ' + error.message, 'error');
        await loadRecords(currentPage);
    }
}

// Refresh time for a specific record
async function refreshRecordTime(recordId) {
    try {
        await loadRecords(currentPage);
        showMessage('Time refreshed successfully', 'success');
    } catch (error) {
        console.error('Error refreshing time:', error);
        showMessage('Error refreshing time', 'error');
    }
}

// Handle create record form submission
async function handleCreateRecord(event) {
    event.preventDefault();
    console.log('Create record form submitted');
    
    const formData = {
        task: document.getElementById('createTask').value,
        book_id: document.getElementById('createBookId').value,
        developer_assignee: document.getElementById('createDeveloperAssignee').value || null,
        page_count: document.getElementById('createPageCount').value ? parseInt(document.getElementById('createPageCount').value) : null,
        ocr: document.getElementById('createOcr').value || null,
        eta: document.getElementById('createEta').value || null
    };
    
    // Validate required fields
    if (!formData.task || !formData.book_id) {
        showMessage('Task and Book ID are required fields', 'error');
        return;
    }
    
    try {
        console.log('Sending create record request:', formData);
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
        closeCreateRecordModal();
        await loadRecords(1);
        
    } catch (error) {
        console.error('Error creating record:', error);
        showMessage('Error creating record: ' + error.message, 'error');
    }
}

// Handle edit record button click
async function handleEditRecord(event) {
    const recordId = event.target.dataset.recordId;
    
    try {
        const response = await fetch(`/records/${recordId}`);
        const record = await response.json();
        
        if (record.error) {
            throw new Error(record.error);
        }
        
        openEditRecordModal(record);
        
    } catch (error) {
        console.error('Error loading record for edit:', error);
        showMessage('Error loading record: ' + error.message, 'error');
    }
}

// Open edit record modal with record data
function openEditRecordModal(record) {
    currentRecordId = record.id;
    
    // Populate form with record data
    document.getElementById('editRecordId').value = record.id;
    document.getElementById('editTask').value = record.task;
    document.getElementById('editBookId').value = record.book_id;
    document.getElementById('editDeveloperAssignee').value = record.developer_assignee || '';
    document.getElementById('editPageCount').value = record.page_count || '';
    document.getElementById('editOcr').value = record.ocr || '';
    document.getElementById('editEta').value = record.eta || '';
    document.getElementById('editStatus').value = record.status;
    
    // Show the modal
    document.getElementById('editRecordModal').style.display = 'block';
}

// Close edit record modal
function closeEditRecordModal() {
    const modal = document.getElementById('editRecordModal');
    if (modal) {
        modal.style.display = 'none';
    }
    currentRecordId = null;
}

// Handle edit record form submission
async function handleEditRecordSubmit(event) {
    event.preventDefault();
    
    if (!currentRecordId) {
        showMessage('No record selected for editing', 'error');
        return;
    }
    
    const formData = {
        task: document.getElementById('editTask').value,
        book_id: document.getElementById('editBookId').value,
        developer_assignee: document.getElementById('editDeveloperAssignee').value || null,
        page_count: document.getElementById('editPageCount').value ? parseInt(document.getElementById('editPageCount').value) : null,
        ocr: document.getElementById('editOcr').value || null,
        eta: document.getElementById('editEta').value || null,
        status: document.getElementById('editStatus').value
    };
    
    try {
        const response = await fetch(`/records/${currentRecordId}/update`, {
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
        
        showMessage('Record updated successfully', 'success');
        closeEditRecordModal();
        await loadRecords(currentPage);
        
    } catch (error) {
        console.error('Error updating record:', error);
        showMessage('Error updating record: ' + error.message, 'error');
    }
}

// Handle delete record
async function handleDeleteRecord() {
    if (!currentRecordId) {
        showMessage('No record selected for deletion', 'error');
        return;
    }
    
    if (!confirm('Are you sure you want to delete this record? This action cannot be undone.')) {
        return;
    }
    
    try {
        const response = await fetch(`/records/${currentRecordId}/delete`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        showMessage('Record deleted successfully', 'success');
        closeEditRecordModal();
        await loadRecords(currentPage);
        
    } catch (error) {
        console.error('Error deleting record:', error);
        showMessage('Error deleting record: ' + error.message, 'error');
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
    
    const container = document.querySelector('.container');
    if (container) {
        container.insertBefore(messageDiv, container.firstChild);
    }
    
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

// Auto-refresh records every 30 seconds to update time tracking
setInterval(() => {
    if (document.visibilityState === 'visible') {
        loadRecords(currentPage);
    }
}, 30000);