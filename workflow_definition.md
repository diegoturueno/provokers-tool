# Flujo de Trabajo PHENOMA/PROVOKERS AI

## FASE 0 — Creación del caso
**Objetivo**: definir la unidad de análisis (persona, perfil, corpus).
- **Acción**: Crear “Caso” con identificador.
- **Estado inicial**: Caso vacío.

## FASE 1 — Ingreso de inputs (materia prima)
**Objetivo**: cargar estímulos sin interpretarlos aún.
- **Tipos**: Frase, Discurso, Relato, Situación narrada.
- **Metadatos**: Fecha, Tipo, Contexto, Fuente.
- **Regla**: No clasificar ejes aún.

## FASE 2 — Detección de patrones
**Objetivo**: pasar de texto a estructura.
- **Acción AI**: Agrupar inputs por temas, posicionamiento, emociones, roles.
- **Propuesta**: Recurrencia, Persistencia, Aparición bajo presión, Contradicciones.
- **Validación**: Usuario valida o ajusta.

## FASE 3 — Vinculación patrón → eje
**Objetivo**: traducir patrones en señales analíticas.
- **Acción**: Asignar patrones a los 6 ejes (o marcarlos como contextuales).
- **Registro**: Inputs vinculados, Tipo de evidencia, Intensidad.

## FASE 4 — Clasificación de los 6 ejes
**Objetivo**: fijar posición por eje basada en patrones.
- **Visualización**: Evidencias a favor/tensión/insuficientes.
- **Acción**: Marcar estado (Definido/Parcial/No definido) y Valor del eje.

## FASE 5 — Detección de tensiones estructurales
**Objetivo**: hacer explícitas las contradicciones.
- **Acción AI**: Revisar incompatibilidades entre ejes o desacoples.
- **Usuario**: Confirmar, Explicar o Descartar.

## FASE 6 — Evaluación de umbral para arquetipo
**Objetivo**: evitar asignaciones débiles.
- **Verificación**: ¿Suficientes ejes? ¿Consistencia?
- **Salida**: "Umbral alcanzado" o "No hay suficiente evidencia".

## FASE 7 — Asignación de arquetipo
**Objetivo**: comparar, no adivinar.
- **Visualización**: Superposición de ejes del caso vs Arquetipos.
- **Acción**: Selección única con justificación.

## FASE 8 — Generación del output
**Objetivo**: estandarizar la salida.
- **Generación**: Reporte final con los 8 puntos estándar, basado en patrones y tensiones validadas.

## FASE 9 — Iteración y tiempo
**Objetivo**: permitir proceso continuo.
- **Acción**: Agregar nuevos inputs, recalcular patrones, comparar evolución.
