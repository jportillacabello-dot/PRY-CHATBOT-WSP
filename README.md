# Chatbot RAG en WhatsApp

Bot que responde por WhatsApp las consultas de los clientes de un negocio usando **solo** la información de sus documentos (RAG). Si la respuesta no está en los documentos, lo dice.

**Flujo:** WhatsApp → Twilio → FastAPI (`src/api/`) → búsqueda en ChromaDB → gpt-5-mini → respuesta en TwiML.

## Instalación

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows  (Linux/Mac: source .venv/bin/activate)
pip install -r requirements.txt
copy .env.example .env          # y completa las claves
```

`.env` necesita:

| Variable | De dónde sale |
|---|---|
| `OPENAI_API_KEY` | platform.openai.com → API keys |
| `TWILIO_ACCOUNT_SID` | console.twilio.com → Account Info |
| `TWILIO_AUTH_TOKEN` | console.twilio.com → Account Info |

`.env` nunca se sube al repositorio.

## Uso

```bash
python main.py ingestar                         # data/documentos/ → base vectorial
python main.py probar-busqueda                  # ¿la búsqueda trae el fragmento correcto?
python main.py preguntar "¿A qué hora abren?"   # una pregunta (sin texto: conversación)
python main.py preguntar --csv data/preguntas_prueba.csv
uvicorn src.api.routes:app                      # servidor del webhook (Fase 3)
```

Para probar sin datos reales, usa el negocio ficticio de `data/ejemplo/`:

```bash
python main.py ingestar --docs data/ejemplo/documentos
python main.py preguntar --csv data/ejemplo/preguntas_prueba.csv
```

Tests: `python -m pytest` (no llaman a OpenAI).

## Estructura

| Carpeta | Contenido |
|---|---|
| `src/` | Código: ingesta, búsqueda, prompts, LLM, pipeline, evaluación, API |
| `tests/` | Pruebas |
| `data/` | Documentos del negocio, preguntas de prueba y negocio de ejemplo |
| `docs/` | Documentación: plan, arquitectura y referencias ([índice](docs/README.md)) |
| `config.yaml` | Modelos, tamaño de fragmentos, umbral, rutas y mensajes |

## Equipo

Jhonatan (ingesta y RAG) · Jenner (WhatsApp, calidad, despliegue y cierre).
