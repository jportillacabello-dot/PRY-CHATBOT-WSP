"""LLM: cliente de gpt-5-mini y extracción del texto de su respuesta.

Pasos:
    1. Crear el cliente    modelo, razonamiento mínimo, timeout y reintentos
    2. Extraer el texto    la respuesta puede venir como texto o por bloques
"""

from __future__ import annotations

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage

from src.utils.config import CONFIG
from src.utils.helpers import verificar_clave


# =====================================================================
# == CONFIGURACIÓN: modelo y límites ==
# =====================================================================

LLM = CONFIG["llm"]  # modelo, reasoning_effort, max_tokens, timeout, max_retries


# =====================================================================
# == PASO 1: Crear el cliente — rápido y con límite de tiempo ==
# =====================================================================

def crear_llm() -> BaseChatModel:
    from langchain_openai import ChatOpenAI

    verificar_clave()
    return ChatOpenAI(
        model=LLM["modelo"],
        reasoning_effort=LLM["reasoning_effort"],
        max_tokens=LLM["max_tokens"],
        timeout=LLM["timeout"],
        max_retries=LLM["max_retries"],
    )


# =====================================================================
# == PASO 2: Extraer el texto — de un mensaje de texto o por bloques ==
# =====================================================================

def extraer_texto(mensaje: BaseMessage) -> str:
    contenido = mensaje.content
    if isinstance(contenido, str):
        return contenido.strip()
    partes = [b.get("text", "") if isinstance(b, dict) else str(b) for b in contenido]
    return "".join(partes).strip()
