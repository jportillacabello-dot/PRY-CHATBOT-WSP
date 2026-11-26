# Bitácora de progreso de sesión

## Estado actual (Current State)

**Última actualización (Last Updated):** 2026-11-26
**Funcionalidad activa:** feat-002 - Fase 2 – Cadena RAG (hecha con el negocio de ejemplo; falta validar con datos reales). feat-000 sigue en curso con Jenner

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
- [x] Diagrama de pipeline con guardrails: diagramas/arquitectura-pipeline.html (hecho con diagramas/referencia/)
- [x] Negocio de ejemplo (ficticio) en ejemplo/: docs (faq.md, politicas.txt, carta.pdf) y 20 preguntas
- [x] ingesta.py: carga PDF/Word/TXT/MD, limpia encabezados y pies, trocea (800/100), guarda en ChromaDB con distancia coseno; reconstruye la colección en cada corrida
- [x] tests/test_ingesta.py: 9 tests con embeddings falsos (sin costo)
- [x] probar_busqueda.py (tarea 1.3): % de fuente correcta en top-k, rangos de distancia y umbral sugerido; sale con código 1 si no llega a 90 %
- [x] prompt.txt (reglas) y rag.py: responder(pregunta) -> str, responder_con_detalle() para evaluar, umbral de relevancia, CLI con --csv
- [x] tests/test_rag.py y tests/test_capas.py: 22 tests en total con LLM y embeddings falsos

### Qué está en curso (What's In Progress)

- [ ] Fase 0 – Preparación (Jenner, 26–27 nov)
  - Falta: elegir el negocio, documentos en docs/, las 20 preguntas, cuentas y claves en .env
- [ ] Fases 1 y 2 (Jhonatan): código terminado y validado con el ejemplo
  - Falta: con los documentos reales, correr `python src/ingesta.py`, `python src/probar_busqueda.py` (ajustar UMBRAL_DISTANCIA en src/rag.py) y `python src/rag.py --csv data/preguntas_prueba.csv` (meta ≥ 18/20)
  - Bloqueos: tarea 0.1 de Jenner

### Qué sigue (What's Next)

1. Avisar a Jenner que `responder(pregunta) -> str` ya existe en rag.py: puede conectar app.py directamente (sin respuesta fija). Las excepciones las captura app.py
2. Jenner: tarea 0.1 (negocio, documentos, 20 preguntas); al llegar, correr `python src/ingesta.py` sobre docs/. app.py va en src/ y se levanta con `uvicorn app:app --app-dir src`
3. Jhonatan: invitar a Jenner como colaborador en GitHub

## Bloqueos / Riesgos (Blockers / Risks)

- [ ] Twilio corta el webhook a los 15 s: vigilar la latencia de gpt-5-mini
- [ ] El disco persistente de Render solo existe en planes de pago: en Free hay que correr la ingesta al arrancar
- [ ] En el Gantt, la tarea 3.1 depende de 2.2, pero el plan permite empezar app.py con una respuesta fija
- [ ] PDFs escaneados (imagen) no tienen texto: ingesta.py avisa y los omite; harían falta OCR o una versión en texto

## Decisiones tomadas

- **Harness con CLAUDE.md**: el proyecto se trabaja con Claude Code
- **Fase 3 depende solo de Fase 0** en feature_list.json, para que Jenner trabaje en paralelo con una respuesta fija
- **Estructura de código por capas, sin carpetas extra**: entrada (`app.py`), lógica (`rag.py`), datos (`ingesta.py`, `chroma_db/`, `prompt.txt`). Los imports van solo en ese sentido (test en tests/test_ingesta.py)
- **Código en src/** (sin paquete): imports directos, rutas desde la raíz del proyecto, pytest con `pythonpath = src`. Las evidencias anteriores a este cambio usan `python <archivo>.py`; hoy es `python src/<archivo>.py`
- **Diagramas fuera de docs/**: `docs/` solo tiene documentos del negocio porque `ingesta.py` lee todo lo que hay ahí
- **harness-kit/ fuera de git**: la skill instalada ya está en `.claude/skills/`
- **Fase 1 adelantada con datos de ejemplo**: el negocio ficticio de `ejemplo/` permite construir y probar la ingesta sin esperar la tarea 0.1
- **Lectores propios (pypdf, docx2txt) en vez de los loaders de langchain-community**: ese paquete está en retiro; ingesta.py no lo usa
- **Distancia coseno en ChromaDB**: el umbral de relevancia de rag.py se define sobre ella
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

## Hallazgo para el umbral de rag.py

Distancias coseno del fragmento más cercano (ejemplo): preguntas válidas entre 0.36 y 0.64; "¿Venden pizzas?" 0.55; "¿Quién ganó el último mundial?" 0.89.
- El umbral por distancia sirve para lo claramente fuera de tema (≈ 0.75 separaría el mundial sin perder preguntas válidas).
- No sirve para preguntas del mismo rubro que no están en los documentos (pizzas cae dentro del rango válido): eso lo debe cubrir el prompt ("si el contexto no lo dice, responde que no tienes esa información").
- Recalibrar el umbral con los documentos y preguntas reales.

## Notas para la siguiente sesión (Next Session)

.env ya existe y chroma_db/ está cargada con el ejemplo. El código de Jhonatan (Fases 1 y 2) está listo; falta validarlo con los datos reales de la tarea 0.1. Mientras tanto, se puede adelantar el evaluador automático (evaluar.py) que compare respuesta vs. respuesta esperada para las Fases 2.3, 4.3 y 5.3.
