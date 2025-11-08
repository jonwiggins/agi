// Dashboard JavaScript

// Load tasks on page load
document.addEventListener('DOMContentLoaded', async () => {
    await loadStats();
    await loadTasks();
    setupNewTaskModal();

    // Refresh every 5 seconds
    setInterval(loadStats, 5000);
    setInterval(loadTasks, 5000);
});

async function loadStats() {
    try {
        const response = await fetch('/api/stats');
        const data = await response.json();

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
        console.error('Error loading stats:', error);
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
        const tasks = await response.json();

        const container = document.getElementById('tasks-container');

        if (!tasks || tasks.length === 0) {
            container.innerHTML = '<div class="empty-state">No tasks yet. Create one to get started!</div>';
            return;
        }

        container.innerHTML = tasks.map(task => `
            <div class="task-card" onclick="window.location.href='/task/${task.task_id}'">
                <div class="task-card-header">
                    <div class="task-title">${truncate(task.context?.title || task.task || 'Untitled Task', 60)}</div>
                    <div class="status-badge ${task.status}">${task.status}</div>
                </div>
                <div class="task-description">
                    ${truncate(task.task || '', 100)}
                </div>
                <div class="task-meta">
                    <span>Created: ${formatDate(task.created_at)}</span>
                    <span>ID: ${task.task_id.substring(0, 8)}</span>
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading tasks:', error);
        document.getElementById('tasks-container').innerHTML =
            '<div class="empty-state">Error loading tasks</div>';
    }
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

        const taskData = {
            task: document.getElementById('task-description').value,
            context: {
                title: document.getElementById('task-title').value
            },
            max_depth: parseInt(document.getElementById('max-depth').value),
            max_agents: parseInt(document.getElementById('max-agents').value),
            timeout: 1800
        };

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
