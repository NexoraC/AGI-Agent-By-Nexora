import os
import json
from core.brain import ask_llm

def get_workspace_path(filename):
    """Safely resolves the file path to the sandbox workspace."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    workspace_dir = os.path.join(base_dir, "sandbox", "workspace")
    os.makedirs(workspace_dir, exist_ok=True)
    
    # Security: Prevent path traversal
    safe_name = os.path.basename(filename)
    return os.path.join(workspace_dir, safe_name)

def write_code(query):
    """
    Writes code to a specific file in the sandbox workspace.
    Requires delimiter "|||" in the query.
    Input query format: "filename.extension|||<code>"
    Example: "index.html|||<!DOCTYPE html><html>..."
    """
    try:
        parts = query.split("|||", 1)
        if len(parts) != 2:
            return "Error: Invalid format. You must separate the filename and the code with '|||'. Example: app.js|||console.log('test');"
            
        filename = parts[0].strip()
        code_content = parts[1].strip()
        
        filepath = get_workspace_path(filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(code_content)
            
        return f"Success! Code written to {filename}. Format detected: {filename.split('.')[-1].upper()}."
    except Exception as e:
        return f"Failed to write code: {str(e)}"

def plan_task(query):
    """
    Acts as a sub-agent to break down a complex task into a structured plan.
    Input query: "A description of the complex task to plan"
    """
    planner_prompt = (
        "You are an expert Project Manager and Architect AI sub-agent. "
        "Your job is to take the user's objective and break it down into a highly detailed, logical, step-by-step technical plan. "
        "Do not write the code itself, just provide the blueprint, file structure, and sequential steps needed."
    )
    
    messages = [
        {"role": "system", "content": planner_prompt},
        {"role": "user", "content": f"Create a step-by-step execution plan for this task: {query}"}
    ]
    
    try:
        # Calls the local LLM silently in the background
        plan_result = ask_llm(messages)
        return f"--- Sub-Agent Execution Plan ---\n{plan_result}\n--- End Plan ---"
    except Exception as e:
        return f"Planning sub-agent failed: {str(e)}"

def fix_code(query):
    """
    Acts as a sub-agent to debug errors and fix broken code.
    Input query: "Error message details OR broken code snippet"
    """
    fixer_prompt = (
        "You are an expert Senior Software Engineer AI sub-agent. "
        "Your task is to analyze the provided error message or broken code snippet. "
        "Identify the root cause of the bug and provide the EXACT corrected code. "
        "Keep your explanation very brief, prioritize providing the fixed, complete code block."
    )
    
    messages = [
        {"role": "system", "content": fixer_prompt},
        {"role": "user", "content": f"Analyze and fix the following issue:\n\n{query}"}
    ]
    
    try:
        # Calls the local LLM silently in the background
        fix_result = ask_llm(messages)
        return f"--- Sub-Agent Code Fix ---\n{fix_result}\n--- End Fix ---"
    except Exception as e:
        return f"Fixer sub-agent failed: {str(e)}"