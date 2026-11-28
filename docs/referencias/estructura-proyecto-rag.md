# Estructura estándar de un proyecto RAG en Python

Guía general para organizar cualquier proyecto RAG (*Retrieval-Augmented Generation*): una carpeta por responsabilidad, configuración fuera del código y un solo punto de entrada. Sirve tal cual para proyectos nuevos; copia este archivo y adapta solo los nombres.

> Basado en el esquema de referencia "Estructura de un Proyecto RAG", con dos carpetas extra que todo RAG termina necesitando: `pipeline/` (orquestación) y `evaluation/` (medir calidad).

---

## 1. Árbol

```
mi-proyecto/
├── README.md              qué hace, cómo instalar, cómo correr, arquitectura
├── requirements.txt       dependencias de Python
├── .env                   claves y datos sensibles (NUNCA a git)
├── .env.example           las mismas variables, vacías (sí va a git)
├── .gitignore
├── config.yaml            modelos, tamaño de chunks, k, umbral, rutas, mensajes
├── main.py                punto de entrada: subcomandos de consola y servidor
├── src/
│   ├── __init__.py
│   ├── ingestion/         cargar datos: PDF, Word, CSV, web… → texto limpio
│   │   └── loader.py
│   ├── chunking/          dividir el texto en fragmentos
│   │   └── chunker.py
│   ├── embeddings/        convertir fragmentos en vectores
│   │   └── embedder.py
│   ├── vectordb/          crear, abrir y llenar la base vectorial (ChromaDB, FAISS, Pinecone…)
│   │   └── vector_store.py
│   ├── retrieval/         buscar los fragmentos relevantes (similitud, umbral, reranking)
│   │   └── retriever.py
│   ├── prompts/           plantillas y reglas del prompt
│   │   ├── prompt_templates.py
│   │   └── system_prompt.txt
│   ├── llm/               cliente del modelo (OpenAI, Claude, Gemini…)
│   │   └── llm_client.py
│   ├── pipeline/          orquesta los pasos: ingesta completa y respuesta completa
│   │   ├── ingest_pipeline.py
│   │   └── rag_pipeline.py
│   ├── evaluation/        medir búsqueda y respuestas con preguntas de prueba
│   │   └── search_eval.py
│   ├── api/               endpoints (FastAPI / Flask, webhooks)
│   │   └── routes.py
│   └── utils/             configuración y funciones comunes
│       ├── config.py
│       └── helpers.py
├── tests/                 pruebas unitarias y de integración (sin llamar a APIs pagadas)
├── data/                  DATOS
│   ├── documentos/        documentos fuente que se indexan (solo eso)
│   ├── preguntas_prueba.csv
│   └── ejemplo/           datos ficticios para probar sin datos reales (opcional)
├── docs/                  DOCUMENTACIÓN del proyecto (índice en docs/README.md)
│   ├── planificacion/     plan, cronograma, presupuesto
│   ├── arquitectura/      diagramas
│   └── referencias/       guías y material de apoyo (como esta guía)
├── harness/               seguimiento del agente de IA (opcional): feature_list.json, progress.md, init.sh…
├── logs/                  registros de ejecución y de consultas (no van a git)
└── <vectordb>/            base vectorial generada (no va a git)
```

Cada carpeta de `src/` lleva un `__init__.py` (aunque esté vacío).

## 2. Qué va en cada carpeta

| Carpeta | Responsabilidad | No debe |
|---|---|---|
| `ingestion/` | Leer cada formato y limpiar el texto (encabezados, pies, espacios). Devuelve documentos con metadata (`fuente`, `pagina`). | Cortar en fragmentos ni llamar a modelos. |
| `chunking/` | Cortar documentos en fragmentos con tamaño y solapamiento de `config.yaml`. | Saber de dónde vino el texto. |
| `embeddings/` | Crear el modelo de embeddings. | Guardar nada. |
| `vectordb/` | Crear, reconstruir y abrir la colección. Única carpeta que conoce la librería de la base. | Decidir qué es relevante. |
| `retrieval/` | Buscar los k más parecidos y aplicar el umbral de relevancia. | Llamar al LLM. |
| `prompts/` | Reglas del sistema (`.txt`) y armado de mensajes (contexto + pregunta). | Llamar al LLM. |
| `llm/` | Crear el cliente del modelo y extraer el texto de su respuesta. | Saber qué es un fragmento. |
| `pipeline/` | Unir los pasos. `ingest_pipeline` = cargar → trocear → embeddings → guardar. `rag_pipeline` = buscar → umbral → prompt → LLM. Expone el **contrato** que usa la API (p. ej. `responder(pregunta) -> str`). | Tener lógica propia de un paso. |
| `evaluation/` | Medir con preguntas de prueba: % de fuente correcta, distancias, umbral sugerido, % de respuestas correctas. | Usarse en producción. |
| `api/` | Recibir peticiones, validar (firma, largo, límites), llamar al contrato del pipeline y responder. | Buscar ni armar prompts por su cuenta. |
| `utils/` | Leer `config.yaml`, resolver rutas desde la raíz, cargar `.env`, helpers de consola. | Importar otras carpetas de `src/`. |

## 3. Reglas de dependencias

Los imports van solo hacia abajo:

```
main.py
  └─ api/ ─────────────► pipeline/ ◄──────── evaluation/
                            │
      ┌───────────┬─────────┼──────────┬──────────┬──────────┐
  ingestion/  chunking/  vectordb/  retrieval/  prompts/    llm/
                            │           │
                       embeddings/   vectordb/
  (todas pueden usar utils/; utils/ no usa a nadie)
```

- Solo `api/` importa FastAPI, Flask, Twilio u otras librerías del canal.
- Nadie importa `api/`, salvo `main.py`.
- Los pasos (`ingestion` … `llm`) no importan `pipeline/`, `evaluation/` ni `api/`.
- Conviene un test que lo verifique leyendo los imports (ver `tests/test_capas.py` en el proyecto de referencia).

Así se puede cambiar el canal (WhatsApp → web), la base (ChromaDB → FAISS) o el modelo tocando una sola carpeta.

## 4. Configuración: `config.yaml` vs `.env`

| Va en `config.yaml` (a git) | Va en `.env` (nunca a git) |
|---|---|
| Nombres de modelos, `chunk_size`, `chunk_overlap`, `k`, umbral, timeouts, rutas relativas, mensajes fijos | API keys, tokens, contraseñas, URLs privadas |

- Las rutas de `config.yaml` son relativas a la raíz del proyecto; `utils/config.py` las resuelve. Así el código funciona desde cualquier carpeta.
- Ningún número "mágico" en el código: si alguien podría querer ajustarlo, va en `config.yaml`.
- `.env.example` siempre actualizado con las mismas variables que `.env`, pero vacías.

## 5. Punto de entrada: `main.py`

Un solo archivo con subcomandos, siempre ejecutado desde la raíz:

```bash
python main.py ingestar                # data/documentos/ → base vectorial
python main.py probar-busqueda         # evaluación de la búsqueda
python main.py preguntar "¿...?"       # una pregunta; sin texto = conversación
python main.py preguntar --csv data/preguntas_prueba.csv
uvicorn src.api.routes:app             # servidor (cuando exista api/)
```

`main.py` solo lee argumentos, llama al pipeline o a la evaluación e imprime. Nada de lógica de negocio.

## 6. Estilo de código

Cada archivo se lee de arriba abajo en el orden del flujo, dividido en secciones:

```python
# =====================================================================
# == CONFIGURACIÓN: qué valores usa este archivo ==
# =====================================================================

# =====================================================================
# == PASO 1: Objetivo del paso — qué hace en pocas palabras ==
# =====================================================================

def funcion():
    # 1.1 Subpaso
    # 1.2 Subpaso
```

- Orden: `CONFIGURACIÓN` → `PASO 1…N` → (`CONTRATO` si expone una interfaz) → `EJECUCIÓN` si tiene `main`.
- El docstring del módulo dice qué hace el archivo y lista sus pasos.
- Funciones pequeñas con docstring de una línea; comentarios para el *por qué*, no para el *qué*.

## 7. Datos, logs y archivos generados

- **Cuatro zonas en la raíz**: código (`src/`, `tests/`, `main.py`), datos (`data/`), documentación (`docs/`) y, si se trabaja con un agente de IA, su seguimiento (`harness/`). En la raíz solo quedan `README.md`, `main.py` y la configuración (`config.yaml`, `requirements.txt`, `.env.example`, `.gitignore`, `pytest.ini`), más `CLAUDE.md`/`AGENTS.md` si el agente lo exige ahí.
- `docs/` es **documentación**, como en el resto de proyectos de software; nunca datos que se ingestan.
- `data/documentos/`: solo documentos a indexar. Todo lo que haya ahí se ingesta.
- `data/preguntas_prueba.csv`: columnas `pregunta,respuesta_esperada,fuente_esperada` (fuente vacía = la respuesta no está en los documentos; sirve para probar el "no sé").
- `logs/`: un `.gitkeep` en git; los `.log` y `.csv` de consultas se ignoran (pueden tener datos de clientes; anonimizar teléfonos o correos).
- La base vectorial (`chroma_db/`, índices FAISS…) se genera con `python main.py ingestar` y no va a git.

`.gitignore` mínimo:

```
.env
.venv/
__pycache__/
.pytest_cache/
chroma_db/
logs/*
!logs/.gitkeep
```

## 8. Tests

- `pytest` con `pythonpath = .` y los tests en `tests/`.
- Sin llamadas pagadas: usar embeddings y LLM falsos (`DeterministicFakeEmbedding`, `FakeListChatModel` de `langchain_core`).
- Un test por regla importante: umbral (sin contexto no se llama al LLM), contrato del pipeline, formatos de ingesta, reconstrucción idempotente de la base, reglas de dependencias.

## 9. Checklist para un proyecto nuevo

1. Crear el árbol de la sección 1 (carpetas con `__init__.py`).
2. `config.yaml` con modelos, chunk, k, umbral y rutas; `.env.example` con las claves.
3. `.gitignore` de la sección 7.
4. Implementar en orden: `utils` → `ingestion` → `chunking` → `embeddings` → `vectordb` → `pipeline/ingest_pipeline` → `retrieval` → `prompts` → `llm` → `pipeline/rag_pipeline` → `evaluation` → `api`.
5. `main.py` con los subcomandos de la sección 5.
6. 20 preguntas de prueba en `data/` (incluir 2 o más sin respuesta) y medir: búsqueda primero, respuestas después.
7. Calibrar el umbral con `probar-busqueda` y ajustar el prompt con dos corridas de `preguntar --csv`.

## 10. Adaptar sin romper la estructura

- **Proyecto muy pequeño**: se puede omitir `evaluation/` o `api/`, pero mantener `config.yaml`, `pipeline/` y la regla de dependencias.
- **Otra base vectorial o modelo**: cambiar solo `vectordb/`, `embeddings/` o `llm/` y su sección en `config.yaml`.
- **Reranking, búsqueda híbrida, memoria**: van en `retrieval/` (reranking, híbrida) o en una carpeta nueva (`memory/`) que el pipeline usa; nunca dentro de `api/`.
