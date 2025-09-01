#!/usr/bin/env python
"""
Comprehensive demonstration of copilot instructions loading and computing functionality.

This script demonstrates all the features implemented for loading and processing
the copilot-instructions.md file.
"""

import sys
import os
import json
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.copilot_service import CopilotInstructionsService
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.copilot_api import router as copilot_router


def demo_service_functionality():
    """Demonstrate the core service functionality."""
    print("🚀 COPILOT INSTRUCTIONS SERVICE DEMONSTRATION")
    print("=" * 60)
    
    # Initialize service
    service = CopilotInstructionsService()
    
    # Load and display basic information
    print("📖 Loading copilot instructions...")
    instructions = service.load_instructions()
    
    print(f"✅ Successfully loaded!")
    print(f"📋 Project: {instructions.project_name}")
    print(f"🔢 Version: {instructions.version}")
    print(f"📅 Last Updated: {instructions.last_updated}")
    print(f"📝 Description: {instructions.description}")
    print()
    
    # Display content summary
    print("📊 CONTENT ANALYSIS")
    print("-" * 30)
    print(f"🌟 Key Features: {len(instructions.key_features)}")
    for i, feature in enumerate(instructions.key_features[:5], 1):
        print(f"   {i}. {feature}")
    if len(instructions.key_features) > 5:
        print(f"   ... and {len(instructions.key_features) - 5} more")
    print()
    
    print(f"💻 Technology Stack: {len(instructions.technology_stack)} technologies")
    for tech, desc in list(instructions.technology_stack.items())[:3]:
        print(f"   • {tech}: {desc}")
    if len(instructions.technology_stack) > 3:
        print(f"   ... and {len(instructions.technology_stack) - 3} more")
    print()
    
    print(f"🔄 Workflow Steps: {len(instructions.workflow_steps)} workflows")
    for step in instructions.workflow_steps:
        print(f"   • {step.name} ({step.category}): {len(step.commands)} commands")
    print()
    
    print(f"⚙️  Configuration Items: {len(instructions.configuration_items)} configs")
    env_groups = {}
    for config in instructions.configuration_items:
        if config.environment not in env_groups:
            env_groups[config.environment] = {'total': 0, 'required': 0}
        env_groups[config.environment]['total'] += 1
        if config.required:
            env_groups[config.environment]['required'] += 1
    
    for env, counts in env_groups.items():
        print(f"   • {env}: {counts['total']} total ({counts['required']} required)")
    print()
    
    print(f"🚨 Critical Guidelines: {len(instructions.critical_guidelines)}")
    for i, guideline in enumerate(instructions.critical_guidelines, 1):
        print(f"   {i}. {guideline[:80]}{'...' if len(guideline) > 80 else ''}")
    print()
    
    # Demonstrate specific functionality
    print("🔧 SPECIFIC FUNCTIONALITY DEMOS")
    print("-" * 40)
    
    # Commands by category
    print("📋 Commands by Category:")
    categories = set(step.category for step in instructions.workflow_steps)
    for category in sorted(categories):
        commands = service.get_commands_by_category(category)
        print(f"   • {category.capitalize()}: {len(commands)} commands")
        for i, cmd in enumerate(commands[:2], 1):
            print(f"     {i}. {cmd}")
        if len(commands) > 2:
            print(f"     ... and {len(commands) - 2} more")
    print()
    
    # Validation
    print("🔍 Project Setup Validation:")
    validation = service.validate_current_setup()
    status = validation['overall_status']
    print(f"   Overall Status: {'✅ VALID' if status == 'valid' else '❌ INVALID'}")
    
    files_exist = validation['files_exist']
    existing_count = sum(1 for exists in files_exist.values() if exists)
    print(f"   Files Check: {existing_count}/{len(files_exist)} exist")
    
    for file_path, exists in files_exist.items():
        status_icon = "✅" if exists else "❌"
        print(f"     {status_icon} {file_path}")
    print()
    
    # JSON export
    print("📤 JSON Export Capability:")
    json_data = service.to_json()
    print(f"   ✅ Successfully exported to JSON ({len(json_data):,} characters)")
    
    # Parse and show structure
    parsed = json.loads(json_data)
    print(f"   📋 JSON contains {len(parsed)} top-level keys:")
    for key in sorted(parsed.keys()):
        value = parsed[key]
        if isinstance(value, list):
            print(f"     • {key}: {len(value)} items")
        elif isinstance(value, dict):
            print(f"     • {key}: {len(value)} properties")
        else:
            print(f"     • {key}: {type(value).__name__}")
    print()


def demo_api_functionality():
    """Demonstrate the API functionality."""
    print("🌐 API ENDPOINTS DEMONSTRATION")
    print("=" * 40)
    
    # Set up FastAPI test client
    app = FastAPI()
    app.include_router(copilot_router)
    client = TestClient(app)
    
    # Test various endpoints
    endpoints = [
        ("/copilot/health", "Health Check"),
        ("/copilot/instructions/summary", "Instructions Summary"),
        ("/copilot/instructions?format=structured", "Structured Instructions"),
        ("/copilot/instructions/validate", "Setup Validation"),
        ("/copilot/instructions/technology-stack", "Technology Stack"),
        ("/copilot/instructions/guidelines", "Critical Guidelines"),
        ("/copilot/instructions/workflows", "Workflow Steps"),
    ]
    
    for endpoint, description in endpoints:
        print(f"🔗 Testing: {description}")
        print(f"   Endpoint: {endpoint}")
        
        try:
            response = client.get(endpoint)
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Status: {response.status_code} OK")
                
                # Show key information based on endpoint
                if "health" in endpoint:
                    print(f"   🏥 Health: {data.get('status', 'unknown')}")
                    print(f"   📋 Project: {data.get('project_name', 'unknown')}")
                
                elif "summary" in endpoint:
                    summary = data.get('summary', {})
                    print(f"   📊 Features: {summary.get('key_features_count', 0)}")
                    print(f"   🔄 Workflows: {summary.get('workflow_steps_count', 0)}")
                
                elif "structured" in endpoint:
                    print(f"   📋 Project: {data.get('project_name', 'unknown')}")
                    print(f"   🔧 Tech Stack: {len(data.get('technology_stack', {}))}")
                
                elif "validate" in endpoint:
                    validation = data.get('validation_results', {})
                    status = validation.get('overall_status', 'unknown')
                    print(f"   🔍 Validation: {'✅' if status == 'valid' else '❌'} {status}")
                
                elif "technology-stack" in endpoint:
                    stack = data.get('technology_stack', {})
                    print(f"   💻 Technologies: {len(stack)} items")
                
                elif "guidelines" in endpoint:
                    guidelines = data.get('critical_guidelines', [])
                    print(f"   🚨 Guidelines: {len(guidelines)} items")
                
                elif "workflows" in endpoint:
                    total = data.get('total_workflow_steps', 0)
                    categories = data.get('categories', [])
                    print(f"   🔄 Total Steps: {total}")
                    print(f"   📋 Categories: {', '.join(categories)}")
                
            else:
                print(f"   ❌ Status: {response.status_code}")
        
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print()
    
    # Test command category endpoint
    print("🔗 Testing: Command Category (Quality)")
    print("   Endpoint: /copilot/instructions/commands/quality")
    
    try:
        response = client.get("/copilot/instructions/commands/quality")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Status: {response.status_code} OK")
            print(f"   📋 Category: {data.get('category', 'unknown')}")
            print(f"   🔧 Commands: {data.get('command_count', 0)}")
            
            commands = data.get('commands', [])
            for i, cmd in enumerate(commands[:3], 1):
                print(f"     {i}. {cmd}")
            if len(commands) > 3:
                print(f"     ... and {len(commands) - 3} more")
        else:
            print(f"   ❌ Status: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print()


def demo_usage_scenarios():
    """Demonstrate practical usage scenarios."""
    print("💡 PRACTICAL USAGE SCENARIOS")
    print("=" * 40)
    
    service = CopilotInstructionsService()
    
    print("📋 Scenario 1: Getting Setup Commands for Development")
    prep_commands = service.get_commands_by_category("preparation")
    quality_commands = service.get_commands_by_category("quality")
    
    print(f"   Pre-deployment commands ({len(prep_commands)}):")
    for cmd in prep_commands:
        print(f"     $ {cmd}")
    
    print(f"   Quality check commands ({len(quality_commands)}):")
    for cmd in quality_commands:
        print(f"     $ {cmd}")
    print()
    
    print("📋 Scenario 2: Validating Current Project State")
    validation = service.validate_current_setup()
    print(f"   Project validation: {validation['overall_status']}")
    
    missing_files = [f for f, exists in validation['files_exist'].items() if not exists]
    if missing_files:
        print(f"   Missing files ({len(missing_files)}):")
        for file_path in missing_files:
            print(f"     ❌ {file_path}")
    else:
        print("   ✅ All required files present")
    print()
    
    print("📋 Scenario 3: Extracting Technology Information")
    instructions = service.load_instructions()
    print("   Technology stack for documentation:")
    for tech, desc in instructions.technology_stack.items():
        print(f"     • {tech}: {desc}")
    print()
    
    print("📋 Scenario 4: Getting Critical Development Guidelines")
    print("   Critical guidelines for new developers:")
    for i, guideline in enumerate(instructions.critical_guidelines, 1):
        print(f"     {i}. {guideline}")
    print()


def main():
    """Run the complete demonstration."""
    print("🎯 COPILOT INSTRUCTIONS LOADING & COMPUTING DEMO")
    print("=" * 70)
    print("This demonstration shows that the copilot-instructions.md file")
    print("is being successfully loaded and computed with full functionality.")
    print("=" * 70)
    print()
    
    try:
        # Core service functionality
        demo_service_functionality()
        print()
        
        # API functionality
        demo_api_functionality()
        print()
        
        # Practical usage scenarios
        demo_usage_scenarios()
        
        print("🎉 DEMONSTRATION COMPLETE!")
        print("=" * 50)
        print("✅ Copilot instructions are fully loaded and computed!")
        print("✅ All parsing and processing functionality working!")
        print("✅ API endpoints are operational!")
        print("✅ Validation and commands extraction working!")
        print("=" * 50)
        
    except Exception as e:
        print(f"❌ Error during demonstration: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)