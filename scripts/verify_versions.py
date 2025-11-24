#!/usr/bin/env python3
"""
Version Verification Script

Verifies that all version references in documentation match the actual 
versions defined in configuration files and Docker images.

Usage:
    python scripts/verify_versions.py

Exit codes:
    0 - All versions match
    1 - Version mismatches found
"""

import re
import sys
import yaml
from pathlib import Path
from typing import Dict, List, Tuple


class VersionVerifier:
    """Verifies version consistency across documentation and configuration."""

    def __init__(self, root_dir: Path):
        self.root_dir = root_dir
        self.errors: List[str] = []
        self.warnings: List[str] = []
        
        # Expected versions from configuration
        self.expected_versions = {
            'python': '3.12.3',
            'django': '5.1.13',
            'postgres': '17.2',
            'redis': '7',
            'memcached': '1.6',
            'rabbitmq': '3.12',
            'nginx': '1.24',
        }

    def verify_python_version_file(self) -> bool:
        """Verify .python-version file."""
        python_version_file = self.root_dir / '.python-version'
        
        if not python_version_file.exists():
            self.errors.append("❌ .python-version file not found")
            return False
            
        with open(python_version_file) as f:
            version = f.read().strip()
            
        if version != self.expected_versions['python']:
            self.errors.append(
                f"❌ .python-version: Expected {self.expected_versions['python']}, "
                f"found {version}"
            )
            return False
            
        print(f"✅ .python-version: {version}")
        return True

    def verify_docker_compose(self) -> bool:
        """Verify Docker Compose image versions."""
        docker_compose_file = self.root_dir / 'docker-compose.base.yml'
        
        if not docker_compose_file.exists():
            self.errors.append("❌ docker-compose.base.yml not found")
            return False
            
        with open(docker_compose_file) as f:
            compose_config = yaml.safe_load(f)
            
        services = compose_config.get('services', {})
        success = True
        
        # Check PostgreSQL
        db_image = services.get('db', {}).get('image', '')
        if f"postgres:{self.expected_versions['postgres']}" not in db_image:
            self.errors.append(
                f"❌ Docker Compose db: Expected postgres:{self.expected_versions['postgres']}, "
                f"found {db_image}"
            )
            success = False
        else:
            print(f"✅ Docker Compose PostgreSQL: {db_image}")
            
        # Check Redis
        redis_image = services.get('redis', {}).get('image', '')
        if f"redis:{self.expected_versions['redis']}" not in redis_image:
            self.errors.append(
                f"❌ Docker Compose redis: Expected redis:{self.expected_versions['redis']}, "
                f"found {redis_image}"
            )
            success = False
        else:
            print(f"✅ Docker Compose Redis: {redis_image}")
            
        # Check Memcached
        memcached_image = services.get('memcached', {}).get('image', '')
        if f"memcached:{self.expected_versions['memcached']}" not in memcached_image:
            self.errors.append(
                f"❌ Docker Compose memcached: Expected memcached:{self.expected_versions['memcached']}, "
                f"found {memcached_image}"
            )
            success = False
        else:
            print(f"✅ Docker Compose Memcached: {memcached_image}")
            
        # Check RabbitMQ
        rabbitmq_image = services.get('rabbitmq', {}).get('image', '')
        if f"rabbitmq:{self.expected_versions['rabbitmq']}" not in rabbitmq_image:
            self.errors.append(
                f"❌ Docker Compose rabbitmq: Expected rabbitmq:{self.expected_versions['rabbitmq']}, "
                f"found {rabbitmq_image}"
            )
            success = False
        else:
            print(f"✅ Docker Compose RabbitMQ: {rabbitmq_image}")
            
        # Check Nginx
        nginx_image = services.get('nginx', {}).get('image', '')
        if f"nginx:{self.expected_versions['nginx']}" not in nginx_image:
            self.errors.append(
                f"❌ Docker Compose nginx: Expected nginx:{self.expected_versions['nginx']}, "
                f"found {nginx_image}"
            )
            success = False
        else:
            print(f"✅ Docker Compose Nginx: {nginx_image}")
            
        return success

    def verify_requirements_file(self) -> bool:
        """Verify requirements file Django version."""
        requirements_file = self.root_dir / 'requirements' / 'base.txt'
        
        if not requirements_file.exists():
            self.errors.append("❌ requirements/base.txt not found")
            return False
            
        with open(requirements_file) as f:
            content = f.read()
            
        django_match = re.search(r'Django==(\d+\.\d+\.\d+)', content)
        if not django_match:
            self.errors.append("❌ Django version not found in requirements/base.txt")
            return False
            
        django_version = django_match.group(1)
        if django_version != self.expected_versions['django']:
            self.errors.append(
                f"❌ requirements/base.txt: Expected Django {self.expected_versions['django']}, "
                f"found {django_version}"
            )
            return False
            
        print(f"✅ requirements/base.txt Django: {django_version}")
        return True

    def verify_documentation(self) -> bool:
        """Verify documentation version references."""
        docs_to_check = [
            'README.md',
            'SOLUTION_ARCHITECTURE_ANALYSIS.md',
            'PR_DESCRIPTION.md',
            'WORK_COMPLETION_SUMMARY.md',
            'SPRINT_COMPLETION_REPORT_v2.md',
        ]
        
        success = True
        
        # Pattern to find incorrect Python versions
        wrong_python_patterns = [
            r'Python\s+3\.12\.5',
            r'python\s+3\.12\.5',
            r'Python\s+3\.12\.1',
            r'python\s+3\.12\.1',
        ]
        
        # Pattern to find incorrect service versions with patch numbers
        wrong_service_patterns = [
            r'Memcached\s+1\.6\.\d+',
            r'memcached\s+1\.6\.\d+',
            r'RabbitMQ\s+3\.12\.\d+',
            r'rabbitmq\s+3\.12\.\d+',
            r'Nginx\s+1\.24\.\d+',
            r'nginx\s+1\.24\.\d+',
        ]
        
        for doc_file in docs_to_check:
            doc_path = self.root_dir / doc_file
            if not doc_path.exists():
                self.warnings.append(f"⚠️  {doc_file} not found (skipping)")
                continue
                
            with open(doc_path) as f:
                content = f.read()
                
            # Check for wrong Python versions
            for pattern in wrong_python_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    self.errors.append(
                        f"❌ {doc_file}: Found incorrect Python version reference(s): {matches}"
                    )
                    success = False
                    
            # Check for overly specific service versions
            for pattern in wrong_service_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    self.warnings.append(
                        f"⚠️  {doc_file}: Found overly specific version reference(s): {matches}"
                    )
        
        if success:
            print("✅ Documentation version references verified")
        
        return success

    def run_all_checks(self) -> bool:
        """Run all verification checks."""
        print("=" * 60)
        print("Version Verification")
        print("=" * 60)
        print()
        
        print("Expected Versions:")
        for key, value in self.expected_versions.items():
            print(f"  {key}: {value}")
        print()
        
        print("Verification Results:")
        print("-" * 60)
        
        checks = [
            ("Python Version File", self.verify_python_version_file),
            ("Docker Compose Images", self.verify_docker_compose),
            ("Requirements File", self.verify_requirements_file),
            ("Documentation", self.verify_documentation),
        ]
        
        all_success = True
        for check_name, check_func in checks:
            try:
                if not check_func():
                    all_success = False
            except Exception as e:
                self.errors.append(f"❌ {check_name}: Exception occurred: {e}")
                all_success = False
        
        print()
        print("=" * 60)
        
        if self.warnings:
            print("Warnings:")
            for warning in self.warnings:
                print(f"  {warning}")
            print()
        
        if self.errors:
            print("Errors:")
            for error in self.errors:
                print(f"  {error}")
            print()
            print("❌ Version verification FAILED")
            return False
        else:
            print("✅ All version checks PASSED")
            return True


def main():
    """Main entry point."""
    root_dir = Path(__file__).parent.parent
    verifier = VersionVerifier(root_dir)
    
    success = verifier.run_all_checks()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
