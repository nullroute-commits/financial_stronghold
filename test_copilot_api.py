#!/usr/bin/env python
"""
Test script for copilot API endpoints using FastAPI test client.

This script tests the FastAPI endpoints for copilot instructions
to verify they work correctly.
"""

import sys
import os
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from app.copilot_api import router


def test_copilot_api():
    """Test the copilot API endpoints."""
    print("🌐 Testing Copilot API Endpoints")
    print("=" * 40)
    
    try:
        # Create a test FastAPI app with our router
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        
        # Create test client
        client = TestClient(app)
        
        # Test health endpoint
        print("🔍 Testing health endpoint...")
        response = client.get("/copilot/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check: {data['status']}")
            print(f"📋 Project: {data.get('project_name', 'Unknown')}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
        
        # Test instructions summary
        print("\n📊 Testing instructions summary...")
        response = client.get("/copilot/instructions/summary")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Summary loaded successfully")
            print(f"📋 Project: {data['project_name']}")
            print(f"🔢 Version: {data['version']}")
            summary = data['summary']
            print(f"📊 Content: {summary['key_features_count']} features, {summary['workflow_steps_count']} workflows")
        else:
            print(f"❌ Summary failed: {response.status_code}")
            return False
        
        # Test full instructions (structured format)
        print("\n📖 Testing full instructions (structured)...")
        response = client.get("/copilot/instructions?format=structured")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Structured instructions loaded")
            print(f"📋 Project: {data['project_name']}")
            print(f"🔧 Technology Stack: {len(data['technology_stack'])} items")
            print(f"🔄 Workflow Steps: {len(data['workflow_steps'])} steps")
        else:
            print(f"❌ Structured instructions failed: {response.status_code}")
            return False
        
        # Test workflow commands for a specific category
        print("\n🔄 Testing workflow commands...")
        response = client.get("/copilot/instructions/commands/quality")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Quality commands loaded: {data['command_count']} commands")
            print(f"📝 First command: {data['commands'][0] if data['commands'] else 'None'}")
        else:
            print(f"❌ Workflow commands failed: {response.status_code}")
        
        # Test validation endpoint
        print("\n🔍 Testing validation...")
        response = client.get("/copilot/instructions/validate")
        if response.status_code == 200:
            data = response.json()
            validation = data['validation_results']
            print(f"✅ Validation completed: {validation['overall_status']}")
            file_checks = validation['files_exist']
            existing_files = sum(1 for exists in file_checks.values() if exists)
            print(f"📁 Files checked: {existing_files}/{len(file_checks)} exist")
        else:
            print(f"❌ Validation failed: {response.status_code}")
        
        # Test technology stack endpoint
        print("\n💻 Testing technology stack...")
        response = client.get("/copilot/instructions/technology-stack")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Technology stack loaded: {len(data['technology_stack'])} technologies")
            for tech, desc in list(data['technology_stack'].items())[:3]:
                print(f"  • {tech}: {desc}")
        else:
            print(f"❌ Technology stack failed: {response.status_code}")
        
        # Test guidelines endpoint
        print("\n🚨 Testing critical guidelines...")
        response = client.get("/copilot/instructions/guidelines")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Guidelines loaded: {data['guideline_count']} guidelines")
            if data['critical_guidelines']:
                print(f"📝 First guideline: {data['critical_guidelines'][0][:80]}...")
        else:
            print(f"❌ Guidelines failed: {response.status_code}")
        
        # Test workflows endpoint
        print("\n🔄 Testing workflows...")
        response = client.get("/copilot/instructions/workflows")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Workflows loaded: {data['total_workflow_steps']} steps")
            print(f"📋 Categories: {', '.join(data['categories'])}")
        else:
            print(f"❌ Workflows failed: {response.status_code}")
        
        print("\n🎉 All API tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing API: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_copilot_api()
    
    print("\n" + "=" * 50)
    print("🏁 API Test completed!")
    if success:
        print("✅ Copilot API endpoints are working correctly!")
    else:
        print("❌ API tests failed!")
    print("=" * 50)