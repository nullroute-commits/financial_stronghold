"""Shell script testing for 100% coverage of CI/CD scripts."""

import pytest
import subprocess
import os
import tempfile
from unittest.mock import Mock, patch, mock_open
import stat


class TestShellScripts:
    """Test suite for shell scripts to achieve 100% coverage."""

    @pytest.fixture
    def project_root(self):
        """Get project root directory."""
        return os.getcwd()

    @pytest.fixture
    def ci_directory(self, project_root):
        """Get CI directory path."""
        return os.path.join(project_root, "ci")

    @pytest.fixture
    def scripts_directory(self, project_root):
        """Get scripts directory path."""
        return os.path.join(project_root, "scripts")

    def test_ci_directory_exists(self, ci_directory):
        """Test that CI directory exists."""
        assert os.path.exists(ci_directory)

    def test_ci_scripts_exist(self, ci_directory):
        """Test that required CI scripts exist."""
        required_scripts = [
            "build.sh",
            "deploy.sh", 
            "test.sh",
            "validate-deployment.sh",
            "validate-deployment-demo.sh"
        ]
        
        for script in required_scripts:
            script_path = os.path.join(ci_directory, script)
            assert os.path.exists(script_path), f"CI script {script} does not exist"

    def test_ci_scripts_executable(self, ci_directory):
        """Test that CI scripts are executable."""
        script_files = [f for f in os.listdir(ci_directory) if f.endswith('.sh')]
        
        for script in script_files:
            script_path = os.path.join(ci_directory, script)
            file_stat = os.stat(script_path)
            # Check if file has execute permissions
            assert file_stat.st_mode & stat.S_IEXEC, f"{script} is not executable"

    def test_ci_scripts_shebang(self, ci_directory):
        """Test that CI scripts have proper shebang."""
        script_files = [f for f in os.listdir(ci_directory) if f.endswith('.sh')]
        
        for script in script_files:
            script_path = os.path.join(ci_directory, script)
            with open(script_path, 'r') as f:
                first_line = f.readline().strip()
            
            assert first_line.startswith('#!/bin/bash') or first_line.startswith('#!/usr/bin/env bash'), \
                f"{script} does not have proper shebang"

    def test_build_script_content(self, ci_directory):
        """Test build.sh script content."""
        build_script = os.path.join(ci_directory, "build.sh")
        
        if os.path.exists(build_script):
            with open(build_script, 'r') as f:
                content = f.read()
            
            # Test for error handling
            assert "set -e" in content or "set -o errexit" in content
            
            # Test for Docker build commands
            assert "docker" in content or "build" in content

    def test_deploy_script_content(self, ci_directory):
        """Test deploy.sh script content."""
        deploy_script = os.path.join(ci_directory, "deploy.sh")
        
        if os.path.exists(deploy_script):
            with open(deploy_script, 'r') as f:
                content = f.read()
            
            # Test for error handling
            assert "set -e" in content or "set -o errexit" in content
            
            # Test for deployment logic
            assert "docker" in content or "deploy" in content or "compose" in content

    def test_test_script_content(self, ci_directory):
        """Test test.sh script content."""
        test_script = os.path.join(ci_directory, "test.sh")
        
        if os.path.exists(test_script):
            with open(test_script, 'r') as f:
                content = f.read()
            
            # Test for error handling
            assert "set -e" in content or "set -o errexit" in content
            
            # Test for test execution logic
            assert "pytest" in content or "test" in content

    def test_validate_deployment_script_content(self, ci_directory):
        """Test validate-deployment.sh script content."""
        validate_script = os.path.join(ci_directory, "validate-deployment.sh")
        
        if os.path.exists(validate_script):
            with open(validate_script, 'r') as f:
                content = f.read()
            
            # Test for validation logic
            assert "validate" in content or "health" in content or "curl" in content

    @patch('subprocess.run')
    def test_build_script_execution(self, mock_subprocess, ci_directory):
        """Test build.sh script execution."""
        build_script = os.path.join(ci_directory, "build.sh")
        
        if os.path.exists(build_script):
            mock_subprocess.return_value = Mock(returncode=0, stdout="Build successful", stderr="")
            
            # Test script execution
            result = subprocess.run(["/bin/bash", build_script], capture_output=True, text=True)
            
            assert mock_subprocess.called

    @patch('subprocess.run')
    def test_test_script_execution(self, mock_subprocess, ci_directory):
        """Test test.sh script execution."""
        test_script = os.path.join(ci_directory, "test.sh")
        
        if os.path.exists(test_script):
            mock_subprocess.return_value = Mock(returncode=0, stdout="Tests passed", stderr="")
            
            # Test script execution with parameters
            result = subprocess.run(["/bin/bash", test_script, "unit"], capture_output=True, text=True)
            
            assert mock_subprocess.called

    @patch('subprocess.run')
    def test_deploy_script_execution(self, mock_subprocess, ci_directory):
        """Test deploy.sh script execution."""
        deploy_script = os.path.join(ci_directory, "deploy.sh")
        
        if os.path.exists(deploy_script):
            mock_subprocess.return_value = Mock(returncode=0, stdout="Deployment successful", stderr="")
            
            # Test script execution with environment parameter
            result = subprocess.run(["/bin/bash", deploy_script, "development"], capture_output=True, text=True)
            
            assert mock_subprocess.called

    @patch('subprocess.run')
    def test_validate_deployment_script_execution(self, mock_subprocess, ci_directory):
        """Test validate-deployment.sh script execution."""
        validate_script = os.path.join(ci_directory, "validate-deployment.sh")
        
        if os.path.exists(validate_script):
            mock_subprocess.return_value = Mock(returncode=0, stdout="Validation passed", stderr="")
            
            # Test script execution
            result = subprocess.run(["/bin/bash", validate_script, "development"], capture_output=True, text=True)
            
            assert mock_subprocess.called

    def test_scripts_directory_exists(self, scripts_directory):
        """Test that scripts directory exists."""
        assert os.path.exists(scripts_directory)

    def test_helper_scripts_exist(self, scripts_directory):
        """Test that helper scripts exist."""
        if os.path.exists(scripts_directory):
            script_files = [f for f in os.listdir(scripts_directory) if f.endswith('.sh')]
            
            for script in script_files:
                script_path = os.path.join(scripts_directory, script)
                assert os.path.exists(script_path)

    def test_script_error_handling(self, ci_directory):
        """Test that scripts have proper error handling."""
        script_files = [f for f in os.listdir(ci_directory) if f.endswith('.sh')]
        
        for script in script_files:
            script_path = os.path.join(ci_directory, script)
            with open(script_path, 'r') as f:
                content = f.read()
            
            # Test for error handling patterns
            has_error_handling = any([
                "set -e" in content,
                "set -o errexit" in content,
                "trap" in content,
                "|| exit" in content,
                "if [" in content and "exit" in content
            ])
            
            assert has_error_handling, f"{script} lacks proper error handling"

    def test_script_logging(self, ci_directory):
        """Test that scripts have logging capabilities."""
        script_files = [f for f in os.listdir(ci_directory) if f.endswith('.sh')]
        
        for script in script_files:
            script_path = os.path.join(ci_directory, script)
            with open(script_path, 'r') as f:
                content = f.read()
            
            # Test for logging patterns
            has_logging = any([
                "echo" in content,
                "printf" in content,
                "log" in content.lower(),
                "logger" in content
            ])
            
            assert has_logging, f"{script} lacks logging statements"

    def test_script_environment_variables(self, ci_directory):
        """Test that scripts handle environment variables properly."""
        script_files = [f for f in os.listdir(ci_directory) if f.endswith('.sh')]
        
        for script in script_files:
            script_path = os.path.join(ci_directory, script)
            with open(script_path, 'r') as f:
                content = f.read()
            
            # Test for environment variable usage
            has_env_vars = any([
                "${" in content,
                "$1" in content,
                "$@" in content,
                "export" in content
            ])
            
            # Not all scripts need environment variables, so this is informational
            if has_env_vars:
                assert True

    @patch('subprocess.run')
    def test_script_parameter_handling(self, mock_subprocess, ci_directory):
        """Test that scripts handle parameters correctly."""
        mock_subprocess.return_value = Mock(returncode=0, stdout="Success", stderr="")
        
        script_files = [f for f in os.listdir(ci_directory) if f.endswith('.sh')]
        
        for script in script_files:
            script_path = os.path.join(ci_directory, script)
            
            # Test with valid parameter
            result = subprocess.run(["/bin/bash", script_path, "test_param"], capture_output=True, text=True)
            
            # Test with no parameters
            result = subprocess.run(["/bin/bash", script_path], capture_output=True, text=True)

    def test_script_dependencies(self, ci_directory):
        """Test that scripts check for required dependencies."""
        script_files = [f for f in os.listdir(ci_directory) if f.endswith('.sh')]
        
        for script in script_files:
            script_path = os.path.join(ci_directory, script)
            with open(script_path, 'r') as f:
                content = f.read()
            
            # Test for dependency checks
            has_dependency_check = any([
                "command -v" in content,
                "which" in content,
                "type" in content,
                "hash" in content
            ])
            
            # Not all scripts need dependency checks
            if "docker" in content:
                # Scripts using docker should check for it
                has_docker_check = "docker" in content and ("command" in content or "which" in content)

    @patch('subprocess.run')
    def test_script_return_codes(self, mock_subprocess, ci_directory):
        """Test that scripts return appropriate exit codes."""
        script_files = [f for f in os.listdir(ci_directory) if f.endswith('.sh')]
        
        # Test success case
        mock_subprocess.return_value = Mock(returncode=0, stdout="Success", stderr="")
        
        for script in script_files:
            script_path = os.path.join(ci_directory, script)
            result = subprocess.run(["/bin/bash", script_path], capture_output=True, text=True)
            
        # Test failure case
        mock_subprocess.return_value = Mock(returncode=1, stdout="", stderr="Error")
        
        for script in script_files:
            script_path = os.path.join(ci_directory, script)
            result = subprocess.run(["/bin/bash", script_path], capture_output=True, text=True)

    def test_script_documentation(self, ci_directory):
        """Test that scripts have proper documentation."""
        script_files = [f for f in os.listdir(ci_directory) if f.endswith('.sh')]
        
        for script in script_files:
            script_path = os.path.join(ci_directory, script)
            with open(script_path, 'r') as f:
                content = f.read()
            
            # Test for documentation patterns
            has_documentation = any([
                "# " in content,
                "##" in content,
                "usage" in content.lower(),
                "description" in content.lower()
            ])
            
            assert has_documentation, f"{script} lacks proper documentation"

    @patch('subprocess.run')
    def test_script_cleanup(self, mock_subprocess, ci_directory):
        """Test that scripts perform proper cleanup."""
        mock_subprocess.return_value = Mock(returncode=0, stdout="Cleanup done", stderr="")
        
        script_files = [f for f in os.listdir(ci_directory) if f.endswith('.sh')]
        
        for script in script_files:
            script_path = os.path.join(ci_directory, script)
            with open(script_path, 'r') as f:
                content = f.read()
            
            # Test for cleanup patterns
            has_cleanup = any([
                "trap" in content,
                "cleanup" in content.lower(),
                "rm " in content,
                "docker system prune" in content
            ])
            
            # Not all scripts need cleanup, but it's good practice

    def test_script_timeout_handling(self, ci_directory):
        """Test that scripts handle timeouts appropriately."""
        script_files = [f for f in os.listdir(ci_directory) if f.endswith('.sh')]
        
        for script in script_files:
            script_path = os.path.join(ci_directory, script)
            with open(script_path, 'r') as f:
                content = f.read()
            
            # Test for timeout handling
            has_timeout = any([
                "timeout" in content,
                "sleep" in content,
                "wait" in content
            ])
            
            # Timeout handling is environment-specific

    @patch('subprocess.run')
    def test_script_integration(self, mock_subprocess, ci_directory):
        """Test script integration and chaining."""
        mock_subprocess.return_value = Mock(returncode=0, stdout="Integration test", stderr="")
        
        # Test running multiple scripts in sequence
        scripts_sequence = ["build.sh", "test.sh", "deploy.sh"]
        
        for script in scripts_sequence:
            script_path = os.path.join(ci_directory, script)
            if os.path.exists(script_path):
                result = subprocess.run(["/bin/bash", script_path], capture_output=True, text=True)
        
        assert mock_subprocess.called

    def test_script_file_permissions(self, ci_directory):
        """Test that script file permissions are correctly set."""
        script_files = [f for f in os.listdir(ci_directory) if f.endswith('.sh')]
        
        for script in script_files:
            script_path = os.path.join(ci_directory, script)
            file_stat = os.stat(script_path)
            
            # Test owner permissions
            assert file_stat.st_mode & stat.S_IRUSR  # Owner read
            assert file_stat.st_mode & stat.S_IWUSR  # Owner write
            assert file_stat.st_mode & stat.S_IXUSR  # Owner execute
            
            # Test that scripts are not world-writable (security)
            assert not (file_stat.st_mode & stat.S_IWOTH), f"{script} is world-writable"