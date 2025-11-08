// Dashboard JavaScript

// Load tasks on page load
document.addEventListener('DOMContentLoaded', async () => {
    await loadStats();
    await loadTasks();
    setupNewTaskModal();
    setupStatsLink();

    // Refresh every 5 seconds
    setInterval(loadStats, 5000);
    setInterval(loadTasks, 5000);
});

async function loadStats() {
    try {
        const response = await fetch('/api/stats');

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        // Handle error response from backend
        if (data.error) {
            console.warn('Stats API Error:', data.error);
            // Keep showing zeros if backend is unavailable
            return;
        }

        if (data.tasks) {
            document.getElementById('total-tasks').textContent = data.tasks.total || 0;
            document.getElementById('processing-tasks').textContent = data.tasks.processing || 0;
            document.getElementById('completed-tasks').textContent = data.tasks.completed || 0;
            document.getElementById('failed-tasks').textContent = data.tasks.failed || 0;
        }

        if (data.costs) {
            document.getElementById('total-cost').textContent = formatCost(data.costs.total_usd || 0);
            document.getElementById('avg-cost').textContent = formatCost(data.costs.average_per_task_usd || 0);
        }
    } catch (error) {
        console.warn('Error loading stats:', error);
        // Silently fail - stats will show default values
    }
}

function formatCost(amount) {
    if (amount === 0) return '$0.00';
    if (amount < 0.01) return `$${amount.toFixed(4)}`;
    return `$${amount.toFixed(2)}`;
}

async function loadTasks() {
    try {
        const response = await fetch('/api/tasks');

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        const container = document.getElementById('tasks-container');
        const loadingState = document.getElementById('loading-state');

        // Hide loading state
        if (loadingState) {
            loadingState.style.display = 'none';
        }

        // Handle error response from backend
        if (data.error) {
            console.error('API Error:', data.error);
            container.innerHTML = `
                <div class="empty-state-dashboard">
                    <svg width="120" height="120" viewBox="0 0 120 120" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <circle cx="60" cy="60" r="50" stroke="#E5E7EB" stroke-width="4"/>
                        <path d="M60 35V60M60 75H60.01" stroke="#E5E7EB" stroke-width="4" stroke-linecap="round"/>
                    </svg>
                    <h3>Connection Error</h3>
                    <p>Unable to connect to backend service. Please ensure the Mind service is running.</p>
                </div>
            `;
            return;
        }

        // Handle empty array or no tasks
        const tasks = Array.isArray(data) ? data : [];

        if (tasks.length === 0) {
            container.innerHTML = `
                <div class="empty-state-dashboard">
                    <svg width="120" height="120" viewBox="0 0 120 120" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <rect x="30" y="30" width="60" height="60" rx="8" stroke="#E5E7EB" stroke-width="4"/>
                        <path d="M45 50H75M45 60H75M45 70H60" stroke="#E5E7EB" stroke-width="4" stroke-linecap="round"/>
                    </svg>
                    <h3>No tasks yet</h3>
                    <p>Create your first task to get started with intelligent agents!</p>
                    <button class="btn btn-primary add-memory-btn" onclick="document.getElementById('new-task-btn').click()">
                        <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M8 1V15M1 8H15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                        </svg>
                        Create First Task
                    </button>
                </div>
            `;
            return;
        }

        // Render modern task cards
        container.innerHTML = tasks.map((task, index) => createTaskCard(task, index)).join('');
    } catch (error) {
        console.error('Error loading tasks:', error);
        const container = document.getElementById('tasks-container');
        const loadingState = document.getElementById('loading-state');

        if (loadingState) {
            loadingState.style.display = 'none';
        }

        container.innerHTML = `
            <div class="empty-state-dashboard">
                <svg width="120" height="120" viewBox="0 0 120 120" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <circle cx="60" cy="60" r="50" stroke="#E5E7EB" stroke-width="4"/>
                    <path d="M60 35V60M60 75H60.01" stroke="#E5E7EB" stroke-width="4" stroke-linecap="round"/>
                </svg>
                <h3>Connection Error</h3>
                <p>Unable to connect to backend service. Please ensure the Mind service is running.</p>
            </div>
        `;
    }
}

function createTaskCard(task, index) {
    const statusClass = task.status || 'processing';
    const statusText = task.status || 'Processing';
    const taskTitle = truncate(task.context?.title || task.task || 'Untitled Task', 60);
    const taskDescription = truncate(task.task || '', 120);
    const createdDate = formatDate(task.created_at);
    const taskId = task.task_id.substring(0, 8);

    return `
        <div class="task-card-modern" style="animation-delay: ${index * 0.05}s;" onclick="window.location.href='/task/${task.task_id}'">
            <div class="task-card-modern-header">
                <div class="task-card-modern-title">${escapeHtml(taskTitle)}</div>
                <div class="status-badge ${statusClass}">
                    <span class="status-indicator ${statusClass}"></span>
                    ${statusText}
                </div>
            </div>
            <div class="task-card-modern-description">
                ${escapeHtml(taskDescription)}
            </div>
            <div class="task-card-modern-footer">
                <div class="task-card-modern-meta">
                    <div class="task-card-modern-meta-item">
                        <svg width="14" height="14" viewBox="0 0 14 14" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M7 13C10.3137 13 13 10.3137 13 7C13 3.68629 10.3137 1 7 1C3.68629 1 1 3.68629 1 7C1 10.3137 3.68629 13 7 13Z" stroke="currentColor" stroke-width="1.5"/>
                            <path d="M7 3.5V7L9.5 8.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                        </svg>
                        <span>${createdDate}</span>
                    </div>
                    <div class="task-card-modern-meta-item">
                        <svg width="14" height="14" viewBox="0 0 14 14" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M12 2H9C9 1.46957 8.78929 0.960859 8.41421 0.585786C8.03914 0.210714 7.53043 0 7 0C6.46957 0 5.96086 0.210714 5.58579 0.585786C5.21071 0.960859 5 1.46957 5 2H2C1.46957 2 0.960859 2.21071 0.585786 2.58579C0.210714 2.96086 0 3.46957 0 4V12C0 12.5304 0.210714 13.0391 0.585786 13.4142C0.960859 13.7893 1.46957 14 2 14H12C12.5304 14 13.0391 13.7893 13.4142 13.4142C13.7893 13.0391 14 12.5304 14 12V4C14 3.46957 13.7893 2.96086 13.4142 2.58579C13.0391 2.21071 12.5304 2 12 2Z" stroke="currentColor" stroke-width="1.5"/>
                        </svg>
                        <span>ID: ${taskId}</span>
                    </div>
                </div>
            </div>
        </div>
    `;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function setupNewTaskModal() {
    const modal = document.getElementById('new-task-modal');
    const btn = document.getElementById('new-task-btn');
    const span = document.getElementsByClassName('close')[0];
    const form = document.getElementById('new-task-form');

    btn.onclick = () => modal.classList.add('active');
    span.onclick = () => modal.classList.remove('active');

    window.onclick = (event) => {
        if (event.target == modal) {
            modal.classList.remove('active');
        }
    };

    form.onsubmit = async (e) => {
        e.preventDefault();

        const maxCostValue = document.getElementById('max-cost').value;

        const taskData = {
            task: document.getElementById('task-description').value,
            context: {
                title: document.getElementById('task-title').value
            },
            max_depth: parseInt(document.getElementById('max-depth').value),
            max_agents: parseInt(document.getElementById('max-agents').value),
            timeout: 1800
        };

        // Only add max_cost if value is provided
        if (maxCostValue && maxCostValue.trim() !== '') {
            taskData.max_cost = parseFloat(maxCostValue);
        }

        try {
            const response = await fetch('/api/tasks', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(taskData)
            });

            const result = await response.json();

            if (result.task_id) {
                window.location.href = `/task/${result.task_id}`;
            }
        } catch (error) {
            console.error('Error creating task:', error);
            alert('Failed to create task');
        }
    };
}

function truncate(str, length) {
    return str.length > length ? str.substring(0, length) + '...' : str;
}

function formatDate(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    const now = new Date();
    const diff = now - date;
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);

    if (minutes < 1) return 'Just now';
    if (minutes < 60) return `${minutes}m ago`;
    if (hours < 24) return `${hours}h ago`;
    return `${days}d ago`;
}

function setupStatsLink() {
    const statsLink = document.getElementById('stats-link');
    if (statsLink) {
        statsLink.addEventListener('click', (e) => {
            e.preventDefault();
            // Scroll to stats section
            document.querySelector('.stats-grid').scrollIntoView({ behavior: 'smooth' });
        });
    }
}
