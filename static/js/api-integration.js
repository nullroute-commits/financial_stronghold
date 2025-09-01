/**
 * Financial Stronghold - API Integration
 * Provides JavaScript functions for dynamic interaction with the FastAPI backend
 */

class FinancialAPI {
    constructor() {
        this.baseURL = '/api'; // Adjust based on your FastAPI mount point
        this.csrfToken = this.getCSRFToken();
    }

    getCSRFToken() {
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'csrftoken') {
                return value;
            }
        }
        return null;
    }

    async makeRequest(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.csrfToken,
            },
            credentials: 'same-origin',
        };

        const mergedOptions = { ...defaultOptions, ...options };
        
        try {
            const response = await fetch(url, mergedOptions);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            return { success: true, data };
        } catch (error) {
            console.error('API request failed:', error);
            return { success: false, error: error.message };
        }
    }

    // Dashboard API methods
    async getDashboardData() {
        return await this.makeRequest('/financial/dashboard');
    }

    async getFinancialSummary() {
        return await this.makeRequest('/financial/dashboard/summary');
    }

    async getAccountSummaries() {
        return await this.makeRequest('/financial/dashboard/accounts');
    }

    async getTransactionSummary() {
        return await this.makeRequest('/financial/dashboard/transactions');
    }

    async getBudgetStatuses() {
        return await this.makeRequest('/financial/dashboard/budgets');
    }

    // Account API methods
    async getAccounts(limit = null, offset = null) {
        let endpoint = '/financial/accounts';
        const params = new URLSearchParams();
        if (limit) params.append('limit', limit);
        if (offset) params.append('offset', offset);
        if (params.toString()) endpoint += '?' + params.toString();
        
        return await this.makeRequest(endpoint);
    }

    async getAccount(accountId) {
        return await this.makeRequest(`/financial/accounts/${accountId}`);
    }

    async createAccount(accountData) {
        return await this.makeRequest('/financial/accounts', {
            method: 'POST',
            body: JSON.stringify(accountData)
        });
    }

    async updateAccount(accountId, accountData) {
        return await this.makeRequest(`/financial/accounts/${accountId}`, {
            method: 'PUT',
            body: JSON.stringify(accountData)
        });
    }

    async deleteAccount(accountId) {
        return await this.makeRequest(`/financial/accounts/${accountId}`, {
            method: 'DELETE'
        });
    }

    // Transaction API methods
    async getTransactions(limit = null, offset = null) {
        let endpoint = '/financial/transactions';
        const params = new URLSearchParams();
        if (limit) params.append('limit', limit);
        if (offset) params.append('offset', offset);
        if (params.toString()) endpoint += '?' + params.toString();
        
        return await this.makeRequest(endpoint);
    }

    async getTransaction(transactionId) {
        return await this.makeRequest(`/financial/transactions/${transactionId}`);
    }

    async createTransaction(transactionData, autoClassify = true, autoTag = true) {
        const params = new URLSearchParams();
        params.append('auto_classify', autoClassify);
        params.append('auto_tag', autoTag);
        
        return await this.makeRequest(`/financial/transactions?${params.toString()}`, {
            method: 'POST',
            body: JSON.stringify(transactionData)
        });
    }

    async updateTransaction(transactionId, transactionData) {
        return await this.makeRequest(`/financial/transactions/${transactionId}`, {
            method: 'PUT',
            body: JSON.stringify(transactionData)
        });
    }

    async deleteTransaction(transactionId) {
        return await this.makeRequest(`/financial/transactions/${transactionId}`, {
            method: 'DELETE'
        });
    }

    // Budget API methods
    async getBudgets(limit = null, offset = null) {
        let endpoint = '/financial/budgets';
        const params = new URLSearchParams();
        if (limit) params.append('limit', limit);
        if (offset) params.append('offset', offset);
        if (params.toString()) endpoint += '?' + params.toString();
        
        return await this.makeRequest(endpoint);
    }

    async getBudget(budgetId) {
        return await this.makeRequest(`/financial/budgets/${budgetId}`);
    }

    async createBudget(budgetData) {
        return await this.makeRequest('/financial/budgets', {
            method: 'POST',
            body: JSON.stringify(budgetData)
        });
    }

    async updateBudget(budgetId, budgetData) {
        return await this.makeRequest(`/financial/budgets/${budgetId}`, {
            method: 'PUT',
            body: JSON.stringify(budgetData)
        });
    }

    async deleteBudget(budgetId) {
        return await this.makeRequest(`/financial/budgets/${budgetId}`, {
            method: 'DELETE'
        });
    }

    // Fee API methods
    async getFees(limit = null, offset = null) {
        let endpoint = '/financial/fees';
        const params = new URLSearchParams();
        if (limit) params.append('limit', limit);
        if (offset) params.append('offset', offset);
        if (params.toString()) endpoint += '?' + params.toString();
        
        return await this.makeRequest(endpoint);
    }

    async getFee(feeId) {
        return await this.makeRequest(`/financial/fees/${feeId}`);
    }

    async createFee(feeData) {
        return await this.makeRequest('/financial/fees', {
            method: 'POST',
            body: JSON.stringify(feeData)
        });
    }

    async updateFee(feeId, feeData) {
        return await this.makeRequest(`/financial/fees/${feeId}`, {
            method: 'PUT',
            body: JSON.stringify(feeData)
        });
    }

    async deleteFee(feeId) {
        return await this.makeRequest(`/financial/fees/${feeId}`, {
            method: 'DELETE'
        });
    }

    // Analytics API methods
    async getAnalyticsSummary() {
        return await this.makeRequest('/financial/analytics/summary');
    }

    async classifyTransactions(transactionData) {
        return await this.makeRequest('/financial/transactions/classify', {
            method: 'POST',
            body: JSON.stringify(transactionData)
        });
    }

    async getMonthlyBreakdown() {
        return await this.makeRequest('/financial/analytics/monthly-breakdown');
    }

    async getTransactionPatterns() {
        return await this.makeRequest('/financial/analytics/patterns');
    }

    async detectAnomalies(requestData) {
        return await this.makeRequest('/financial/analytics/anomalies', {
            method: 'POST',
            body: JSON.stringify(requestData)
        });
    }
}

// Utility functions for UI updates
class UIUpdater {
    static showLoading(elementId) {
        const element = document.getElementById(elementId);
        if (element) {
            element.innerHTML = '<div class="text-center"><i class="fas fa-spinner fa-spin fa-2x"></i><br>Loading...</div>';
        }
    }

    static showError(elementId, message) {
        const element = document.getElementById(elementId);
        if (element) {
            element.innerHTML = `<div class="alert alert-danger"><i class="fas fa-exclamation-triangle"></i> ${message}</div>`;
        }
    }

    static updateAccountList(accounts) {
        const accountList = document.getElementById('accountList');
        if (!accountList) return;

        if (accounts.length === 0) {
            accountList.innerHTML = `
                <div class="text-center py-4">
                    <i class="fas fa-university fa-3x text-muted mb-3"></i>
                    <p class="text-muted">No accounts found</p>
                </div>
            `;
            return;
        }

        accountList.innerHTML = accounts.map(account => `
            <div class="account-card p-3 mb-3">
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <h6 class="mb-1">${account.name}</h6>
                        <small class="account-type">${account.account_type}</small>
                    </div>
                    <div class="text-end">
                        <div class="account-balance">$${account.balance.toFixed(2)}</div>
                        <small class="text-${account.is_active ? 'success' : 'muted'}">
                            <i class="fas fa-circle"></i> ${account.is_active ? 'Active' : 'Inactive'}
                        </small>
                    </div>
                </div>
            </div>
        `).join('');
    }

    static updateTransactionList(transactions) {
        const transactionList = document.getElementById('transactionList');
        if (!transactionList) return;

        if (transactions.length === 0) {
            transactionList.innerHTML = `
                <div class="text-center py-4">
                    <i class="fas fa-exchange-alt fa-3x text-muted mb-3"></i>
                    <p class="text-muted">No transactions found</p>
                </div>
            `;
            return;
        }

        transactionList.innerHTML = `
            <div class="table-responsive">
                <table class="table transaction-table">
                    <thead>
                        <tr>
                            <th>Description</th>
                            <th>Amount</th>
                            <th>Type</th>
                            <th>Date</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${transactions.map(transaction => `
                            <tr class="transaction-row">
                                <td><strong>${transaction.description}</strong></td>
                                <td>
                                    <span class="transaction-amount ${transaction.transaction_type === 'income' ? 'positive' : 'negative'}">
                                        ${transaction.transaction_type === 'income' ? '+' : '-'}$${transaction.amount.toFixed(2)}
                                    </span>
                                </td>
                                <td>
                                    <span class="badge bg-secondary">${transaction.transaction_type}</span>
                                </td>
                                <td>${new Date(transaction.created_at).toLocaleDateString()}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;
    }

    static updateDashboardStats(summary) {
        if (summary.total_balance !== undefined) {
            const balanceEl = document.getElementById('totalBalance');
            if (balanceEl) balanceEl.textContent = `$${summary.total_balance.toFixed(2)}`;
        }

        if (summary.total_income !== undefined) {
            const incomeEl = document.getElementById('totalIncome');
            if (incomeEl) incomeEl.textContent = `$${summary.total_income.toFixed(2)}`;
        }

        if (summary.total_expenses !== undefined) {
            const expensesEl = document.getElementById('totalExpenses');
            if (expensesEl) expensesEl.textContent = `$${summary.total_expenses.toFixed(2)}`;
        }

        if (summary.net_worth !== undefined) {
            const netWorthEl = document.getElementById('netWorth');
            if (netWorthEl) netWorthEl.textContent = `$${summary.net_worth.toFixed(2)}`;
        }
    }
}

// Auto-refresh functionality
class AutoRefresh {
    constructor(api) {
        this.api = api;
        this.intervals = new Map();
    }

    startDashboardRefresh(intervalMinutes = 5) {
        const intervalId = setInterval(async () => {
            const result = await this.api.getFinancialSummary();
            if (result.success) {
                UIUpdater.updateDashboardStats(result.data);
            }
        }, intervalMinutes * 60 * 1000);

        this.intervals.set('dashboard', intervalId);
    }

    startAccountRefresh(intervalMinutes = 10) {
        const intervalId = setInterval(async () => {
            const result = await this.api.getAccountSummaries();
            if (result.success) {
                UIUpdater.updateAccountList(result.data);
            }
        }, intervalMinutes * 60 * 1000);

        this.intervals.set('accounts', intervalId);
    }

    stopRefresh(type) {
        if (this.intervals.has(type)) {
            clearInterval(this.intervals.get(type));
            this.intervals.delete(type);
        }
    }

    stopAllRefresh() {
        this.intervals.forEach((intervalId) => clearInterval(intervalId));
        this.intervals.clear();
    }
}

// Initialize global instances
const financialAPI = new FinancialAPI();
const autoRefresh = new AutoRefresh(financialAPI);

// Export for use in other scripts
window.FinancialAPI = FinancialAPI;
window.UIUpdater = UIUpdater;
window.AutoRefresh = AutoRefresh;
window.financialAPI = financialAPI;
window.autoRefresh = autoRefresh;