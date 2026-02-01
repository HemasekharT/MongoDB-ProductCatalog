// API Configuration
const API_BASE_URL = 'https://product-catalog-backend-qcl7ofomoa-uc.a.run.app';

// State
let currentSearchType = 'semantic';
let currentFilters = {};

// DOM Elements
const searchInput = document.getElementById('searchInput');
const searchBtn = document.getElementById('searchBtn');
const productsGrid = document.getElementById('productsGrid');
const loadingSpinner = document.getElementById('loadingSpinner');
const emptyState = document.getElementById('emptyState');
const resultsTitle = document.getElementById('resultsTitle');
const resultsCount = document.getElementById('resultsCount');
const categoryFilter = document.getElementById('categoryFilter');
const stockFilter = document.getElementById('stockFilter');
const clearFiltersBtn = document.getElementById('clearFilters');
const chatPanel = document.getElementById('chatPanel');
const chatToggle = document.getElementById('chatToggle');
const chatClose = document.getElementById('chatClose');
const chatInput = document.getElementById('chatInput');
const chatSend = document.getElementById('chatSend');
const chatMessages = document.getElementById('chatMessages');
const productModal = document.getElementById('productModal');
const modalClose = document.getElementById('modalClose');
const modalBody = document.getElementById('modalBody');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadProducts();
    setupEventListeners();
});

// Event Listeners
function setupEventListeners() {
    // Search
    searchBtn.addEventListener('click', handleSearch);
    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleSearch();
    });

    // Search type toggle
    document.querySelectorAll('.toggle-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.toggle-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentSearchType = btn.dataset.type;
        });
    });

    // Filters
    categoryFilter.addEventListener('change', handleFilterChange);
    stockFilter.addEventListener('change', handleFilterChange);
    clearFiltersBtn.addEventListener('click', clearFilters);

    // Chat
    chatToggle.addEventListener('click', () => chatPanel.classList.add('open'));
    chatClose.addEventListener('click', () => chatPanel.classList.remove('open'));
    chatSend.addEventListener('click', sendChatMessage);
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendChatMessage();
    });

    // Modal
    modalClose.addEventListener('click', () => productModal.classList.remove('open'));
    productModal.addEventListener('click', (e) => {
        if (e.target === productModal) productModal.classList.remove('open');
    });
}

// Load Products
async function loadProducts() {
    showLoading();

    try {
        const response = await fetch(`${API_BASE_URL}/api/products?limit=20`);
        const data = await response.json();

        displayProducts(data.products);
        resultsTitle.textContent = 'All Products';
        resultsCount.textContent = `${data.count} products`;
    } catch (error) {
        console.error('Failed to load products:', error);
        showEmpty();
    }
}

// Handle Search
async function handleSearch() {
    const query = searchInput.value.trim();

    if (!query) {
        loadProducts();
        return;
    }

    showLoading();

    try {
        let endpoint;
        let body = {
            query: query,
            limit: 20,
            filters: buildFilters()
        };

        switch (currentSearchType) {
            case 'semantic':
                endpoint = `${API_BASE_URL}/api/products/semantic-search`;
                break;
            case 'hybrid':
                endpoint = `${API_BASE_URL}/api/products/hybrid-search`;
                break;
            case 'keyword':
                endpoint = `${API_BASE_URL}/api/products/search`;
                break;
        }

        const response = await fetch(endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(body)
        });

        const data = await response.json();

        displayProducts(data.results);
        resultsTitle.textContent = `Search Results for "${query}"`;
        resultsCount.textContent = `${data.count} products`;
    } catch (error) {
        console.error('Search failed:', error);
        showEmpty();
    }
}

// Handle Filter Change
function handleFilterChange() {
    currentFilters = buildFilters();

    if (searchInput.value.trim()) {
        handleSearch();
    } else {
        loadProducts();
    }
}

// Build Filters
function buildFilters() {
    const filters = {};

    if (categoryFilter.value) {
        filters.category = categoryFilter.value;
    }

    if (stockFilter.value) {
        filters.in_stock = stockFilter.value === 'true';
    }

    return filters;
}

// Clear Filters
function clearFilters() {
    categoryFilter.value = '';
    stockFilter.value = '';
    currentFilters = {};

    if (searchInput.value.trim()) {
        handleSearch();
    } else {
        loadProducts();
    }
}

// Display Products
function displayProducts(products) {
    hideLoading();

    if (!products || products.length === 0) {
        showEmpty();
        return;
    }

    hideEmpty();

    productsGrid.innerHTML = products.map(product => createProductCard(product)).join('');

    // Add click listeners
    document.querySelectorAll('.product-card').forEach(card => {
        card.addEventListener('click', () => {
            const productId = card.dataset.productId;
            showProductDetails(productId);
        });
    });
}

// Create Product Card
function createProductCard(product) {
    const inStock = product.inventory?.in_stock ?? false;
    const price = product.price?.current ?? 0;
    const categoryIcon = getCategoryIcon(product.category?.primary);

    return `
        <div class="product-card" data-product-id="${product.product_id}">
            <div class="product-image">${categoryIcon}</div>
            <div class="product-info">
                <div class="product-brand">${product.brand}</div>
                <h3 class="product-name">${product.name}</h3>
                <p class="product-description">${product.description}</p>
            </div>
            <div class="product-footer">
                <div class="product-price">$${price.toFixed(2)}</div>
                <div class="product-stock ${inStock ? 'in-stock' : 'out-of-stock'}">
                    ${inStock ? '✓ In Stock' : '✗ Out of Stock'}
                </div>
            </div>
        </div>
    `;
}

// Get Category Icon
function getCategoryIcon(category) {
    const icons = {
        'Tools': '🔨',
        'Electronics': '💻',
        'Furniture': '🛋️',
        'Appliances': '🏠',
        'Home Improvement': '🏗️'
    };

    return icons[category] || '📦';
}

// Show Product Details
async function showProductDetails(productId) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/products/${productId}`);
        const product = await response.json();

        modalBody.innerHTML = `
            <div class="product-detail">
                <div class="product-detail-header">
                    <div class="product-detail-image">${getCategoryIcon(product.category?.primary)}</div>
                    <div class="product-detail-info">
                        <div class="product-brand">${product.brand}</div>
                        <h2>${product.name}</h2>
                        <div class="product-price">$${product.price.current.toFixed(2)}</div>
                        ${product.price.current < product.price.original ?
                `<div class="product-original-price">Was: $${product.price.original.toFixed(2)}</div>` : ''}
                    </div>
                </div>
                <div class="product-detail-body">
                    <h3>Description</h3>
                    <p>${product.long_description}</p>
                    
                    <h3>Details</h3>
                    <ul>
                        <li><strong>Category:</strong> ${product.category.primary} › ${product.category.subcategory}</li>
                        <li><strong>Brand:</strong> ${product.brand}</li>
                        <li><strong>SKU:</strong> ${product.product_id}</li>
                        <li><strong>Stock:</strong> ${product.inventory.in_stock ?
                `In Stock (${product.inventory.quantity} available)` : 'Out of Stock'}</li>
                        <li><strong>Rating:</strong> ${product.ratings.average} ⭐ (${product.ratings.count} reviews)</li>
                    </ul>
                    
                    ${Object.keys(product.attributes).length > 0 ? `
                        <h3>Specifications</h3>
                        <ul>
                            ${Object.entries(product.attributes).map(([key, value]) =>
                    `<li><strong>${key}:</strong> ${value}</li>`
                ).join('')}
                        </ul>
                    ` : ''}
                </div>
            </div>
        `;

        productModal.classList.add('open');
    } catch (error) {
        console.error('Failed to load product details:', error);
    }
}

// Chat Functions
async function sendChatMessage() {
    const message = chatInput.value.trim();

    if (!message) return;

    // Add user message
    addChatMessage(message, 'user');
    chatInput.value = '';

    // Show typing indicator
    const typingId = addTypingIndicator();

    try {
        const response = await fetch(`${API_BASE_URL}/api/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message })
        });

        const data = await response.json();

        // Remove typing indicator
        removeTypingIndicator(typingId);

        // Add assistant response
        addChatMessage(data.response, 'assistant');

        // If products were returned, show them
        if (data.products && data.products.length > 0) {
            displayProducts(data.products);
            resultsTitle.textContent = 'AI Recommended Products';
            resultsCount.textContent = `${data.products.length} products`;
        }
    } catch (error) {
        console.error('Chat failed:', error);
        removeTypingIndicator(typingId);
        addChatMessage('Sorry, I encountered an error. Please try again.', 'assistant');
    }
}

function addChatMessage(text, sender) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${sender}`;
    messageDiv.innerHTML = `
        <div class="message-content">
            <p>${text}</p>
        </div>
    `;

    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function addTypingIndicator() {
    const id = 'typing-' + Date.now();
    const typingDiv = document.createElement('div');
    typingDiv.id = id;
    typingDiv.className = 'chat-message assistant';
    typingDiv.innerHTML = `
        <div class="message-content">
            <p>Thinking...</p>
        </div>
    `;

    chatMessages.appendChild(typingDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    return id;
}

function removeTypingIndicator(id) {
    const element = document.getElementById(id);
    if (element) {
        element.remove();
    }
}

// Loading States
function showLoading() {
    productsGrid.style.display = 'none';
    emptyState.style.display = 'none';
    loadingSpinner.style.display = 'block';
}

function hideLoading() {
    loadingSpinner.style.display = 'none';
    productsGrid.style.display = 'grid';
}

function showEmpty() {
    productsGrid.style.display = 'none';
    loadingSpinner.style.display = 'none';
    emptyState.style.display = 'block';
}

function hideEmpty() {
    emptyState.style.display = 'none';
}
