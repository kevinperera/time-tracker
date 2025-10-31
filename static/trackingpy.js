// Global variables
let statusChart = null;
let timeChart = null;
let developers = [];

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('Tracking dashboard loaded');
    initializeTracking();
});

async function initializeTracking() {
    await loadDevelopers();
    await loadStatusOverview();
    await loadDeveloperStats();
    setupEventListeners();
}

function setupEventListeners() {
    // Set default dates (last 30 days)
    const endDate = new Date();
    const startDate = new Date();
    startDate.setDate(startDate.getDate() - 30);
    
    document.getElementById('startDate').valueAsDate = startDate;
    document.getElementById('endDate').valueAsDate = endDate;
}

// Load developers for dropdown
async function loadDevelopers() {
    try {
        const response = await fetch('/api/developers');
        if (!response.ok) throw new Error('Failed to load developers');
        
        const data = await response.json();
        developers = data.developers || [];
        
        const select = document.getElementById('developerSelect');
        select.innerHTML = '<option value="">Select a developer</option>';
        
        developers.forEach(dev => {
            const option = document.createElement('option');
            option.value = dev.username;
            option.textContent = dev.username;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading developers:', error);
        showMessage('Error loading developers', 'error');
    }
}

// Apply filters and reload all data
async function applyFilters() {
    await loadStatusOverview();
    await loadDeveloperStats();
    
    const developerSelect = document.getElementById('developerSelect');
    if (developerSelect.value) {
        await loadDeveloperRecords();
    }
}

// Load status overview charts
async function loadStatusOverview() {
    try {
        const startDate = document.getElementById('startDate').value;
        const endDate = document.getElementById('endDate').value;
        
        let url = '/api/trackingpy/status-overview';
        const params = new URLSearchParams();
        
        if (startDate) params.append('start_date', startDate);
        if (endDate) params.append('end_date', endDate);
        
        if (params.toString()) {
            url += '?' + params.toString();
        }
        
        const response = await fetch(url);
        if (!response.ok) throw new Error('Failed to load status overview');
        
        const data = await response.json();
        
        // Update status chart
        updateStatusChart(data);
        
        // Update time chart
        updateTimeChart(data);
        
    } catch (error) {
        console.error('Error loading status overview:', error);
        showMessage('Error loading status overview', 'error');
    }
}

// Update status distribution chart
function updateStatusChart(data) {
    const ctx = document.getElementById('statusChart').getContext('2d');
    
    // Destroy existing chart if it exists
    if (statusChart) {
        statusChart.destroy();
    }
    
    const backgroundColors = [
        '#bdc3c7', // Backlog - Gray
        '#3498db', // TODO - Blue
        '#f39c12', // In Progress - Orange
        '#9b59b6', // In Review - Purple
        '#27ae60'  // Published - Green
    ];
    
    statusChart = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: data.status_labels,
            datasets: [{
                data: data.status_values,
                backgroundColor: backgroundColors,
                borderWidth: 2,
                borderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 20,
                        usePointStyle: true
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.raw || 0;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = Math.round((value / total) * 100);
                            return `${label}: ${value} records (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
}

// Update time distribution chart
function updateTimeChart(data) {
    const ctx = document.getElementById('timeChart').getContext('2d');
    
    // Destroy existing chart if it exists
    if (timeChart) {
        timeChart.destroy();
    }
    
    timeChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.time_labels,
            datasets: [{
                label: 'Hours',
                data: data.time_values,
                backgroundColor: [
                    'rgba(52, 152, 219, 0.8)', // TODO - Blue
                    'rgba(243, 156, 18, 0.8)'  // In Progress - Orange
                ],
                borderColor: [
                    'rgb(52, 152, 219)',
                    'rgb(243, 156, 18)'
                ],
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Hours'
                    }
                }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const hours = context.raw;
                            const wholeHours = Math.floor(hours);
                            const minutes = Math.round((hours - wholeHours) * 60);
                            
                            if (wholeHours === 0) {
                                return `${minutes}m`;
                            } else if (minutes === 0) {
                                return `${wholeHours}h`;
                            } else {
                                return `${wholeHours}h ${minutes}m`;
                            }
                        }
                    }
                }
            }
        }
    });
}

// Load developer statistics
async function loadDeveloperStats() {
    try {
        const startDate = document.getElementById('startDate').value;
        const endDate = document.getElementById('endDate').value;
        
        let url = '/api/trackingpy/developer-stats';
        const params = new URLSearchParams();
        
        if (startDate) params.append('start_date', startDate);
        if (endDate) params.append('end_date', endDate);
        
        if (params.toString()) {
            url += '?' + params.toString();
        }
        
        const response = await fetch(url);
        if (!response.ok) throw new Error('Failed to load developer stats');
        
        const data = await response.json();
        displayDeveloperStats(data.developers);
        
    } catch (error) {
        console.error('Error loading developer stats:', error);
        showMessage('Error loading developer statistics', 'error');
    }
}

// Display developer statistics
function displayDeveloperStats(developers) {
    const container = document.getElementById('developerStats');
    
    if (!developers || developers.length === 0) {
        container.innerHTML = '<div class="no-data">No developer data available</div>';
        return;
    }
    
    container.innerHTML = developers.map(dev => `
        <div class="developer-stat-card">
            <div class="dev-stat-header">
                <h3>${escapeHtml(dev.username)}</h3>
                <span class="total-records">${dev.total_records} records</span>
            </div>
            
            <div class="dev-time-stats">
                <div class="time-stat">
                    <span class="time-label">TODO Time:</span>
                    <span class="time-value">${formatTime(dev.total_todo_time)}</span>
                </div>
                <div class="time-stat">
                    <span class="time-label">In Progress Time:</span>
                    <span class="time-value">${formatTime(dev.total_in_progress_time)}</span>
                </div>
            </div>
            
            <div class="dev-status-stats">
                <h4>Records by Status:</h4>
                <div class="status-bars">
                    ${Object.entries(dev.records_by_status).map(([status, count]) => `
                        <div class="status-bar">
                            <span class="status-label">${status}:</span>
                            <span class="status-count">${count}</span>
                        </div>
                    `).join('')}
                </div>
            </div>
            
            <button class="view-records-btn" onclick="selectDeveloper('${escapeHtml(dev.username)}')">
                View Records
            </button>
        </div>
    `).join('');
}

// Load developer records
async function loadDeveloperRecords() {
    const developerSelect = document.getElementById('developerSelect');
    const developer = developerSelect.value;
    
    if (!developer) {
        document.getElementById('developerRecords').innerHTML = '';
        return;
    }
    
    try {
        const startDate = document.getElementById('startDate').value;
        const endDate = document.getElementById('endDate').value;
        
        let url = `/api/trackingpy/developer-records?developer=${encodeURIComponent(developer)}`;
        const params = new URLSearchParams();
        
        if (startDate) params.append('start_date', startDate);
        if (endDate) params.append('end_date', endDate);
        
        if (params.toString()) {
            url += '&' + params.toString();
        }
        
        const response = await fetch(url);
        if (!response.ok) throw new Error('Failed to load developer records');
        
        const data = await response.json();
        displayDeveloperRecords(data.records, developer);
        
    } catch (error) {
        console.error('Error loading developer records:', error);
        showMessage('Error loading developer records', 'error');
    }
}

// Display developer records
function displayDeveloperRecords(records, developer) {
    const container = document.getElementById('developerRecords');
    
    if (!records || records.length === 0) {
        container.innerHTML = `
            <div class="no-data">
                <h3>No records found for ${escapeHtml(developer)}</h3>
                <p>Try adjusting the date range</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = `
        <h3>Records for ${escapeHtml(developer)} (${records.length} records)</h3>
        <div class="records-list">
            ${records.map(record => `
                <div class="tracking-record-card">
                    <div class="tracking-record-header">
                        <div class="tracking-record-title">${escapeHtml(record.task)}</div>
                        <span class="tracking-record-status status-${record.status.toLowerCase().replace(' ', '')}">
                            ${record.status}
                        </span>
                    </div>
                    
                    <div class="tracking-record-details">
                        <div class="tracking-detail">
                            <strong>Book ID:</strong> ${escapeHtml(record.book_id)}
                        </div>
                        <div class="tracking-detail">
                            <strong>Created:</strong> ${formatDate(record.created_date)}
                        </div>
                        <div class="tracking-detail">
                            <strong>Page Count:</strong> ${record.page_count || 'N/A'}
                        </div>
                        <div class="tracking-detail">
                            <strong>OCR:</strong> ${record.ocr || 'N/A'}
                        </div>
                        ${record.eta ? `
                        <div class="tracking-detail">
                            <strong>ETA:</strong> ${formatDate(record.eta)}
                        </div>
                        ` : ''}
                    </div>
                    
                    <div class="tracking-time-stats">
                        <div class="tracking-time-stat">
                            <span class="tracking-time-label">TODO:</span>
                            <span class="tracking-time-value">${formatTime(record.time_todo)}</span>
                        </div>
                        <div class="tracking-time-stat">
                            <span class="tracking-time-label">In Progress:</span>
                            <span class="tracking-time-value">${formatTime(record.time_in_progress)}</span>
                        </div>
                    </div>
                </div>
            `).join('')}
        </div>
    `;
}

// Select developer from stats card
function selectDeveloper(developer) {
    const select = document.getElementById('developerSelect');
    select.value = developer;
    loadDeveloperRecords();
}

// Utility functions
function formatTime(hours) {
    const wholeHours = Math.floor(hours);
    const minutes = Math.round((hours - wholeHours) * 60);
    
    if (wholeHours === 0 && minutes === 0) return '0m';
    if (wholeHours === 0) return `${minutes}m`;
    if (minutes === 0) return `${wholeHours}h`;
    return `${wholeHours}h ${minutes}m`;
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