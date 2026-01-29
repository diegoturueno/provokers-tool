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

def delete_case(case_id):
    conn = get_db_connection()
    c = conn.cursor()
    
    # Delete from all tables referencing case_id
    # Order matters slightly if we had strict foreign key enforcement enabled, 
    # but here we just want to be thorough.
    tables = [
        'inputs', 
        'patterns', 
        'axis_assignments', 
        'axis_states', 
        'tensions', 
        'threshold_evaluations', 
        'archetype_assignments'
    ]
    
    for table in tables:
        c.execute(f'DELETE FROM {table} WHERE case_id = ?', (case_id,))
        
    # Finally delete the case itself
    c.execute('DELETE FROM cases WHERE id = ?', (case_id,))
    
    conn.commit()
    conn.close()
    return True

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
    
    # 1. Core Tables
    c.execute('''CREATE TABLE IF NOT EXISTS cases
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, identifier TEXT, description TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, status TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS inputs
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, case_id INTEGER, content TEXT, input_type TEXT, metadata TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS patterns
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, case_id INTEGER, description TEXT, recurrence TEXT, persistence TEXT, pressure_context TEXT, contradictions TEXT, is_validated BOOLEAN DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS axis_assignments
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, case_id INTEGER, pattern_id INTEGER, axis_name TEXT, justification TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

    # 2. Phase 4: Axis States
    c.execute('''
        CREATE TABLE IF NOT EXISTS axis_states (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id INTEGER NOT NULL,
            axis_name TEXT NOT NULL,
            status TEXT NOT NULL,
            value TEXT,
            justification TEXT,
            FOREIGN KEY (case_id) REFERENCES cases (id)
        )
    ''')

    # 3. Phase 5: Tensions
    c.execute('''
        CREATE TABLE IF NOT EXISTS tensions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id INTEGER NOT NULL,
            description TEXT NOT NULL,
            type TEXT NOT NULL,
            axes_involved TEXT,
            severity TEXT,
            FOREIGN KEY (case_id) REFERENCES cases (id)
        )
    ''')

    # 4. Phase 6: Threshold
    c.execute('''
        CREATE TABLE IF NOT EXISTS threshold_evaluations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id INTEGER NOT NULL,
            score INTEGER NOT NULL,
            status TEXT NOT NULL,
            reasoning TEXT,
            created_at TEXT
        )
    ''')

    # 5. Phase 7: Archetype
    c.execute('''
        CREATE TABLE IF NOT EXISTS archetype_assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id INTEGER NOT NULL,
            archetype_name TEXT NOT NULL,
            description TEXT,
            fit_score INTEGER,
            key_traits TEXT,
            created_at TEXT
        )
    ''')

    conn.commit()
    conn.close()

# Inicializar DB al importar si no existe
init_db()
