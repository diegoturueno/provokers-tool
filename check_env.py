import sys
import os
import sqlite3
from database import get_case_inputs, init_db

print(f"Python: {sys.version}")

# 1. Check Database
print("\nChecking Database...")
try:
    init_db()
    # Create a dummy case if needed or check existing
    conn = sqlite3.connect('phenoma.db')
    cursor = conn.cursor()
    cursor.execute("SELECT count(*) FROM cases")
    count = cursor.fetchone()[0]
    print(f"Cases found: {count}")
    conn.close()
except Exception as e:
    print(f"Database Error: {e}")

# 2. Check Ollama
print("\nChecking Ollama...")
try:
    import ollama
    print("Ollama module imported.")
    try:
        # List models to check connection
        models = ollama.list()
        print("Ollama connection successful.")
        # Check if llama3 exists
        has_llama3 = any('llama3' in m.get('name', '') for m in models.get('models', []))
        print(f"Has llama3: {has_llama3}")
    except Exception as e:
        print(f"Ollama Connection Error: {e}")
        print("Make sure Ollama is running (ollama serve).")
except ImportError:
    print("Ollama module NOT installed.")
