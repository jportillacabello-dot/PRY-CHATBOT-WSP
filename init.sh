#!/bin/bash
set -e

echo "=== Inicialización del harness: Chatbot RAG WhatsApp ==="

PY="$(command -v python3 || command -v python || true)"
if [ -z "$PY" ]; then
  echo "ERROR: no se encontró Python 3.10+"
  exit 1
fi

# Activar el entorno virtual si existe (Windows o Linux)
if [ -f .venv/Scripts/activate ]; then
  source .venv/Scripts/activate
  PY=python
elif [ -f .venv/bin/activate ]; then
  source .venv/bin/activate
  PY=python
else
  echo "AVISO: no hay .venv todavía (se crea en la Fase 0)"
fi
"$PY" --version

echo "=== Estado del harness ==="
"$PY" -c "import json; d=json.load(open('feature_list.json', encoding='utf-8')); print('feature_list.json OK:', len(d['features']), 'funcionalidades')"

echo "=== Chequeos de seguridad ==="
if [ -f .env ]; then
  if ! grep -qxE '\.env' .gitignore 2>/dev/null; then
    echo "ERROR: existe .env pero no está en .gitignore"
    exit 1
  fi
  echo ".env protegido por .gitignore"
fi

if [ -f requirements.txt ]; then
  if ! grep -qi '^python-multipart' requirements.txt; then
    echo "ERROR: falta python-multipart en requirements.txt (FastAPI lo necesita para el webhook de Twilio)"
    exit 1
  fi
  echo "requirements.txt OK"
fi

echo "=== Sintaxis de Python ==="
"$PY" -m compileall -q -x '(^|/)(\.?venv|env|node_modules|build|dist|__pycache__|chroma_db|harness-kit|\.claude)(/|$)' .

echo "=== Tests ==="
if [ -d tests ]; then
  "$PY" -m pytest
else
  echo "Sin carpeta tests/ todavía"
fi

echo "=== Verificación completa ==="
echo ""
echo "Próximos pasos (Next steps):"
echo "1. Lee feature_list.json para ver el estado actual de las fases"
echo "2. Elige UNA funcionalidad sin terminar cuyas dependencias estén en done"
echo "3. Implementa solo esa funcionalidad"
echo "4. Vuelve a verificar antes de decir que está terminada"
