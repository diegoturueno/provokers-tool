# Clasificador de Masculinidades Provokers

Herramienta para clasificar textos según el modelo de "Nuevas Masculinidades" del Observatorio Provokers, utilizando OpenAI GPT.

## Instalación

1.  **Requisitos**: Python 3.8+
2.  **Instalar dependencias**:
    ```bash
    pip install -r requirements.txt
    ```
3.  **Configuración**:
    - Crea un archivo `.env` basado en el ejemplo:
      ```bash
      cp .env.example .env
      ```
    - Edita `.env` y coloca tu `OPENAI_API_KEY`.

## Uso

### Clasificar un texto directo
```bash
python classifier.py "Texto a analizar..."
```

### Clasificar un archivo
```bash
python classifier.py sample_stimulus.txt
```

### Argumentos opcionales
- `--model`: Ruta a un archivo de definición de modelo alternativo.
- `--local`: Usa un modelo local vía Ollama en lugar de OpenAI.
- `--local-model-name`: Nombre del modelo local (ej: `llama3`, `mistral`). Por defecto `llama3`.

## Ejecución Local (Gratis y Privada)
Para usarlo sin enviar datos a OpenAI:

1.  **Instala Ollama**: Descarga desde [ollama.com](https://ollama.com).
2.  **Descarga un modelo**: En tu terminal ejecuta `ollama pull llama3`.
3.  **Ejecuta el clasificador**:
    ```bash
    python classifier.py sample_stimulus.txt --local
    ```

- `classifier.py`: Script principal.
- `model_definition.md`: Prompt del sistema con las reglas de clasificación.
- `sample_stimulus.txt`: Ejemplo de texto para pruebas.
