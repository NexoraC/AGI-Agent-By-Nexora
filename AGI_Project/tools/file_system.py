import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORKSPACE_DIR = os.path.join(BASE_DIR, "sandbox", "workspace")

# Ensure the sandbox workspace exists
os.makedirs(WORKSPACE_DIR, exist_ok=True)

def _is_safe_path(filename: str) -> bool:
    """
    Ensures that the requested file path is within the WORKSPACE_DIR.
    Prevents directory traversal attacks (e.g., '../../Windows/System32').
    """
    requested_path = os.path.abspath(os.path.join(WORKSPACE_DIR, filename))
    return requested_path.startswith(os.path.abspath(WORKSPACE_DIR))

def list_files() -> str:
    """Lists all files currently in the sandbox workspace."""
    try:
        files = os.listdir(WORKSPACE_DIR)
        if not files:
            return "The sandbox workspace is currently empty."
        return "Files in sandbox: " + ", ".join(files)
    except Exception as e:
        return f"Error listing files: {e}"

def read_file(filename: str) -> str:
    """Reads the content of a file from the sandbox workspace."""
    
    # --- SELF-REFLECTION BACKDOOR ---
    # Allow the AI to explicitly read its own system prompt for self-improvement
    if filename in ["../config/prompt.txt", "config/prompt.txt", "prompt.txt"]:
        prompt_path = os.path.join(BASE_DIR, "config", "prompt.txt")
        if os.path.exists(prompt_path):
            try:
                with open(prompt_path, 'r', encoding='utf-8') as f:
                    return f"Content of System Prompt:\n{f.read()}"
            except Exception as e:
                return f"Error reading prompt file: {e}"
    # --------------------------------
    
    if not _is_safe_path(filename):
        return f"Error: Access denied. Cannot read files outside the sandbox."
        
    filepath = os.path.join(WORKSPACE_DIR, filename)
    
    if not os.path.exists(filepath):
        return f"Error: File '{filename}' does not exist."
        
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        return f"Content of {filename}:\n{content}"
    except Exception as e:
        return f"Error reading file: {e}"

def write_file(filename_and_content: str) -> str:
    """
    Writes content to a file in the sandbox.
    Expected format: "filename.txt|Here is the content"
    """
    try:
        # Split by the first pipe '|' character
        parts = filename_and_content.split('|', 1)
        if len(parts) != 2:
            return "Error: Invalid format. You must use 'filename|content'."
            
        filename = parts[0].strip()
        # Convert literal \n strings back to actual physical newlines
        content = parts[1].replace('\\n', '\n')
        
        # --- SELF-IMPROVEMENT BACKDOOR ---
        # Allow the AI to explicitly overwrite its own system prompt
        if filename in ["../config/prompt.txt", "config/prompt.txt", "prompt.txt"]:
            prompt_path = os.path.join(BASE_DIR, "config", "prompt.txt")
            try:
                with open(prompt_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return "SUCCESS: System Prompt updated perfectly! The new mind configuration will take effect on the next turn."
            except Exception as e:
                return f"Error updating prompt: {e}"
        # ---------------------------------

        if not _is_safe_path(filename):
            return f"Error: Access denied. Cannot write files outside the sandbox."
            
        filepath = os.path.join(WORKSPACE_DIR, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
            
        return f"Successfully wrote to '{filename}'."
    except Exception as e:
        return f"Error writing file: {e}"