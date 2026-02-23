import sqlite3
import json
import os
from datetime import datetime

# Get absolute path to the directory where this script is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Force DB to be in this directory
DB_NAME = os.path.join(BASE_DIR, 'phenoma.db')

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    
    # 0. Projects Framework (Fase 0.5)
    c.execute('''CREATE TABLE IF NOT EXISTS projects
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, description TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

    # 1. Crear Tablas Principales
    c.execute('''CREATE TABLE IF NOT EXISTS cases
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, identifier TEXT, description TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, status TEXT)''')
    
    # Check if project_id exists in cases, if not add it (Migration)
    c.execute("PRAGMA table_info(cases)")
    columns = [info[1] for info in c.fetchall()]
    if 'project_id' not in columns:
        print("Migrating DB: Adding project_id to cases table...")
        c.execute('ALTER TABLE cases ADD COLUMN project_id INTEGER DEFAULT 1')
        # Create default project if needed
        c.execute('INSERT OR IGNORE INTO projects (id, name, description) VALUES (1, "General", "Carpeta por defecto para casos migrados")')
        c.execute('UPDATE cases SET project_id = 1 WHERE project_id IS NULL')

    c.execute('''CREATE TABLE IF NOT EXISTS inputs
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, case_id INTEGER, content TEXT, input_type TEXT, metadata TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (case_id) REFERENCES cases (id))''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS patterns
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, case_id INTEGER, description TEXT, recurrence TEXT, persistence TEXT, pressure_context TEXT, contradictions TEXT, is_validated BOOLEAN DEFAULT 0, FOREIGN KEY (case_id) REFERENCES cases (id))''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS axis_assignments
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, case_id INTEGER, pattern_id INTEGER, axis_name TEXT, justification TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (case_id) REFERENCES cases (id))''')

    # 2. Fase 4: Estados de Ejes
    c.execute('''CREATE TABLE IF NOT EXISTS axis_states (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id INTEGER NOT NULL,
            axis_name TEXT NOT NULL,
            status TEXT NOT NULL,
            value TEXT,
            justification TEXT,
            FOREIGN KEY (case_id) REFERENCES cases (id)
        )''')

    # 3. Fase 5: Tensiones
    c.execute('''CREATE TABLE IF NOT EXISTS tensions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id INTEGER NOT NULL,
            description TEXT NOT NULL,
            type TEXT NOT NULL,
            axes_involved TEXT,
            severity TEXT,
            FOREIGN KEY (case_id) REFERENCES cases (id)
        )''')

    # 4. Fase 6: Umbral
    c.execute('''CREATE TABLE IF NOT EXISTS threshold_evaluations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id INTEGER NOT NULL,
            score INTEGER NOT NULL,
            status TEXT NOT NULL,
            reasoning TEXT,
            created_at TEXT
        )''')

    # 5. Fase 7: Arquetipo
    c.execute('''CREATE TABLE IF NOT EXISTS archetype_assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id INTEGER NOT NULL,
            archetype_name TEXT NOT NULL,
            description TEXT,
            fit_score INTEGER,
            key_traits TEXT,
            created_at TEXT
        )''')
    # 6. Reportes de Proyecto
    c.execute('''CREATE TABLE IF NOT EXISTS project_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL UNIQUE,
            report_data TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE
        )''')

    conn.commit()
    conn.close()
# --- PROJECT DAOs ---

def create_project(name, description=""):
    conn = get_db_connection()
    c = conn.cursor()
    created_at = datetime.now().isoformat()
    c.execute('INSERT INTO projects (name, description, created_at) VALUES (?, ?, ?)',
              (name, description, created_at))
    pid = c.lastrowid
    conn.commit()
    conn.close()
    return pid

def get_all_projects():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        SELECT p.*, COUNT(c.id) as case_count 
        FROM projects p 
        LEFT JOIN cases c ON p.id = c.project_id 
        GROUP BY p.id 
        ORDER BY p.created_at DESC
    ''')
    projects = c.fetchall()
    conn.close()
    return [dict(ix) for ix in projects]

def get_project(project_id):
    conn = get_db_connection()
    project = conn.execute('SELECT * FROM projects WHERE id = ?', (project_id,)).fetchone()
    conn.close()
    return dict(project) if project else None

def delete_project(project_id):
    conn = get_db_connection()
    c = conn.cursor()
    # Delete all cases in project (cascade logic implemented manually)
    cases = c.execute('SELECT id FROM cases WHERE project_id = ?', (project_id,)).fetchall()
    for case_row in cases:
        case_id = case_row['id']
        # Delete case data (tables list from delete_case)
        tables = ['inputs', 'patterns', 'axis_assignments', 'axis_states', 'tensions', 'threshold_evaluations', 'archetype_assignments']
        for table in tables:
             try: c.execute(f'DELETE FROM {table} WHERE case_id = ?', (case_id,))
             except: pass
        c.execute('DELETE FROM cases WHERE id = ?', (case_id,))
    
    # Finally delete project
    c.execute('DELETE FROM projects WHERE id = ?', (project_id,))
    conn.commit()
    conn.close()
    return True

# --- Funciones de Acceso a Datos (DAO) ---

def create_case(identifier, description="", project_id=1):
    conn = get_db_connection()
    c = conn.cursor()
    created_at = datetime.now().isoformat()
    c.execute('INSERT INTO cases (identifier, description, project_id, created_at) VALUES (?, ?, ?, ?)',
              (identifier, description, project_id, created_at))
    case_id = c.lastrowid
    conn.commit()
    conn.close()
    return case_id

def get_all_cases(project_id=None):
    conn = get_db_connection()
    if project_id:
        cases = conn.execute('SELECT * FROM cases WHERE project_id = ? ORDER BY created_at DESC', (project_id,)).fetchall()
    else:
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
    tables = ['inputs', 'patterns', 'axis_assignments', 'axis_states', 'tensions', 'threshold_evaluations', 'archetype_assignments']
    for table in tables:
        try:
            c.execute(f'DELETE FROM {table} WHERE case_id = ?', (case_id,))
        except sqlite3.OperationalError:
            pass # Table might not exist yet
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

# --- PHASE 4: AXIS STATES ---

def save_axis_state(case_id, axis_name, status, value, justification):
    conn = get_db_connection()
    c = conn.cursor()
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

def save_tension(case_id, description, tension_type, axes_involved, severity):
    conn = get_db_connection()
    c = conn.cursor()
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

# --- PHASE 6: THRESHOLD EVALUATION ---

def save_threshold_evaluation(case_id, score, status, reasoning):
    conn = get_db_connection()
    c = conn.cursor()
    created_at = datetime.now().isoformat()
    c.execute('DELETE FROM threshold_evaluations WHERE case_id = ?', (case_id,))
    c.execute('INSERT INTO threshold_evaluations (case_id, score, status, reasoning, created_at) VALUES (?, ?, ?, ?, ?)',
              (case_id, score, status, reasoning, created_at))
    conn.commit()
    conn.close()

def get_threshold_evaluation(case_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM threshold_evaluations WHERE case_id = ?', (case_id,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None

# --- PHASE 7: ARCHETYPE ASSIGNMENT ---

def save_archetype_assignment(case_id, name, description, fit_score, key_traits):
    conn = get_db_connection()
    c = conn.cursor()
    created_at = datetime.now().isoformat()
    c.execute('DELETE FROM archetype_assignments WHERE case_id = ?', (case_id,))
    c.execute('INSERT INTO archetype_assignments (case_id, archetype_name, description, fit_score, key_traits, created_at) VALUES (?, ?, ?, ?, ?, ?)',
              (case_id, name, description, fit_score, json.dumps(key_traits), created_at))
    conn.commit()
    conn.close()

def get_archetype_assignment(case_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM archetype_assignments WHERE case_id = ?', (case_id,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None

# --- PROJECT AGGREGATION ---
def get_project_cases_full(project_id):
    cases = get_all_cases(project_id)
    full_data = []
    for case in cases:
        c_id = case['id']
        case_dict = dict(case)
        case_dict['archetype'] = get_archetype_assignment(c_id)
        case_dict['axis_states'] = get_axis_states(c_id)
        case_dict['patterns'] = get_case_patterns(c_id)
        full_data.append(case_dict)
    return full_data

# --- PROJECT REPORTS ---
def save_project_report(project_id, report_data):
    conn = get_db_connection()
    c = conn.cursor()
    created_at = datetime.now().isoformat()
    # Replace existing or insert new
    c.execute('DELETE FROM project_reports WHERE project_id = ?', (project_id,))
    c.execute('INSERT INTO project_reports (project_id, report_data, created_at) VALUES (?, ?, ?)',
              (project_id, json.dumps(report_data), created_at))
    conn.commit()
    conn.close()

def get_project_report(project_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM project_reports WHERE project_id = ?', (project_id,))
    row = c.fetchone()
    conn.close()
    if row:
        data = dict(row)
        try:
            data['report_data'] = json.loads(data['report_data'])
        except:
            data['report_data'] = {}
        return data
    return None


# Inicializar DB al importar si no existe
init_db()
