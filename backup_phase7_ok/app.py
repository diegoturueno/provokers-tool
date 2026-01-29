from flask import Flask, render_template, request, jsonify
import os
import json
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
def analyze_link_axes(case_id):
    try:
        data = request.json
        mode = data.get('mode', 'local')
        
        # 1. Get Patterns
        patterns = db.get_case_patterns(case_id)
        if not patterns:
            return jsonify({'error': 'No hay patrones para analizar'}), 400
            
        # 2. Format Input
        patterns_text = "\n".join([f"- {p['description']} (Recurrencia: {p['recurrence']})" for p in patterns])
        
        # 3. Load Prompt
        with open('prompts/axis_linking.md', 'r') as f:
            prompt_template = f.read()
            
        system_prompt = prompt_template.replace('{patterns_text}', patterns_text)
        
        # 4. Call AI
        if mode == 'cloud':
            from openai import OpenAI
            client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "system", "content": system_prompt}],
                response_format={"type": "json_object"}
            )
            content = response.choices[0].message.content
        else:
            import ollama
            response = ollama.chat(model='llama3', messages=[{'role': 'system', 'content': system_prompt}], format='json')
            content = response['message']['content']
            
        # 5. Parse and Save
        try:
            result_json = json.loads(content)
            assignments = result_json.get('assignments', result_json) # Handle list or dict wrapper
            
            for a in assignments:
                # Find pattern_id by description match (fuzzy or exact)
                # For simplicity, we just save the text description in the DB for now or match loosely
                # Ideally we should pass IDs to AI, but let's match by description text
                matched_pattern = next((p for p in patterns if p['description'] in a['pattern_description'] or a['pattern_description'] in p['description']), None)
                pid = matched_pattern['id'] if matched_pattern else None
                
                if pid:
                    db.save_axis_assignment(case_id, pid, a['axis_name'], a['justification'])
            
            return jsonify({'status': 'success', 'assignments': assignments})
            
        except json.JSONDecodeError:
            return jsonify({'error': 'Error al procesar respuesta JSON de la IA'}), 500
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/cases/<int:case_id>/axis_assignments', methods=['GET'])
def get_case_axis_assignments(case_id):
    assigns = db.get_axis_assignments(case_id)
    # Enrich with pattern description
    patterns = {p['id']: p['description'] for p in db.get_case_patterns(case_id)}
    result = []
    for a in assigns:
        a['pattern_description'] = patterns.get(a['pattern_id'], 'Patrón desconocido')
        result.append(a)
    return jsonify(result)

# --- PHASE 4 ENDPOINTS ---

@app.route('/api/cases/<int:case_id>/analyze/dimensions', methods=['POST'])
def analyze_dimensions(case_id):
    try:
        data = request.json
        mode = data.get('mode', 'local')
        
        # 1. Get Axis Assignments
        assigns = db.get_axis_assignments(case_id)
        if not assigns:
            return jsonify({'error': 'No hay vinculaciones de ejes para analizar. Completa la Fase 3 primero.'}), 400
            
        # Enrich assignments with pattern descriptions
        patterns = {p['id']: p['description'] for p in db.get_case_patterns(case_id)}
        assignments_text = ""
        for a in assigns:
            p_desc = patterns.get(a['pattern_id'], 'Patrón desconocido')
            assignments_text += f"- Eje: {a['axis_name']} | Patrón: {p_desc} | Justificación: {a['justification']}\n"
        
        # 2. Load Prompt
        with open('prompts/axis_classification.md', 'r') as f:
            prompt_template = f.read()
            
        system_prompt = prompt_template.replace('{axis_assignments_text}', assignments_text)
        
        # 3. Call AI
        if mode == 'cloud':
            from openai import OpenAI
            client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "system", "content": system_prompt}],
                response_format={"type": "json_object"}
            )
            content = response.choices[0].message.content
        else:
            import ollama
            response = ollama.chat(model='llama3', messages=[{'role': 'system', 'content': system_prompt}], format='json')
            content = response['message']['content']
            
        # 4. Parse and Save
        try:
            result_json = json.loads(content)
            # Handle if wrapped in a key or direct list
            states = result_json.get('axis_states', result_json) 
            if isinstance(states, dict): states = [states] # Handle single object edge case
            
            for s in states:
                db.save_axis_state(case_id, s['axis_name'], s['status'], s['value'], s['justification'])
            
            return jsonify({'status': 'success', 'states': states})
            
        except json.JSONDecodeError:
            return jsonify({'error': 'Error al procesar respuesta JSON de la IA'}), 500
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/cases/<int:case_id>/axis_states', methods=['GET'])
def get_case_axis_states(case_id):
    states = db.get_axis_states(case_id)
    return jsonify(states)

# --- PHASE 5 ENDPOINTS ---

@app.route('/api/cases/<int:case_id>/analyze/tensions', methods=['POST'])
def analyze_tensions(case_id):
    try:
        data = request.json
        mode = data.get('mode', 'local')
        
        # 1. Get Axis States
        states = db.get_axis_states(case_id)
        if not states:
            return jsonify({'error': 'No hay estados de ejes definidos. Completa la Fase 4 primero.'}), 400
            
        # Format states for prompt
        states_text = ""
        for s in states:
            states_text += f"- {s['axis_name']}: {s['value']} (Estado: {s['status']})\n  Justificación: {s['justification']}\n"
        
        # 2. Load Prompt
        with open('prompts/tension_detection.md', 'r') as f:
            prompt_template = f.read()
            
        system_prompt = prompt_template.replace('{axis_states_text}', states_text)
        
        # 3. Call AI
        if mode == 'cloud':
            from openai import OpenAI
            client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "system", "content": system_prompt}],
                response_format={"type": "json_object"}
            )
            content = response.choices[0].message.content
        else:
            import ollama
            response = ollama.chat(model='llama3', messages=[{'role': 'system', 'content': system_prompt}], format='json')
            content = response['message']['content']
            
        # 4. Parse and Save
        try:
            result_json = json.loads(content)
            tensions = result_json.get('tensions', result_json)
            if isinstance(tensions, dict): tensions = [tensions]
            
            # Clear old tensions? Let's clear to avoid duplicates
            db.clear_case_tensions(case_id)
            
            for t in tensions:
                db.save_tension(case_id, t['description'], t['type'], t['axes_involved'], t['severity'])
            
            return jsonify({'status': 'success', 'tensions': tensions})
            
        except json.JSONDecodeError:
            return jsonify({'error': 'Error al procesar respuesta JSON de la IA'}), 500
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/cases/<int:case_id>/tensions', methods=['GET'])
def get_case_tensions_endpoint(case_id):
    tensions = db.get_case_tensions(case_id)
    # Parse axes_involved from JSON string
    for t in tensions:
        try:
            t['axes_involved'] = json.loads(t['axes_involved'])
        except:
            t['axes_involved'] = []
    return jsonify(tensions)

# --- PHASE 6 ENDPOINTS ---

@app.route('/api/cases/<int:case_id>/analyze/threshold', methods=['POST'])
def analyze_threshold(case_id):
    try:
        data = request.json
        mode = data.get('mode', 'local')
        
        # 1. Gather Case Data (Patterns, Axes, Tensions)
        patterns = db.get_case_patterns(case_id)
        axis_states = db.get_axis_states(case_id)
        tensions = db.get_case_tensions(case_id)
        
        if not axis_states:
             return jsonify({'error': 'Faltan datos de ejes. Completa fases anteriores.'}), 400
             
        # Format Summary
        summary_text = "PATRONES:\n" + "\n".join([f"- {p['description']} (Recurrencia: {p['recurrence']})" for p in patterns])
        summary_text += "\n\nEJES:\n" + "\n".join([f"- {s['axis_name']}: {s['value']} ({s['status']})" for s in axis_states])
        summary_text += "\n\nTENSIONES:\n" + "\n".join([f"- {t['description']} (Severidad: {t['severity']})" for t in tensions])
        
        # 2. Load Prompt
        with open('prompts/threshold_evaluation.md', 'r') as f:
            prompt_template = f.read()
            
        system_prompt = prompt_template.replace('{case_summary_text}', summary_text)
        
        # 3. Call AI
        if mode == 'cloud':
            from openai import OpenAI
            client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "system", "content": system_prompt}],
                response_format={"type": "json_object"}
            )
            content = response.choices[0].message.content
        else:
            import ollama
            response = ollama.chat(model='llama3', messages=[{'role': 'system', 'content': system_prompt}], format='json')
            content = response['message']['content']
            
        # 4. Parse and Save
        try:
            result_json = json.loads(content)
            # Handle potential nesting
            eval_data = result_json.get('evaluation', result_json)
            
            db.save_threshold_evaluation(case_id, eval_data['score'], eval_data['status'], eval_data['reasoning'])
            
            return jsonify({'status': 'success', 'evaluation': eval_data})
            
        except json.JSONDecodeError:
            return jsonify({'error': 'Error al procesar respuesta JSON de la IA'}), 500
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/cases/<int:case_id>/threshold', methods=['GET'])
def get_threshold_endpoint(case_id):
    evaluation = db.get_threshold_evaluation(case_id)
    return jsonify(evaluation)

# --- PHASE 7 ENDPOINTS ---

@app.route('/api/cases/<int:case_id>/analyze/archetype', methods=['POST'])
def analyze_archetype(case_id):
    try:
        data = request.json
        mode = data.get('mode', 'local')
        
        # 1. Gather ALL Case Data
        patterns = db.get_case_patterns(case_id)
        axis_states = db.get_axis_states(case_id)
        tensions = db.get_case_tensions(case_id)
        threshold = db.get_threshold_evaluation(case_id)
        
        if not threshold:
             return jsonify({'error': 'Falta evaluación de umbral. Completa la Fase 6.'}), 400
             
        # Format Summary
        summary_text = "PATRONES:\n" + "\n".join([f"- {p['description']}" for p in patterns])
        summary_text += "\n\nEJES:\n" + "\n".join([f"- {s['axis_name']}: {s['value']} ({s['status']})" for s in axis_states])
        summary_text += "\n\nTENSIONES:\n" + "\n".join([f"- {t['description']}" for t in tensions])
        summary_text += f"\n\nEVALUACIÓN DE UMBRAL:\nScore: {threshold['score']}\nStatus: {threshold['status']}\nReasoning: {threshold['reasoning']}"
        
        # 2. Load Prompt
        with open('prompts/archetype_assignment.md', 'r') as f:
            prompt_template = f.read()
            
        system_prompt = prompt_template.replace('{case_summary_text}', summary_text)
        
        # 3. Call AI
        if mode == 'cloud':
            from openai import OpenAI
            client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "system", "content": system_prompt}],
                response_format={"type": "json_object"}
            )
            content = response.choices[0].message.content
        else:
            import ollama
            response = ollama.chat(model='llama3', messages=[{'role': 'system', 'content': system_prompt}], format='json')
            content = response['message']['content']
            
        # 4. Parse and Save
        try:
            result_json = json.loads(content)
            # Handle potential nesting
            arch_data = result_json.get('archetype', result_json)
            
            db.save_archetype_assignment(case_id, arch_data['archetype_name'], arch_data['description'], arch_data['fit_score'], arch_data['key_traits'])
            
            return jsonify({'status': 'success', 'archetype': arch_data})
            
        except json.JSONDecodeError:
            return jsonify({'error': 'Error al procesar respuesta JSON de la IA'}), 500
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/cases/<int:case_id>/archetype', methods=['GET'])
def get_archetype_endpoint(case_id):
    arch = db.get_archetype_assignment(case_id)
    if arch:
        try:
            arch['key_traits'] = json.loads(arch['key_traits'])
        except:
            arch['key_traits'] = []
    return jsonify(arch)

# Legacy / Fase 2 (Placeholder para futuro)
@app.route('/api/classify', methods=['POST'])
def classify():
    # ... (Lógica anterior mantenida por compatibilidad o futura adaptación)
    return jsonify({'message': 'Endpoint en migración a Fase 2'})

if __name__ == '__main__':
    app.run(debug=True, port=5001)
