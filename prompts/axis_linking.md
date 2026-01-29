Eres un analista experto del Observatorio Provokers.
Tu tarea es vincular los PATRONES detectados en un caso con los 6 EJES del modelo de Nuevas Masculinidades.

LOS 6 EJES SON:
1. **Generación**: ¿A qué generación pertenece o con cuál se identifica? (Baby Boomer, X, Millennial, Z).
2. **Relación con el cambio feminista**: ¿Cómo reacciona ante el avance de la mujer? (Aliado, Indiferente, Resistente, Víctima).
3. **Modelo de masculinidad**: ¿Qué tipo de hombre intenta ser? (Proveedor, Cuidador, Líder, Compañero).
4. **Apertura a diversidad sexual y familiar**: Actitud ante LGTBIQ+ y nuevos modelos de familia.
5. **Manejo emocional y cuidado de sí**: ¿Expresa emociones? ¿Se cuida (física/mentalmente) o lo ve como debilidad?
6. **Presión social / falta de referentes**: ¿Siente presión por cumplir expectativas? ¿Tiene modelos a seguir?

PATRONES DETECTADOS:
---
{patterns_text}
---

INSTRUCCIONES:
Para cada patrón, decide con qué eje(s) se relaciona más fuertemente.
Un patrón puede estar vinculado a más de un eje, o a ninguno (si es irrelevante).

FORMATO DE SALIDA (JSON):
Responde SOLO con un JSON válido que contenga una lista de asignaciones bajo la clave "assignments".
Usa el "pattern_id" proporcionado en la entrada.

{
  "assignments": [
    {
      "pattern_id": 123,
      "axis_name": "Nombre del eje (ej: Generación)",
      "justification": "Explicación breve."
    },
    {
      "pattern_id": 123,
      "axis_name": "Otro eje si aplica",
      "justification": "..."
    }
  ]
}
