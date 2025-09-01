"""
Copilot Instructions API endpoints.

This module provides FastAPI endpoints for accessing and managing copilot instructions,
including loading, parsing, validation, and serving the processed content.
"""

import json
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Query, status

from app.services.copilot_service import CopilotInstructionsService


# Create router for copilot instructions endpoints
router = APIRouter(prefix="/copilot", tags=["copilot"])


@router.get("/instructions")
def get_copilot_instructions(
    format: str = Query("json", description="Response format: json or structured"),
    force_reload: bool = Query(False, description="Force reload from file"),
):
    """Get processed copilot instructions."""
    try:
        service = CopilotInstructionsService()
        
        if format == "structured":
            instructions = service.load_instructions(force_reload=force_reload)
            return {
                "project_name": instructions.project_name,
                "version": instructions.version,
                "last_updated": instructions.last_updated,
                "description": instructions.description,
                "key_features": instructions.key_features,
                "technology_stack": instructions.technology_stack,
                "workflow_steps": [
                    {
                        "name": step.name,
                        "category": step.category,
                        "commands": step.commands,
                        "description": step.description
                    }
                    for step in instructions.workflow_steps
                ],
                "configuration_items": [
                    {
                        "key": config.key,
                        "value": config.value,
                        "environment": config.environment,
                        "required": config.required,
                        "description": config.description
                    }
                    for config in instructions.configuration_items
                ],
                "critical_guidelines": instructions.critical_guidelines,
                "deployment_strategies": instructions.deployment_strategies,
                "loaded_at": instructions.loaded_at.isoformat()
            }
        else:
            return json.loads(service.to_json())
            
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Copilot instructions file not found"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing copilot instructions: {str(e)}"
        )


@router.get("/instructions/commands/{category}")
def get_workflow_commands(
    category: str,
    force_reload: bool = Query(False, description="Force reload from file"),
):
    """Get workflow commands for a specific category."""
    try:
        service = CopilotInstructionsService()
        commands = service.get_commands_by_category(category)
        
        if not commands:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No commands found for category: {category}"
            )
        
        return {
            "category": category,
            "commands": commands,
            "command_count": len(commands)
        }
        
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Copilot instructions file not found"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving commands: {str(e)}"
        )


@router.get("/instructions/validate")
def validate_project_setup():
    """Validate current project setup against copilot instructions."""
    try:
        service = CopilotInstructionsService()
        validation_results = service.validate_current_setup()
        
        return {
            "validation_results": validation_results,
            "validated_at": datetime.now(timezone.utc).isoformat()
        }
        
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Copilot instructions file not found"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error validating setup: {str(e)}"
        )


@router.get("/instructions/summary")
def get_instructions_summary():
    """Get a summary of copilot instructions."""
    try:
        service = CopilotInstructionsService()
        instructions = service.load_instructions()
        
        return {
            "project_name": instructions.project_name,
            "version": instructions.version,
            "last_updated": instructions.last_updated,
            "summary": {
                "key_features_count": len(instructions.key_features),
                "technology_stack_count": len(instructions.technology_stack),
                "workflow_steps_count": len(instructions.workflow_steps),
                "configuration_items_count": len(instructions.configuration_items),
                "critical_guidelines_count": len(instructions.critical_guidelines),
                "deployment_strategies_count": len(instructions.deployment_strategies)
            },
            "workflow_categories": list(set(step.category for step in instructions.workflow_steps)),
            "environment_types": list(set(config.environment for config in instructions.configuration_items)),
            "loaded_at": instructions.loaded_at.isoformat()
        }
        
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Copilot instructions file not found"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting summary: {str(e)}"
        )


@router.get("/instructions/technology-stack")
def get_technology_stack():
    """Get technology stack information from copilot instructions."""
    try:
        service = CopilotInstructionsService()
        instructions = service.load_instructions()
        
        return {
            "technology_stack": instructions.technology_stack,
            "project_name": instructions.project_name,
            "version": instructions.version,
            "loaded_at": instructions.loaded_at.isoformat()
        }
        
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Copilot instructions file not found"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving technology stack: {str(e)}"
        )


@router.get("/instructions/guidelines")
def get_critical_guidelines():
    """Get critical development guidelines from copilot instructions."""
    try:
        service = CopilotInstructionsService()
        instructions = service.load_instructions()
        
        return {
            "critical_guidelines": instructions.critical_guidelines,
            "project_name": instructions.project_name,
            "guideline_count": len(instructions.critical_guidelines),
            "loaded_at": instructions.loaded_at.isoformat()
        }
        
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Copilot instructions file not found"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving guidelines: {str(e)}"
        )


@router.get("/instructions/workflows")
def get_workflow_steps():
    """Get all workflow steps organized by category."""
    try:
        service = CopilotInstructionsService()
        instructions = service.load_instructions()
        
        # Organize workflows by category
        workflows_by_category = {}
        for step in instructions.workflow_steps:
            if step.category not in workflows_by_category:
                workflows_by_category[step.category] = []
            
            workflows_by_category[step.category].append({
                "name": step.name,
                "description": step.description,
                "commands": step.commands,
                "command_count": len(step.commands)
            })
        
        return {
            "workflows_by_category": workflows_by_category,
            "total_workflow_steps": len(instructions.workflow_steps),
            "categories": list(workflows_by_category.keys()),
            "project_name": instructions.project_name,
            "loaded_at": instructions.loaded_at.isoformat()
        }
        
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Copilot instructions file not found"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving workflows: {str(e)}"
        )


@router.get("/health")
def copilot_health_check():
    """Health check endpoint for copilot instructions service."""
    try:
        service = CopilotInstructionsService()
        instructions = service.load_instructions()
        
        return {
            "status": "healthy",
            "service": "copilot-instructions",
            "file_loaded": True,
            "project_name": instructions.project_name,
            "last_updated": instructions.last_updated,
            "loaded_at": instructions.loaded_at.isoformat(),
            "data_summary": {
                "key_features": len(instructions.key_features),
                "workflow_steps": len(instructions.workflow_steps),
                "configuration_items": len(instructions.configuration_items),
                "critical_guidelines": len(instructions.critical_guidelines)
            }
        }
        
    except FileNotFoundError:
        return {
            "status": "unhealthy",
            "service": "copilot-instructions",
            "file_loaded": False,
            "error": "Copilot instructions file not found",
            "checked_at": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "copilot-instructions",
            "file_loaded": False,
            "error": f"Error loading copilot instructions: {str(e)}",
            "checked_at": datetime.now(timezone.utc).isoformat()
        }