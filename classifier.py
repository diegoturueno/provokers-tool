import os
import sys
import argparse
from dotenv import load_dotenv
from openai import OpenAI
import ollama

# Cargar variables de entorno
load_dotenv()

def load_model_definition(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"Error: No se encontró el archivo de definición del modelo en {path}")
        sys.exit(1)

def classify_stimulus_openai(stimulus_text, model_definition):
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    if not client.api_key:
        print("Error: OPENAI_API_KEY no encontrada en variables de entorno.")
        return None

    system_prompt = f"""
Eres un experto analista de comportamiento y sociología.
Tu tarea es clasificar el siguiente estímulo basándote ESTRICTAMENTE en la definición del modelo provista.

DEFINICIÓN DEL MODELO:
---
{model_definition}
---

Instrucciones adicionales:
- Sigue el formato de salida al pie de la letra.
- No añadas introducciones ni conclusiones fuera del formato.
"""
    user_prompt = f"ESTÍMULO A ANALIZAR:\n{stimulus_text}"

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error al llamar a la API de OpenAI: {e}"

def classify_stimulus_local(stimulus_text, model_definition, model_name="llama3"):
    print(f"Usando modelo local: {model_name} (vía Ollama)...")
    
    prompt = f"""
[INST]
Eres un experto analista. Clasifica el siguiente estímulo basándote ESTRICTAMENTE en la definición del modelo provista.

DEFINICIÓN DEL MODELO:
---
{model_definition}
---

ESTÍMULO A ANALIZAR:
{stimulus_text}

FORMATO DE SALIDA REQUERIDO:
[1] Generación:
...
[8] Explicación:

Responde SOLO con la clasificación.
[/INST]
"""
    try:
        response = ollama.chat(model=model_name, messages=[
            {'role': 'user', 'content': prompt},
        ])
        return response['message']['content']
    except Exception as e:
        return f"Error al llamar a Ollama: {e}\n¿Tienes Ollama instalado y corriendo? (https://ollama.com)"

def main():
    parser = argparse.ArgumentParser(description="Clasificador de Masculinidades Provokers")
    parser.add_argument('input', help="Texto a analizar o ruta a un archivo de texto")
    parser.add_argument('--model', default='model_definition.md', help="Ruta al archivo de definición del modelo")
    parser.add_argument('--local', action='store_true', help="Usar modelo local (Ollama) en lugar de OpenAI")
    parser.add_argument('--local-model-name', default='llama3', help="Nombre del modelo local a usar (default: llama3)")
    
    args = parser.parse_args()

    # Determinar si el input es un archivo o texto directo
    if os.path.isfile(args.input):
        with open(args.input, 'r', encoding='utf-8') as f:
            stimulus = f.read()
    else:
        stimulus = args.input

    # Cargar definición
    model_path = args.model
    if not os.path.isabs(model_path) and not os.path.exists(model_path):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(script_dir, args.model)
    
    model_def = load_model_definition(model_path)

    print("Analizando estímulo...")
    
    if args.local:
        result = classify_stimulus_local(stimulus, model_def, args.local_model_name)
    else:
        result = classify_stimulus_openai(stimulus, model_def)
    
    print("\nRESULTADO DE LA CLASIFICACIÓN:\n")
    print(result)

if __name__ == "__main__":
    main()
