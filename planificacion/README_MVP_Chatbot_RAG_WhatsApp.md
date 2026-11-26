# MVP – Chatbot RAG en WhatsApp

> Bot que responde por WhatsApp las consultas de los clientes de un negocio usando **solo** la información de sus documentos (RAG: *Retrieval-Augmented Generation*).

| | |
|---|---|
| **Equipo** | Jhonatan (ingesta + RAG) · Jenner (preparación, WhatsApp, calidad, despliegue, cierre) |
| **Fechas** | Jueves 26-nov-2026 → Viernes 11-dic-2026 |
| **Esfuerzo estimado** | 37.5 h (Jhonatan ≈ 15 h · Jenner ≈ 22.5 h) |
| **Meta de calidad** | ≥ 18 de 20 preguntas de prueba respondidas correctamente |

---

## 1. Problema y alcance

- **Qué resuelve:** responder 24/7 preguntas frecuentes de clientes (horarios, precios, procesos, políticas) sin intervención humana.
- **Dentro del MVP:** un solo negocio/tema, documentos en PDF/Word/FAQ, respuestas de texto en WhatsApp, registro de preguntas.
- **Fuera del MVP:** audios e imágenes, historial de conversación largo, panel de administración, varios negocios.
- **Regla clave:** el bot solo responde sobre el negocio. Si no encuentra la información, dice que no sabe. Esto evita que invente respuestas y cumple la política de WhatsApp (desde el 15-ene-2026 Meta prohíbe los chatbots de IA de propósito general; los bots de atención al cliente sí están permitidos).

---

## 2. Cómo funciona (analogía del restaurante)

| Pieza | En el restaurante | Herramienta |
|---|---|---|
| Canal del cliente | El cliente hace el pedido | WhatsApp |
| Intermediario | El mesero lleva el pedido a la cocina | Twilio (BSP autorizado por Meta) |
| Puerta de la cocina | Entrada desde la calle | ngrok (pruebas) → Render (nube) |
| Cocina | Donde se prepara la respuesta | FastAPI (Python) |
| Libro de recetas | Información del negocio | ChromaDB (base vectorial) |
| Chef | Redacta la respuesta | OpenAI gpt-5-mini |
| Orden al chef | Reglas de cómo responder | System prompt |

### Flujo 1 – Preparar la cocina (una sola vez)

```
Documentos del negocio (PDF, Word, FAQs)
   → Script de ingesta: los corta en pedazos (chunks)
      → OpenAI: convierte cada pedazo en un embedding (huella de significado)
         → ChromaDB: guarda pedazos + embeddings
```

### Flujo 2 – Atender un mensaje

```
Cliente escribe en WhatsApp
  → Twilio recibe el mensaje y llama al webhook /whatsapp
    → FastAPI busca en ChromaDB los 3-4 pedazos más parecidos
      → Arma: reglas + pedazos + pregunta → gpt-5-mini redacta la respuesta
    ← FastAPI devuelve la respuesta en formato TwiML
  ← Twilio la entrega al cliente
```

---

## 3. Arquitectura C4

### C1 – Contexto

| Elemento | Tipo | Responsabilidad |
|---|---|---|
| Cliente | Persona | Hace preguntas por WhatsApp |
| Administrador | Persona | Carga y actualiza los documentos |
| WhatsApp + Twilio | Sistema externo | Transporta los mensajes en ambos sentidos |
| **Chatbot RAG** | **Nuestro sistema** | Busca la información y arma la respuesta |
| OpenAI API | Sistema externo | Embeddings y redacción de respuestas |

### C2 – Contenedores

| Contenedor | Tecnología | Qué hace | Cuándo corre |
|---|---|---|---|
| API del Bot (`app.py`) | Python + FastAPI + LangChain | Recibe el webhook, valida la firma de Twilio, ejecuta la cadena RAG y responde en TwiML | Con cada mensaje |
| Base vectorial (`/chroma_db`) | ChromaDB persistido en disco | Guarda los fragmentos y encuentra los más parecidos | Con cada consulta |
| Script de ingesta (`ingesta.py`) | Python + LangChain | Carga y trocea los documentos y genera los embeddings | Una vez, y cuando cambian los documentos |
| Log de preguntas | CSV / SQLite | Registra qué preguntan, para detectar documentos faltantes | Con cada mensaje |

> En el MVP los cuatro contenedores corren en un solo servidor.

---

## 4. Herramientas

| Herramienta | Para qué la usamos | Costo | Link |
|---|---|---|---|
| **Python 3.10+** | Lenguaje de todo el proyecto | Gratis | https://www.python.org |
| **FastAPI + Uvicorn** | Servidor web que recibe el webhook `/whatsapp` | Gratis | https://fastapi.tiangolo.com |
| **LangChain** | Carga de documentos, chunking y cadena RAG (retriever + prompt + LLM) | Gratis | https://python.langchain.com |
| **ChromaDB** | Base vectorial local (el "libro de recetas") | Gratis (corre en el mismo servidor) | https://docs.trychroma.com |
| **OpenAI API – gpt-5-mini** | Redactar las respuestas | $0.25 / 1M tokens de entrada · $2.00 / 1M de salida | https://platform.openai.com |
| **OpenAI API – text-embedding-3-small** | Generar embeddings | $0.02 / 1M tokens | https://platform.openai.com |
| **Twilio (WhatsApp Sandbox)** | Conectar WhatsApp con nuestro servidor; el sandbox sirve para probar sin trámites con Meta | $0.005 por mensaje (entrante o saliente); crédito de prueba al crear la cuenta | https://console.twilio.com |
| **Meta (tarifa WhatsApp)** | Cobro de Meta por las respuestas que envía el bot, trasladado por Twilio | 1,000 mensajes de servicio gratis al mes por número; después $0.03 por mensaje en Perú (desde 1-oct-2026) | https://developers.facebook.com/docs/whatsapp/pricing |
| **ngrok** | Túnel que expone la PC a internet mientras probamos | Gratis (la URL cambia al reiniciar) | https://ngrok.com |
| **Render** | Hosting en la nube para dejar el bot 24/7 | Free (se duerme tras 15 min) · Starter $7/mes · Standard $25/mes | https://render.com |
| **GitHub** | Repositorio del código; Render despliega desde aquí | Gratis | https://github.com |
| **python-dotenv** | Leer las claves desde `.env` (nunca se suben al repo) | Gratis | https://pypi.org/project/python-dotenv/ |

### Dependencias (`requirements.txt`)

```
fastapi
uvicorn
twilio
langchain
langchain-openai
langchain-chroma
langchain-community
chromadb
openai
python-dotenv
pypdf
```

### Variables de entorno (`.env`)

```
OPENAI_API_KEY=...
TWILIO_ACCOUNT_SID=...
TWILIO_AUTH_TOKEN=...
```

---

## 5. Estructura del repositorio

```
chatbot-rag-whatsapp/
├── docs/                  # Documentos fuente del negocio
├── chroma_db/             # Base vectorial (generada por ingesta.py)
├── data/
│   ├── preguntas_prueba.csv   # 20 preguntas + respuesta esperada
│   └── log_preguntas.csv      # Registro de consultas reales
├── ingesta.py             # Flujo 1: documentos → ChromaDB
├── rag.py                 # Cadena RAG: función responder(pregunta)
├── app.py                 # FastAPI: webhook /whatsapp → TwiML
├── prompt.txt             # Reglas del bot
├── requirements.txt
├── .env                   # Claves (en .gitignore)
└── README.md
```

---

## 6. Plan por fases

| Fase | Fechas | Responsable | Entregable | Depende de |
|---|---|---|---|---|
| 0. Preparación | 26–27 nov | Jenner (Jhonatan apoya en cuentas) | Entorno listo + documentos + 20 preguntas de prueba | — |
| 1. Ingesta | 28–30 nov | Jhonatan | ChromaDB cargada y búsqueda validada | Fase 0 |
| 2. Cadena RAG | 1–3 dic | Jhonatan | `rag.py` con `responder()` ≥ 18/20 en consola | Fase 1 |
| 3. WhatsApp | 4–6 dic | Jenner | Bot respondiendo en WhatsApp (Sandbox + ngrok) | Fase 2 |
| 4. Calidad | 7–8 dic | Jenner | Log, firma de Twilio validada, evaluación ≥ 18/20 | Fase 3 |
| 5. Despliegue | 9–10 dic | Jenner | Bot 24/7 en Render, sin depender de la PC | Fase 4 |
| 6. Cierre | 11 dic | Jenner (Jhonatan apoya en la demo) | README, diagramas, demo y costos reales vs. presupuesto | Fase 5 |

**Traspaso crítico:** la Fase 3 (Jenner) necesita `rag.py` (Jhonatan). Para no bloquearse, Jenner puede adelantar `app.py` con una respuesta fija de prueba y conectarlo a `responder()` cuando esté listo.

> Detalle de pasos, fechas y horas: `Plan_MVP_Chatbot_RAG_WhatsApp.xlsx`.

---

## 7. Presupuesto mensual estimado (USD)

| Concepto | 1. Pruebas (200 consultas) | 2. Piloto (1,000) | 3. Crecimiento (5,000) |
|---|---|---|---|
| LLM (gpt-5-mini) | 0.27 | 1.35 | 6.75 |
| Embeddings | 0.00 | 0.00 | 0.01 |
| Twilio ($0.005 × 2 mensajes) | 2.00 | 10.00 | 50.00 |
| Meta (respuestas sobre 1,000 × $0.03) | 0.00 | 0.00 | 120.00 |
| Número propio (aprox.) | 0.00 | 1.15 | 1.15 |
| Servidor | 0 (PC + ngrok) | 7 (Render Starter) | 25 (Render Standard) |
| **Total** | **≈ 2.27** | **≈ 19.50** | **≈ 202.91** |

- Costo único de indexar los documentos: ≈ $0.01.
- Para controlar el costo de Meta: respuestas cortas (cada mensaje extra se cobra), y aprovechar que los mensajes que entran por anuncios Click-to-WhatsApp son gratis.

---

## 8. Riesgos y cómo los cubrimos

| Riesgo | Mitigación |
|---|---|
| El bot inventa respuestas | Prompt que obliga a usar solo el contexto y a decir "no sé" |
| Búsqueda trae fragmentos equivocados | Probar las 20 preguntas en la Fase 1 y ajustar el tamaño de chunk y k |
| La URL de ngrok cambia | Volver a pegarla en Twilio; desaparece al pasar a Render |
| Claves expuestas | `.env` en `.gitignore` y variables de entorno en Render |
| Peticiones falsas al webhook | Validar la firma `X-Twilio-Signature` |
| Sandbox solo para invitados | Suficiente para el MVP; para clientes reales, número propio aprobado por Meta |
| Atraso de una persona bloquea a la otra | Trabajo en paralelo con respuesta fija mientras se termina `rag.py` |

---

*Precios revisados en noviembre de 2026; confirmar en las páginas oficiales antes de pasar a producción.*
