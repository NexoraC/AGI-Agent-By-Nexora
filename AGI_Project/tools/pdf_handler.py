import os

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

def get_workspace_path(filename):
    """Safely resolves the file path to the sandbox workspace."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    workspace_dir = os.path.join(base_dir, "sandbox", "workspace")
    os.makedirs(workspace_dir, exist_ok=True)
    return os.path.join(workspace_dir, filename)

def read_pdf(query):
    """
    Reads all the text from a PDF file located in the sandbox workspace.
    Input query: filename (e.g., 'document.pdf')
    """
    if PdfReader is None:
        return "SYSTEM ERROR: 'pypdf' library is missing. Ask the user to run 'pip install pypdf'."
        
    filename = query.strip()
    filepath = get_workspace_path(filename)
    
    if not os.path.exists(filepath):
        return f"Error: The file '{filename}' does not exist in the sandbox workspace."
        
    try:
        reader = PdfReader(filepath)
        text_content = []
        for i, page in enumerate(reader.pages):
            page_text = page.extract_text()
            if page_text:
                text_content.append(f"--- Page {i+1} ---\n{page_text}")
                
        full_text = "\n".join(text_content)
        if not full_text.strip():
            return "File parsed successfully, but no extractable text was found (it might be scanned images)."
            
        return full_text
    except Exception as e:
        return f"Error reading PDF: {e}"

def analyze_pdf(query):
    """
    Extracts metadata, page count, and a brief preview of a PDF file.
    Input query: filename (e.g., 'report.pdf')
    """
    if PdfReader is None:
        return "SYSTEM ERROR: 'pypdf' library is missing. Ask the user to run 'pip install pypdf'."
        
    filename = query.strip()
    filepath = get_workspace_path(filename)
    
    if not os.path.exists(filepath):
        return f"Error: The file '{filename}' does not exist in the sandbox workspace."
        
    try:
        reader = PdfReader(filepath)
        metadata = reader.metadata
        num_pages = len(reader.pages)
        
        # Get a snippet from the first page
        first_page_snippet = "No text found on page 1."
        if num_pages > 0:
            first_page_text = reader.pages[0].extract_text()
            if first_page_text:
                first_page_snippet = first_page_text[:500] + "..."
                
        analysis = f"""
PDF Analysis for: {filename}
=============================
Total Pages: {num_pages}
Author: {metadata.author if metadata and metadata.author else 'Unknown'}
Title: {metadata.title if metadata and metadata.title else 'Unknown'}
Creator: {metadata.creator if metadata and metadata.creator else 'Unknown'}
Producer: {metadata.producer if metadata and metadata.producer else 'Unknown'}

--- PREVIEW (First Page) ---
{first_page_snippet}
"""
        return analysis
    except Exception as e:
        return f"Error analyzing PDF: {e}"