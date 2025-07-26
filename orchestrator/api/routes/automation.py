"""Automation API routes."""

from typing import List, Dict, Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from orchestrator.api.app import orchestrator


router = APIRouter()


class AutomationScriptRequest(BaseModel):
    """Automation script execution request."""
    session_id: str
    commands: List[str]
    expect_prompts: Optional[List[str]] = None
    timeout: float = 30.0


class ExpectRequest(BaseModel):
    """Expect pattern request."""
    session_id: str
    patterns: List[str]
    timeout: float = 30.0


@router.post("/execute")
async def execute_script(request: AutomationScriptRequest):
    """Execute automation script on session.
    
    Args:
        request: Script execution request
        
    Returns:
        Execution result
    """
    session = orchestrator.session_manager.get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    if not session.pexpect_handler:
        raise HTTPException(
            status_code=400,
            detail="Session does not have automation enabled"
        )
        
    results = []
    
    try:
        for i, command in enumerate(request.commands):
            # Send command
            prompt = request.expect_prompts[i] if request.expect_prompts and i < len(request.expect_prompts) else "$"
            
            output = session.pexpect_handler.send_command(
                command,
                expect_prompt=True,
                prompt=prompt
            )
            
            results.append({
                "command": command,
                "output": output,
                "success": True
            })
            
    except TimeoutError as e:
        results.append({
            "command": command,
            "output": str(e),
            "success": False
        })
        
    return {
        "session_id": request.session_id,
        "results": results
    }


@router.post("/expect")
async def expect_pattern(request: ExpectRequest):
    """Wait for pattern in session output.
    
    Args:
        request: Expect request
        
    Returns:
        Match result
    """
    session = orchestrator.session_manager.get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    if not session.pexpect_handler:
        raise HTTPException(
            status_code=400,
            detail="Session does not have automation enabled"
        )
        
    try:
        matched_index = session.pexpect_handler.expect(
            request.patterns,
            timeout=request.timeout
        )
        
        return {
            "matched": True,
            "pattern_index": matched_index,
            "pattern": request.patterns[matched_index]
        }
        
    except TimeoutError:
        return {
            "matched": False,
            "pattern_index": -1,
            "pattern": None
        }


@router.get("/templates")
async def list_automation_templates():
    """List available automation templates.
    
    Returns:
        List of templates
    """
    # In production, these would be loaded from files
    templates = [
        {
            "name": "git-clone",
            "description": "Clone a git repository",
            "commands": [
                "cd /workspace",
                "git clone {repository_url}",
                "cd {repository_name}",
                "ls -la"
            ],
            "variables": ["repository_url", "repository_name"]
        },
        {
            "name": "python-setup",
            "description": "Setup Python virtual environment",
            "commands": [
                "cd /workspace",
                "python -m venv venv",
                "source venv/bin/activate",
                "pip install --upgrade pip",
                "pip install -r requirements.txt"
            ],
            "variables": []
        },
        {
            "name": "docker-build",
            "description": "Build Docker image",
            "commands": [
                "cd /workspace",
                "docker build -t {image_name}:{tag} .",
                "docker images | grep {image_name}"
            ],
            "variables": ["image_name", "tag"]
        }
    ]
    
    return templates


@router.post("/templates/{template_name}/execute")
async def execute_template(
    template_name: str,
    session_id: str,
    variables: Optional[Dict[str, str]] = None
):
    """Execute automation template.
    
    Args:
        template_name: Template name
        session_id: Session ID
        variables: Template variables
        
    Returns:
        Execution result
    """
    # Get template (in production, from storage)
    templates = {
        "git-clone": {
            "commands": [
                "cd /workspace",
                "git clone {repository_url}",
                "cd {repository_name}",
                "ls -la"
            ]
        },
        "python-setup": {
            "commands": [
                "cd /workspace",
                "python -m venv venv",
                "source venv/bin/activate",
                "pip install --upgrade pip",
                "pip install -r requirements.txt"
            ]
        }
    }
    
    if template_name not in templates:
        raise HTTPException(status_code=404, detail="Template not found")
        
    # Substitute variables
    commands = templates[template_name]["commands"]
    if variables:
        commands = [cmd.format(**variables) for cmd in commands]
        
    # Execute
    request = AutomationScriptRequest(
        session_id=session_id,
        commands=commands
    )
    
    return await execute_script(request)