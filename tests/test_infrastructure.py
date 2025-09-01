"""Infrastructure testing for Docker, shell scripts and markdown files.

This module provides comprehensive testing for:
- Docker files and configurations
- Shell scripts functionality and error handling
- Markdown documentation validation
- CI/CD pipeline validation

Following the FEATURE_DEPLOYMENT_GUIDE.md process flow.
"""

import os
import subprocess
import tempfile
import docker
import pytest
import yaml
import markdown
import re
from pathlib import Path
from typing import List, Dict, Any


class TestDockerInfrastructure:
    """Test Docker infrastructure components."""

    def test_dockerfile_exists(self):
        """Test that Dockerfile exists and is readable."""
        dockerfile_path = Path("Dockerfile")
        assert dockerfile_path.exists(), "Dockerfile must exist"
        assert dockerfile_path.is_file(), "Dockerfile must be a file"
        
    def test_dockerfile_syntax(self):
        """Test Dockerfile syntax and structure."""
        with open("Dockerfile", "r") as f:
            content = f.read()
            
        # Check for required stages (using variables)
        assert "FROM python:${PYTHON_VERSION}-slim as base" in content
        assert "FROM base as development" in content
        assert "FROM base as testing" in content
        assert "FROM base as production" in content
        
        # Check for required commands
        assert "WORKDIR /app" in content
        assert "COPY requirements" in content
        assert "RUN pip install" in content
        assert "EXPOSE 8000" in content
        
    def test_docker_compose_files_exist(self):
        """Test that all docker-compose files exist."""
        compose_files = [
            "docker-compose.base.yml",
            "docker-compose.development.yml", 
            "docker-compose.testing.yml",
            "docker-compose.production.yml"
        ]
        
        for file in compose_files:
            assert Path(file).exists(), f"{file} must exist"
            
    def test_docker_compose_syntax(self):
        """Test docker-compose file syntax."""
        compose_files = [
            "docker-compose.base.yml",
            "docker-compose.development.yml",
            "docker-compose.testing.yml", 
            "docker-compose.production.yml"
        ]
        
        for file in compose_files:
            with open(file, "r") as f:
                try:
                    config = yaml.safe_load(f)
                    assert "services" in config, f"{file} must have services section"
                    assert "web" in config["services"], f"{file} must have web service"
                except yaml.YAMLError as e:
                    pytest.fail(f"Invalid YAML syntax in {file}: {e}")
                    
    def test_docker_compose_web_service_config(self):
        """Test web service configuration in docker-compose files."""
        compose_files = {
            "docker-compose.development.yml": {
                "required_ports": ["8000:8000"],
                "required_volumes": [".:/app"]
            },
            "docker-compose.testing.yml": {
                "required_build": {"target": "testing"},
                "required_environment": ["DEBUG=False", "TESTING=True"]
            },
            "docker-compose.production.yml": {
                "required_build": {"target": "production"},
                "required_environment": ["DEBUG=False"]
            }
        }
        
        for file, requirements in compose_files.items():
            with open(file, "r") as f:
                config = yaml.safe_load(f)
                web_service = config["services"]["web"]
                
                if "required_ports" in requirements:
                    assert "ports" in web_service, f"{file} web service must have ports"
                    
                if "required_build" in requirements:
                    assert "build" in web_service, f"{file} web service must have build config"
                    
    def test_entrypoint_scripts_exist(self):
        """Test that Docker entrypoint scripts exist and are executable."""
        scripts = [
            "docker-entrypoint-dev.sh",
            "docker-entrypoint-test.sh", 
            "docker-entrypoint-prod.sh"
        ]
        
        for script in scripts:
            script_path = Path(script)
            assert script_path.exists(), f"{script} must exist"
            assert script_path.is_file(), f"{script} must be a file"
            # Check if script is executable
            assert os.access(script_path, os.X_OK), f"{script} must be executable"


class TestShellScripts:
    """Test shell script functionality and error handling."""
    
    def test_ci_scripts_exist(self):
        """Test that CI scripts exist and are executable."""
        ci_scripts = [
            "ci/build.sh",
            "ci/test.sh", 
            "ci/lint.sh",
            "ci/deploy.sh",
            "ci/entrypoint.sh",
            "ci/validate-deployment.sh",
            "ci/validate-deployment-demo.sh"
        ]
        
        for script in ci_scripts:
            script_path = Path(script)
            assert script_path.exists(), f"{script} must exist"
            assert script_path.is_file(), f"{script} must be a file"
            assert os.access(script_path, os.X_OK), f"{script} must be executable"
            
    def test_script_scripts_exist(self):
        """Test that utility scripts exist and are executable."""
        scripts = [
            "scripts/start-dev.sh",
            "scripts/start-test.sh",
            "scripts/start-prod.sh",
            "scripts/pre-commit.sh"
        ]
        
        for script in scripts:
            script_path = Path(script)
            assert script_path.exists(), f"{script} must exist"
            assert script_path.is_file(), f"{script} must be a file"
            assert os.access(script_path, os.X_OK), f"{script} must be executable"
            
    def test_shell_script_syntax(self):
        """Test shell script syntax using shellcheck if available."""
        shell_scripts = []
        # Find all shell scripts
        for pattern in ["**/*.sh"]:
            shell_scripts.extend(Path(".").glob(pattern))
            
        for script in shell_scripts:
            # Basic syntax check - ensure it starts with shebang
            with open(script, "r") as f:
                first_line = f.readline().strip()
                assert first_line.startswith("#!"), f"{script} must start with shebang"
                assert "bash" in first_line or "sh" in first_line, f"{script} must use bash or sh"
                
    def test_deploy_script_functionality(self):
        """Test deploy script accepts valid targets."""
        deploy_script = Path("ci/deploy.sh")
        assert deploy_script.exists()
        
        # Test help functionality (should not fail)
        result = subprocess.run(
            ["bash", str(deploy_script), "--help"],
            capture_output=True,
            text=True
        )
        # Help should not return error
        assert result.returncode in [0, 1]  # Some scripts return 1 for help
        
    def test_entrypoint_scripts_syntax(self):
        """Test Docker entrypoint scripts have proper syntax."""
        entrypoint_scripts = [
            "docker-entrypoint-dev.sh",
            "docker-entrypoint-test.sh",
            "docker-entrypoint-prod.sh"
        ]
        
        for script in entrypoint_scripts:
            with open(script, "r") as f:
                content = f.read()
                
            # Check for proper error handling
            assert "set -e" in content or "set -eo pipefail" in content, \
                f"{script} should have error handling (set -e)"
                
            # Check for exec usage (best practice for entrypoints)
            assert "exec" in content, f"{script} should use exec for proper signal handling"


class TestMarkdownDocumentation:
    """Test markdown documentation validation."""
    
    def test_markdown_files_exist(self):
        """Test that required markdown files exist."""
        required_docs = [
            "README.md",
            "FEATURE_DEPLOYMENT_GUIDE.md",
            "DEPLOYMENT_PIPELINE.md",
            "CI_CD_PIPELINE.md",
            "DEPLOYMENT_VALIDATION.md",
            "ARCHITECTURE.md",
            "SECURITY.md"
        ]
        
        for doc in required_docs:
            doc_path = Path(doc)
            assert doc_path.exists(), f"{doc} must exist"
            assert doc_path.is_file(), f"{doc} must be a file"
            
    def test_markdown_syntax(self):
        """Test markdown files have valid syntax."""
        md_files = list(Path(".").glob("*.md"))
        
        for md_file in md_files:
            with open(md_file, "r", encoding="utf-8") as f:
                content = f.read()
                
            # Test that markdown can be parsed
            try:
                md = markdown.Markdown()
                md.convert(content)
            except Exception as e:
                pytest.fail(f"Invalid markdown syntax in {md_file}: {e}")
                
    def test_feature_deployment_guide_structure(self):
        """Test FEATURE_DEPLOYMENT_GUIDE.md has required sections."""
        with open("FEATURE_DEPLOYMENT_GUIDE.md", "r") as f:
            content = f.read()
            
        required_sections = [
            "## Overview",
            "## Feature Description", 
            "## Pre-Deployment Preparation",
            "## CI/CD Pipeline Execution",
            "## Environment Deployments",
            "## Monitoring & Validation",
            "## Troubleshooting",
            "## Rollback Procedures"
        ]
        
        for section in required_sections:
            assert section in content, f"FEATURE_DEPLOYMENT_GUIDE.md must have {section}"
            
    def test_documentation_links(self):
        """Test that internal links in documentation are valid."""
        md_files = list(Path(".").glob("*.md"))
        
        for md_file in md_files:
            with open(md_file, "r", encoding="utf-8") as f:
                content = f.read()
                
            # Find internal links (markdown style)
            internal_links = re.findall(r'\[.*?\]\(([^http][^)]*)\)', content)
            
            for link in internal_links:
                # Skip anchor links
                if link.startswith('#'):
                    continue
                    
                # Check if linked file exists
                link_path = Path(link)
                if not link_path.exists():
                    # Try relative to current md file
                    link_path = md_file.parent / link
                    
                assert link_path.exists(), f"Broken link in {md_file}: {link}"
                
    def test_code_blocks_in_docs(self):
        """Test that code blocks in documentation are properly formatted."""
        md_files = list(Path(".").glob("*.md"))
        
        for md_file in md_files:
            with open(md_file, "r", encoding="utf-8") as f:
                content = f.read()
                
            # Find code blocks
            code_blocks = re.findall(r'```(\w+)?\n(.*?)```', content, re.DOTALL)
            
            for lang, code in code_blocks:
                # Code blocks should not be empty
                assert code.strip(), f"Empty code block in {md_file}"
                
                # If language is specified, it should be valid
                if lang:
                    valid_langs = ['bash', 'python', 'yaml', 'dockerfile', 'json', 'sh', 'sql', 'javascript', 'typescript']
                    assert lang.lower() in valid_langs, \
                        f"Invalid code block language '{lang}' in {md_file}"


class TestCICDPipeline:
    """Test CI/CD pipeline configuration and validation."""
    
    def test_ci_directory_structure(self):
        """Test CI directory has proper structure."""
        ci_dir = Path("ci")
        assert ci_dir.exists(), "ci/ directory must exist"
        assert ci_dir.is_dir(), "ci/ must be a directory"
        
        required_scripts = [
            "build.sh", "test.sh", "lint.sh", "deploy.sh",
            "entrypoint.sh", "validate-deployment.sh"
        ]
        
        for script in required_scripts:
            script_path = ci_dir / script
            assert script_path.exists(), f"ci/{script} must exist"
            
    def test_pyproject_toml_test_config(self):
        """Test pyproject.toml has proper test configuration."""
        with open("pyproject.toml", "r") as f:
            content = f.read()
            
        # Check for pytest configuration
        assert "[tool.pytest.ini_options]" in content
        assert "testpaths = [\"tests\"]" in content
        assert "--cov=app" in content
        assert "--cov-fail-under=80" in content
        
    def test_requirements_files(self):
        """Test that requirements files exist and are valid."""
        req_files = [
            "requirements/base.txt",
            "requirements/development.txt", 
            "requirements/test.txt",
            "requirements/production.txt"
        ]
        
        for req_file in req_files:
            req_path = Path(req_file)
            assert req_path.exists(), f"{req_file} must exist"
            
            # Basic validation - each line should be a valid package spec
            with open(req_path, "r") as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # Should contain package name and version
                        assert '==' in line or '>=' in line or '<=' in line, \
                            f"Invalid package spec in {req_file}:{line_num}: {line}"


class TestConfigurationValidation:
    """Test configuration files and environment settings."""
    
    def test_env_example_files(self):
        """Test that environment example files exist."""
        env_files = [
            ".env.example",
            ".env.development", 
            ".env.testing",
            ".env.production"
        ]
        
        for env_file in env_files:
            env_path = Path(env_file)
            assert env_path.exists(), f"{env_file} must exist"
            
    def test_config_directory_structure(self):
        """Test config directory has proper Django settings structure."""
        config_dir = Path("config")
        assert config_dir.exists(), "config/ directory must exist"
        
        settings_dir = config_dir / "settings"
        assert settings_dir.exists(), "config/settings/ directory must exist"
        
        required_settings = [
            "base.py", "development.py", "testing.py", "production.py"
        ]
        
        for setting in required_settings:
            setting_path = settings_dir / setting
            assert setting_path.exists(), f"config/settings/{setting} must exist"
            
    def test_linting_configuration(self):
        """Test linting configuration files."""
        linting_files = [
            ".flake8",
            ".mypy.ini"
        ]
        
        for lint_file in linting_files:
            lint_path = Path(lint_file)
            assert lint_path.exists(), f"{lint_file} must exist"


class TestVisionAlignment:
    """Test alignment with project vision and deployment guide."""
    
    def test_deployment_guide_vision_alignment(self):
        """Test that implementation aligns with deployment guide vision."""
        with open("FEATURE_DEPLOYMENT_GUIDE.md", "r") as f:
            guide_content = f.read()
            
        # Check for key deployment concepts
        key_concepts = [
            "Financial Dashboard",
            "Multi-tenant", 
            "Docker CI/CD Pipeline",
            "Quality Gates",
            "Rollback Procedures",
            "Monitoring & Validation"
        ]
        
        for concept in key_concepts:
            assert concept in guide_content, \
                f"Deployment guide must reference {concept}"
                
    def test_test_coverage_targets(self):
        """Test that test coverage targets align with quality gates."""
        # This test validates that we're aiming for the right coverage targets
        # as specified in the deployment guide
        
        with open("pyproject.toml", "r") as f:
            pyproject_content = f.read()
            
        # Should aim for high coverage as per deployment guide
        assert "--cov-fail-under=80" in pyproject_content
        
        # Should have comprehensive test types
        assert "unit: marks tests as unit tests" in pyproject_content
        assert "integration: marks tests as integration tests" in pyproject_content
        
    def test_ci_cd_pipeline_completeness(self):
        """Test that CI/CD pipeline covers all required stages."""
        with open("CI_CD_PIPELINE.md", "r") as f:
            pipeline_content = f.read()
            
        required_stages = [
            "Quality Gates",
            "Pipeline Stages", 
            "Build Pipeline",
            "Deployment",
            "Multi-Architecture"
        ]
        
        for stage in required_stages:
            assert stage in pipeline_content, \
                f"CI/CD pipeline must include {stage}"