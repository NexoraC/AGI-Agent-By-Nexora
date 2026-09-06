import os
import subprocess

WORKSPACE_DIR = os.path.abspath("sandbox/workspace")
os.makedirs(WORKSPACE_DIR, exist_ok=True)

def calculator(expression):
    """Evaluates basic math expressions safely."""
    try:
        # Using eval with restricted globals for basic safety
        allowed_names = {"__builtins__": None}
        result = eval(expression, allowed_names, {})
        return str(result)
    except Exception as e:
        return f"Calculator Error: {str(e)}"

def list_files(_query=None):
    """Lists all files in the sandbox workspace. Ignores the query parameter."""
    try:
        files = os.listdir(WORKSPACE_DIR)
        if not files:
            return "The workspace is empty."
        return "\n".join(files)
    except Exception as e:
        return f"Error listing files: {str(e)}"

def run_python(filename):
    """Executes a Python script located in the sandbox workspace."""
    filepath = os.path.abspath(os.path.join(WORKSPACE_DIR, filename))
    
    # Security check to prevent directory traversal
    if not filepath.startswith(WORKSPACE_DIR):
        return "Error: Path violation. Cannot execute files outside the workspace."
        
    if not os.path.exists(filepath):
        return f"Error: File '{filename}' does not exist."

    try:
        # Run the script and capture output, with a timeout to prevent infinite loops
        result = subprocess.run(
            ["python", filepath],
            capture_output=True,
            text=True,
            timeout=10 
        )
        output = result.stdout
        if result.stderr:
            output += f"\nErrors:\n{result.stderr}"
            
        return output.strip() if output.strip() else "Script executed successfully with no output."
    except subprocess.TimeoutExpired:
        return "Error: Script execution timed out after 10 seconds."
    except Exception as e:
        return f"Execution Error: {str(e)}"