"""Prompts: reglas del bot y armado de los mensajes para el LLM.

Pasos:
    1. Cargar reglas     system_prompt.txt con el mensaje "sin información"
    2. Armar contexto    fragmentos con el nombre de su archivo
    3. Armar mensajes    sistema (reglas) + cliente (contexto y pregunta)
"""

from __future__ import annotations

from pathlib import Path

from langchain_core.documents import Document
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage

from src.utils.config import CONFIG


# =====================================================================
# == CONFIGURACIÓN: archivo de reglas y mensajes fijos ==
# =====================================================================

PROMPT_PATH = Path(__file__).with_name("system_prompt.txt")
MENSAJE_SIN_INFO = CONFIG["mensajes"]["sin_info"]
MENSAJE_VACIO = CONFIG["mensajes"]["vacio"]


# =====================================================================
# == PASO 1: Cargar reglas — {sin_info} se reemplaza por el mensaje fijo ==
# =====================================================================

def cargar_prompt(ruta: Path = PROMPT_PATH) -> str:
    return Path(ruta).read_text(encoding="utf-8").replace("{sin_info}", MENSAJE_SIN_INFO)


# =====================================================================
# == PASO 2: Armar contexto — cada fragmento con su archivo ==
# =====================================================================

def armar_contexto(documentos: list[Document]) -> str:
    return "\n\n".join(f"[{d.metadata.get('fuente', '?')}]\n{d.page_content}" for d in documentos)


# =====================================================================
# == PASO 3: Armar mensajes — reglas + contexto + pregunta ==
# =====================================================================

def armar_mensajes(pregunta: str, documentos: list[Document]) -> list[BaseMessage]:
    return [
        SystemMessage(cargar_prompt()),
        HumanMessage(f"CONTEXTO:\n{armar_contexto(documentos)}\n\nPREGUNTA DEL CLIENTE:\n{pregunta}"),
    ]
