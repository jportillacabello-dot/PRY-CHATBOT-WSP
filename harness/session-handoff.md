# Traspaso de sesión (Session Handoff)

## Objetivo actual (Current Objective)

- Meta: MVP de chatbot RAG en WhatsApp (26-nov → 11-dic-2026), ≥ 18/20 preguntas correctas.
- Estado actual: código de Jhonatan (Fases 1 y 2) terminado y probado con el negocio de ejemplo. Bloqueado por la tarea 0.1 de Jenner (negocio real, documentos, 20 preguntas). Avance total 37 %.
- Rama / commit: `main` en https://github.com/jportillacabello-dot/PRY-CHATBOT-WSP (último: ver `git log --oneline -1`).

## Completado en las sesiones del 26 y 28-nov

- [x] Harness (CLAUDE.md en la raíz; resto en `harness/`) y skill `harness-creator` en `.claude/skills/` (validador ajustado para buscar en `harness/`).
- [x] Estructura: `src/` (ingestion, chunking, embeddings, vectordb, retrieval, prompts, llm, pipeline, evaluation, api, utils), `tests/`, `data/` (documentos/, preguntas, ejemplo/), `docs/` (planificacion/, arquitectura/, referencias/), `harness/`, `main.py`, `config.yaml`.
- [x] Ingesta, búsqueda con umbral de relevancia, prompt (9 reglas) y `responder(pregunta) -> str`. Con el ejemplo: 18/18 en búsqueda, 20/20 en respuestas (2 corridas), máx. 4.2 s, 4/4 intentos de manipulación rechazados.
- [x] Guía general `docs/referencias/estructura-proyecto-rag.md` (copia global en `C:\Users\JHONATAN\.claude\instrucciones\`, referenciada desde el CLAUDE.md global).
- [x] Código comentado por pasos (`PASO N: objetivo`).
- [x] Excel del plan con % de avance por paso, tarea, fase y responsable.
- [x] Twilio (Trial) verificado; credenciales en `.env` (cuenta compartida por los dos).
- [x] README raíz, `docs/README.md`, diagrama en PNG visible en GitHub.
- [x] Versiones fijas en `requirements.txt`, `.python-version` = 3.11.9, GitHub Action de tests en verde.
- [x] Comparación con `JimeFioni/laburen-ai-agent`: lo pendiente quedó en `feat-007`.

## Evidencia de verificación (Verification Evidence)

| Chequeo | Comando | Resultado | Notas |
|---|---|---|---|
| Tests | `bash harness/init.sh` | 48 passed | También desde otra carpeta |
| Harness | `node .claude/skills/harness-creator/scripts/validate-harness.mjs --target .` | 100/100 | |
| CI | GitHub Actions `tests.yml` | success (40 s) | Usa "la última 3.11" |
| Búsqueda | `python main.py probar-busqueda --preguntas data/ejemplo/preguntas_prueba.csv` | 18/18 | Umbral sugerido 0.69 (actual 0.75) |
| Respuestas | `python main.py preguntar --csv data/ejemplo/preguntas_prueba.csv` | 20/20 | Revisado a mano |
| Instalación limpia | venv nuevo + `pip install -r requirements.txt` + `pip check` | OK | En Windows usar una ruta corta (límite de 260 caracteres) |

## Decisiones tomadas

- Código en `src/` con una carpeta por responsabilidad; `main.py` en la raíz; valores en `config.yaml`; reglas de dependencias verificadas por `tests/test_capas.py`.
- `docs/` es documentación; los documentos del negocio que se ingestan van en `data/documentos/`.
- Una sola cuenta de Twilio y una de Render (recomendado que la cree Jenner). Nunca compartir contraseñas.
- Sin coautoría de Claude en commits ni documentos. Al cierre (Fase 6), `CLAUDE.md`, `.claude/` y `harness/` salen del repo y de su historial (ver CLAUDE.md).

## Bloqueos / Riesgos (Blockers / Risks)

- Tarea 0.1 de Jenner (bloquea validar las Fases 1 y 2 con datos reales).
- Render gratis no guarda `chroma_db/`: hace falta ingesta al arrancar (en `feat-007`).
- Twilio corta el webhook a los 15 s.
- PDFs escaneados no tienen texto (harían falta OCR).

## Arranque de la siguiente sesión (Next Session Startup)

1. Lee `CLAUDE.md`.
2. Lee `harness/feature_list.json` y `harness/progress.md` (sección "Qué sigue").
3. Revisa este traspaso.
4. Ejecuta `bash harness/init.sh` antes de editar.

## Siguiente paso recomendado (Recommended Next Step)

- Si llegaron los datos reales: correr ingesta, `probar-busqueda` y `preguntar --csv` y actualizar el % en el Excel.
- Si no: el evaluador automático de respuestas (`python main.py evaluar`), o ayudar a Jenner a arrancar `src/api/routes.py`.
