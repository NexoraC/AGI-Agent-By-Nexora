import urllib.request
import urllib.parse
import re
import json

def search_youtube(query: str, max_results: int = 3) -> str:
    """
    Searches YouTube and returns video titles and URLs.
    Uses zero external dependencies.
    """
    try:
        encoded_query = urllib.parse.quote(query)
        url = f"https://www.youtube.com/results?search_query={encoded_query}"
        
        # Disguise the request to avoid being blocked
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
        html = urllib.request.urlopen(req).read().decode('utf-8')
        
        # Attempt to extract the initial JSON data embedded in the YouTube page
        match = re.search(r'ytInitialData\s*=\s*({.+?});\s*</script>', html)
        
        if not match:
            # Fallback: simple regex to just grab Video IDs if JSON parsing fails
            video_ids = re.findall(r"watch\?v=(\S{11})", html)
            unique_ids = list(dict.fromkeys(video_ids)) # Deduplicate while preserving order
            
            if not unique_ids:
                return "No results found on YouTube."
                
            urls = [f"https://www.youtube.com/watch?v={vid}" for vid in unique_ids[:max_results]]
            return "Found YouTube URLs (Titles unavailable):\n" + "\n".join(urls)

        data = json.loads(match.group(1))
        results = []
        
        # Drill down into YouTube's JSON structure to get titles and IDs
        try:
            contents = data['contents']['twoColumnSearchResultsRenderer']['primaryContents']['sectionListRenderer']['contents'][0]['itemSectionRenderer']['contents']
            for item in contents:
                if 'videoRenderer' in item:
                    vid = item['videoRenderer']['videoId']
                    title = item['videoRenderer']['title']['runs'][0]['text']
                    results.append(f"- {title}: https://www.youtube.com/watch?v={vid}")
                    if len(results) >= max_results:
                        break
        except KeyError:
            pass
        
        if not results:
            return "Could not parse search results."
            
        return "YouTube Search Results:\n" + "\n".join(results)
        
    except Exception as e:
        return f"Error searching YouTube: {str(e)}"