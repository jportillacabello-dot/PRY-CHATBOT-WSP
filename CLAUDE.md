# CLAUDE.md

MVP de un chatbot RAG en WhatsApp: responde las consultas de los clientes de un negocio usando **solo** sus documentos (Twilio → FastAPI → ChromaDB → gpt-5-mini → TwiML).

- Plan, arquitectura C1/C2, herramientas y presupuesto: [README_MVP_Chatbot_RAG_WhatsApp.md](README_MVP_Chatbot_RAG_WhatsApp.md)
- Fechas, horas y responsables por paso: `Plan_MVP_Chatbot_RAG_WhatsApp.xlsx`
- Equipo: Jhonatan (Fases 1–2: ingesta + RAG) · Jenner (Fases 0, 3–6: preparación, WhatsApp, calidad, despliegue, cierre)
- Plazo: 26-nov → 11-dic-2026 · Meta de calidad: ≥ 18/20 preguntas de prueba correctas

## Flujo de inicio (Startup Workflow)

Antes de escribir código:

1. **Confirma el directorio de trabajo** con `pwd`
2. **Lee este archivo** completo
3. **Lee `progress.md`** y, si existe, `session-handoff.md`
4. **Ejecuta `bash init.sh`** (Git Bash en Windows) para verificar que el entorno está sano
5. **Lee `feature_list.json`** para ver el estado de las fases
6. **Revisa los commits recientes** con `git log --oneline -5` (cuando el repo ya exista)

Si la verificación base falla, arréglala primero antes de añadir alcance nuevo.

## Reglas de trabajo

- **Una funcionalidad a la vez (One feature at a time)**: trabaja en una sola fase/funcionalidad de `feature_list.json` cuyas dependencias estén en `done`
- **Verificación obligatoria**: no digas "terminado" sin haber ejecutado `bash init.sh` y la prueba propia de la fase
- **Actualiza los artefactos**: antes de cerrar la sesión, actualiza `progress.md` y `feature_list.json`
- **Mantente en el alcance (Stay in scope)**: fuera del MVP quedan audios/imágenes, historial largo, panel de administración y varios negocios
- **Deja el repo limpio (clean)**: la siguiente sesión debe poder ejecutar `bash init.sh` de inmediato

## Reglas del proyecto

- **Autoría**: nunca incluyas a Claude como autor ni contribuidor. Nada de `Co-Authored-By: Claude`, "Generated with Claude Code" ni menciones similares en commits, pull requests, README, código o documentación.
- **Capas e imports**: tres capas en archivos planos, sin carpetas extra. Entrada (`app.py`) → lógica (`rag.py`) → datos (`ingesta.py`, `chroma_db/`, `prompt.txt`). Los imports van solo en ese sentido: `rag.py` e `ingesta.py` nunca importan FastAPI ni Twilio, y `app.py` solo usa `responder()` de `rag.py`.
- **Cierre del proyecto**: al terminar el MVP (Fase 6), `CLAUDE.md` sale del repositorio y de su historial:
  1. Agregar `CLAUDE.md` a `.gitignore`.
  2. Reescribir el historial con `git filter-repo --path CLAUDE.md --invert-paths` (se instala con `pip install git-filter-repo`), trabajando sobre una copia del repo.
  3. Volver a conectar el remoto y subir con `git push --force`. Avisar antes a Jenner: los hashes de los commits cambian y tendrá que clonar de nuevo.
  4. Conservar el archivo en local.
- **Secretos**: las claves van solo en `.env` (en `.gitignore`) o en las variables de entorno de Render. Nunca en código, logs ni commits.
- **El bot no inventa**: el prompt (`prompt.txt`) obliga a responder solo con el contexto recuperado y a decir "no sé" si no está. Es requisito de la política de WhatsApp (solo bots de atención al cliente).
- **Guardrails**: en `rag.py`, umbral de relevancia (sin fragmentos relevantes no se llama al LLM). En `app.py`, solo texto, máximo 500 caracteres, 10 mensajes por minuto por número y respuesta de respaldo si OpenAI falla. Ver `diagramas/arquitectura-pipeline.html`.
- **Contrato entre fases**: `rag.py` expone `responder(pregunta: str) -> str`. `app.py` solo depende de esa función; mientras no exista, usa una respuesta fija.
- **Webhook**: Twilio envía formulario (requiere `python-multipart`), espera TwiML y corta a los 15 s. Validar `X-Twilio-Signature` y mantener respuestas cortas (cada mensaje extra se cobra).
- **Log**: en `data/log_preguntas.csv` el número de teléfono va anonimizado.
- **Modelos**: `gpt-5-mini` para responder, `text-embedding-3-small` para embeddings. Si se cambia el modelo de embeddings, hay que volver a correr `ingesta.py`.

## Artefactos requeridos

- `feature_list.json` — Estado de las fases del MVP (fuente de verdad)
- `progress.md` — Bitácora de continuidad entre sesiones
- `init.sh` — Ruta estándar de arranque y verificación
- `session-handoff.md` — Opcional, para sesiones largas
- `data/preguntas_prueba.csv` — Las 20 preguntas con su respuesta esperada (base de toda evaluación)

## Definición de terminado (Definition of Done)

Una funcionalidad está terminada solo cuando se cumple TODO lo siguiente:

- [ ] El comportamiento objetivo está implementado
- [ ] La verificación requerida se ejecutó de verdad (`bash init.sh` + la prueba de la fase, p. ej. las 20 preguntas)
- [ ] La evidencia quedó registrada en `feature_list.json` (campo `evidence`) o `progress.md`
- [ ] El repositorio sigue pudiendo arrancar desde la ruta estándar (restartable)

## Fin de sesión (End of Session)

Antes de terminar una sesión:

1. Actualiza `progress.md` con el estado actual
2. Actualiza `feature_list.json` con el nuevo estado de la funcionalidad
3. Registra riesgos o bloqueos sin resolver
4. Haz commit con un mensaje descriptivo cuando el trabajo esté en un estado seguro (sin líneas de coautoría de Claude)
5. Deja el repo lo bastante limpio para que la siguiente sesión ejecute `bash init.sh` de inmediato

## Comandos de verificación (Verification Commands)

```bash
# Verificación completa (recomendada)
bash init.sh
```

Chequeos requeridos:
- `python -m compileall -q .` (sin errores de sintaxis)
- `python -m pytest` (cuando exista la carpeta `tests/`)
- `feature_list.json` es JSON válido
- `.env` está en `.gitignore`

## Escalamiento

Si te encuentras con:
- **Decisiones de arquitectura**: consulta el README del MVP; si no lo resuelve, pregunta al usuario
- **Requisitos poco claros**: revisa el Excel del plan; si no lo resuelve, pregunta al usuario
- **Fallos de tests repetidos o < 18/20 correctas**: registra el resultado en `progress.md` y márcalo para revisión humana
- **Alcance ambiguo**: vuelve a leer `feature_list.json` para ver la definición de terminado
