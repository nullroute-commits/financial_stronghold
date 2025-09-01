"""
Unit tests for Copilot Instructions Service.

Tests the loading, parsing, and processing of copilot-instructions.md file.
"""

import pytest
import tempfile
import json
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, mock_open

from app.services.copilot_service import (
    CopilotInstructionsService,
    CopilotInstructions,
    WorkflowStep,
    ConfigurationItem
)


class TestCopilotInstructionsService:
    """Test cases for CopilotInstructionsService."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.sample_markdown = """# GitHub Copilot Instructions for Financial Stronghold

**Project**: Django 5 Multi-Architecture CI/CD Pipeline - Financial Stronghold  
**Last Updated**: 2024-12-19  
**SOP Compliance**: Following FEATURE_DEPLOYMENT_GUIDE.md containerized development process  

## Repository Overview

### Project Description
Financial Stronghold is a production-ready multi-tenant Django 5 application with comprehensive financial management capabilities.

### Key Features
- **Django 5.1.10** with Python 3.12.5
- **Multi-tenant architecture** with user and organization scoping
- **PostgreSQL 17.2** database with SQLAlchemy 1.4.49 ORM

### Repository Structure
```
financial_stronghold/
├── app/                          # Main application code
│   ├── api.py                    # FastAPI endpoints
│   ├── auth.py                   # Authentication & authorization
└── docker-compose.*.yml          # Environment-specific Docker configs
```

## Architecture & Technology Stack

### Core Technologies
- **Backend Framework**: Django 5.1.10 + FastAPI
- **Database**: PostgreSQL 17.2 with SQLAlchemy 1.4.49
- **Cache**: Memcached 1.6.22 for high-performance caching

## Development Workflow & SOP

#### 1. Pre-Deployment Preparation
```bash
# Environment verification
docker --version  # >= 24.0.7
docker compose --version  # >= 2.18.1
```

#### 2. Code Quality Gates
```bash
# Format code
black app/ --line-length 120 --target-version py312
# Lint code
flake8 app/ --max-line-length=120 --ignore=E203,W503
```

## Configuration Management

### Environment Files
```bash
# environments/.env.development.example
DEBUG=True
DJANGO_SETTINGS_MODULE=config.settings.development
SECRET_KEY=dev-secret-key
```

## Code Quality Standards

### Linting Configuration
```ini
# .flake8
[flake8]
max-line-length = 120
ignore = E203, W503
```

## Deployment Strategies
- **Blue-Green Deployment**: Zero-downtime deployments
- **Rolling Updates**: Gradual service updates

## Critical Guidelines for GitHub Copilot

### 🚨 **ALWAYS Follow These Patterns**

1. **Multi-Tenant Context**: Every database operation MUST include tenant scoping
2. **Authentication Required**: All API endpoints MUST use tenant context dependency
"""
    
    def test_service_initialization(self):
        """Test service initialization with default and custom paths."""
        # Default initialization
        service = CopilotInstructionsService()
        assert service.instructions_path.name == "copilot-instructions.md"
        
        # Custom path initialization
        custom_path = "/custom/path/instructions.md"
        service_custom = CopilotInstructionsService(custom_path)
        assert str(service_custom.instructions_path) == custom_path
    
    def test_load_instructions_file_not_found(self):
        """Test handling of missing instructions file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            non_existent_path = Path(temp_dir) / "missing.md"
            service = CopilotInstructionsService(str(non_existent_path))
            
            with pytest.raises(FileNotFoundError):
                service.load_instructions()
    
    def test_load_instructions_success(self):
        """Test successful loading and parsing of instructions."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as temp_file:
            temp_file.write(self.sample_markdown)
            temp_file.flush()
            
            service = CopilotInstructionsService(temp_file.name)
            instructions = service.load_instructions()
            
            # Verify basic metadata
            assert instructions.project_name == "Financial Stronghold"
            assert instructions.last_updated == "2024-12-19"
            assert instructions.version == "5.1.10"
            assert isinstance(instructions.loaded_at, datetime)
            
            # Verify parsed content
            assert len(instructions.key_features) == 3
            assert len(instructions.technology_stack) == 3
            assert len(instructions.workflow_steps) == 2
            assert len(instructions.critical_guidelines) >= 1  # At least 1 guideline
            
            # Clean up
            Path(temp_file.name).unlink()
    
    def test_caching_behavior(self):
        """Test that instructions are cached on subsequent loads."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as temp_file:
            temp_file.write(self.sample_markdown)
            temp_file.flush()
            
            service = CopilotInstructionsService(temp_file.name)
            
            # First load
            instructions1 = service.load_instructions()
            
            # Second load (should use cache)
            instructions2 = service.load_instructions()
            
            # Should be the same object (cached)
            assert instructions1 is instructions2
            
            # Force reload should create new instance
            instructions3 = service.load_instructions(force_reload=True)
            assert instructions1 is not instructions3
            assert instructions1.project_name == instructions3.project_name
            
            # Clean up
            Path(temp_file.name).unlink()
    
    def test_extract_project_name(self):
        """Test project name extraction."""
        service = CopilotInstructionsService()
        
        # Test with full title
        content = "# GitHub Copilot Instructions for Test Project\n"
        name = service._extract_project_name(content)
        assert name == "Test Project"
        
        # Test with simple title
        content = "# Simple Project\n"
        name = service._extract_project_name(content)
        assert name == "Simple Project"
        
        # Test with no title
        content = "No title here"
        name = service._extract_project_name(content)
        assert name == "Unknown Project"
    
    def test_extract_key_features(self):
        """Test key features extraction."""
        service = CopilotInstructionsService()
        
        content = """
### Key Features
- **Feature 1**: Description 1
- **Feature 2**: Description 2
- **Feature 3**: Description 3
"""
        features = service._extract_key_features(content)
        assert len(features) == 3
        assert "**Feature 1**: Description 1" in features
        assert "**Feature 2**: Description 2" in features
    
    def test_extract_technology_stack(self):
        """Test technology stack extraction."""
        service = CopilotInstructionsService()
        
        content = """
### Core Technologies
- **Backend**: Django 5.1.10
- **Database**: PostgreSQL 17.2
- **Cache**: Redis 6.2
"""
        stack = service._extract_technology_stack(content)
        assert len(stack) == 3
        assert stack["Backend"] == "Django 5.1.10"
        assert stack["Database"] == "PostgreSQL 17.2"
        assert stack["Cache"] == "Redis 6.2"
    
    def test_extract_workflow_steps(self):
        """Test workflow steps extraction."""
        service = CopilotInstructionsService()
        
        content = """
#### 1. Pre-Deployment Preparation
```bash
# Environment verification
docker --version
python --version
```

#### 2. Code Quality Gates
```bash
# Format code
black app/
# Lint code
flake8 app/
```
"""
        steps = service._extract_workflow_steps(content)
        assert len(steps) == 2
        
        prep_step = next(s for s in steps if s.name == "Pre-Deployment Preparation")
        assert prep_step.category == "preparation"
        assert len(prep_step.commands) == 2
        assert "docker --version" in prep_step.commands
        
        quality_step = next(s for s in steps if s.name == "Code Quality Gates")
        assert quality_step.category == "quality"
        assert len(quality_step.commands) == 2
        assert "black app/" in quality_step.commands
    
    def test_extract_configuration_items(self):
        """Test configuration items extraction."""
        service = CopilotInstructionsService()
        
        content = """
```bash
# environments/.env.development.example
DEBUG=True
DJANGO_SETTINGS_MODULE=config.settings.development
SECRET_KEY=dev-secret-key
DATABASE_URL=postgresql://localhost/test
```
"""
        configs = service._extract_configuration_items(content)
        assert len(configs) == 4
        
        debug_config = next(c for c in configs if c.key == "DEBUG")
        assert debug_config.value == "True"
        assert debug_config.environment == "development"
        assert debug_config.required is True  # DEBUG is in required list
        
        db_config = next(c for c in configs if c.key == "DATABASE_URL")
        assert db_config.value == "postgresql://localhost/test"
        assert db_config.required is False
    
    def test_get_commands_by_category(self):
        """Test retrieving commands by category."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as temp_file:
            temp_file.write(self.sample_markdown)
            temp_file.flush()
            
            service = CopilotInstructionsService(temp_file.name)
            
            # Get preparation commands
            prep_commands = service.get_commands_by_category("preparation")
            assert len(prep_commands) == 2
            assert "docker --version  # >= 24.0.7" in prep_commands
            
            # Get quality commands
            quality_commands = service.get_commands_by_category("quality")
            assert len(quality_commands) == 2
            assert "black app/ --line-length 120 --target-version py312" in quality_commands
            
            # Get non-existent category
            missing_commands = service.get_commands_by_category("nonexistent")
            assert len(missing_commands) == 0
            
            # Clean up
            Path(temp_file.name).unlink()
    
    def test_validate_current_setup(self):
        """Test project setup validation."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as temp_file:
            temp_file.write(self.sample_markdown)
            temp_file.flush()
            
            service = CopilotInstructionsService(temp_file.name)
            validation_results = service.validate_current_setup()
            
            # Check structure
            assert "files_exist" in validation_results
            assert "configurations_match" in validation_results
            assert "overall_status" in validation_results
            
            # Check that some key files are checked
            files_checked = validation_results["files_exist"]
            assert "requirements/base.txt" in files_checked
            assert "manage.py" in files_checked
            assert ".flake8" in files_checked
            
            # Clean up
            Path(temp_file.name).unlink()
    
    def test_to_dict_and_json(self):
        """Test dictionary and JSON conversion."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as temp_file:
            temp_file.write(self.sample_markdown)
            temp_file.flush()
            
            service = CopilotInstructionsService(temp_file.name)
            
            # Test dictionary conversion
            data_dict = service.to_dict()
            assert isinstance(data_dict, dict)
            assert "project_name" in data_dict
            assert "workflow_steps" in data_dict
            assert data_dict["project_name"] == "Financial Stronghold"
            
            # Test JSON conversion
            json_str = service.to_json()
            parsed_json = json.loads(json_str)
            assert isinstance(parsed_json, dict)
            assert parsed_json["project_name"] == "Financial Stronghold"
            assert "loaded_at" in parsed_json
            
            # Clean up
            Path(temp_file.name).unlink()
    
    def test_error_handling_invalid_content(self):
        """Test handling of invalid or malformed content."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as temp_file:
            # Write minimal content that might cause parsing issues
            temp_file.write("# Minimal Content\nNot much here.")
            temp_file.flush()
            
            service = CopilotInstructionsService(temp_file.name)
            instructions = service.load_instructions()
            
            # Should handle gracefully with defaults
            assert instructions.project_name == "Minimal Content"
            assert instructions.version == "Unknown"
            assert len(instructions.key_features) == 0
            assert len(instructions.workflow_steps) == 0
            
            # Clean up
            Path(temp_file.name).unlink()


class TestDataClasses:
    """Test the data classes used by the service."""
    
    def test_workflow_step_creation(self):
        """Test WorkflowStep data class."""
        step = WorkflowStep(
            name="Test Step",
            commands=["cmd1", "cmd2"],
            description="Test description",
            category="test"
        )
        
        assert step.name == "Test Step"
        assert len(step.commands) == 2
        assert step.category == "test"
    
    def test_configuration_item_creation(self):
        """Test ConfigurationItem data class."""
        config = ConfigurationItem(
            key="TEST_KEY",
            value="test_value",
            description="Test config",
            environment="test",
            required=True
        )
        
        assert config.key == "TEST_KEY"
        assert config.required is True
        assert config.environment == "test"
    
    def test_copilot_instructions_creation(self):
        """Test CopilotInstructions data class."""
        now = datetime.utcnow()
        instructions = CopilotInstructions(
            project_name="Test Project",
            last_updated="2024-01-01",
            version="1.0.0",
            description="Test description",
            key_features=["Feature 1", "Feature 2"],
            technology_stack={"tech1": "desc1"},
            repository_structure={"dir1": "desc1"},
            workflow_steps=[],
            configuration_items=[],
            code_quality_standards={},
            deployment_strategies=[],
            troubleshooting_items=[],
            critical_guidelines=[],
            loaded_at=now
        )
        
        assert instructions.project_name == "Test Project"
        assert instructions.version == "1.0.0"
        assert len(instructions.key_features) == 2
        assert instructions.loaded_at == now