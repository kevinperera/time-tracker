// Workload Tracking JavaScript
let currentDate = new Date().toISOString().split('T')[0];
let currentDeveloper = '';
let developers = [];

document.addEventListener('DOMContentLoaded', function() {
    console.log('Workload dashboard loaded');
    initializeWorkloadDashboard();
});

async function initializeWorkloadDashboard() {
    // Set default date to today
    document.getElementById('workloadDate').value = currentDate;
    
    await loadDevelopers();
    await loadWorkloadData();
}

async function loadDevelopers() {
    try {
        const response = await fetch('/api/developers/workload');
        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        developers = data.developers;
        const developerFilter = document.getElementById('developerFilter');
        
        developerFilter.innerHTML = '<option value="">All Developers</option>';
        developers.forEach(dev => {
            const option = document.createElement('option');
            option.value = dev.username;
            option.textContent = dev.username;
            developerFilter.appendChild(option);
        });
        
    } catch (error) {
        console.error('Error loading developers:', error);
        showErrorToast(error, 'Error loading developers');
    }
}

async function loadWorkloadData() {
    try {
        const date = document.getElementById('workloadDate').value || currentDate;
        const developer = document.getElementById('developerFilter').value || '';
        
        currentDate = date;
        currentDeveloper = developer;
        
        let url = `/api/workload?date=${date}`;
        if (developer) {
            url += `&developer=${encodeURIComponent(developer)}`;
        }
        
        const response = await fetch(url);
        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        displayWorkloadSummary(data.workload);
        displayActivities(data.activities);
        
    } catch (error) {
        console.error('Error loading workload data:', error);
        showErrorToast(error, 'Error loading workload data');
        
        document.getElementById('workloadSummary').innerHTML = `
            <div class="error-message">
                Error loading workload data: ${error.message}
            </div>
        `;
        
        document.getElementById('activitiesList').innerHTML = `
            <div class="error-message">
                Error loading activities: ${error.message}
            </div>
        `;
    }
}

function displayWorkloadSummary(workloadData) {
    const container = document.getElementById('workloadSummary');
    
    if (!workloadData || Object.keys(workloadData).length === 0) {
        container.innerHTML = `
            <div class="no-records">
                <h3>No workload data found</h3>
                <p>No developer activities found for the selected date and filters</p>
            </div>
        `;
        return;
    }
    
    let summaryHTML = '<div class="workload-grid">';
    
    Object.entries(workloadData).forEach(([developer, data]) => {
        const totalHours = data.total_time;
        const formattedTotalTime = formatTimeDisplay(totalHours);
        
        summaryHTML += `
            <div class="developer-workload-card">
                <div class="workload-header">
                    <h3 class="developer-name">${escapeHtml(developer)}</h3>
                    <div class="workload-total">
                        <span class="total-hours">${formattedTotalTime}</span>
                        <span class="total-records">${data.record_count} records</span>
                    </div>
                </div>
                
                <div class="time-breakdown">
                    <div class="time-category">
                        <div class="category-label">
                            <span class="status-indicator todo"></span>
                            TODO
                        </div>
                        <div class="category-time">${formatTimeDisplay(data.todo_time)}</div>
                        <div class="category-records">${data.status_breakdown['TODO'] ? data.status_breakdown['TODO'].record_count : 0} records</div>
                    </div>
                    
                    <div class="time-category">
                        <div class="category-label">
                            <span class="status-indicator in-progress"></span>
                            In Progress
                        </div>
                        <div class="category-time">${formatTimeDisplay(data.in_progress_time)}</div>
                        <div class="category-records">${data.status_breakdown['In Progress'] ? data.status_breakdown['In Progress'].record_count : 0} records</div>
                    </div>
                    
                    <div class="time-category">
                        <div class="category-label">
                            <span class="status-indicator in-review"></span>
                            In Review
                        </div>
                        <div class="category-time">${formatTimeDisplay(data.in_review_time)}</div>
                        <div class="category-records">${data.status_breakdown['In Review'] ? data.status_breakdown['In Review'].record_count : 0} records</div>
                    </div>
                    
                    <div class="time-category">
                        <div class="category-label">
                            <span class="status-indicator review-failed"></span>
                            Review Failed
                        </div>
                        <div class="category-time">${formatTimeDisplay(data.review_failed_time)}</div>
                        <div class="category-records">${data.status_breakdown['Review failed - In Progress'] ? data.status_breakdown['Review failed - In Progress'].record_count : 0} records</div>
                    </div>
                </div>
                
                <div class="workload-progress">
                    <div class="progress-bar">
                        <div class="progress-segment todo" style="width: ${(data.todo_time / totalHours) * 100 || 0}%"></div>
                        <div class="progress-segment in-progress" style="width: ${(data.in_progress_time / totalHours) * 100 || 0}%"></div>
                        <div class="progress-segment in-review" style="width: ${(data.in_review_time / totalHours) * 100 || 0}%"></div>
                        <div class="progress-segment review-failed" style="width: ${(data.review_failed_time / totalHours) * 100 || 0}%"></div>
                    </div>
                </div>
            </div>
        `;
    });
    
    summaryHTML += '</div>';
    container.innerHTML = summaryHTML;
}

function displayActivities(activities) {
    const container = document.getElementById('activitiesList');
    
    if (!activities || activities.length === 0) {
        container.innerHTML = `
            <div class="no-records">
                <h3>No activities found</h3>
                <p>No developer activities found for the selected date and filters</p>
            </div>
        `;
        return;
    }
    
    let activitiesHTML = `
        <div class="activities-header">
            <div class="activities-count">Showing ${activities.length} activities</div>
        </div>
        <div class="activities-table-container">
            <table class="activities-table">
                <thead>
                    <tr>
                        <th>Developer</th>
                        <th>Task</th>
                        <th>Book ID</th>
                        <th>Status</th>
                        <th>TODO Time</th>
                        <th>In Progress</th>
                        <th>In Review</th>
                        <th>Review Failed</th>
                        <th>Total Time</th>
                        <th>Created</th>
                    </tr>
                </thead>
                <tbody>
    `;
    
    activities.forEach(activity => {
        activitiesHTML += `
            <tr class="activity-row">
                <td class="developer-cell">
                    <span class="developer-badge">${escapeHtml(activity.developer_assignee)}</span>
                </td>
                <td class="task-cell">${escapeHtml(activity.task)}</td>
                <td class="book-id-cell">${escapeHtml(activity.book_id)}</td>
                <td class="status-cell">
                    <span class="record-status status-${activity.status.toLowerCase().replace(' ', '').replace('-', '')}">
                        ${activity.status}
                    </span>
                </td>
                <td class="time-cell">${formatTimeDisplay(activity.todo_time)}</td>
                <td class="time-cell">${formatTimeDisplay(activity.in_progress_time)}</td>
                <td class="time-cell">${formatTimeDisplay(activity.in_review_time)}</td>
                <td class="time-cell">${formatTimeDisplay(activity.review_failed_time)}</td>
                <td class="time-cell total-time">${formatTimeDisplay(activity.total_time)}</td>
                <td class="date-cell">${formatDate(activity.created_date)}</td>
            </tr>
        `;
    });
    
    activitiesHTML += `
                </tbody>
            </table>
        </div>
    `;
    
    container.innerHTML = activitiesHTML;
}

function formatTimeDisplay(hours) {
    if (hours === 0) return '0h';
    
    const totalMinutes = hours * 60;
    const displayHours = Math.floor(totalMinutes / 60);
    const displayMinutes = Math.round(totalMinutes % 60);
    
    if (displayHours === 0) {
        return `${displayMinutes}m`;
    } else if (displayMinutes === 0) {
        return `${displayHours}h`;
    } else {
        return `${displayHours}h ${displayMinutes}m`;
    }
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

async function exportWorkloadReport() {
    try {
        let url = `/api/workload?date=${currentDate}`;
        if (currentDeveloper) {
            url += `&developer=${encodeURIComponent(currentDeveloper)}`;
        }
        
        const response = await fetch(url);
        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        // Create CSV content
        let csvContent = 'Workload Report - ' + currentDate + '\n\n';
        
        // Summary section
        csvContent += 'Developer Workload Summary\n';
        csvContent += 'Developer,Total Time,Total Records,TODO Time,In Progress Time,In Review Time,Review Failed Time\n';
        
        Object.entries(data.workload).forEach(([developer, workload]) => {
            csvContent += `"${developer}","${formatTimeDisplay(workload.total_time)}","${workload.record_count}","${formatTimeDisplay(workload.todo_time)}","${formatTimeDisplay(workload.in_progress_time)}","${formatTimeDisplay(workload.in_review_time)}","${formatTimeDisplay(workload.review_failed_time)}"\n`;
        });
        
        csvContent += '\n\nDetailed Activities\n';
        csvContent += 'Developer,Task,Book ID,Status,TODO Time,In Progress Time,In Review Time,Review Failed Time,Total Time,Created Date\n';
        
        data.activities.forEach(activity => {
            csvContent += `"${activity.developer_assignee}","${activity.task}","${activity.book_id}","${activity.status}","${formatTimeDisplay(activity.todo_time)}","${formatTimeDisplay(activity.in_progress_time)}","${formatTimeDisplay(activity.in_review_time)}","${formatTimeDisplay(activity.review_failed_time)}","${formatTimeDisplay(activity.total_time)}","${activity.created_date}"\n`;
        });
        
        // Create and download file
        const blob = new Blob([csvContent], { type: 'text/csv' });
        const urlBlob = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = urlBlob;
        a.download = `workload-report-${currentDate}.csv`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(urlBlob);
        
        showSuccessToast('Workload report exported successfully');
        
    } catch (error) {
        console.error('Error exporting workload report:', error);
        showErrorToast(error, 'Error exporting report');
    }
}

// Use existing toast functions from script.js
function showErrorToast(error, context = '') {
    const message = context ? `${context}: ${error.message || error}` : (error.message || error);
    console.error('Error:', error);
    // This would use your existing toast system
    alert(`Error: ${message}`); // Fallback to alert for now
}

function showSuccessToast(message) {
    console.log('Success:', message);
    // This would use your existing toast system
    alert(`Success: ${message}`); // Fallback to alert for now
}