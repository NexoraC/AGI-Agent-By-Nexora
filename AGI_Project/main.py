from core.brain import ask_llm
from tools.calculator import calculate
from tools.web_search import search_web
from tools.file_system import read_file, write_file, list_files
from tools.python_runner import run_python_file
from tools.youtube_search import search_youtube  # <-- IMPORTED NEW TOOL
from memory.episodic import log_interaction, search_memory
from memory.semantic import add_to_semantic_memory, search_semantic_memory
import json
import time
import os
import re

def load_system_prompt():
    """Loads the system prompt from the external config file."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    prompt_path = os.path.join(base_dir, "config", "prompt.txt")
    
    try:
        with open(prompt_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"⚠️ [WARNING] Failed to load prompt.txt: {e}. Using fallback prompt.")
        return "You are an AI. Use tools formatted as JSON."

def main():
    print("="*50)
    print("🧠 AGI Core Initialized - V8.1 (YouTube Enabled)")
    print("="*50)
    print("Type 'exit' or 'quit' to close.\n")
    
    system_prompt = load_system_prompt()
    messages = [{"role": "system", "content": system_prompt}]
    
    while True:
        user_input = input("User: ")
        
        if user_input.lower() in ['exit', 'quit']:
            print("Shutting down...")
            break
            
        if not user_input.strip():
            continue
            
        print("System is thinking...")
        
        messages.append({"role": "user", "content": user_input})
        log_interaction("user", user_input)
        add_to_semantic_memory(f"user_{time.time()}", f"User said: {user_input}")
        
        # Request the first response from the LLM
        response = ask_llm(messages)
        
        # --- AUTONOMOUS ACTION LOOP (ReAct) ---
        max_steps = 20
        step_count = 0
        final_answer_reached = False
        
        while step_count < max_steps:
            step_count += 1
            
            # 1. SMARTER JSON EXTRACTION (Using Regex to capture everything between { and })
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            
            if not json_match:
                # SYSTEM REFLEX: The LLM hallucinated text instead of JSON. Force it to correct itself!
                print("⚠️ [WARNING] LLM did not output JSON. Forcing self-correction...")
                error_msg = "SYSTEM ERROR: You did not output a JSON block. You MUST use a tool in strict JSON format."
                messages.append({"role": "assistant", "content": response})
                messages.append({"role": "user", "content": error_msg})
                response = ask_llm(messages)
                continue
                
            json_str = json_match.group(0)
            
            try:
                # 2. BULLETPROOF SANITIZATION
                safe_json_str = json_str
                safe_json_str = safe_json_str.replace('\\', '\\\\') # Escape ALL backslashes first
                safe_json_str = safe_json_str.replace('\\\\"', '\\"') 
                safe_json_str = safe_json_str.replace('\\\\b', '\\b').replace('\\\\f', '\\f').replace('\\\\r', '\\r').replace('\\\\n', '\\n').replace('\\\\t', '\\t')
                safe_json_str = safe_json_str.replace(r'\[', '[').replace(r'\]', ']')
                
                tool_request = json.loads(safe_json_str)
                tool_name = tool_request.get("tool")
                query = tool_request.get("query", "")
                
                # <-- ADDED youtube_search TO VALID TOOLS
                valid_tools = ["calculator", "web_search", "list_files", "read_file", "write_file", "run_python", "search_memory", "search_semantic", "learn_lesson", "youtube_search", "final_answer"]
                
                if tool_name not in valid_tools:
                    raise ValueError(f"Tool '{tool_name}' does not exist.")
                    
                if tool_name == "final_answer":
                    print(f"\n🎯 [GOAL REACHED] Final Answer Ready.")
                    response = query 
                    final_answer_reached = True
                    break
                    
                print(f"\n🔧 [STEP {step_count}] Using Tool: {tool_name.upper()}")
                print(f"🔧 [QUERY]  {query}")
                
                # Execute Tools
                if tool_name == "calculator": result = calculate(query)
                elif tool_name == "web_search": result = search_web(query)
                elif tool_name == "list_files": result = list_files()
                elif tool_name == "read_file": result = read_file(query)
                elif tool_name == "write_file": result = write_file(query)
                elif tool_name == "run_python": result = run_python_file(query)
                elif tool_name == "search_memory": result = search_memory(query)
                elif tool_name == "search_semantic": result = search_semantic_memory(query)
                elif tool_name == "youtube_search": result = search_youtube(query)  # <-- EXECUTING NEW TOOL
                elif tool_name == "learn_lesson":
                    add_to_semantic_memory(f"lesson_{time.time()}", f"LEARNED FACT: {query}")
                    result = f"Successfully learned and stored: {query}"
                    
                print(f"⚙️ [RESULT] {result}\n")
                
                # Feed result back to LLM
                messages.append({"role": "assistant", "content": json_str})
                messages.append({"role": "user", "content": f"TOOL_RESULT: {result}. Continue."})
                
                log_interaction("tool_call", json_str)
                log_interaction("tool_result", str(result))
                
                print("System is thinking about the next step...")
                response = ask_llm(messages) 
                
            except json.JSONDecodeError as e:
                print(f"⚠️ [JSON ERROR] {e}. Forcing LLM to fix its JSON...")
                messages.append({"role": "assistant", "content": json_str})
                messages.append({"role": "user", "content": f"SYSTEM ERROR: Invalid JSON format ({e}). You MUST use double quotes for keys and values. Example: {{\"tool\": \"final_answer\", \"query\": \"your message\"}}. Fix it."})
                response = ask_llm(messages)
                continue
            except Exception as e:
                print(f"⚠️ [EXECUTION ERROR] {e}. Forcing LLM to handle it...")
                messages.append({"role": "assistant", "content": json_str})
                messages.append({"role": "user", "content": f"SYSTEM ERROR executing tool: {e}. Ensure you are using a valid tool name and format: {{\"tool\": \"tool_name\", \"query\": \"...\"}}."})
                response = ask_llm(messages)
                continue
            
        if not final_answer_reached and step_count >= max_steps:
            print(f"⚠️ [WARNING] Reached maximum autonomous steps ({max_steps}).")
            response = "I ran out of steps to solve this problem."
        
        print("\nAGI:")
        print(response)
        messages.append({"role": "assistant", "content": response})
        log_interaction("assistant", response) 
        add_to_semantic_memory(f"agi_{time.time()}", f"AGI responded: {response}")
        print("-" * 50)

if __name__ == "__main__":
    main()