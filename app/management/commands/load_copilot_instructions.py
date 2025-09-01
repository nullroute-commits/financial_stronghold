"""
Django management command to load and compute copilot instructions.

This command loads the copilot-instructions.md file, parses its content,
and provides various operations for working with the extracted information.
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from typing import Optional
import json
import sys

from app.services.copilot_service import CopilotInstructionsService


class Command(BaseCommand):
    """Management command for loading and computing copilot instructions."""
    
    help = 'Load and compute copilot instructions from copilot-instructions.md'
    
    def add_arguments(self, parser):
        """Add command line arguments."""
        parser.add_argument(
            '--action',
            type=str,
            default='load',
            choices=['load', 'validate', 'extract', 'commands', 'json'],
            help='Action to perform with copilot instructions'
        )
        
        parser.add_argument(
            '--category',
            type=str,
            help='Filter by category (for commands action)'
        )
        
        parser.add_argument(
            '--output',
            type=str,
            help='Output file path for JSON export'
        )
        
        parser.add_argument(
            '--path',
            type=str,
            help='Custom path to copilot-instructions.md file'
        )
        
        parser.add_argument(
            '--force-reload',
            action='store_true',
            help='Force reload of instructions from file'
        )
        
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Verbose output'
        )
    
    def handle(self, *args, **options):
        """Handle the command execution."""
        try:
            # Initialize the service
            service = CopilotInstructionsService(options.get('path'))
            
            # Execute the requested action
            action = options['action']
            
            if action == 'load':
                self._handle_load(service, options)
            elif action == 'validate':
                self._handle_validate(service, options)
            elif action == 'extract':
                self._handle_extract(service, options)
            elif action == 'commands':
                self._handle_commands(service, options)
            elif action == 'json':
                self._handle_json(service, options)
            else:
                raise CommandError(f"Unknown action: {action}")
                
        except FileNotFoundError as e:
            raise CommandError(f"File not found: {e}")
        except Exception as e:
            if options['verbose']:
                import traceback
                traceback.print_exc()
            raise CommandError(f"Error processing copilot instructions: {e}")
    
    def _handle_load(self, service: CopilotInstructionsService, options: dict):
        """Handle the load action."""
        self.stdout.write(self.style.HTTP_INFO("Loading copilot instructions..."))
        
        instructions = service.load_instructions(force_reload=options.get('force_reload', False))
        
        self.stdout.write(self.style.SUCCESS("✅ Successfully loaded copilot instructions!"))
        self.stdout.write("")
        
        # Display summary
        self.stdout.write(self.style.HTTP_INFO("📋 Instructions Summary:"))
        self.stdout.write(f"Project: {instructions.project_name}")
        self.stdout.write(f"Version: {instructions.version}")
        self.stdout.write(f"Last Updated: {instructions.last_updated}")
        self.stdout.write(f"Loaded At: {instructions.loaded_at.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        self.stdout.write("")
        
        self.stdout.write(f"Key Features: {len(instructions.key_features)} items")
        self.stdout.write(f"Technology Stack: {len(instructions.technology_stack)} items")
        self.stdout.write(f"Workflow Steps: {len(instructions.workflow_steps)} steps")
        self.stdout.write(f"Configuration Items: {len(instructions.configuration_items)} configs")
        self.stdout.write(f"Critical Guidelines: {len(instructions.critical_guidelines)} guidelines")
        
        if options.get('verbose'):
            self._display_detailed_info(instructions)
    
    def _handle_validate(self, service: CopilotInstructionsService, options: dict):
        """Handle the validate action."""
        self.stdout.write(self.style.HTTP_INFO("Validating current setup against copilot instructions..."))
        
        validation_results = service.validate_current_setup()
        
        self.stdout.write("")
        self.stdout.write(self.style.HTTP_INFO("🔍 Validation Results:"))
        
        # File existence checks
        self.stdout.write(self.style.HTTP_INFO("📁 File Existence:"))
        for file_path, exists in validation_results['files_exist'].items():
            status = self.style.SUCCESS("✅") if exists else self.style.ERROR("❌")
            self.stdout.write(f"  {status} {file_path}")
        
        # Configuration checks
        if validation_results['configurations_match']:
            self.stdout.write(self.style.HTTP_INFO("⚙️  Configuration Status:"))
            for config_key, valid in validation_results['configurations_match'].items():
                status = self.style.SUCCESS("✅") if valid else self.style.ERROR("❌")
                self.stdout.write(f"  {status} {config_key}")
        
        # Overall status
        overall_status = validation_results['overall_status']
        if overall_status == 'valid':
            self.stdout.write(self.style.SUCCESS("🎉 Overall Status: VALID"))
        else:
            self.stdout.write(self.style.ERROR("⚠️  Overall Status: INVALID"))
    
    def _handle_extract(self, service: CopilotInstructionsService, options: dict):
        """Handle the extract action."""
        self.stdout.write(self.style.HTTP_INFO("Extracting key information from copilot instructions..."))
        
        instructions = service.load_instructions(force_reload=options.get('force_reload', False))
        
        self.stdout.write("")
        self.stdout.write(self.style.HTTP_INFO("🔧 Technology Stack:"))
        for tech, description in instructions.technology_stack.items():
            self.stdout.write(f"  • {tech}: {description}")
        
        self.stdout.write("")
        self.stdout.write(self.style.HTTP_INFO("🚀 Key Features:"))
        for feature in instructions.key_features:
            self.stdout.write(f"  • {feature}")
        
        self.stdout.write("")
        self.stdout.write(self.style.HTTP_INFO("📋 Deployment Strategies:"))
        for strategy in instructions.deployment_strategies:
            self.stdout.write(f"  • {strategy}")
        
        if options.get('verbose'):
            self.stdout.write("")
            self.stdout.write(self.style.HTTP_INFO("🚨 Critical Guidelines:"))
            for guideline in instructions.critical_guidelines:
                self.stdout.write(f"  • {guideline}")
    
    def _handle_commands(self, service: CopilotInstructionsService, options: dict):
        """Handle the commands action."""
        category = options.get('category')
        
        if category:
            self.stdout.write(self.style.HTTP_INFO(f"Commands for category: {category}"))
            commands = service.get_commands_by_category(category)
            
            if not commands:
                self.stdout.write(self.style.WARNING(f"No commands found for category: {category}"))
                return
            
            for i, command in enumerate(commands, 1):
                self.stdout.write(f"{i:2d}. {command}")
        else:
            # Show all workflow steps with commands
            instructions = service.load_instructions(force_reload=options.get('force_reload', False))
            
            self.stdout.write(self.style.HTTP_INFO("🔄 All Workflow Steps:"))
            
            for step in instructions.workflow_steps:
                self.stdout.write("")
                self.stdout.write(self.style.HTTP_INFO(f"📌 {step.name} ({step.category}):"))
                self.stdout.write(f"   Description: {step.description}")
                self.stdout.write("   Commands:")
                
                for i, command in enumerate(step.commands, 1):
                    self.stdout.write(f"     {i}. {command}")
    
    def _handle_json(self, service: CopilotInstructionsService, options: dict):
        """Handle the json action."""
        self.stdout.write(self.style.HTTP_INFO("Exporting copilot instructions to JSON..."))
        
        json_data = service.to_json()
        
        output_file = options.get('output')
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(json_data)
            self.stdout.write(self.style.SUCCESS(f"✅ JSON exported to: {output_file}"))
        else:
            # Output to stdout
            self.stdout.write("")
            self.stdout.write(json_data)
    
    def _display_detailed_info(self, instructions):
        """Display detailed information about loaded instructions."""
        self.stdout.write("")
        self.stdout.write(self.style.HTTP_INFO("📖 Detailed Information:"))
        
        self.stdout.write("")
        self.stdout.write(self.style.HTTP_INFO("Description:"))
        self.stdout.write(f"  {instructions.description}")
        
        if instructions.workflow_steps:
            self.stdout.write("")
            self.stdout.write(self.style.HTTP_INFO("Workflow Categories:"))
            categories = set(step.category for step in instructions.workflow_steps)
            for category in sorted(categories):
                step_count = sum(1 for step in instructions.workflow_steps if step.category == category)
                self.stdout.write(f"  • {category}: {step_count} steps")
        
        if instructions.configuration_items:
            self.stdout.write("")
            self.stdout.write(self.style.HTTP_INFO("Configuration Environments:"))
            environments = set(config.environment for config in instructions.configuration_items)
            for env in sorted(environments):
                config_count = sum(1 for config in instructions.configuration_items if config.environment == env)
                required_count = sum(1 for config in instructions.configuration_items 
                                   if config.environment == env and config.required)
                self.stdout.write(f"  • {env}: {config_count} configs ({required_count} required)")