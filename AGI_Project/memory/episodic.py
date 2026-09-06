import sqlite3
import os
import datetime

# Define paths for the database
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "memory.db")

# Ensure the data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

def init_db():
    """
    Initializes the SQLite database and creates the episodic log table.
    This stores a permanent record of all interactions.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create a table for episodic memory if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS episodic_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            role TEXT,
            content TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

def log_interaction(role: str, content: str):
    """
    Saves a single interaction to the long-term SQLite memory.
    :param role: 'user', 'assistant', 'tool_call', or 'tool_result'
    :param content: The actual text content
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get current time in ISO format
        timestamp = datetime.datetime.now().isoformat()
        
        cursor.execute('''
            INSERT INTO episodic_log (timestamp, role, content)
            VALUES (?, ?, ?)
        ''', (timestamp, role, content))
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"⚠️ [MEMORY ERROR] Failed to log interaction: {e}")

def search_memory(query: str, limit: int = 5) -> str:
    """
    Searches the episodic memory for a specific keyword or phrase.
    Returns the most recent interactions matching the query.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Using LIKE for basic text search. 
        # (Later in V2, we will use ChromaDB for semantic search).
        cursor.execute('''
            SELECT timestamp, role, content 
            FROM episodic_log 
            WHERE content LIKE ? 
            ORDER BY id DESC 
            LIMIT ?
        ''', (f'%{query}%', limit))
        
        results = cursor.fetchall()
        conn.close()
        
        if not results:
            return f"No memories found containing '{query}'."
            
        memory_str = f"Found {len(results)} past memories:\n"
        for row in results:
            timestamp, role, content = row
            # Truncate content slightly to save context window if it's too long
            short_content = content[:200] + "..." if len(content) > 200 else content
            memory_str += f"[{timestamp}] {role.upper()}: {short_content}\n"
            
        return memory_str
    except Exception as e:
        return f"Error retrieving memory: {e}"

# Initialize the database automatically when this module is imported
init_db()