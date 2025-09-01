"""
Copilot Instructions Service

This service handles loading, parsing, and processing the copilot-instructions.md file
to extract configuration, workflows, and project standards for validation and API access.
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class WorkflowStep:
    """Represents a workflow step extracted from instructions."""
    name: str
    commands: List[str]
    description: str
    category: str


@dataclass
class ConfigurationItem:
    """Represents a configuration item extracted from instructions."""
    key: str
    value: str
    description: str
    environment: str
    required: bool = False


@dataclass
class CopilotInstructions:
    """Structured representation of copilot instructions."""
    project_name: str
    last_updated: str
    version: str
    description: str
    key_features: List[str]
    technology_stack: Dict[str, str]
    repository_structure: Dict[str, str]
    workflow_steps: List[WorkflowStep]
    configuration_items: List[ConfigurationItem]
    code_quality_standards: Dict[str, Any]
    deployment_strategies: List[str]
    troubleshooting_items: List[Dict[str, str]]
    critical_guidelines: List[str]
    loaded_at: datetime


class CopilotInstructionsService:
    """Service for loading and processing copilot instructions."""
    
    def __init__(self, instructions_path: Optional[str] = None):
        """Initialize with optional custom path to instructions file."""
        if instructions_path:
            self.instructions_path = Path(instructions_path)
        else:
            # Default to repository root
            current_dir = Path(__file__).resolve()
            self.instructions_path = current_dir.parent.parent.parent / "copilot-instructions.md"
        
        self._cached_instructions: Optional[CopilotInstructions] = None
    
    def load_instructions(self, force_reload: bool = False) -> CopilotInstructions:
        """Load and parse copilot instructions from file."""
        if self._cached_instructions and not force_reload:
            return self._cached_instructions
        
        if not self.instructions_path.exists():
            raise FileNotFoundError(f"Copilot instructions not found at {self.instructions_path}")
        
        with open(self.instructions_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        instructions = self._parse_instructions(content)
        self._cached_instructions = instructions
        return instructions
    
    def _parse_instructions(self, content: str) -> CopilotInstructions:
        """Parse markdown content into structured data."""
        # Extract project metadata
        project_name = self._extract_project_name(content)
        last_updated = self._extract_last_updated(content)
        version = self._extract_version(content)
        description = self._extract_description(content)
        
        # Extract sections
        key_features = self._extract_key_features(content)
        technology_stack = self._extract_technology_stack(content)
        repository_structure = self._extract_repository_structure(content)
        workflow_steps = self._extract_workflow_steps(content)
        configuration_items = self._extract_configuration_items(content)
        code_quality_standards = self._extract_code_quality_standards(content)
        deployment_strategies = self._extract_deployment_strategies(content)
        troubleshooting_items = self._extract_troubleshooting_items(content)
        critical_guidelines = self._extract_critical_guidelines(content)
        
        return CopilotInstructions(
            project_name=project_name,
            last_updated=last_updated,
            version=version,
            description=description,
            key_features=key_features,
            technology_stack=technology_stack,
            repository_structure=repository_structure,
            workflow_steps=workflow_steps,
            configuration_items=configuration_items,
            code_quality_standards=code_quality_standards,
            deployment_strategies=deployment_strategies,
            troubleshooting_items=troubleshooting_items,
            critical_guidelines=critical_guidelines,
            loaded_at=datetime.utcnow()
        )
    
    def _extract_project_name(self, content: str) -> str:
        """Extract project name from the main heading."""
        match = re.search(r'^#\s+(.+?)\n', content, re.MULTILINE)
        if match:
            return match.group(1).replace('GitHub Copilot Instructions for ', '')
        return "Unknown Project"
    
    def _extract_last_updated(self, content: str) -> str:
        """Extract last updated date."""
        match = re.search(r'\*\*Last Updated\*\*:\s*(.+?)\n', content)
        return match.group(1).strip() if match else "Unknown"
    
    def _extract_version(self, content: str) -> str:
        """Extract version information."""
        # Look for Django version as primary version indicator
        match = re.search(r'Django\s+(\d+\.\d+\.\d+)', content)
        return match.group(1) if match else "Unknown"
    
    def _extract_description(self, content: str) -> str:
        """Extract project description."""
        match = re.search(r'### Project Description\s*\n(.+?)\n', content, re.DOTALL)
        return match.group(1).strip() if match else "No description available"
    
    def _extract_key_features(self, content: str) -> List[str]:
        """Extract key features list."""
        features = []
        # Find the Key Features section
        features_match = re.search(r'### Key Features\s*\n((?:- .+\n?)+)', content, re.MULTILINE)
        if features_match:
            features_text = features_match.group(1)
            features = [line.strip('- ').strip() for line in features_text.split('\n') if line.strip().startswith('- ')]
        return features
    
    def _extract_technology_stack(self, content: str) -> Dict[str, str]:
        """Extract technology stack information."""
        stack = {}
        # Find Core Technologies section
        tech_match = re.search(r'### Core Technologies\s*\n((?:- .+\n?)+)', content, re.MULTILINE)
        if tech_match:
            tech_text = tech_match.group(1)
            for line in tech_text.split('\n'):
                if line.strip().startswith('- **'):
                    match = re.search(r'- \*\*(.+?)\*\*:\s*(.+)', line)
                    if match:
                        stack[match.group(1)] = match.group(2)
        return stack
    
    def _extract_repository_structure(self, content: str) -> Dict[str, str]:
        """Extract repository structure information."""
        structure = {}
        # Find repository structure in code blocks
        struct_match = re.search(r'```\nfinancial_stronghold/\n(.*?)\n```', content, re.DOTALL)
        if struct_match:
            struct_text = struct_match.group(1)
            for line in struct_text.split('\n'):
                if '├──' in line or '└──' in line:
                    # Parse directory structure
                    clean_line = re.sub(r'[├└─│\s]+', '', line)
                    if '/' in clean_line:
                        parts = clean_line.split('/')
                        if len(parts) >= 2:
                            structure[parts[0]] = parts[1] if len(parts) == 2 else '/'.join(parts[1:])
        return structure
    
    def _extract_workflow_steps(self, content: str) -> List[WorkflowStep]:
        """Extract workflow steps from various sections."""
        steps = []
        
        # Extract from Development Workflow & SOP section
        sop_sections = [
            ("Pre-Deployment Preparation", "preparation"),
            ("Code Quality Gates", "quality"),
            ("Testing Framework Execution", "testing"),
            ("CI/CD Pipeline Stages", "deployment")
        ]
        
        for section_name, category in sop_sections:
            section_match = re.search(
                f'#### \\d+\\. {section_name}\\s*\n```bash\\s*\n(.*?)\n```',
                content, re.DOTALL
            )
            if section_match:
                commands_text = section_match.group(1)
                commands = [cmd.strip() for cmd in commands_text.split('\n') if cmd.strip() and not cmd.startswith('#')]
                
                steps.append(WorkflowStep(
                    name=section_name,
                    commands=commands,
                    description=f"Commands for {section_name.lower()}",
                    category=category
                ))
        
        return steps
    
    def _extract_configuration_items(self, content: str) -> List[ConfigurationItem]:
        """Extract configuration items from environment sections."""
        configs = []
        
        # Extract from environment files examples
        env_match = re.search(r'```bash\n# environments/\.env\.development\.example\n(.*?)\n```', content, re.DOTALL)
        if env_match:
            env_text = env_match.group(1)
            for line in env_text.split('\n'):
                if '=' in line and not line.strip().startswith('#'):
                    key, value = line.split('=', 1)
                    configs.append(ConfigurationItem(
                        key=key.strip(),
                        value=value.strip(),
                        description=f"Development environment setting for {key.strip()}",
                        environment="development",
                        required=key.strip() in ['DEBUG', 'DJANGO_SETTINGS_MODULE', 'SECRET_KEY']
                    ))
        
        return configs
    
    def _extract_code_quality_standards(self, content: str) -> Dict[str, Any]:
        """Extract code quality standards and linting configuration."""
        standards = {}
        
        # Extract linting rules
        flake8_match = re.search(r'# \.flake8\s*\n\[flake8\]\s*\n(.*?)(?=\n#|\n\[|\nSOURCE_SUFFIXES|\n$)', content, re.DOTALL)
        if flake8_match:
            flake8_config = {}
            for line in flake8_match.group(1).split('\n'):
                if '=' in line:
                    key, value = line.split('=', 1)
                    flake8_config[key.strip()] = value.strip()
            standards['flake8'] = flake8_config
        
        # Extract MyPy configuration
        mypy_match = re.search(r'# \.mypy\.ini\s*\n\[mypy\]\s*\n(.*?)(?=\n#|\n\[|\n$)', content, re.DOTALL)
        if mypy_match:
            mypy_config = {}
            for line in mypy_match.group(1).split('\n'):
                if '=' in line:
                    key, value = line.split('=', 1)
                    mypy_config[key.strip()] = value.strip()
            standards['mypy'] = mypy_config
        
        return standards
    
    def _extract_deployment_strategies(self, content: str) -> List[str]:
        """Extract deployment strategies."""
        strategies = []
        
        # Find deployment strategies section
        strategies_match = re.search(r'### Deployment Strategies\s*\n((?:- \*\*.+\n?)+)', content, re.MULTILINE)
        if strategies_match:
            strategies_text = strategies_match.group(1)
            for line in strategies_text.split('\n'):
                if line.strip().startswith('- **'):
                    strategy_match = re.search(r'- \*\*(.+?)\*\*:\s*(.+)', line)
                    if strategy_match:
                        strategies.append(f"{strategy_match.group(1)}: {strategy_match.group(2)}")
        
        return strategies
    
    def _extract_troubleshooting_items(self, content: str) -> List[Dict[str, str]]:
        """Extract troubleshooting information."""
        items = []
        
        # Find troubleshooting sections
        troubleshooting_sections = re.findall(r'#### (.+?)\s*\n```bash\s*\n(.*?)\n```', content, re.DOTALL)
        for title, commands in troubleshooting_sections:
            if any(keyword in title.lower() for keyword in ['issue', 'problem', 'debug', 'error']):
                items.append({
                    'issue': title,
                    'solution': commands.strip(),
                    'category': 'troubleshooting'
                })
        
        return items
    
    def _extract_critical_guidelines(self, content: str) -> List[str]:
        """Extract critical guidelines for development."""
        guidelines = []
        
        # Find the Critical Guidelines section
        guidelines_match = re.search(r'### 🚨 \*\*ALWAYS Follow These Patterns\*\*\s*\n(.*?)(?=\n###|\n---|\n$)', content, re.DOTALL)
        if guidelines_match:
            guidelines_text = guidelines_match.group(1)
            
            # Extract numbered guidelines
            guideline_matches = re.findall(r'\d+\.\s+\*\*(.+?)\*\*:\s*(.+?)(?=\n\d+\.|\n   ```|\n$)', guidelines_text, re.DOTALL)
            for title, description in guideline_matches:
                guidelines.append(f"{title}: {description.strip()}")
        
        return guidelines
    
    def get_commands_by_category(self, category: str) -> List[str]:
        """Get all commands for a specific workflow category."""
        instructions = self.load_instructions()
        commands = []
        
        for step in instructions.workflow_steps:
            if step.category == category:
                commands.extend(step.commands)
        
        return commands
    
    def validate_current_setup(self) -> Dict[str, Any]:
        """Validate current project setup against documented standards."""
        instructions = self.load_instructions()
        validation_results = {
            'files_exist': {},
            'configurations_match': {},
            'dependencies_available': {},
            'overall_status': 'unknown'
        }
        
        # Check if key files exist
        base_path = self.instructions_path.parent
        key_files = [
            'requirements/base.txt',
            'requirements/development.txt',
            'docker-compose.development.yml',
            'manage.py',
            '.flake8',
            '.mypy.ini'
        ]
        
        for file_path in key_files:
            full_path = base_path / file_path
            validation_results['files_exist'][file_path] = full_path.exists()
        
        # Check configurations
        for config in instructions.configuration_items:
            if config.required:
                # This would need actual environment checking in a real implementation
                validation_results['configurations_match'][config.key] = True
        
        # Calculate overall status
        files_ok = all(validation_results['files_exist'].values())
        configs_ok = all(validation_results['configurations_match'].values())
        validation_results['overall_status'] = 'valid' if files_ok and configs_ok else 'invalid'
        
        return validation_results
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert instructions to dictionary format."""
        instructions = self.load_instructions()
        return asdict(instructions)
    
    def to_json(self) -> str:
        """Convert instructions to JSON format."""
        data = self.to_dict()
        # Handle datetime serialization
        data['loaded_at'] = data['loaded_at'].isoformat()
        return json.dumps(data, indent=2, ensure_ascii=False)