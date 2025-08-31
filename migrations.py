"""
Multi-tenancy database migration for Financial Stronghold.

This script provides SQL commands to add multi-tenancy support to the existing database.
"""

# Migration 001: Add Organizations table
MIGRATION_001_ORGANIZATIONS = """
-- Create organizations table
CREATE TABLE organizations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(120) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id)
);

-- Create index for organizations
CREATE INDEX idx_organizations_name ON organizations(name);
"""

# Migration 002: Add User-Organization association table
MIGRATION_002_USER_ORG_LINK = """
-- Create user-organization link table
CREATE TABLE user_organization_link (
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    org_id INTEGER REFERENCES organizations(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL DEFAULT 'member',
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    PRIMARY KEY (user_id, org_id),
    CONSTRAINT uq_user_org_link UNIQUE (user_id, org_id)
);

-- Create indexes for user-organization links
CREATE INDEX idx_user_org_link_user_id ON user_organization_link(user_id);
CREATE INDEX idx_user_org_link_org_id ON user_organization_link(org_id);
CREATE INDEX idx_user_org_link_role ON user_organization_link(role);
"""

# Migration 003: Add financial tables with tenant scoping
MIGRATION_003_FINANCIAL_TABLES = """
-- Create accounts table
CREATE TABLE accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(120) NOT NULL,
    account_type VARCHAR(50) NOT NULL,
    account_number VARCHAR(50),
    balance NUMERIC(12, 2) NOT NULL DEFAULT 0,
    currency VARCHAR(3) NOT NULL DEFAULT 'USD',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    description TEXT,
    tenant_type VARCHAR(20) NOT NULL DEFAULT 'user',
    tenant_id VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id)
);

-- Create transactions table
CREATE TABLE transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    amount NUMERIC(12, 2) NOT NULL,
    currency VARCHAR(3) NOT NULL DEFAULT 'USD',
    description TEXT,
    transaction_type VARCHAR(50) NOT NULL,
    reference_number VARCHAR(100),
    account_id UUID,
    to_account_id UUID,
    status VARCHAR(20) NOT NULL DEFAULT 'completed',
    category VARCHAR(100),
    tags TEXT,
    tenant_type VARCHAR(20) NOT NULL DEFAULT 'user',
    tenant_id VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id)
);

-- Create fees table
CREATE TABLE fees (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(120) NOT NULL,
    amount NUMERIC(12, 2) NOT NULL,
    currency VARCHAR(3) NOT NULL DEFAULT 'USD',
    fee_type VARCHAR(50) NOT NULL,
    description TEXT,
    transaction_id UUID,
    account_id UUID,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    frequency VARCHAR(20),
    tenant_type VARCHAR(20) NOT NULL DEFAULT 'user',
    tenant_id VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id)
);

-- Create budgets table
CREATE TABLE budgets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(120) NOT NULL,
    total_amount NUMERIC(12, 2) NOT NULL,
    spent_amount NUMERIC(12, 2) NOT NULL DEFAULT 0,
    currency VARCHAR(3) NOT NULL DEFAULT 'USD',
    start_date TIMESTAMP WITH TIME ZONE NOT NULL,
    end_date TIMESTAMP WITH TIME ZONE NOT NULL,
    categories TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    alert_threshold NUMERIC(5, 2),
    alert_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    tenant_type VARCHAR(20) NOT NULL DEFAULT 'user',
    tenant_id VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id)
);
"""

# Migration 004: Create indexes for optimal performance
MIGRATION_004_INDEXES = """
-- Create tenant-aware indexes for accounts
CREATE INDEX idx_accounts_tenant ON accounts(tenant_type, tenant_id);
CREATE INDEX idx_accounts_type ON accounts(account_type);
CREATE INDEX idx_accounts_active ON accounts(is_active);
CREATE INDEX idx_accounts_balance ON accounts(balance);

-- Create tenant-aware indexes for transactions
CREATE INDEX idx_transactions_tenant ON transactions(tenant_type, tenant_id);
CREATE INDEX idx_transactions_account ON transactions(account_id);
CREATE INDEX idx_transactions_type ON transactions(transaction_type);
CREATE INDEX idx_transactions_status ON transactions(status);
CREATE INDEX idx_transactions_category ON transactions(category);
CREATE INDEX idx_transactions_date ON transactions(created_at);

-- Create tenant-aware indexes for fees
CREATE INDEX idx_fees_tenant ON fees(tenant_type, tenant_id);
CREATE INDEX idx_fees_type ON fees(fee_type);
CREATE INDEX idx_fees_status ON fees(status);
CREATE INDEX idx_fees_transaction ON fees(transaction_id);
CREATE INDEX idx_fees_account ON fees(account_id);

-- Create tenant-aware indexes for budgets
CREATE INDEX idx_budgets_tenant ON budgets(tenant_type, tenant_id);
CREATE INDEX idx_budgets_active ON budgets(is_active);
CREATE INDEX idx_budgets_dates ON budgets(start_date, end_date);
"""

# Migration 005: Add constraints and triggers
MIGRATION_005_CONSTRAINTS = """
-- Add check constraints for tenant types
ALTER TABLE accounts ADD CONSTRAINT chk_accounts_tenant_type 
    CHECK (tenant_type IN ('user', 'organization'));
    
ALTER TABLE transactions ADD CONSTRAINT chk_transactions_tenant_type 
    CHECK (tenant_type IN ('user', 'organization'));
    
ALTER TABLE fees ADD CONSTRAINT chk_fees_tenant_type 
    CHECK (tenant_type IN ('user', 'organization'));
    
ALTER TABLE budgets ADD CONSTRAINT chk_budgets_tenant_type 
    CHECK (tenant_type IN ('user', 'organization'));

-- Add check constraints for roles
ALTER TABLE user_organization_link ADD CONSTRAINT chk_user_org_role
    CHECK (role IN ('owner', 'admin', 'member'));

-- Add check constraints for currencies
ALTER TABLE accounts ADD CONSTRAINT chk_accounts_currency_length
    CHECK (LENGTH(currency) = 3);
    
ALTER TABLE transactions ADD CONSTRAINT chk_transactions_currency_length
    CHECK (LENGTH(currency) = 3);
    
ALTER TABLE fees ADD CONSTRAINT chk_fees_currency_length
    CHECK (LENGTH(currency) = 3);
    
ALTER TABLE budgets ADD CONSTRAINT chk_budgets_currency_length
    CHECK (LENGTH(currency) = 3);

-- Add updated_at trigger function (if not exists)
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers for updated_at
CREATE TRIGGER trigger_accounts_updated_at
    BEFORE UPDATE ON accounts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_transactions_updated_at
    BEFORE UPDATE ON transactions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_fees_updated_at
    BEFORE UPDATE ON fees
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_budgets_updated_at
    BEFORE UPDATE ON budgets
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_organizations_updated_at
    BEFORE UPDATE ON organizations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
"""

# Rollback scripts
ROLLBACK_MIGRATIONS = """
-- Rollback Migration 005: Remove constraints and triggers
DROP TRIGGER IF EXISTS trigger_budgets_updated_at ON budgets;
DROP TRIGGER IF EXISTS trigger_fees_updated_at ON fees;
DROP TRIGGER IF EXISTS trigger_transactions_updated_at ON transactions;
DROP TRIGGER IF EXISTS trigger_accounts_updated_at ON accounts;
DROP TRIGGER IF EXISTS trigger_organizations_updated_at ON organizations;

ALTER TABLE budgets DROP CONSTRAINT IF EXISTS chk_budgets_currency_length;
ALTER TABLE fees DROP CONSTRAINT IF EXISTS chk_fees_currency_length;
ALTER TABLE transactions DROP CONSTRAINT IF EXISTS chk_transactions_currency_length;
ALTER TABLE accounts DROP CONSTRAINT IF EXISTS chk_accounts_currency_length;
ALTER TABLE user_organization_link DROP CONSTRAINT IF EXISTS chk_user_org_role;
ALTER TABLE budgets DROP CONSTRAINT IF EXISTS chk_budgets_tenant_type;
ALTER TABLE fees DROP CONSTRAINT IF EXISTS chk_fees_tenant_type;
ALTER TABLE transactions DROP CONSTRAINT IF EXISTS chk_transactions_tenant_type;
ALTER TABLE accounts DROP CONSTRAINT IF EXISTS chk_accounts_tenant_type;

-- Rollback Migration 004: Remove indexes
DROP INDEX IF EXISTS idx_budgets_dates;
DROP INDEX IF EXISTS idx_budgets_active;
DROP INDEX IF EXISTS idx_budgets_tenant;
DROP INDEX IF EXISTS idx_fees_account;
DROP INDEX IF EXISTS idx_fees_transaction;
DROP INDEX IF EXISTS idx_fees_status;
DROP INDEX IF EXISTS idx_fees_type;
DROP INDEX IF EXISTS idx_fees_tenant;
DROP INDEX IF EXISTS idx_transactions_date;
DROP INDEX IF EXISTS idx_transactions_category;
DROP INDEX IF EXISTS idx_transactions_status;
DROP INDEX IF EXISTS idx_transactions_type;
DROP INDEX IF EXISTS idx_transactions_account;
DROP INDEX IF EXISTS idx_transactions_tenant;
DROP INDEX IF EXISTS idx_accounts_balance;
DROP INDEX IF EXISTS idx_accounts_active;
DROP INDEX IF EXISTS idx_accounts_type;
DROP INDEX IF EXISTS idx_accounts_tenant;

-- Rollback Migration 003: Remove financial tables
DROP TABLE IF EXISTS budgets;
DROP TABLE IF EXISTS fees;
DROP TABLE IF EXISTS transactions;
DROP TABLE IF EXISTS accounts;

-- Rollback Migration 002: Remove user-organization link table
DROP INDEX IF EXISTS idx_user_org_link_role;
DROP INDEX IF EXISTS idx_user_org_link_org_id;
DROP INDEX IF EXISTS idx_user_org_link_user_id;
DROP TABLE IF EXISTS user_organization_link;

-- Rollback Migration 001: Remove organizations table
DROP INDEX IF EXISTS idx_organizations_name;
DROP TABLE IF EXISTS organizations;
"""

def print_migration_sql():
    """Print all migration SQL commands."""
    print("-- Migration 001: Organizations table")
    print(MIGRATION_001_ORGANIZATIONS)
    print()
    
    print("-- Migration 002: User-Organization link table")
    print(MIGRATION_002_USER_ORG_LINK)
    print()
    
    print("-- Migration 003: Financial tables")
    print(MIGRATION_003_FINANCIAL_TABLES)
    print()
    
    print("-- Migration 004: Indexes")
    print(MIGRATION_004_INDEXES)
    print()
    
    print("-- Migration 005: Constraints and triggers")
    print(MIGRATION_005_CONSTRAINTS)

def print_rollback_sql():
    """Print rollback SQL commands."""
    print("-- Rollback all migrations")
    print(ROLLBACK_MIGRATIONS)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "rollback":
        print_rollback_sql()
    else:
        print_migration_sql()