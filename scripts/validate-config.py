#!/usr/bin/env python3
"""
Configuration validation script.
Checks for common configuration issues and mismatches.
"""

import os
import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

def validate_django_settings():
    """Validate Django settings configuration."""
    issues = []
    
    # Check for duplicate settings files
    app_settings = project_root / "app" / "settings.py"
    config_settings = project_root / "config" / "settings"
    
    if app_settings.exists() and config_settings.exists():
        issues.append("⚠️  Duplicate settings files found: app/settings.py and config/settings/")
    
    # Check SECRET_KEY configuration
    for settings_file in [app_settings, config_settings / "base.py"]:
        if settings_file.exists():
            with open(settings_file, 'r') as f:
                content = f.read()
                if 'django-insecure-change-me' in content:
                    issues.append(f"⚠️  Default SECRET_KEY found in {settings_file}")
    
    return issues

def validate_requirements():
    """Validate requirements files consistency."""
    issues = []
    
    # Read pyproject.toml dependencies
    pyproject_path = project_root / "pyproject.toml"
    pyproject_deps = {}
    
    if pyproject_path.exists():
        with open(pyproject_path, 'r') as f:
            in_deps = False
            for line in f:
                if line.strip() == 'dependencies = [':
                    in_deps = True
                elif in_deps and line.strip() == ']':
                    break
                elif in_deps and '==' in line:
                    dep = line.strip().strip('",')
                    name, version = dep.split('==')
                    pyproject_deps[name.lower()] = version
    
    # Check each requirements file
    req_dir = project_root / "requirements"
    for req_file in req_dir.glob("*.txt"):
        with open(req_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '==' in line:
                    name, version = line.split('==')
                    name = name.lower()
                    if name in pyproject_deps and pyproject_deps[name] != version:
                        issues.append(
                            f"⚠️  Version mismatch for {name}: "
                            f"pyproject.toml has {pyproject_deps[name]}, "
                            f"{req_file.name} has {version}"
                        )
    
    return issues

def validate_docker_compose():
    """Validate Docker Compose configurations."""
    issues = []
    
    compose_files = list(project_root.glob("docker-compose.*.yml"))
    
    for compose_file in compose_files:
        # Basic syntax check would require PyYAML
        # For now, just check file exists and is readable
        try:
            with open(compose_file, 'r') as f:
                content = f.read()
                if not content.strip():
                    issues.append(f"⚠️  Empty Docker Compose file: {compose_file.name}")
        except Exception as e:
            issues.append(f"❌ Error reading {compose_file.name}: {e}")
    
    return issues

def validate_environment_files():
    """Validate environment configuration files."""
    issues = []
    
    env_dir = project_root / "environments"
    required_envs = ['development', 'testing', 'staging', 'production']
    
    for env in required_envs:
        env_file = env_dir / f".env.{env}.example"
        if not env_file.exists():
            issues.append(f"⚠️  Missing environment file: {env_file.name}")
    
    return issues

def main():
    """Run all validation checks."""
    print("=== Configuration Validation ===\n")
    
    all_issues = []
    
    # Run validation checks
    checks = [
        ("Django Settings", validate_django_settings),
        ("Requirements", validate_requirements),
        ("Docker Compose", validate_docker_compose),
        ("Environment Files", validate_environment_files),
    ]
    
    for check_name, check_func in checks:
        print(f"Checking {check_name}...")
        issues = check_func()
        if issues:
            all_issues.extend(issues)
            for issue in issues:
                print(f"  {issue}")
        else:
            print(f"  ✅ No issues found")
        print()
    
    # Summary
    if all_issues:
        print(f"\n❌ Found {len(all_issues)} configuration issues")
        return 1
    else:
        print("\n✅ All configuration checks passed!")
        return 0

if __name__ == "__main__":
    sys.exit(main())