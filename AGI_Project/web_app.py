"""
Web wrapper for the AGI Core agent.
Serves a chat UI on port 3000 and exposes a /api/chat endpoint
that runs the ReAct agent loop.
"""

import os
import json
import re
import time
import uuid

from flask import Flask, request, jsonify, render_template

from core.brain import ask_llm
from tools.calculator import calculate
from tools.web_search import search_web
from tools.file_system import read_file, write_file, list_files
from tools.python_runner import run_python_file
from tools.youtube_search import search_youtube
from memory.episodic import log_interaction, search_memory
from memory.semantic import add_to_semantic_memory, search_semantic_memory

app = Flask(__name__)

# In-memory conversation sessions (session_id -> messages list)
sessions = {}

VALID_TOOLS = [
    "calculator", "web_search", "list_files", "read_file", "write_file",
    "run_python", "search_memory", "search_semantic", "learn_lesson",
    "youtube_search", "final_answer"
]


def load_system_prompt():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    prompt_path = os.path.join(base_dir, "config", "prompt.txt")
    try:
        with open(prompt_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return "You are an AI. Use tools formatted as JSON."


def execute_tool(tool_name, query):
    """Execute a single tool and return its result string."""
    if tool_name == "calculator":
        return calculate(query)
    elif tool_name == "web_search":
        return search_web(query)
    elif tool_name == "list_files":
        return list_files()
    elif tool_name == "read_file":
        return read_file(query)
    elif tool_name == "write_file":
        return write_file(query)
    elif tool_name == "run_python":
        return run_python_file(query)
    elif tool_name == "search_memory":
        return search_memory(query)
    elif tool_name == "search_semantic":
        return search_semantic_memory(query)
    elif tool_name == "youtube_search":
        return search_youtube(query)
    elif tool_name == "learn_lesson":
        add_to_semantic_memory(f"lesson_{time.time()}", f"LEARNED FACT: {query}")
        return f"Successfully learned and stored: {query}"
    return f"Unknown tool: {tool_name}"


def run_agent(messages):
    """
    Run the ReAct agent loop.
    Returns (steps, final_answer).
    """
    steps = []
    max_steps = 20
    response = ask_llm(messages)

    for step_count in range(1, max_steps + 1):
        json_match = re.search(r'\{.*\}', response, re.DOTALL)

        if not json_match:
            messages.append({"role": "assistant", "content": response})
            messages.append({"role": "user", "content": "SYSTEM ERROR: You did not output a JSON block. You MUST use a tool in strict JSON format."})
            response = ask_llm(messages)
            continue

        json_str = json_match.group(0)

        try:
            safe_json_str = json_str
            safe_json_str = safe_json_str.replace('\\', '\\\\')
            safe_json_str = safe_json_str.replace('\\"', '"')
            safe_json_str = safe_json_str.replace('\\\\b', '\\b').replace('\\\\f', '\\f').replace('\\\\r', '\\r').replace('\\\\n', '\\n').replace('\\\\t', '\\t')
            safe_json_str = safe_json_str.replace(r'\[', '[').replace(r'\]', ']')

            tool_request = json.loads(safe_json_str)
            tool_name = tool_request.get("tool")
            query = tool_request.get("query", "")

            if tool_name not in VALID_TOOLS:
                raise ValueError(f"Tool '{tool_name}' does not exist.")

            if tool_name == "final_answer":
                steps.append({
                    "step": step_count,
                    "tool": "final_answer",
                    "query": query,
                    "result": None
                })
                return steps, query

            result = execute_tool(tool_name, query)
            steps.append({
                "step": step_count,
                "tool": tool_name,
                "query": query,
                "result": str(result)[:500]
            })

            messages.append({"role": "assistant", "content": json_str})
            messages.append({"role": "user", "content": f"TOOL_RESULT: {result}. Continue."})

            log_interaction("tool_call", json_str)
            log_interaction("tool_result", str(result))

            response = ask_llm(messages)

        except json.JSONDecodeError as e:
            messages.append({"role": "assistant", "content": json_str})
            messages.append({"role": "user", "content": f"SYSTEM ERROR: Invalid JSON format ({e}). You MUST use double quotes for keys and values. Example: {{\"tool\": \"final_answer\", \"query\": \"your message\"}}. Fix it."})
            response = ask_llm(messages)
            continue
        except Exception as e:
            messages.append({"role": "assistant", "content": json_str})
            messages.append({"role": "user", "content": f"SYSTEM ERROR executing tool: {e}. Ensure you are using a valid tool name and format: {{\"tool\": \"tool_name\", \"query\": \"...\"}}."})
            response = ask_llm(messages)
            continue

    return steps, "I ran out of steps to solve this problem."


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_input = data.get('message', '').strip()
    session_id = data.get('session_id')

    if not user_input:
        return jsonify({"error": "Empty message"}), 400

    # Get or create session
    if not session_id or session_id not in sessions:
        session_id = str(uuid.uuid4())
        sessions[session_id] = [{"role": "system", "content": load_system_prompt()}]

    messages = sessions[session_id]

    messages.append({"role": "user", "content": user_input})
    log_interaction("user", user_input)
    add_to_semantic_memory(f"user_{time.time()}", f"User said: {user_input}")

    steps, final_answer = run_agent(messages)

    messages.append({"role": "assistant", "content": final_answer})
    log_interaction("assistant", final_answer)
    add_to_semantic_memory(f"agi_{time.time()}", f"AGI responded: {final_answer}")

    return jsonify({
        "session_id": session_id,
        "steps": steps,
        "answer": final_answer
    })


@app.route('/api/reset', methods=['POST'])
def reset():
    data = request.get_json() or {}
    session_id = data.get('session_id')
    if session_id and session_id in sessions:
        del sessions[session_id]
    return jsonify({"ok": True})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)
