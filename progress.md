# Bitácora de progreso de sesión

## Estado actual (Current State)

**Última actualización (Last Updated):** 2026-11-26
**Funcionalidad activa:** feat-000 - Fase 0 – Preparación

## Estado

### Qué está hecho (What's Done)

- [x] Plan del MVP (README + Excel con Gantt, pasos y horas)
- [x] Harness instalado: CLAUDE.md, feature_list.json, progress.md, session-handoff.md, init.sh
- [x] Skill harness-creator instalada en .claude/skills/
- [x] Repo en GitHub: https://github.com/jportillacabello-dot/PRY-CHATBOT-WSP (rama main)
- [x] Carpetas docs/, data/, diagramas/
- [x] requirements.txt (con python-multipart, docx2txt y pytest), .gitignore, .env.example
- [x] .venv con dependencias instaladas
- [x] Plantilla data/preguntas_prueba.csv (columnas pregunta,respuesta_esperada)
- [x] Diagrama de pipeline con guardrails: diagramas/arquitectura-pipeline.html (hecho con arquitectura-ref/)

### Qué está en curso (What's In Progress)

- [ ] Fase 0 – Preparación (Jenner, 26–27 nov)
  - Falta: elegir el negocio, documentos en docs/, las 20 preguntas, cuentas y claves en .env
  - Bloqueos: Fase 1 necesita los documentos y las preguntas reales

### Qué sigue (What's Next)

1. Jenner: tarea 0.1 (negocio, documentos, 20 preguntas)
2. Jhonatan: API key de OpenAI en .env; invitar a Jenner como colaborador en GitHub
3. Jhonatan: ingesta.py con documentos de prueba mientras llegan los reales

## Bloqueos / Riesgos (Blockers / Risks)

- [ ] Twilio corta el webhook a los 15 s: vigilar la latencia de gpt-5-mini
- [ ] El disco persistente de Render solo existe en planes de pago: en Free hay que correr la ingesta al arrancar
- [ ] En el Gantt, la tarea 3.1 depende de 2.2, pero el plan permite empezar app.py con una respuesta fija

## Decisiones tomadas

- **Harness con CLAUDE.md**: el proyecto se trabaja con Claude Code
- **Fase 3 depende solo de Fase 0** en feature_list.json, para que Jenner trabaje en paralelo con una respuesta fija
- **Estructura de código por capas, sin carpetas extra**: entrada (`app.py`), lógica (`rag.py`), datos (`ingesta.py`, `chroma_db/`, `prompt.txt`). Es la estructura plana del README; no se añaden paquetes ni capas adicionales en el MVP
- **Diagramas fuera de docs/**: `docs/` solo tiene documentos del negocio porque `ingesta.py` lee todo lo que hay ahí
- **harness-kit/ fuera de git**: la skill instalada ya está en `.claude/skills/`

## Evidencia de cierre (Evidence of Completion)

- [ ] `bash init.sh` pasa

## Notas para la siguiente sesión (Next Session)

Aún no hay código ni repo git. Empezar por la Fase 0.
