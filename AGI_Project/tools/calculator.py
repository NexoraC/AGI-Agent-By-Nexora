import re

def calculate(expression: str) -> str:
    """
    A simple and relatively safe calculator tool.
    Limits the evaluation to basic math operations to avoid execution vulnerabilities.
    """
    try:
        # Remove any characters that are not numbers or basic operators
        cleaned_expr = re.sub(r'[^0-9+\-*/().\s]', '', expression)
        
        if not cleaned_expr.strip():
            return "Error: Empty or invalid expression."
            
        # Using eval with empty built-ins to prevent dangerous code execution (Sandbox Stub)
        result = eval(cleaned_expr, {"__builtins__": None}, {})
        
        return str(result)
        
    except Exception as e:
        return f"Error during calculation: {e}"