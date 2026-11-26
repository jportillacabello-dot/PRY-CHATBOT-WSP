"""Funciones comunes: claves de .env, rutas cortas y consola en UTF-8.

Pasos:
    1. Verificar la clave de OpenAI
    2. Mostrar rutas cortas en los mensajes
    3. Preparar la consola para tildes
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from src.utils.config import RAIZ


# =====================================================================
# == PASO 1: Verificar la clave — cargar .env y fallar claro si falta ==
# =====================================================================

def verificar_clave() -> None:
    """Carga .env y falla con un mensaje claro si no hay OPENAI_API_KEY."""
    from dotenv import load_dotenv

    load_dotenv(RAIZ / ".env")
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("Falta OPENAI_API_KEY. Copia .env.example como .env y pega tu clave.")


# =====================================================================
# == PASO 2: Rutas cortas — relativas a la carpeta actual si se puede ==
# =====================================================================

def mostrar(ruta: Path) -> str:
    ruta = Path(ruta).resolve()
    try:
        return ruta.relative_to(Path.cwd()).as_posix()
    except ValueError:
        return ruta.as_posix()


# =====================================================================
# == PASO 3: Consola en UTF-8 — tildes correctas también en Git Bash ==
# =====================================================================

def consola_utf8() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
