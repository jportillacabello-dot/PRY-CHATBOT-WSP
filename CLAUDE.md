# CLAUDE.md

MVP de un chatbot RAG en WhatsApp: responde las consultas de los clientes de un negocio usando **solo** sus documentos (Twilio → FastAPI → ChromaDB → gpt-5-mini → TwiML).

- Plan, arquitectura C1/C2, herramientas y presupuesto: [docs/planificacion/README_MVP_Chatbot_RAG_WhatsApp.md](docs/planificacion/README_MVP_Chatbot_RAG_WhatsApp.md)
- Fechas, horas, responsables y % de avance por paso: `docs/planificacion/Plan_MVP_Chatbot_RAG_WhatsApp.xlsx`
- Equipo: Jhonatan (Fases 1–2: ingesta + RAG) · Jenner (Fases 0, 3–6: preparación, WhatsApp, calidad, despliegue, cierre)
- Plazo: 26-nov → 11-dic-2026 · Meta de calidad: ≥ 18/20 preguntas de prueba correctas

## Estructura

Sigue la guía general [docs/referencias/estructura-proyecto-rag.md](docs/referencias/estructura-proyecto-rag.md) (carpetas, dependencias, configuración, estilo). Ante cualquier duda de dónde va algo, manda esa guía.

```
├── README.md        portada: qué es, cómo instalar y correr
├── main.py          punto de entrada: ingestar · probar-busqueda · preguntar
├── config.yaml      modelos, chunk, k, umbral, rutas y mensajes (las claves van en .env)
├── CLAUDE.md        este archivo (Claude Code solo lo lee en la raíz)
├── src/             CÓDIGO
│   ├── ingestion/ chunking/ embeddings/ vectordb/     ingesta (Jhonatan)
│   ├── retrieval/ prompts/ llm/                      respuesta (Jhonatan)
│   ├── pipeline/    ingest_pipeline.py · rag_pipeline.py (contrato responder)
│   ├── evaluation/  search_eval.py
│   ├── api/         routes.py: webhook /whatsapp (Jenner)
│   └── utils/       config.py · helpers.py
├── tests/           CÓDIGO de pruebas (pytest, sin llamadas a OpenAI)
├── data/            DATOS
│   ├── documentos/  documentos del negocio: la ingesta lee TODO lo que hay aquí
│   ├── preguntas_prueba.csv
│   └── ejemplo/     negocio ficticio (documentos/ + preguntas) para probar sin datos reales
├── docs/            DOCUMENTACIÓN (índice en docs/README.md)
│   ├── planificacion/   plan del MVP, Gantt con % de avance, imagen
│   ├── arquitectura/    diagramas del proyecto
│   └── referencias/     guía RAG, plantilla de diagramas, harness-kit (local)
├── harness/         HARNESS: feature_list.json · progress.md · session-handoff.md · init.sh
└── logs/ · chroma_db/ · .venv/ · .env   generados o locales (no van a git)
```

Comandos (desde la raíz): `python main.py ingestar` · `python main.py probar-busqueda` · `python main.py preguntar --csv data/preguntas_prueba.csv` · servidor: `uvicorn src.api.routes:app` · verificación: `bash harness/init.sh`.

## Flujo de inicio (Startup Workflow)

Antes de escribir código:

1. **Confirma el directorio de trabajo** con `pwd`
2. **Lee este archivo** completo
3. **Lee `harness/progress.md`** y, si existe, `harness/session-handoff.md`
4. **Ejecuta `bash harness/init.sh`** (Git Bash en Windows) para verificar que el entorno está sano
5. **Lee `harness/feature_list.json`** para ver el estado de las fases
6. **Revisa los commits recientes** con `git log --oneline -5`

Si la verificación base falla, arréglala primero antes de añadir alcance nuevo.

## Reglas de trabajo

- **Una funcionalidad a la vez (One feature at a time)**: trabaja en una sola fase/funcionalidad de `harness/feature_list.json` cuyas dependencias estén en `done`
- **Verificación obligatoria**: no digas "terminado" sin haber ejecutado `bash harness/init.sh` y la prueba propia de la fase
- **Actualiza los artefactos**: antes de cerrar la sesión, actualiza `harness/progress.md` y `harness/feature_list.json`
- **Mantente en el alcance (Stay in scope)**: fuera del MVP quedan audios/imágenes, historial largo, panel de administración y varios negocios
- **Deja el repo limpio (clean)**: la siguiente sesión debe poder ejecutar `bash harness/init.sh` de inmediato

## Reglas del proyecto

- **Autoría**: nunca incluyas a Claude como autor ni contribuidor. Nada de `Co-Authored-By: Claude`, "Generated with Claude Code" ni menciones similares en commits, pull requests, README, código o documentación.
- **Dónde va cada cosa**: código en `src/` (y `main.py`), pruebas en `tests/`, datos en `data/`, documentación en `docs/`, seguimiento de Claude en `harness/`. Nada que no sea un documento del negocio va en `data/documentos/`.
- **Dependencias**: `main.py` → `api/` → `pipeline/` → pasos (`ingestion`, `chunking`, `embeddings`, `vectordb`, `retrieval`, `prompts`, `llm`) → `utils/`. Solo `api/` importa FastAPI o Twilio; nadie importa `api/`; los pasos no importan `pipeline/`, `evaluation/` ni `api/`; `utils/` no importa a nadie. Lo verifica `tests/test_capas.py`.
- **Configuración**: ningún número o nombre de modelo fijo en el código; va en `config.yaml` y se lee con `src.utils.config`.
- **Estilo de código**: cada archivo de `src/` y `main.py` se lee de arriba abajo en el orden del flujo, dividido en secciones con este encabezado:
  ```python
  # =====================================================================
  # == PASO 1: Objetivo del paso — qué hace en pocas palabras ==
  # =====================================================================
  ```
  Primero `CONFIGURACIÓN`, luego `PASO 1…N` y al final `EJECUCIÓN` (el `main`). Los subpasos dentro de una función se marcan con `# 1.1 …`, `# 1.2 …`. El docstring del módulo lista los pasos.
- **Cierre del proyecto**: al terminar el MVP (Fase 6), `CLAUDE.md`, `.claude/` y `harness/` salen del repositorio y de su historial:
  1. Agregar `CLAUDE.md`, `.claude/` y `harness/` a `.gitignore`.
  2. Reescribir el historial con `git filter-repo --path CLAUDE.md --path .claude --path harness --path feature_list.json --path progress.md --path session-handoff.md --path init.sh --invert-paths` (los cuatro últimos estuvieron en la raíz antes de mover el harness) (se instala con `pip install git-filter-repo`), trabajando sobre una copia del repo. Revisar también los mensajes de commit que nombran esos archivos.
  3. Volver a conectar el remoto y subir con `git push --force`. Avisar antes a Jenner: los hashes de los commits cambian y tendrá que clonar de nuevo.
  4. Conservar todo en local.
- **Secretos**: las claves van solo en `.env` (en `.gitignore`) o en las variables de entorno de Render. Nunca en código, logs ni commits.
- **El bot no inventa**: el prompt (`src/prompts/system_prompt.txt`) obliga a responder solo con el contexto recuperado y a decir "no sé" si no está. Es requisito de la política de WhatsApp (solo bots de atención al cliente).
- **Guardrails**: en `retrieval/`, umbral de relevancia (sin fragmentos relevantes no se llama al LLM). En `api/`, solo texto, máximo 500 caracteres, 10 mensajes por minuto por número y respuesta de respaldo si OpenAI falla. Ver `docs/arquitectura/arquitectura-pipeline.html`.
- **Contrato entre fases**: `src/pipeline/rag_pipeline.py` expone `responder(pregunta: str) -> str` (ya existe). `api/` solo depende de esa función y captura sus excepciones.
- **Webhook**: Twilio envía formulario (requiere `python-multipart`), espera TwiML y corta a los 15 s. Validar `X-Twilio-Signature` y mantener respuestas cortas (cada mensaje extra se cobra).
- **Log**: en `logs/log_preguntas.csv` el número de teléfono va anonimizado.
- **Modelos**: `gpt-5-mini` para responder, `text-embedding-3-small` para embeddings (ambos en `config.yaml`). Si se cambia el modelo de embeddings, hay que volver a correr `python main.py ingestar`.

## Artefactos requeridos

- `harness/feature_list.json` — Estado de las fases del MVP (fuente de verdad)
- `harness/progress.md` — Bitácora de continuidad entre sesiones
- `harness/init.sh` — Ruta estándar de arranque y verificación
- `harness/session-handoff.md` — Opcional, para sesiones largas
- `data/preguntas_prueba.csv` — Las 20 preguntas con su respuesta esperada (base de toda evaluación)

## Definición de terminado (Definition of Done)

Una funcionalidad está terminada solo cuando se cumple TODO lo siguiente:

- [ ] El comportamiento objetivo está implementado
- [ ] La verificación requerida se ejecutó de verdad (`bash harness/init.sh` + la prueba de la fase, p. ej. las 20 preguntas)
- [ ] La evidencia quedó registrada en `harness/feature_list.json` (campo `evidence`) o `harness/progress.md`
- [ ] El repositorio sigue pudiendo arrancar desde la ruta estándar (restartable)

## Fin de sesión (End of Session)

Antes de terminar una sesión:

1. Actualiza `harness/progress.md` con el estado actual
2. Actualiza `harness/feature_list.json` con el nuevo estado de la funcionalidad
3. Registra riesgos o bloqueos sin resolver
4. Haz commit con un mensaje descriptivo cuando el trabajo esté en un estado seguro (sin líneas de coautoría de Claude)
5. Deja el repo lo bastante limpio para que la siguiente sesión ejecute `bash harness/init.sh` de inmediato

## Comandos de verificación (Verification Commands)

```bash
# Verificación completa (recomendada)
bash harness/init.sh
```

Chequeos requeridos:
- `python -m compileall -q .` (sin errores de sintaxis)
- `python -m pytest` (cuando exista la carpeta `tests/`)
- `harness/feature_list.json` es JSON válido
- `.env` está en `.gitignore`

## Escalamiento

Si te encuentras con:
- **Decisiones de arquitectura**: consulta el README del MVP (`docs/planificacion/`); si no lo resuelve, pregunta al usuario
- **Requisitos poco claros**: revisa el Excel del plan; si no lo resuelve, pregunta al usuario
- **Fallos de tests repetidos o < 18/20 correctas**: registra el resultado en `harness/progress.md` y márcalo para revisión humana
- **Alcance ambiguo**: vuelve a leer `harness/feature_list.json` para ver la definición de terminado
