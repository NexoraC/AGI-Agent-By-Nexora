import requests
import re

def search_web(query: str) -> str:
    """
    A basic web search tool utilizing the free Wikipedia API.
    Returns a short summary of the top results.
    """
    url = "https://en.wikipedia.org/w/api.php"
    
    params = {
        "action": "query",
        "format": "json",
        "list": "search",
        "srsearch": query,
        "utf8": 1,
        "srlimit": 3 # Limit to top 3 results to save LLM context window
    }
    
    # Adding a custom User-Agent header to avoid 403 Forbidden errors from Wikipedia
    headers = {
        "User-Agent": "AGI_Experimental_Core/1.0 (Local Testing)"
    }
    
    try:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        results = data.get("query", {}).get("search", [])
        
        if not results:
            return "No results found on Wikipedia for this query."
            
        snippets = []
        for res in results:
            title = res.get("title", "")
            # Remove HTML tags from the snippet using regex
            raw_snippet = res.get("snippet", "")
            clean_snippet = re.sub(r'<[^>]+>', '', raw_snippet)
            snippets.append(f"Title: {title}\nSummary: {clean_snippet}")
            
        return "\n\n".join(snippets)
        
    except Exception as e:
        return f"Error during web search: {e}"