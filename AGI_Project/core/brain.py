"""
Brain module - LLM provider routing with automatic fallback.
Reconstructed from bytecode (core/__pycache__/brain.cpython-314.pyc).

Routes requests to Gemini (default), Groq, or local Ollama,
falling back down the chain if a provider fails.
"""

import os
import time
import requests
import json
import logging
from typing import List, Dict

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] Brain: %(message)s')
logger = logging.getLogger(__name__)

# --- Provider Configuration (env vars, no hardcoded keys) ---
OLLAMA_API_URL = os.environ.get('OLLAMA_API_URL', 'http://localhost:11434/api/chat')
OLLAMA_MODEL = os.environ.get('OLLAMA_MODEL', 'qwen2.5:14b')
GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')
GROQ_MODEL = os.environ.get('GROQ_MODEL', 'llama-3.3-70b-versatile')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
GEMINI_MODEL = os.environ.get('GEMINI_MODEL', 'gemini-flash-latest')
GEMINI_FALLBACK_MODEL = os.environ.get('GEMINI_FALLBACK_MODEL', 'gemini-flash-lite-latest')
PROVIDER = os.environ.get('PROVIDER', 'gemini')


def ask_llm(messages: List[Dict], temperature: float = 0.0, max_retries: int = 3, timeout: int = 120) -> str:
    """
    Main Interface: Routes the request to Gemini, Groq, or local Ollama,
    with automatic fallback down the chain if a provider fails.
    """
    chain = ('gemini', 'groq', 'ollama')
    # Start from the configured provider, fall back to the rest
    try:
        start = chain.index(PROVIDER)
    except ValueError:
        start = 0
    chain = chain[start:]

    for provider in chain:
        if provider == 'gemini':
            if GEMINI_API_KEY and not GEMINI_API_KEY.startswith('ضع_'):
                result = _ask_gemini(messages, temperature, max_retries, timeout)
                if result:
                    return result
            else:
                logger.warning('Gemini API key missing/invalid, skipping...')
        elif provider == 'groq':
            if GROQ_API_KEY:
                result = _ask_groq(messages, temperature, max_retries, timeout)
                if result:
                    return result
            else:
                logger.warning('Groq API key missing/invalid, skipping...')
        elif provider == 'ollama':
            result = _ask_ollama(messages, temperature, max_retries, timeout)
            if result:
                return result

    return '{"tool": "final_answer", "query": "SYSTEM ERROR: All providers failed."}'


def _mask_secret(text: str) -> str:
    """Strips API keys out of error strings so they never end up in logs/screenshots."""
    for secret in (GEMINI_API_KEY, GROQ_API_KEY):
        if secret:
            text = text.replace(secret, '***')
    return text


def _call_gemini_model(model_name: str, payload: dict, headers: dict, max_retries: int = 3, timeout: int = 120) -> str | None:
    """Tries one specific Gemini model with retries. Returns text, or None if this model failed entirely."""
    url = f'https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={GEMINI_API_KEY}'

    for attempt in range(max_retries):
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=timeout)
            if response.status_code >= 400:
                body = _mask_secret(response.text[:200])
                logger.error(f'Gemini [{model_name}] HTTP {response.status_code} (Attempt {attempt + 1}/{max_retries}): {body}')
                if response.status_code in (400, 401, 403):
                    break  # permanent error — no point retrying
            else:
                response.raise_for_status()
                data = response.json()
                return data['candidates'][0]['content']['parts'][0]['text']
        except Exception as e:
            logger.error(f'Gemini [{model_name}] Error (Attempt {attempt + 1}/{max_retries}): {_mask_secret(str(e))}')
        if attempt < max_retries - 1:
            time.sleep(min(2 ** attempt, 10))
    return None


def _ask_gemini(messages: List[Dict], temperature: float = 0.0, max_retries: int = 3, timeout: int = 120) -> str | None:
    """
    Sends the request to Google's Gemini API. Tries the main model, then a lighter fallback model
    if the main one is overloaded (503). Returns None on total failure (to allow provider fallback).
    """
    headers = {'Content-Type': 'application/json'}
    system_text_parts = []
    contents = []

    for m in messages:
        role = m.get('role')
        text = m.get('content', '')
        if role == 'system':
            system_text_parts.append(text)
        elif role == 'assistant':
            contents.append({'role': 'model', 'parts': [{'text': text}]})
        else:
            contents.append({'role': 'user', 'parts': [{'text': text}]})

    payload = {
        'contents': contents,
        'generationConfig': {
            'temperature': temperature,
            'maxOutputTokens': 4096
        }
    }

    if system_text_parts:
        payload['systemInstruction'] = {'parts': [{'text': '\n'.join(system_text_parts)}]}

    result = _call_gemini_model(GEMINI_MODEL, payload, headers, max_retries, timeout)
    if result:
        return result

    logger.warning(f'Falling back to lighter Gemini model: {GEMINI_FALLBACK_MODEL}')
    result = _call_gemini_model(GEMINI_FALLBACK_MODEL, payload, headers, max_retries, timeout)
    if result:
        return result

    logger.error('All attempts to contact Gemini failed (both models).')
    return None


def _ask_groq(messages: List[Dict], temperature: float = 0.0, max_retries: int = 3, timeout: int = 120) -> str | None:
    """Sends the request to Groq's API. Returns None on total failure (to allow fallback)."""
    url = 'https://api.groq.com/openai/v1/chat/completions'
    headers = {
        'Authorization': f'Bearer {GROQ_API_KEY}',
        'Content-Type': 'application/json; charset=utf-8'
    }
    payload = {
        'model': GROQ_MODEL,
        'messages': messages,
        'temperature': temperature,
        'max_tokens': 4096
    }

    for attempt in range(max_retries):
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=timeout)
            if response.status_code >= 400:
                body = _mask_secret(response.text[:200])
                logger.error(f'Groq API HTTP {response.status_code} (Attempt {attempt + 1}/{max_retries}): {body}')
                if response.status_code in (400, 401, 403):
                    break  # permanent error — no point retrying
            else:
                response.raise_for_status()
                data = response.json()
                return data['choices'][0]['message']['content']
        except Exception as e:
            logger.error(f'Groq API Error (Attempt {attempt + 1}/{max_retries}): {_mask_secret(str(e))}')
        if attempt < max_retries - 1:
            time.sleep(min(2 ** attempt, 10))

    logger.error('All attempts to contact Groq failed.')
    return None


def _ask_ollama(messages: List[Dict], temperature: float = 0.0, max_retries: int = 3, timeout: int = 120) -> str | None:
    """Sends the cognitive reasoning request to the Local Ollama Server (final fallback)."""
    payload = {
        'model': OLLAMA_MODEL,
        'messages': messages,
        'stream': False,
        'keep_alive': '30m',
        'options': {
            'temperature': temperature,
            'top_p': 0.9,
            'num_ctx': 4096
        }
    }
    headers = {'Content-Type': 'application/json'}

    for attempt in range(max_retries):
        try:
            response = requests.post(OLLAMA_API_URL, json=payload, headers=headers, timeout=timeout)
            response.raise_for_status()
            return response.json().get('message', {}).get('content', '')
        except requests.exceptions.ConnectionError:
            logger.error(f'Local Ollama not reachable at {OLLAMA_API_URL} — is it running?')
            break  # connection refused won't fix itself by retrying
        except Exception as e:
            logger.error(f'Local Ollama Error (Attempt {attempt + 1}/{max_retries}): {e}')
        if attempt < max_retries - 1:
            time.sleep(min(2 ** attempt, 10))

    return '{"tool": "final_answer", "query": "SYSTEM ERROR: All LLM providers are offline."}'


if __name__ == '__main__':
    print('Testing connection... Provider chain starts at: ' + PROVIDER.upper())
    test_messages = [{'role': 'user', 'content': "Reply with exactly one word: 'Online'"}]
    start_time = time.time()
    result = ask_llm(test_messages)
    elapsed = time.time() - start_time
    print(f'Response: {result}')
    print(f'Latency: {elapsed:.2f} seconds')
