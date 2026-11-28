# Bitácora de progreso de sesión

## Estado actual (Current State)

**Última actualización (Last Updated):** 2026-11-28
**Funcionalidad activa:** feat-002 - Fase 2 – Cadena RAG (hecha con el negocio de ejemplo; falta validar con datos reales). feat-000 sigue en curso con Jenner

## Estado

### Qué está hecho (What's Done)

- [x] Plan del MVP (README + Excel con Gantt, pasos y horas)
- [x] Harness instalado: CLAUDE.md, feature_list.json, progress.md, session-handoff.md, init.sh
- [x] Skill harness-creator instalada en .claude/skills/
- [x] Repo en GitHub: https://github.com/jportillacabello-dot/PRY-CHATBOT-WSP (rama main)
- [x] Carpetas: src/ y tests/ (código), data/ (documentos/, preguntas, ejemplo/), docs/ (planificacion/, arquitectura/, referencias/), harness/
- [x] requirements.txt (con python-multipart, docx2txt y pytest), .gitignore, .env.example
- [x] .venv con dependencias instaladas
- [x] Plantilla data/preguntas_prueba.csv (columnas pregunta,respuesta_esperada,fuente_esperada)
- [x] Diagrama de pipeline con guardrails: docs/arquitectura/arquitectura-pipeline.html (hecho con docs/referencias/diagramas/)
- [x] Negocio de ejemplo (ficticio) en data/ejemplo/: documentos/ (faq.md, politicas.txt, carta.pdf) y 20 preguntas
- [x] ingesta.py: carga PDF/Word/TXT/MD, limpia encabezados y pies, trocea (800/100), guarda en ChromaDB con distancia coseno; reconstruye la colección en cada corrida
- [x] tests/test_ingesta.py: 9 tests con embeddings falsos (sin costo)
- [x] probar_busqueda.py (tarea 1.3): % de fuente correcta en top-k, rangos de distancia y umbral sugerido; sale con código 1 si no llega a 90 %
- [x] prompt.txt (reglas) y rag.py: responder(pregunta) -> str, responder_con_detalle() para evaluar, umbral de relevancia, CLI con --csv
- [x] tests/test_rag.py y tests/test_capas.py: 22 tests en total con LLM y embeddings falsos
- [x] Guía general reutilizable: docs/referencias/estructura-proyecto-rag.md (copia global en ~/.claude/instrucciones/)
- [x] Estructura por carpetas aplicada: main.py, config.yaml, src/{ingestion,chunking,embeddings,vectordb,retrieval,prompts,llm,pipeline,evaluation,api,utils}, logs/. 48 tests OK; mismo resultado con OpenAI (18/18 búsqueda, 20/20 respuestas, máximo 3.3 s)

### Qué está en curso (What's In Progress)

- [ ] Fase 0 – Preparación (Jenner, 26–27 nov)
  - Falta: elegir el negocio, documentos en data/documentos/, las 20 preguntas, activar el Sandbox de WhatsApp, ngrok y la cuenta de Render
  - Hecho: cuenta de Twilio (Trial) activa; TWILIO_ACCOUNT_SID y TWILIO_AUTH_TOKEN en .env y verificados contra la API (26-nov)
- [ ] Fases 1 y 2 (Jhonatan): código terminado y validado con el ejemplo
  - Falta: con los documentos reales, correr `python main.py ingestar`, `python main.py probar-busqueda` (ajustar `retrieval.umbral_distancia` en config.yaml) y `python main.py preguntar --csv data/preguntas_prueba.csv` (meta ≥ 18/20, dos corridas)
  - Bloqueos: tarea 0.1 de Jenner

### Qué sigue (What's Next)

1. Avisar a Jenner que `responder(pregunta) -> str` ya existe en `src/pipeline/rag_pipeline.py`: su webhook va en `src/api/routes.py` (instrucciones en `src/api/__init__.py`) y se levanta con `uvicorn src.api.routes:app`. Las excepciones las captura api/
2. Jenner: tarea 0.1 (negocio, documentos, 20 preguntas); al llegar, correr `python main.py ingestar`
3. Jhonatan: invitar a Jenner como colaborador en GitHub y pasarle por canal seguro las variables de .env (OpenAI y Twilio)

## Bloqueos / Riesgos (Blockers / Risks)

- [ ] Twilio corta el webhook a los 15 s: vigilar la latencia de gpt-5-mini
- [ ] El disco persistente de Render solo existe en planes de pago: en Free hay que correr la ingesta al arrancar
- [ ] En el Gantt, la tarea 3.1 depende de 2.2, pero el plan permitía empezar la API con una respuesta fija (ya no hace falta: responder() existe)
- [ ] PDFs escaneados (imagen) no tienen texto: la ingesta avisa y los omite; harían falta OCR o una versión en texto

## Decisiones tomadas

- **Harness con CLAUDE.md**: el proyecto se trabaja con Claude Code
- **Fase 3 depende solo de Fase 0** en feature_list.json, para que Jenner trabaje en paralelo con una respuesta fija
- **Estructura por carpetas (reemplaza la estructura plana anterior)**: se sigue `docs/referencias/estructura-proyecto-rag.md`. Una carpeta por responsabilidad en `src/`, valores en `config.yaml`, entrada única `main.py`, dependencias verificadas por `tests/test_capas.py`. Equivalencias con evidencias anteriores: `ingesta.py` → `main.py ingestar`; `probar_busqueda.py` → `main.py probar-busqueda`; `rag.py --csv` → `main.py preguntar --csv`; `prompt.txt` → `src/prompts/system_prompt.txt`; `app.py` → `src/api/routes.py`; log → `logs/log_preguntas.csv`
- **Separación código / datos / documentación / harness (28-nov)**: `src/` y `tests/` = código; `data/` = datos (los documentos del negocio pasaron de `docs/` a `data/documentos/`, y `ejemplo/` a `data/ejemplo/` con `documentos/`); `docs/` = documentación (`planificacion/`, `arquitectura/` antes `diagramas/`, `referencias/`); `harness/` = feature_list.json, progress.md, session-handoff.md, init.sh. CLAUDE.md sigue en la raíz porque Claude Code solo lo lee ahí. El validador local (`.claude/skills/.../harness-utils.mjs`) busca también en `harness/`. Basado en PyPA (src layout), Cookiecutter Data Science y Diátaxis. Las evidencias anteriores usan las rutas viejas
- **harness-kit/ fuera de git** (en docs/referencias/harness-kit/): la skill instalada ya está en `.claude/skills/`
- **Material de referencia junto en docs/referencias/**: guía RAG, plantilla de diagramas y harness-kit
- **Fase 1 adelantada con datos de ejemplo**: el negocio ficticio de `data/ejemplo/` permite construir y probar la ingesta sin esperar la tarea 0.1
- **Lectores propios (pypdf, docx2txt) en vez de los loaders de langchain-community**: ese paquete está en retiro; src/ingestion no lo usa
- **Una sola cuenta de Twilio para los dos** (la que está en .env). Render: también una sola cuenta, recomendado que la cree Jenner (Fase 5); despliega solo con cada push a main. Nunca compartir contraseñas, solo variables de entorno por canal seguro
- **Responsables actualizados en el Excel (26-nov)**: pasos 0.2.1–0.2.3 y 0.3.1–0.3.3 a cargo de Jhonatan
- **Distancia coseno en ChromaDB**: el umbral de relevancia de retrieval/ se define sobre ella
- **CLAUDE.md y .claude/ fuera del repo y de su historial al cierre** (Fase 6, ver CLAUDE.md)

## Evidencia de cierre (Evidence of Completion)

- [x] `bash init.sh` pasa: 9 tests OK (2026-11-26)
- [x] `python ingesta.py --docs ejemplo/docs`: 3 archivos, 3 páginas, 5 fragmentos; se detiene con mensaje claro por falta de OPENAI_API_KEY
- [x] Ingesta con embeddings reales de OpenAI: `python ingesta.py --docs ejemplo/docs` → 5 fragmentos en chroma_db/, costo < $0.0001
- [x] Búsqueda de prueba con las 20 preguntas de ejemplo (k=3): fuente correcta en 18/18. Poco exigente: con 5 fragmentos, k=3 cubre el 60 % de la base
- [x] `python rag.py --csv ejemplo/preguntas_prueba.csv`: 20/20 correctas en dos corridas seguidas, promedio 1.7 s, máximo 4.2 s (límite de Twilio: 15 s)
- [x] 4/4 intentos de manipulación rechazados (poema, revelar instrucciones, cambiar un precio, "asistente general"): 1 por umbral, 3 por prompt

## Ajustes al prompt (con el ejemplo)

- v1 ofrecía acciones que el bot no puede hacer ("¿Te ayudo a hacer el pedido?") y cerraba con preguntas → regla 5: solo informa, sin preguntas al final.
- v2 dijo "no tengo esa información" a "¿Aceptan cheques?" (la respuesta sí estaba) por la frase "o solo la contiene en parte" → regla 2: si está en parte, responde esa parte.
- MENSAJE_SIN_INFO ya no termina en pregunta: el modelo lo copiaba al final de respuestas válidas.
- gpt-5-mini no es determinista: evaluar siempre con 2 corridas.

## Hallazgo para el umbral de relevancia

Distancias coseno del fragmento más cercano (ejemplo): preguntas válidas entre 0.36 y 0.64; "¿Venden pizzas?" 0.55; "¿Quién ganó el último mundial?" 0.89.
- El umbral por distancia sirve para lo claramente fuera de tema (≈ 0.75 separaría el mundial sin perder preguntas válidas).
- No sirve para preguntas del mismo rubro que no están en los documentos (pizzas cae dentro del rango válido): eso lo debe cubrir el prompt ("si el contexto no lo dice, responde que no tienes esa información").
- Recalibrar el umbral con los documentos y preguntas reales.

## Mejoras pendientes para el final (comparación con laburen-ai-agent, 28-nov)

Hechas el 28-nov: versiones fijas en requirements.txt y .python-version (3.11.9); diagrama visible en GitHub (docs/arquitectura/README.md + PNG); GitHub Action de tests (.github/workflows/tests.yml).

Pendientes (feat-007 en harness/feature_list.json, al final del MVP):
- [ ] GET /health en src/api/ (y endpoint de prueba solo protegido o desactivado en producción) — Jenner
- [ ] Respaldo cuando OpenAI falla o tarda > 15 s: devolver el fragmento más relevante — Jhonatan
- [ ] Procfile o render.yaml con arranque y ingesta al iniciar si falta chroma_db/ — Jenner
- [ ] docs/despliegue-whatsapp.md y README con endpoints, demo y despliegue — Jenner
- [ ] logging de Python en lugar de print — Jenner

## Notas para la siguiente sesión (Next Session)

.env ya existe y chroma_db/ está cargada con el ejemplo. El código de Jhonatan (Fases 1 y 2) está listo; falta validarlo con los datos reales de la tarea 0.1. Mientras tanto, se puede adelantar el evaluador automático de respuestas (src/evaluation/answer_eval.py + `python main.py evaluar`) para las Fases 2.3, 4.3 y 5.3, y un README.md en la raíz para Jenner.
