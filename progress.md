# Bitácora de progreso de sesión

## Estado actual (Current State)

**Última actualización (Last Updated):** 2026-11-26
**Funcionalidad activa:** feat-001 - Fase 1 – Ingesta (adelantada con el negocio de ejemplo; feat-000 sigue en curso con Jenner)

## Estado

### Qué está hecho (What's Done)

- [x] Plan del MVP (README + Excel con Gantt, pasos y horas)
- [x] Harness instalado: CLAUDE.md, feature_list.json, progress.md, session-handoff.md, init.sh
- [x] Skill harness-creator instalada en .claude/skills/
- [x] Repo en GitHub: https://github.com/jportillacabello-dot/PRY-CHATBOT-WSP (rama main)
- [x] Carpetas docs/, data/, diagramas/
- [x] requirements.txt (con python-multipart, docx2txt y pytest), .gitignore, .env.example
- [x] .venv con dependencias instaladas
- [x] Plantilla data/preguntas_prueba.csv (columnas pregunta,respuesta_esperada,fuente_esperada)
- [x] Diagrama de pipeline con guardrails: diagramas/arquitectura-pipeline.html (hecho con arquitectura-ref/)
- [x] Negocio de ejemplo (ficticio) en ejemplo/: docs (faq.md, politicas.txt, carta.pdf) y 20 preguntas
- [x] ingesta.py: carga PDF/Word/TXT/MD, limpia encabezados y pies, trocea (800/100), guarda en ChromaDB con distancia coseno; reconstruye la colección en cada corrida
- [x] tests/test_ingesta.py: 9 tests con embeddings falsos (sin costo), incluido el chequeo de capas

### Qué está en curso (What's In Progress)

- [ ] Fase 0 – Preparación (Jenner, 26–27 nov)
  - Falta: elegir el negocio, documentos en docs/, las 20 preguntas, cuentas y claves en .env
- [ ] Fase 1 – Ingesta (Jhonatan)
  - Falta: correr con embeddings reales de OpenAI (necesita .env) y la tarea 1.3: probar la búsqueda con las 20 preguntas y ajustar chunk/k
  - Bloqueos: sin OPENAI_API_KEY no se puede correr `python ingesta.py`

### Qué sigue (What's Next)

1. Jhonatan: crear .env con OPENAI_API_KEY y correr `python ingesta.py --docs ejemplo/docs`
2. Jhonatan: script para la tarea 1.3 (por cada pregunta, ¿el fragmento correcto está entre los k primeros?) usando la columna fuente_esperada
3. Jenner: tarea 0.1 (negocio, documentos, 20 preguntas); al llegar, correr `python ingesta.py` sobre docs/
4. Jhonatan: invitar a Jenner como colaborador en GitHub

## Bloqueos / Riesgos (Blockers / Risks)

- [ ] Twilio corta el webhook a los 15 s: vigilar la latencia de gpt-5-mini
- [ ] El disco persistente de Render solo existe en planes de pago: en Free hay que correr la ingesta al arrancar
- [ ] En el Gantt, la tarea 3.1 depende de 2.2, pero el plan permite empezar app.py con una respuesta fija
- [ ] PDFs escaneados (imagen) no tienen texto: ingesta.py avisa y los omite; harían falta OCR o una versión en texto

## Decisiones tomadas

- **Harness con CLAUDE.md**: el proyecto se trabaja con Claude Code
- **Fase 3 depende solo de Fase 0** en feature_list.json, para que Jenner trabaje en paralelo con una respuesta fija
- **Estructura de código por capas, sin carpetas extra**: entrada (`app.py`), lógica (`rag.py`), datos (`ingesta.py`, `chroma_db/`, `prompt.txt`). Los imports van solo en ese sentido (test en tests/test_ingesta.py)
- **Diagramas fuera de docs/**: `docs/` solo tiene documentos del negocio porque `ingesta.py` lee todo lo que hay ahí
- **harness-kit/ fuera de git**: la skill instalada ya está en `.claude/skills/`
- **Fase 1 adelantada con datos de ejemplo**: el negocio ficticio de `ejemplo/` permite construir y probar la ingesta sin esperar la tarea 0.1
- **Lectores propios (pypdf, docx2txt) en vez de los loaders de langchain-community**: ese paquete está en retiro; ingesta.py no lo usa
- **Distancia coseno en ChromaDB**: el umbral de relevancia de rag.py se define sobre ella
- **CLAUDE.md fuera del repo y de su historial al cierre** (Fase 6, ver CLAUDE.md)

## Evidencia de cierre (Evidence of Completion)

- [x] `bash init.sh` pasa: 9 tests OK (2026-11-26)
- [x] `python ingesta.py --docs ejemplo/docs`: 3 archivos, 3 páginas, 5 fragmentos; se detiene con mensaje claro por falta de OPENAI_API_KEY
- [ ] Ingesta con embeddings reales de OpenAI

## Notas para la siguiente sesión (Next Session)

Empezar por crear .env y correr la ingesta real sobre ejemplo/docs. Después, la tarea 1.3 (prueba de búsqueda).
