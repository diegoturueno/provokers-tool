from flask import Flask, render_template, request, jsonify
import os
import database as db
from classifier import classify_stimulus_openai, classify_stimulus_local, load_model_definition

app = Flask(__name__)

# --- Rutas de Vistas (Frontend) ---

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/case/<int:case_id>')
def case_view(case_id):
    return render_template('case_view.html', case_id=case_id)

# --- API Endpoints ---

# FASE 0: Gestión de Casos
@app.route('/api/cases', methods=['GET'])
def list_cases():
    cases = db.get_all_cases()
    return jsonify(cases)

@app.route('/api/cases', methods=['POST'])
def create_case():
    data = request.json
    identifier = data.get('identifier')
    description = data.get('description', '')
    
    if not identifier:
        return jsonify({'error': 'Identificador es requerido'}), 400
        
    case_id = db.create_case(identifier, description)
    return jsonify({'id': case_id, 'message': 'Caso creado exitosamente'})

@app.route('/api/cases/<int:case_id>', methods=['GET'])
def get_case_details(case_id):
    case = db.get_case(case_id)
    if not case:
        return jsonify({'error': 'Caso no encontrado'}), 404
    return jsonify(case)

# FASE 1: Inputs
@app.route('/api/cases/<int:case_id>/inputs', methods=['GET'])
def list_inputs(case_id):
    inputs = db.get_case_inputs(case_id)
    return jsonify(inputs)

@app.route('/api/cases/<int:case_id>/inputs', methods=['POST'])
def add_input(case_id):
    data = request.json
    content = data.get('content')
    input_type = data.get('input_type', 'frase')
    metadata = data.get('metadata', {})
    
    if not content:
        return jsonify({'error': 'Contenido es requerido'}), 400
        
    input_id = db.add_input(case_id, content, input_type, metadata)
    return jsonify({'id': input_id, 'message': 'Input registrado'})

# FASE 2: Patrones
@app.route('/api/cases/<int:case_id>/patterns', methods=['GET'])
def list_patterns(case_id):
    patterns = db.get_case_patterns(case_id)
    return jsonify(patterns)

@app.route('/api/cases/<int:case_id>/analyze/patterns', methods=['POST'])
def analyze_patterns(case_id):
    try:
        data = request.json or {}
        mode = data.get('mode', 'local')
        
        # 1. Obtener inputs
        inputs = db.get_case_inputs(case_id)
        if not inputs:
            return jsonify({'error': 'No hay inputs para analizar'}), 400
        
        # 2. Formatear inputs
        inputs_text = "\n".join([f"- [{i['input_type']}] {i['content']} (Fecha: {i.get('created_at', '')})" for i in inputs])
        
        # 3. Cargar prompt
        try:
            with open('prompts/pattern_detection.md', 'r', encoding='utf-8') as f:
                prompt_template = f.read()
        except FileNotFoundError:
            return jsonify({'error': 'Prompt de patrones no encontrado'}), 500

        # FIX: Usar replace en lugar de format porque el prompt contiene JSON con llaves {}
        system_prompt = prompt_template.replace('{inputs_text}', inputs_text)
        
        patterns = []
        
        if mode == 'cloud':
            # OpenAI Logic
            from openai import OpenAI
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                return jsonify({'error': 'Falta OPENAI_API_KEY en .env'}), 400
                
            client = OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "system", "content": system_prompt}],
                response_format={"type": "json_object"},
                temperature=0.2
            )
            import json
            result_json = json.loads(response.choices[0].message.content)
            # Manejar si devuelve lista o dict
            if isinstance(result_json, list):
                patterns = result_json
            else:
                patterns = result_json.get('patterns', result_json)
            
        else:
            # Ollama Logic (Local)
            import ollama
            local_prompt = system_prompt + "\n\nIMPORTANTE: Responde ÚNICAMENTE con el JSON válido. Sin markdown, sin explicaciones."
            
            response = ollama.chat(model='llama3', messages=[
                {'role': 'user', 'content': local_prompt},
            ])
            content = response['message']['content']
            
            import json
            import re
            match = re.search(r'(\[.*\]|\{.*\})', content, re.DOTALL)
            if match:
                json_str = match.group(1)
                try:
                    result_json = json.loads(json_str)
                    # Manejar si devuelve lista o dict
                    if isinstance(result_json, list):
                        patterns = result_json
                    else:
                        patterns = result_json.get('patterns', result_json)
                except json.JSONDecodeError:
                     return jsonify({'error': 'La IA devolvió un JSON malformado.'}), 500
            else:
                return jsonify({'error': 'La IA local no devolvió un JSON válido.'}), 500

        # Normalizar lista (asegurar que es lista de dicts)
        if isinstance(patterns, dict): patterns = [patterns]
        if not isinstance(patterns, list): patterns = []

        # 5. Guardar en DB
        saved_patterns = []
        for p in patterns:
            db.add_pattern(
                case_id, 
                p.get('description', 'Sin descripción'),
                p.get('recurrence', 'Media'),
                p.get('persistence', 'Desconocida'),
                p.get('pressure_context', 'No especificado'),
                p.get('contradictions', 'Ninguna')
            )
            saved_patterns.append(p)
            
        return jsonify({'message': 'Análisis completado', 'patterns': saved_patterns})

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': f"Error interno: {str(e)}"}), 500

# FASE 3: Vinculación Ejes
@app.route('/api/cases/<int:case_id>/axis_assignments', methods=['GET'])
def list_assignments(case_id):
    assigns = db.get_axis_assignments(case_id)
    return jsonify(assigns)

@app.route('/api/cases/<int:case_id>/analyze/link_axes', methods=['POST'])
def link_axes(case_id):
    try:
        data = request.json or {}
        mode = data.get('mode', 'local')
        
        # 1. Obtener patrones
        patterns = db.get_case_patterns(case_id)
        if not patterns:
            return jsonify({'error': 'No hay patrones para vincular'}), 400
            
        # 2. Formatear para prompt
        patterns_text = "\n".join([f"ID: {p['id']}\nDescripción: {p['description']}\n---" for p in patterns])
        
        # 3. Cargar prompt
        with open('prompts/axis_linking.md', 'r', encoding='utf-8') as f:
            prompt_template = f.read()
            
        system_prompt = prompt_template.replace('{patterns_text}', patterns_text)
        
        assignments = []
        
        # 4. Llamar AI
        if mode == 'cloud':
            from openai import OpenAI
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "system", "content": system_prompt}],
                response_format={"type": "json_object"},
                temperature=0.2
            )
            import json
            result_json = json.loads(response.choices[0].message.content)
            assignments = result_json if isinstance(result_json, list) else result_json.get('assignments', [])
            if isinstance(assignments, dict): assignments = [assignments] # Fallback
            
        else:
            import ollama
            local_prompt = system_prompt + "\n\nIMPORTANTE: Responde ÚNICAMENTE con el JSON válido."
            response = ollama.chat(model='llama3', messages=[{'role': 'user', 'content': local_prompt}])
            content = response['message']['content']
            import json, re
            match = re.search(r'(\[.*\]|\{.*\})', content, re.DOTALL)
            if match:
                try:
                    result_json = json.loads(match.group(1))
                    assignments = result_json if isinstance(result_json, list) else result_json.get('assignments', [])
                except: pass

        # 5. Guardar
        saved_count = 0
        for item in assignments:
            pid = item.get('pattern_id')
            matches = item.get('axis_matches', [])
            for m in matches:
                db.save_axis_assignment(case_id, pid, m.get('axis_name'), m.get('justification'))
                saved_count += 1
                
        return jsonify({'message': f'Vinculación completada. {saved_count} asignaciones creadas.', 'assignments': assignments})

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': f"Error interno: {str(e)}"}), 500

# Legacy / Fase 2 (Placeholder para futuro)
@app.route('/api/classify', methods=['POST'])
def classify():
    # ... (Lógica anterior mantenida por compatibilidad o futura adaptación)
    return jsonify({'message': 'Endpoint en migración a Fase 2'})

if __name__ == '__main__':
    app.run(debug=True, port=5001)
