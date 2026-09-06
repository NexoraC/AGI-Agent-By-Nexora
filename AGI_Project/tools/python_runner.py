import subprocess
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORKSPACE_DIR = os.path.join(BASE_DIR, "sandbox", "workspace")

def run_python_file(filename: str) -> str:
    """
    Executes a python file located in the sandbox workspace.
    Returns the standard output and standard error.
    Includes a timeout to prevent infinite loops.
    """
    # Clean up the filename in case the LLM adds "python " at the beginning
    if filename.startswith("python "):
        filename = filename.replace("python ", "", 1).strip()
        
    filepath = os.path.join(WORKSPACE_DIR, filename)
    
    if not os.path.exists(filepath):
        return f"Error: File '{filename}' does not exist in the sandbox."
        
    try:
        # Using subprocess.run to execute the python script
        # timeout=10 ensures the agent can't freeze the system with an infinite loop (e.g. while True: pass)
        result = subprocess.run(
            ["python", filepath],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=WORKSPACE_DIR # Force execution directory to be the sandbox
        )
        
        output = result.stdout
        
        if result.stderr:
            output += f"\n[ERRORS]:\n{result.stderr}"
            
        if not output.strip():
            return "Script executed successfully but produced no output (no print statements)."
            
        return output
        
    except subprocess.TimeoutExpired:
        return "Error: Script execution timed out (exceeded 10 seconds). The code might have an infinite loop."
    except Exception as e:
        return f"Error executing script: {e}"