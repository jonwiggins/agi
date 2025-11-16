// Memories JavaScript
let allMemories = [];
let filteredMemories = [];
let currentCategory = 'all';
let currentSearchQuery = '';

document.addEventListener('DOMContentLoaded', () => {
    setupTabs();
    setupSearch();
    setupStatsLink();
    setupAddMemoryButton();
    loadMemories();
});

// Load memories from API
async function loadMemories() {
    const container = document.getElementById('memories-container');
    const loadingState = document.getElementById('loading-state');
    const emptyState = document.getElementById('empty-state');

    try {
        loadingState.style.display = 'flex';

        const response = await fetch('/api/memories');

        if (!response.ok) {
            throw new Error('Failed to load memories');
        }

        const data = await response.json();
        allMemories = Array.isArray(data) ? data : (data.memories || []);
        filteredMemories = [...allMemories];

        loadingState.style.display = 'none';

        if (allMemories.length === 0) {
            emptyState.style.display = 'flex';
            updateStats();
            return;
        }

        emptyState.style.display = 'none';
        renderMemories(filteredMemories);
        updateStats();

    } catch (error) {
        console.error('Error loading memories:', error);
        loadingState.style.display = 'none';

        // Show demo data if API fails
        loadDemoMemories();
    }
}

// Load demo memories for testing
function loadDemoMemories() {
    allMemories = [
        {
            id: '1',
            category: 'knowledge',
            title: 'Successful Pattern: REST API Design',
            content: 'When designing REST APIs, decompose into: endpoint design, data models, error handling, and authentication.',
            importance: 5,
            usageCount: 12,
            timestamp: Date.now() - 2 * 60 * 60 * 1000, // 2 hours ago
            metadata: {
                successRate: 0.95,
                tags: ['api', 'design', 'rest']
            }
        },
        {
            id: '2',
            category: 'patterns',
            title: 'Task Decomposition Strategy',
            content: 'For complex implementation tasks: (1) Research approach, (2) Design architecture, (3) Implement components, (4) Test and integrate.',
            importance: 4,
            usageCount: 7,
            timestamp: Date.now() - 24 * 60 * 60 * 1000, // 1 day ago
            metadata: {
                successRate: 0.85,
                tags: ['strategy', 'planning']
            }
        },
        {
            id: '3',
            category: 'experiences',
            title: 'Code Execution Insight',
            content: 'Python code execution works best with explicit error handling and timeout settings of 30s.',
            importance: 4,
            usageCount: 5,
            timestamp: Date.now() - 3 * 24 * 60 * 60 * 1000, // 3 days ago
            metadata: {
                confidence: 0.92,
                taskId: 'abc-123',
                tags: ['python', 'execution']
            }
        },
        {
            id: '4',
            category: 'knowledge',
            title: 'Docker Best Practices',
            content: 'Always use multi-stage builds to reduce image size and improve security. Keep base images updated.',
            importance: 5,
            usageCount: 15,
            timestamp: Date.now() - 5 * 24 * 60 * 60 * 1000,
            metadata: {
                tags: ['docker', 'devops', 'security']
            }
        },
        {
            id: '5',
            category: 'patterns',
            title: 'Error Handling Pattern',
            content: 'Implement graceful degradation: try primary approach, fall back to alternatives, always provide meaningful error messages.',
            importance: 3,
            usageCount: 8,
            timestamp: Date.now() - 7 * 24 * 60 * 60 * 1000,
            metadata: {
                successRate: 0.78,
                tags: ['error-handling', 'reliability']
            }
        }
    ];

    filteredMemories = [...allMemories];
    renderMemories(filteredMemories);
    updateStats();
}

// Render memories to the DOM
function renderMemories(memories) {
    const container = document.getElementById('memories-container');
    const loadingState = document.getElementById('loading-state');
    const emptyState = document.getElementById('empty-state');

    // Hide loading and empty states
    loadingState.style.display = 'none';

    if (memories.length === 0) {
        emptyState.style.display = 'flex';
        // Clear existing memory cards
        const existingCards = container.querySelectorAll('.memory-card-modern');
        existingCards.forEach(card => card.remove());
        return;
    }

    emptyState.style.display = 'none';

    // Clear existing memory cards
    const existingCards = container.querySelectorAll('.memory-card-modern');
    existingCards.forEach(card => card.remove());

    // Render new memories
    memories.forEach((memory, index) => {
        const card = createMemoryCard(memory, index);
        container.appendChild(card);
    });
}

// Create a memory card element
function createMemoryCard(memory, index) {
    const card = document.createElement('div');
    card.className = 'memory-card-modern';
    card.style.animationDelay = `${index * 0.05}s`;

    const categoryClass = getCategoryClass(memory.category);
    const categoryIcon = getCategoryIcon(memory.category);
    const timeAgo = getTimeAgo(memory.timestamp);
    const stars = generateStars(memory.importance || 3);

    card.innerHTML = `
        <div class="memory-card-header">
            <div class="memory-category-badge ${categoryClass}">
                ${categoryIcon}
                <span>${memory.category || 'General'}</span>
            </div>
            <div class="memory-time">${timeAgo}</div>
        </div>

        <div class="memory-card-body">
            <h3 class="memory-title">${escapeHtml(memory.title || 'Untitled Memory')}</h3>
            <p class="memory-description">${escapeHtml(memory.content || memory.description || 'No description')}</p>
        </div>

        <div class="memory-card-footer">
            <div class="memory-importance">
                <div class="importance-label">Importance</div>
                <div class="stars">${stars}</div>
            </div>

            <div class="memory-stats-inline">
                ${memory.usageCount !== undefined ? `
                    <div class="stat-inline">
                        <svg width="14" height="14" viewBox="0 0 14 14" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M7 13C10.3137 13 13 10.3137 13 7C13 3.68629 10.3137 1 7 1C3.68629 1 1 3.68629 1 7C1 10.3137 3.68629 13 7 13Z" stroke="currentColor" stroke-width="1.5"/>
                            <path d="M7 3.5V7L9.5 8.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                        </svg>
                        <span>Used ${memory.usageCount}x</span>
                    </div>
                ` : ''}

                ${memory.metadata?.successRate !== undefined ? `
                    <div class="stat-inline">
                        <svg width="14" height="14" viewBox="0 0 14 14" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M12 4L5.5 10.5L2 7" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                        </svg>
                        <span>${(memory.metadata.successRate * 100).toFixed(0)}% success</span>
                    </div>
                ` : ''}

                ${memory.metadata?.confidence !== undefined ? `
                    <div class="stat-inline">
                        <svg width="14" height="14" viewBox="0 0 14 14" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M7 1L8.5 5L13 5.5L9.5 8.5L10.5 13L7 10.5L3.5 13L4.5 8.5L1 5.5L5.5 5L7 1Z" stroke="currentColor" stroke-width="1.5"/>
                        </svg>
                        <span>${(memory.metadata.confidence * 100).toFixed(0)}% confidence</span>
                    </div>
                ` : ''}
            </div>
        </div>

        ${memory.metadata?.tags && memory.metadata.tags.length > 0 ? `
            <div class="memory-tags">
                ${memory.metadata.tags.map(tag => `<span class="memory-tag">${escapeHtml(tag)}</span>`).join('')}
            </div>
        ` : ''}
    `;

    return card;
}

// Generate star rating HTML
function generateStars(importance) {
    const maxStars = 5;
    const filledStars = Math.min(Math.max(Math.round(importance), 0), maxStars);
    let starsHtml = '';

    for (let i = 0; i < maxStars; i++) {
        if (i < filledStars) {
            starsHtml += `
                <svg class="star star-filled" width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M8 1L9.5 5.5L14 6.5L11 9.5L11.7 14L8 11.8L4.3 14L5 9.5L2 6.5L6.5 5.5L8 1Z" fill="currentColor" stroke="currentColor" stroke-width="1.5"/>
                </svg>
            `;
        } else {
            starsHtml += `
                <svg class="star star-empty" width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M8 1L9.5 5.5L14 6.5L11 9.5L11.7 14L8 11.8L4.3 14L5 9.5L2 6.5L6.5 5.5L8 1Z" stroke="currentColor" stroke-width="1.5"/>
                </svg>
            `;
        }
    }

    return starsHtml;
}

// Get category class for styling
function getCategoryClass(category) {
    const categoryMap = {
        'knowledge': 'category-knowledge',
        'patterns': 'category-patterns',
        'experiences': 'category-experiences',
        'pattern': 'category-patterns',
        'experience': 'category-experiences'
    };
    return categoryMap[category?.toLowerCase()] || 'category-general';
}

// Get category icon SVG
function getCategoryIcon(category) {
    const icons = {
        'knowledge': `<svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M8 1L2 4L8 7L14 4L8 1Z" stroke="currentColor" stroke-width="1.5"/>
            <path d="M2 10L8 13L14 10M2 7L8 10L14 7" stroke="currentColor" stroke-width="1.5"/>
        </svg>`,
        'patterns': `<svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M8 1L9.5 5.5L14 6.5L11 9.5L11.7 14L8 11.8L4.3 14L5 9.5L2 6.5L6.5 5.5L8 1Z" stroke="currentColor" stroke-width="1.5"/>
        </svg>`,
        'experiences': `<svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="8" cy="8" r="6" stroke="currentColor" stroke-width="1.5"/>
            <path d="M8 4V8L10.5 9.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
        </svg>`,
        'pattern': `<svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M8 1L9.5 5.5L14 6.5L11 9.5L11.7 14L8 11.8L4.3 14L5 9.5L2 6.5L6.5 5.5L8 1Z" stroke="currentColor" stroke-width="1.5"/>
        </svg>`,
        'experience': `<svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="8" cy="8" r="6" stroke="currentColor" stroke-width="1.5"/>
            <path d="M8 4V8L10.5 9.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
        </svg>`
    };
    return icons[category?.toLowerCase()] || icons['knowledge'];
}

// Get time ago string
function getTimeAgo(timestamp) {
    if (!timestamp) return 'Recently';

    const now = Date.now();
    const diff = now - timestamp;

    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);

    if (days > 0) return `${days} day${days > 1 ? 's' : ''} ago`;
    if (hours > 0) return `${hours} hour${hours > 1 ? 's' : ''} ago`;
    if (minutes > 0) return `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
    return 'Just now';
}

// Update statistics
function updateStats() {
    const total = allMemories.length;
    const knowledge = allMemories.filter(m => m.category?.toLowerCase() === 'knowledge').length;
    const patterns = allMemories.filter(m => m.category?.toLowerCase() === 'patterns' || m.category?.toLowerCase() === 'pattern').length;
    const experiences = allMemories.filter(m => m.category?.toLowerCase() === 'experiences' || m.category?.toLowerCase() === 'experience').length;

    document.getElementById('total-memories').textContent = total;
    document.getElementById('knowledge-count').textContent = knowledge;
    document.getElementById('patterns-count').textContent = patterns;
    document.getElementById('experiences-count').textContent = experiences;
}

// Setup tabs
function setupTabs() {
    const tabs = document.querySelectorAll('.tab');

    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            // Remove active from all tabs
            tabs.forEach(t => t.classList.remove('active'));

            // Add active to clicked tab
            tab.classList.add('active');

            // Filter memories
            currentCategory = tab.dataset.category;
            applyFilters();
        });
    });
}

// Setup search
function setupSearch() {
    const searchInput = document.getElementById('memory-search');
    const clearBtn = document.getElementById('clear-search');

    searchInput.addEventListener('input', (e) => {
        currentSearchQuery = e.target.value;

        // Show/hide clear button
        if (currentSearchQuery) {
            clearBtn.style.display = 'flex';
        } else {
            clearBtn.style.display = 'none';
        }

        // Debounce search
        clearTimeout(searchInput.searchTimeout);
        searchInput.searchTimeout = setTimeout(() => {
            applyFilters();
        }, 300);
    });

    clearBtn.addEventListener('click', () => {
        searchInput.value = '';
        currentSearchQuery = '';
        clearBtn.style.display = 'none';
        applyFilters();
    });

    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            applyFilters();
        }
    });
}

// Apply filters
function applyFilters() {
    let filtered = [...allMemories];

    // Apply category filter
    if (currentCategory !== 'all') {
        filtered = filtered.filter(memory => {
            const cat = memory.category?.toLowerCase();
            return cat === currentCategory ||
                   (currentCategory === 'patterns' && cat === 'pattern') ||
                   (currentCategory === 'experiences' && cat === 'experience');
        });
    }

    // Apply search filter
    if (currentSearchQuery) {
        const query = currentSearchQuery.toLowerCase();
        filtered = filtered.filter(memory => {
            const title = (memory.title || '').toLowerCase();
            const content = (memory.content || memory.description || '').toLowerCase();
            const tags = (memory.metadata?.tags || []).join(' ').toLowerCase();
            return title.includes(query) || content.includes(query) || tags.includes(query);
        });
    }

    filteredMemories = filtered;
    renderMemories(filteredMemories);
}

// Setup stats link
function setupStatsLink() {
    const statsLink = document.getElementById('stats-link');
    if (statsLink) {
        statsLink.addEventListener('click', (e) => {
            e.preventDefault();
            window.location.href = '/';
        });
    }
}

// Setup add memory button
function setupAddMemoryButton() {
    const addBtn = document.getElementById('add-memory-btn');
    const addBtnEmpty = document.getElementById('add-memory-empty');

    const handleAddMemory = () => {
        alert('Add Memory functionality coming soon! This will open a modal to create a new memory.');
        // TODO: Implement add memory modal
    };

    if (addBtn) {
        addBtn.addEventListener('click', handleAddMemory);
    }

    if (addBtnEmpty) {
        addBtnEmpty.addEventListener('click', handleAddMemory);
    }
}

// Utility function to escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
