"""API (Fase 3, Jenner): webhook POST /whatsapp en routes.py.

routes.py debe:
    - crear la app de FastAPI (se levanta con: uvicorn src.api.routes:app)
    - validar la firma X-Twilio-Signature, el largo del mensaje y el límite por número
    - llamar solo a src.pipeline.rag_pipeline.responder(pregunta)
    - capturar excepciones y responder un mensaje de respaldo en TwiML
    - registrar cada consulta en logs/log_preguntas.csv (teléfono anonimizado)

Es la única carpeta que puede importar FastAPI y Twilio.
"""
