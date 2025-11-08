// Memories JavaScript

document.addEventListener('DOMContentLoaded', () => {
    setupTabs();
    setupSearch();
});

function setupTabs() {
    const tabs = document.querySelectorAll('.tab');

    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            // Remove active from all tabs
            tabs.forEach(t => t.classList.remove('active'));

            // Add active to clicked tab
            tab.classList.add('active');

            // Filter memories
            const category = tab.dataset.category;
            filterMemories(category);
        });
    });
}

function setupSearch() {
    const searchInput = document.getElementById('memory-search');
    const searchBtn = searchInput.nextElementSibling;

    searchBtn.addEventListener('click', () => {
        const query = searchInput.value;
        searchMemories(query);
    });

    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            const query = searchInput.value;
            searchMemories(query);
        }
    });
}

function filterMemories(category) {
    const memories = document.querySelectorAll('.memory-card');

    memories.forEach(memory => {
        const memoryCategory = memory.querySelector('.memory-category').textContent.toLowerCase();

        if (category === 'all' || memoryCategory === category) {
            memory.style.display = 'block';
        } else {
            memory.style.display = 'none';
        }
    });
}

function searchMemories(query) {
    const memories = document.querySelectorAll('.memory-card');
    const lowerQuery = query.toLowerCase();

    memories.forEach(memory => {
        const content = memory.textContent.toLowerCase();

        if (content.includes(lowerQuery)) {
            memory.style.display = 'block';
        } else {
            memory.style.display = 'none';
        }
    });
}

// In production, load memories from API
async function loadMemories() {
    try {
        const response = await fetch('/api/memories');
        const memories = await response.json();

        const container = document.getElementById('memories-container');

        if (memories.length === 0) {
            container.innerHTML = '<div class="empty-state">No memories found</div>';
            return;
        }

        // Render memories (implementation would go here)
    } catch (error) {
        console.error('Error loading memories:', error);
    }
}
