"""Embeddings: modelo de OpenAI que convierte texto en vectores.

Pasos:
    1. Crear el modelo   con la clave de .env
"""

from __future__ import annotations

from langchain_core.embeddings import Embeddings

from src.utils.config import CONFIG
from src.utils.helpers import verificar_clave


# =====================================================================
# == CONFIGURACIÓN: modelo de embeddings ==
# =====================================================================

MODELO_EMBEDDINGS = CONFIG["embeddings"]["modelo"]


# =====================================================================
# == PASO 1: Crear el modelo — necesita OPENAI_API_KEY en .env ==
# =====================================================================

def crear_embeddings() -> Embeddings:
    from langchain_openai import OpenAIEmbeddings

    verificar_clave()
    return OpenAIEmbeddings(model=MODELO_EMBEDDINGS)
