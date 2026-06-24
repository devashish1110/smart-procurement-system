"""
Instantiate the LLM service and print status — helpful for debugging Groq client initialization.
Run: python scripts/check_llm.py
"""
import traceback
import os
import sys

# Ensure project root is on sys.path so 'backend' package imports work
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def try_import():
    try:
        import importlib
        module = importlib.import_module('backend.ai.llm_service')
        print('Imported backend.ai.llm_service OK')
        return module
    except Exception:
        print('Importing backend.ai.llm_service FAILED')
        traceback.print_exc()
        return None


mod = try_import()
if mod:
    try:
        svc = mod.get_llm_service()
        print('LLM service initialized OK:', type(svc))
    except Exception:
        print('LLM service initialization FAILED after import')
        traceback.print_exc()

    # One-shot generation test (short prompt)
    try:
        print('\nRunning one-shot generation test...')
        resp = svc.generate_response('Hello, can you introduce yourself briefly?')
        print('\nLLM generation result:\n', resp)
    except Exception:
        print('LLM generation FAILED')
        traceback.print_exc()
