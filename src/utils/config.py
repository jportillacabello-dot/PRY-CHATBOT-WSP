"""Configuración del proyecto: lee config.yaml una sola vez y resuelve rutas.

Pasos:
    1. Leer config.yaml   una vez por proceso
    2. Resolver rutas     relativas a la raíz del proyecto
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml


# =====================================================================
# == CONFIGURACIÓN: dónde está la raíz y el archivo de configuración ==
# =====================================================================

RAIZ = Path(__file__).resolve().parents[2]  # src/utils/config.py -> raíz
CONFIG_PATH = RAIZ / "config.yaml"


# =====================================================================
# == PASO 1: Leer config.yaml — una sola vez por proceso ==
# =====================================================================

@lru_cache(maxsize=1)
def cargar_config(ruta: Path = CONFIG_PATH) -> dict:
    with open(ruta, encoding="utf-8") as archivo:
        return yaml.safe_load(archivo)


CONFIG = cargar_config()


# =====================================================================
# == PASO 2: Resolver rutas — siempre desde la raíz del proyecto ==
# =====================================================================

def ruta(clave: str) -> Path:
    """Ruta absoluta de una entrada de `rutas:` en config.yaml."""
    return RAIZ / CONFIG["rutas"][clave]
