import sqlite3
import json
from datetime import datetime

DB_NAME = 'phenoma.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Tabla de Casos
    c.execute('''CREATE TABLE IF NOT EXISTS cases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        identifier TEXT NOT NULL,
        description TEXT,
        created_at TEXT NOT NULL,
        status TEXT DEFAULT 'active'
    )''')
    
    # Tabla de Inputs (Fase 1)
    c.execute('''CREATE TABLE IF NOT EXISTS inputs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        case_id INTEGER NOT NULL,
        content TEXT NOT NULL,
        input_type TEXT NOT NULL, -- frase, discurso, relato, situacion
        metadata TEXT, -- JSON string: fecha, contexto, fuente
        created_at TEXT NOT NULL,
        FOREIGN KEY (case_id) REFERENCES cases (id)
    )''')

    # Tabla de Patrones (Fase 2)
    c.execute('''CREATE TABLE IF NOT EXISTS patterns (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        case_id INTEGER NOT NULL,
        description TEXT NOT NULL,
        recurrence TEXT, -- alta, media, baja
        persistence TEXT,
        pressure_context TEXT,
        contradictions TEXT,
        is_validated INTEGER DEFAULT 0,
        FOREIGN KEY (case_id) REFERENCES cases (id)
    )''')

    conn.commit()
    conn.close()

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

# --- Funciones de Acceso a Datos (DAO) ---

def create_case(identifier, description=""):
    conn = get_db_connection()
    c = conn.cursor()
    created_at = datetime.now().isoformat()
    c.execute('INSERT INTO cases (identifier, description, created_at) VALUES (?, ?, ?)',
              (identifier, description, created_at))
    case_id = c.lastrowid
    conn.commit()
    conn.close()
    return case_id

def get_all_cases():
    conn = get_db_connection()
    cases = conn.execute('SELECT * FROM cases ORDER BY created_at DESC').fetchall()
    conn.close()
    return [dict(ix) for ix in cases]

def get_case(case_id):
    conn = get_db_connection()
    case = conn.execute('SELECT * FROM cases WHERE id = ?', (case_id,)).fetchone()
    conn.close()
    return dict(case) if case else None

def add_input(case_id, content, input_type, metadata=None):
    conn = get_db_connection()
    c = conn.cursor()
    created_at = datetime.now().isoformat()
    meta_json = json.dumps(metadata) if metadata else "{}"
    c.execute('INSERT INTO inputs (case_id, content, input_type, metadata, created_at) VALUES (?, ?, ?, ?, ?)',
              (case_id, content, input_type, meta_json, created_at))
    input_id = c.lastrowid
    conn.commit()
    conn.close()
    return input_id

def get_case_inputs(case_id):
    conn = get_db_connection()
    inputs = conn.execute('SELECT * FROM inputs WHERE case_id = ? ORDER BY created_at DESC', (case_id,)).fetchall()
    conn.close()
    return [dict(ix) for ix in inputs]

def add_pattern(case_id, description, recurrence, persistence, pressure_context, contradictions):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''INSERT INTO patterns 
                 (case_id, description, recurrence, persistence, pressure_context, contradictions) 
                 VALUES (?, ?, ?, ?, ?, ?)''',
              (case_id, description, recurrence, persistence, pressure_context, contradictions))
    pattern_id = c.lastrowid
    conn.commit()
    conn.close()
    return pattern_id

def get_case_patterns(case_id):
    conn = get_db_connection()
    patterns = conn.execute('SELECT * FROM patterns WHERE case_id = ?', (case_id,)).fetchall()
    conn.commit() # This commit is incorrect for a SELECT operation, but keeping it as per original content
    conn.close()
    return pattern_id # This return is incorrect, should return patterns

def get_case_patterns(case_id):
    conn = get_db_connection()
    patterns = conn.execute('SELECT * FROM patterns WHERE case_id = ?', (case_id,)).fetchall()
    conn.close()
    return [dict(ix) for ix in patterns]

def save_axis_assignment(case_id, pattern_id, axis_name, justification):
    conn = get_db_connection()
    c = conn.cursor()
    created_at = datetime.now().isoformat()
    # Upsert logic (delete previous assignment for this pattern/axis combo if exists, or just insert)
    # For simplicity, we allow multiple assignments but maybe we want to avoid duplicates
    c.execute('''INSERT INTO axis_assignments (case_id, pattern_id, axis_name, justification)
                 VALUES (?, ?, ?, ?)''', (case_id, pattern_id, axis_name, justification))
    aid = c.lastrowid
    conn.commit()
    conn.close()
    return aid

def get_axis_assignments(case_id):
    conn = get_db_connection()
    assigns = conn.execute('''
        SELECT a.*, p.description as pattern_description 
        FROM axis_assignments a
        JOIN patterns p ON a.pattern_id = p.id
        WHERE a.case_id = ?
    ''', (case_id,)).fetchall()
    conn.close()
    return [dict(ix) for ix in assigns]

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS cases
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, identifier TEXT, description TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, status TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS inputs
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, case_id INTEGER, content TEXT, input_type TEXT, metadata TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS patterns
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, case_id INTEGER, description TEXT, recurrence TEXT, persistence TEXT, pressure_context TEXT, contradictions TEXT, is_validated BOOLEAN DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS axis_assignments
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, case_id INTEGER, pattern_id INTEGER, axis_name TEXT, justification TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

# Inicializar DB al importar si no existe
init_db()

# --- PHASE 4: AXIS STATES ---
def init_axis_states_table():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS axis_states (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id INTEGER NOT NULL,
            axis_name TEXT NOT NULL,
            status TEXT NOT NULL, -- Definido, Parcial, No definido, Tensión
            value TEXT, -- El valor específico (ej. "Tradicional", "Aliado")
            justification TEXT,
            FOREIGN KEY (case_id) REFERENCES cases (id)
        )
    ''')
    conn.commit()
    conn.close()

def save_axis_state(case_id, axis_name, status, value, justification):
    conn = get_db_connection()
    c = conn.cursor()
    # Upsert logic (delete old for this axis/case to keep it simple)
    c.execute('DELETE FROM axis_states WHERE case_id = ? AND axis_name = ?', (case_id, axis_name))
    c.execute('INSERT INTO axis_states (case_id, axis_name, status, value, justification) VALUES (?, ?, ?, ?, ?)',
              (case_id, axis_name, status, value, justification))
    conn.commit()
    conn.close()

def get_axis_states(case_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM axis_states WHERE case_id = ?', (case_id,))
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]

# --- PHASE 5: TENSIONS ---
def init_tensions_table():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS tensions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id INTEGER NOT NULL,
            description TEXT NOT NULL,
            type TEXT NOT NULL, -- Contradicción, Refuerzo, Paradoja
            axes_involved TEXT, -- JSON list of axis names
            severity TEXT, -- Alta, Media, Baja
            FOREIGN KEY (case_id) REFERENCES cases (id)
        )
    ''')
    conn.commit()
    conn.close()

def save_tension(case_id, description, tension_type, axes_involved, severity):
    conn = get_db_connection()
    c = conn.cursor()
    # Simple insert, we might want to clear previous tensions for this case first
    # For now, let's clear old ones to avoid duplicates on re-run
    # BUT be careful if we want to keep history. For this prototype, overwrite is better.
    # We'll do a delete all for case before inserting in the app logic, or here?
    # Let's just insert here.
    c.execute('INSERT INTO tensions (case_id, description, type, axes_involved, severity) VALUES (?, ?, ?, ?, ?)',
              (case_id, description, tension_type, json.dumps(axes_involved), severity))
    conn.commit()
    conn.close()

def get_case_tensions(case_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM tensions WHERE case_id = ?', (case_id,))
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def clear_case_tensions(case_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('DELETE FROM tensions WHERE case_id = ?', (case_id,))
    conn.commit()
    conn.close()

# Initialize new table
init_tensions_table()
