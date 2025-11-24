# Contributing to Financial Stronghold

Thank you for your interest in contributing to Financial Stronghold! This document provides guidelines and best practices for contributing to the project.

---

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Workflow](#development-workflow)
4. [Coding Standards](#coding-standards)
5. [Testing Requirements](#testing-requirements)
6. [Documentation](#documentation)
7. [Pull Request Process](#pull-request-process)
8. [Security](#security)
9. [Getting Help](#getting-help)

---

## Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inclusive environment for all contributors, regardless of background or identity.

### Our Standards

**Examples of behavior that contributes to a positive environment:**
- Using welcoming and inclusive language
- Being respectful of differing viewpoints
- Gracefully accepting constructive criticism
- Focusing on what is best for the community
- Showing empathy towards other community members

**Examples of unacceptable behavior:**
- Use of sexualized language or imagery
- Trolling, insulting/derogatory comments, or personal attacks
- Public or private harassment
- Publishing others' private information without permission
- Other conduct which could reasonably be considered inappropriate

### Enforcement

Instances of abusive, harassing, or otherwise unacceptable behavior may be reported to the project team. All complaints will be reviewed and investigated promptly and fairly.

---

## Getting Started

### Prerequisites

Before contributing, ensure you have:

- Python 3.12.3 installed
- Docker and Docker Compose
- Git configured with your name and email
- A GitHub account

### Fork and Clone

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/financial_stronghold.git
   cd financial_stronghold
   ```

3. **Add upstream remote:**
   ```bash
   git remote add upstream https://github.com/nullroute-commits/financial_stronghold.git
   ```

4. **Verify remotes:**
   ```bash
   git remote -v
   # origin    https://github.com/YOUR_USERNAME/financial_stronghold.git (fetch)
   # origin    https://github.com/YOUR_USERNAME/financial_stronghold.git (push)
   # upstream  https://github.com/nullroute-commits/financial_stronghold.git (fetch)
   # upstream  https://github.com/nullroute-commits/financial_stronghold.git (push)
   ```

### Set Up Development Environment

```bash
# Start development environment
./scripts/start-dev.sh

# Or manually with Docker Compose
docker-compose -f docker-compose.development.yml up -d
```

---

## Development Workflow

### 1. Create a Branch

Always create a new branch for your work:

```bash
# Update your local main branch
git checkout main
git pull upstream main

# Create feature branch
git checkout -b feature/your-feature-name

# Or for bug fixes
git checkout -b fix/bug-description
```

**Branch Naming Conventions:**
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation changes
- `refactor/` - Code refactoring
- `test/` - Test additions or modifications
- `chore/` - Maintenance tasks

### 2. Make Changes

Make your changes following our [coding standards](#coding-standards).

```bash
# View changed files
git status

# View changes
git diff
```

### 3. Run Tests

Before committing, ensure tests pass:

```bash
# Run all tests
pytest

# Run specific tests
pytest tests/test_models.py

# Run with coverage
pytest --cov=app

# Run linting
black app/ config/ --check
flake8 app/ config/
mypy app/ config/
```

### 4. Commit Changes

Write clear, descriptive commit messages:

```bash
# Stage changes
git add .

# Commit with descriptive message
git commit -m "Add user profile API endpoint"
```

**Commit Message Guidelines:**

```
<type>: <subject>

<body>

<footer>
```

**Types:**
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `style:` - Code style changes (formatting, etc.)
- `refactor:` - Code refactoring
- `test:` - Test additions or modifications
- `chore:` - Maintenance tasks

**Example:**
```
feat: Add transaction import from CSV

- Implement CSV parser for transaction data
- Add validation for required fields
- Include error handling for malformed files

Closes #123
```

### 5. Push Changes

```bash
# Push to your fork
git push origin feature/your-feature-name
```

### 6. Create Pull Request

1. Go to your fork on GitHub
2. Click "New Pull Request"
3. Select your branch
4. Fill in the PR template
5. Submit the PR

---

## Coding Standards

### Python Style Guide

We follow [PEP 8](https://pep8.org/) with some modifications:

- **Line Length:** 120 characters maximum
- **Indentation:** 4 spaces (no tabs)
- **Quotes:** Double quotes for strings, single for dictionary keys
- **Imports:** Organized by type (standard library, third-party, local)

### Code Formatting

Use [Black](https://black.readthedocs.io/) for code formatting:

```bash
# Format code
black app/ config/ --line-length 120

# Check formatting
black app/ config/ --check --line-length 120
```

### Linting

Use [Flake8](https://flake8.pycqa.org/) for linting:

```bash
# Run linter
flake8 app/ config/ --max-line-length=120

# Configuration in .flake8 or pyproject.toml
```

### Type Hints

Use type hints for function signatures:

```python
from typing import List, Optional
from decimal import Decimal

def calculate_total(amounts: List[Decimal], discount: Optional[Decimal] = None) -> Decimal:
    """Calculate total with optional discount."""
    total = sum(amounts)
    if discount:
        total -= discount
    return total
```

Verify types with [MyPy](http://mypy-lang.org/):

```bash
# Type check
mypy app/ config/
```

### Docstrings

Use Google-style docstrings:

```python
def import_transactions(file_path: str, user_id: int) -> dict:
    """
    Import transactions from a file.

    Args:
        file_path: Path to the file containing transactions
        user_id: ID of the user importing transactions

    Returns:
        Dictionary containing import statistics:
        {
            'total': int,
            'successful': int,
            'failed': int,
            'errors': List[str]
        }

    Raises:
        FileNotFoundError: If file_path doesn't exist
        ValidationError: If file format is invalid

    Example:
        >>> result = import_transactions('/path/to/file.csv', user_id=1)
        >>> print(result['successful'])
        150
    """
    # Implementation
    pass
```

### Import Organization

Organize imports in this order:

```python
# 1. Standard library imports
import os
import sys
from typing import List, Optional

# 2. Third-party imports
import django
from rest_framework import viewsets

# 3. Local application imports
from app.models import Transaction
from app.services import ImportService
```

Use [isort](https://pycqa.github.io/isort/) for automatic organization:

```bash
# Sort imports
isort app/ config/

# Check import sorting
isort app/ config/ --check
```

### Code Comments

- Write self-documenting code when possible
- Use comments to explain **why**, not **what**
- Keep comments up-to-date with code changes

**Good:**
```python
# Apply discount only for premium users to maintain subscription incentive
if user.is_premium:
    total = apply_discount(total, user.discount_rate)
```

**Bad:**
```python
# Check if user is premium
if user.is_premium:
    # Apply discount
    total = apply_discount(total, user.discount_rate)
```

### Error Handling

Always handle exceptions appropriately:

```python
from django.core.exceptions import ValidationError
import logging

logger = logging.getLogger(__name__)

def process_transaction(transaction_data: dict) -> Transaction:
    """Process and save a transaction."""
    try:
        # Validate data
        validate_transaction_data(transaction_data)
        
        # Create transaction
        transaction = Transaction.objects.create(**transaction_data)
        
        logger.info(f"Transaction {transaction.id} created successfully")
        return transaction
        
    except ValidationError as e:
        logger.error(f"Validation error: {e}")
        raise
        
    except Exception as e:
        logger.exception("Unexpected error processing transaction")
        raise
```

---

## Testing Requirements

All contributions must include tests. We aim for 85% code coverage minimum.

### Writing Tests

```python
import pytest
from app.models import Transaction


class TestTransaction:
    """Test Transaction model."""
    
    def test_create_transaction(self, user, account):
        """Test creating a transaction."""
        transaction = Transaction.objects.create(
            user=user,
            account=account,
            description="Test transaction",
            amount=100.00,
            date="2025-11-24"
        )
        
        assert transaction.user == user
        assert transaction.amount == 100.00
        assert transaction.description == "Test transaction"
    
    def test_negative_amount_is_debit(self):
        """Test that negative amounts are marked as debit."""
        transaction = Transaction(amount=-50.00)
        assert transaction.is_debit is True
    
    @pytest.mark.parametrize('amount,expected_type', [
        (100.00, 'CREDIT'),
        (-100.00, 'DEBIT'),
        (0.00, 'ZERO'),
    ])
    def test_transaction_type_detection(self, amount, expected_type):
        """Test transaction type is correctly detected."""
        transaction = Transaction(amount=amount)
        assert transaction.get_type() == expected_type
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_models.py

# Run specific test
pytest tests/test_models.py::TestTransaction::test_create_transaction

# Run with coverage
pytest --cov=app --cov-report=html

# Run only fast tests
pytest -m "not slow"

# Run in parallel
pytest -n auto
```

### Test Requirements

- **Unit Tests:** For new models, services, utilities
- **Integration Tests:** For new API endpoints
- **Security Tests:** For authentication/authorization changes
- **Performance Tests:** For performance-critical features

See [Testing Guide](docs/TESTING_GUIDE.md) for detailed information.

---

## Documentation

### When to Update Documentation

Update documentation when:
- Adding new features
- Changing API endpoints
- Modifying configuration
- Fixing bugs that affect user experience
- Changing deployment procedures

### Documentation Standards

**API Endpoints:**
```markdown
### Create Transaction

**Endpoint:** `POST /api/v1/transactions/`

**Request:**
```json
{
  "account": "account-uuid",
  "description": "Coffee Shop",
  "amount": -5.50,
  "date": "2025-11-24"
}
```

**Response (201 Created):**
```json
{
  "id": "transaction-uuid",
  "account": "account-uuid",
  "description": "Coffee Shop",
  "amount": "-5.50",
  "date": "2025-11-24",
  "created_at": "2025-11-24T08:00:00Z"
}
```
```

**Code Examples:**
```python
# Always include working code examples
from app.models import Transaction

# Create a transaction
transaction = Transaction.objects.create(
    user=user,
    description="Sample transaction",
    amount=100.00
)
```

### Building Documentation

```bash
# Build docs locally
./scripts/build_docs.sh

# Or manually
mkdocs build

# Serve docs locally
mkdocs serve
# Visit http://localhost:8000
```

---

## Pull Request Process

### Before Submitting

Ensure your PR:
- [ ] Passes all tests (`pytest`)
- [ ] Meets code coverage requirements (≥85%)
- [ ] Follows coding standards (`black`, `flake8`, `mypy`)
- [ ] Includes appropriate tests
- [ ] Updates relevant documentation
- [ ] Has a clear, descriptive title
- [ ] References related issues

### PR Template

When creating a PR, fill out the template:

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] All tests passing locally

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex logic
- [ ] Documentation updated
- [ ] No new warnings generated

## Related Issues
Fixes #123
Related to #456
```

### Review Process

1. **Automated Checks**
   - CI/CD pipeline runs automatically
   - All checks must pass

2. **Code Review**
   - At least one approval required
   - Address reviewer feedback
   - Update PR as needed

3. **Merge**
   - Maintainer will merge when approved
   - PR will be squashed into a single commit

### After Merge

- Delete your feature branch
- Update your local main branch
- Close related issues

---

## Security

### Reporting Security Issues

**DO NOT** create public GitHub issues for security vulnerabilities.

Instead, report security concerns through GitHub's Security Advisory feature:
1. Go to https://github.com/nullroute-commits/financial_stronghold/security/advisories
2. Click "New draft security advisory"
3. Provide details about the vulnerability

Or create a private security vulnerability report at:
https://github.com/nullroute-commits/financial_stronghold/security/advisories/new

Include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

### Security Best Practices

When contributing:
- Never commit secrets or credentials
- Use environment variables for configuration
- Validate and sanitize all user input
- Follow Django security best practices
- Keep dependencies up-to-date

---

## Getting Help

### Resources

- **Documentation:** Check docs/ directory
- **Wiki:** Browse project wiki
- **Issues:** Search existing issues
- **Discussions:** Ask questions in discussions

### Communication Channels

- **GitHub Issues:** Bug reports and feature requests
- **GitHub Discussions:** General questions and discussions
- **Pull Requests:** Code reviews and feedback

### Questions?

If you have questions:
1. Check existing documentation
2. Search closed issues
3. Ask in GitHub Discussions
4. Create a new issue with `question` label

---

## Recognition

We value all contributions! Contributors will be:
- Listed in release notes
- Mentioned in commit messages (Co-authored-by)
- Recognized in project documentation

---

## License

By contributing to Financial Stronghold, you agree that your contributions will be licensed under the MIT License.

---

**Thank you for contributing to Financial Stronghold! 🙏**

---

**Last Updated:** 2025-11-24  
**Version:** 1.0
