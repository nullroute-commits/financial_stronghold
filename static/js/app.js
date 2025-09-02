/*
JavaScript functionality for Financial Stronghold
Modern ES6+ JavaScript with Bootstrap 5 integration
Created by Team Zeta (Frontend & UX Agents)
*/

// Global application object
const FinancialApp = {
    // Configuration
    config: {
        apiBaseUrl: '/api/v1/',
        refreshInterval: 300000, // 5 minutes
        animationDuration: 300
    },
    
    // Initialize application
    init() {
        this.setupEventListeners();
        this.setupAjaxDefaults();
        this.initializeComponents();
        console.log('Financial Stronghold initialized');
    },
    
    // Setup global event listeners
    setupEventListeners() {
        // Form validation
        document.addEventListener('submit', this.handleFormSubmit.bind(this));
        
        // AJAX loading indicators
        document.addEventListener('click', this.handleAjaxButtons.bind(this));
        
        // Auto-save functionality
        document.addEventListener('input', this.handleAutoSave.bind(this));
        
        // Keyboard shortcuts
        document.addEventListener('keydown', this.handleKeyboardShortcuts.bind(this));
    },
    
    // Setup AJAX defaults
    setupAjaxDefaults() {
        // Get CSRF token
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
        
        // Setup fetch defaults
        const originalFetch = window.fetch;
        window.fetch = function(url, options = {}) {
            options.headers = {
                'X-CSRFToken': csrfToken,
                'Content-Type': 'application/json',
                ...options.headers
            };
            
            if (options.method && ['POST', 'PUT', 'PATCH', 'DELETE'].includes(options.method.toUpperCase())) {
                options.credentials = 'same-origin';
            }
            
            return originalFetch(url, options);
        };
    },
    
    // Initialize components
    initializeComponents() {
        this.initializeTooltips();
        this.initializeModals();
        this.initializeCharts();
        this.startPeriodicUpdates();
    },
    
    // Initialize Bootstrap tooltips
    initializeTooltips() {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    },
    
    // Initialize Bootstrap modals
    initializeModals() {
        const modalElements = document.querySelectorAll('.modal');
        modalElements.forEach(modalEl => {
            new bootstrap.Modal(modalEl);
        });
    },
    
    // Initialize charts (placeholder for future Chart.js integration)
    initializeCharts() {
        const chartElements = document.querySelectorAll('[data-chart]');
        chartElements.forEach(chartEl => {
            // Future: Initialize Chart.js charts
            console.log('Chart placeholder:', chartEl.dataset.chart);
        });
    },
    
    // Start periodic updates
    startPeriodicUpdates() {
        setInterval(() => {
            this.updateDashboardData();
        }, this.config.refreshInterval);
    },
    
    // Handle form submissions
    handleFormSubmit(event) {
        const form = event.target;
        
        // Add loading state
        const submitBtn = form.querySelector('button[type="submit"]');
        if (submitBtn) {
            const originalText = submitBtn.innerHTML;
            submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Processing...';
            submitBtn.disabled = true;
            
            // Reset button after delay if form doesn't redirect
            setTimeout(() => {
                submitBtn.innerHTML = originalText;
                submitBtn.disabled = false;
            }, 5000);
        }
    },
    
    // Handle AJAX button clicks
    handleAjaxButtons(event) {
        const button = event.target.closest('[data-ajax]');
        if (!button) return;
        
        event.preventDefault();
        
        const url = button.dataset.ajax;
        const method = button.dataset.method || 'GET';
        
        this.makeAjaxRequest(url, method, button);
    },
    
    // Handle auto-save functionality
    handleAutoSave(event) {
        const element = event.target;
        if (!element.dataset.autosave) return;
        
        clearTimeout(element.autoSaveTimeout);
        element.autoSaveTimeout = setTimeout(() => {
            this.autoSaveField(element);
        }, 1000);
    },
    
    // Handle keyboard shortcuts
    handleKeyboardShortcuts(event) {
        // Ctrl/Cmd + K for quick search (future enhancement)
        if ((event.ctrlKey || event.metaKey) && event.key === 'k') {
            event.preventDefault();
            // Future: Open quick search modal
            console.log('Quick search shortcut');
        }
        
        // Escape to close modals
        if (event.key === 'Escape') {
            const openModal = document.querySelector('.modal.show');
            if (openModal) {
                bootstrap.Modal.getInstance(openModal).hide();
            }
        }
    },
    
    // Make AJAX request with loading states
    async makeAjaxRequest(url, method = 'GET', triggerElement = null) {
        try {
            if (triggerElement) {
                triggerElement.classList.add('disabled');
                const originalText = triggerElement.innerHTML;
                triggerElement.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Loading...';
            }
            
            const response = await fetch(url, { method });
            const data = await response.json();
            
            if (response.ok) {
                this.showNotification('Success', 'success');
                return data;
            } else {
                throw new Error(data.message || 'Request failed');
            }
            
        } catch (error) {
            console.error('AJAX request failed:', error);
            this.showNotification('Error: ' + error.message, 'danger');
        } finally {
            if (triggerElement) {
                triggerElement.classList.remove('disabled');
                // Reset button text would go here
            }
        }
    },
    
    // Auto-save field data
    async autoSaveField(element) {
        const url = element.dataset.autosave;
        const value = element.value;
        const field = element.name;
        
        try {
            await this.makeAjaxRequest(url, 'PATCH', null);
            element.classList.add('is-valid');
            setTimeout(() => element.classList.remove('is-valid'), 2000);
        } catch (error) {
            element.classList.add('is-invalid');
            setTimeout(() => element.classList.remove('is-invalid'), 2000);
        }
    },
    
    // Update dashboard data
    async updateDashboardData() {
        try {
            const response = await fetch('/api/v1/health/');
            const data = await response.json();
            
            // Update health status indicator
            const healthIndicator = document.querySelector('[data-health-status]');
            if (healthIndicator) {
                healthIndicator.className = data.status === 'healthy' ? 'text-success' : 'text-danger';
                healthIndicator.title = `System ${data.status} - Last checked: ${new Date().toLocaleTimeString()}`;
            }
            
        } catch (error) {
            console.error('Failed to update dashboard data:', error);
        }
    },
    
    // Show notification toast
    showNotification(message, type = 'info') {
        // Create toast element
        const toastHtml = `
            <div class="toast align-items-center text-white bg-${type} border-0" role="alert">
                <div class="d-flex">
                    <div class="toast-body">
                        ${message}
                    </div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
                </div>
            </div>
        `;
        
        // Add to toast container
        let toastContainer = document.querySelector('.toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
            document.body.appendChild(toastContainer);
        }
        
        toastContainer.insertAdjacentHTML('beforeend', toastHtml);
        
        // Initialize and show toast
        const toastElement = toastContainer.lastElementChild;
        const toast = new bootstrap.Toast(toastElement);
        toast.show();
        
        // Remove toast element after it's hidden
        toastElement.addEventListener('hidden.bs.toast', () => {
            toastElement.remove();
        });
    },
    
    // Format currency values
    formatCurrency(amount, currency = 'USD') {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: currency
        }).format(amount);
    },
    
    // Format dates
    formatDate(dateString) {
        return new Date(dateString).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    },
    
    // Debounce function for performance
    debounce(func, wait) {
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
};

// Account-specific functionality
const AccountManager = {
    // Load account balance via AJAX
    async loadBalance(accountId) {
        try {
            const response = await fetch(`/api/v1/accounts/${accountId}/balance/`);
            const data = await response.json();
            
            // Update balance display
            const balanceElement = document.querySelector(`[data-account-balance="${accountId}"]`);
            if (balanceElement) {
                balanceElement.textContent = FinancialApp.formatCurrency(data.balance, data.currency);
                balanceElement.className = data.balance >= 0 ? 'text-success' : 'text-danger';
            }
            
            return data;
        } catch (error) {
            console.error('Failed to load account balance:', error);
        }
    },
    
    // Refresh all account balances
    async refreshAllBalances() {
        const balanceElements = document.querySelectorAll('[data-account-balance]');
        const promises = Array.from(balanceElements).map(el => 
            this.loadBalance(el.dataset.accountBalance)
        );
        
        await Promise.all(promises);
    }
};

// Transaction-specific functionality
const TransactionManager = {
    // Load transaction summary
    async loadSummary() {
        try {
            const response = await fetch('/api/v1/transactions/summary/');
            const data = await response.json();
            
            // Update summary display
            this.updateSummaryDisplay(data);
            
            return data;
        } catch (error) {
            console.error('Failed to load transaction summary:', error);
        }
    },
    
    // Update summary display elements
    updateSummaryDisplay(data) {
        const elements = {
            income: document.querySelector('[data-summary="income"]'),
            expenses: document.querySelector('[data-summary="expenses"]'),
            net: document.querySelector('[data-summary="net"]'),
            count: document.querySelector('[data-summary="count"]')
        };
        
        if (elements.income) {
            elements.income.textContent = FinancialApp.formatCurrency(data.total_income);
        }
        if (elements.expenses) {
            elements.expenses.textContent = FinancialApp.formatCurrency(data.total_expenses);
        }
        if (elements.net) {
            elements.net.textContent = FinancialApp.formatCurrency(data.net_income);
            elements.net.className = data.net_income >= 0 ? 'text-success' : 'text-danger';
        }
        if (elements.count) {
            elements.count.textContent = data.transaction_count;
        }
    }
};

// Initialize application when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    FinancialApp.init();
    
    // Initialize page-specific functionality
    if (document.body.dataset.page === 'dashboard') {
        AccountManager.refreshAllBalances();
        TransactionManager.loadSummary();
    }
});

// Export for global access
window.FinancialApp = FinancialApp;
window.AccountManager = AccountManager;
window.TransactionManager = TransactionManager;