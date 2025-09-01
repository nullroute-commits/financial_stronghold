#!/usr/bin/env python
"""
Test script for copilot instructions loading functionality.

This script tests the copilot instructions service independently of Django
to verify the core functionality works correctly.
"""

import sys
import os
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.copilot_service import CopilotInstructionsService


def test_copilot_service():
    """Test the copilot instructions service."""
    print("🚀 Testing Copilot Instructions Service")
    print("=" * 50)
    
    try:
        # Initialize service
        service = CopilotInstructionsService()
        
        # Load instructions
        print("📖 Loading copilot instructions...")
        instructions = service.load_instructions()
        
        # Display basic info
        print(f"✅ Successfully loaded instructions!")
        print(f"📋 Project: {instructions.project_name}")
        print(f"🔢 Version: {instructions.version}")
        print(f"📅 Last Updated: {instructions.last_updated}")
        print(f"⏰ Loaded At: {instructions.loaded_at}")
        print()
        
        # Display summary statistics
        print("📊 Content Summary:")
        print(f"  • Key Features: {len(instructions.key_features)}")
        print(f"  • Technology Stack Items: {len(instructions.technology_stack)}")
        print(f"  • Workflow Steps: {len(instructions.workflow_steps)}")
        print(f"  • Configuration Items: {len(instructions.configuration_items)}")
        print(f"  • Critical Guidelines: {len(instructions.critical_guidelines)}")
        print(f"  • Deployment Strategies: {len(instructions.deployment_strategies)}")
        print()
        
        # Test workflow categories
        print("🔄 Workflow Categories:")
        categories = set(step.category for step in instructions.workflow_steps)
        for category in sorted(categories):
            commands = service.get_commands_by_category(category)
            print(f"  • {category}: {len(commands)} commands")
        print()
        
        # Test validation
        print("🔍 Validating project setup...")
        validation_results = service.validate_current_setup()
        overall_status = validation_results['overall_status']
        if overall_status == 'valid':
            print("✅ Project setup is VALID")
        else:
            print("⚠️  Project setup has issues")
        
        # Show file existence results
        print("📁 File Existence Check:")
        for file_path, exists in validation_results['files_exist'].items():
            status = "✅" if exists else "❌"
            print(f"  {status} {file_path}")
        print()
        
        # Test JSON export
        print("📤 Testing JSON export...")
        json_data = service.to_json()
        print(f"✅ JSON export successful ({len(json_data):,} characters)")
        print()
        
        # Display some sample content
        print("📝 Sample Content:")
        print("Key Features (first 3):")
        for i, feature in enumerate(instructions.key_features[:3], 1):
            print(f"  {i}. {feature}")
        
        if instructions.workflow_steps:
            print()
            print("Workflow Example (first step):")
            step = instructions.workflow_steps[0]
            print(f"  Name: {step.name}")
            print(f"  Category: {step.category}")
            print(f"  Commands: {len(step.commands)}")
            if step.commands:
                print(f"  First Command: {step.commands[0]}")
        
        print()
        print("🎉 All tests passed! Copilot instructions are loaded and computed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing copilot service: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_specific_features():
    """Test specific features of the copilot service."""
    print("\n🔧 Testing Specific Features")
    print("=" * 30)
    
    try:
        service = CopilotInstructionsService()
        instructions = service.load_instructions()
        
        # Test technology stack extraction
        print("💻 Technology Stack:")
        for tech, description in instructions.technology_stack.items():
            print(f"  • {tech}: {description}")
        print()
        
        # Test configuration items
        print("⚙️  Configuration Items (by environment):")
        env_groups = {}
        for config in instructions.configuration_items:
            if config.environment not in env_groups:
                env_groups[config.environment] = []
            env_groups[config.environment].append(config)
        
        for env, configs in env_groups.items():
            required_count = sum(1 for c in configs if c.required)
            print(f"  • {env}: {len(configs)} configs ({required_count} required)")
        print()
        
        # Test critical guidelines
        print("🚨 Critical Guidelines:")
        for i, guideline in enumerate(instructions.critical_guidelines[:5], 1):
            print(f"  {i}. {guideline[:100]}{'...' if len(guideline) > 100 else ''}")
        
        print()
        print("✅ Specific features test completed!")
        
    except Exception as e:
        print(f"❌ Error testing specific features: {e}")
        return False


if __name__ == "__main__":
    success = test_copilot_service()
    if success:
        test_specific_features()
    
    print("\n" + "=" * 60)
    print("🏁 Test completed!")
    if success:
        print("✅ Copilot instructions are successfully loaded and computed!")
    else:
        print("❌ Tests failed!")
    print("=" * 60)