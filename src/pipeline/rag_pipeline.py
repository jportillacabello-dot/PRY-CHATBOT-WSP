"""Pipeline RAG: pregunta -> fragmentos -> gpt-5-mini -> respuesta.

Expone el contrato que usa la API: responder(pregunta) -> str.

Pasos:
    1. Abrir base y modelo   una sola vez por proceso
    2. Responder             buscar, filtrar por umbral y, si pasa, llamar al LLM
"""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache

from langchain_chroma import Chroma
from langchain_core.language_models.chat_models import BaseChatModel

from src.llm.llm_client import crear_llm, extraer_texto
from src.prompts.prompt_templates import MENSAJE_SIN_INFO, MENSAJE_VACIO, armar_mensajes
from src.retrieval.retriever import K, UMBRAL_DISTANCIA, buscar, filtrar_relevantes
from src.vectordb.vector_store import abrir_base


# =====================================================================
# == CONFIGURACIÓN: forma de la respuesta detallada ==
# =====================================================================

@dataclass
class Respuesta:
    """Resultado completo de una consulta (para evaluar y depurar)."""

    texto: str
    fuentes: list[str] = field(default_factory=list)
    distancias: list[float] = field(default_factory=list)
    uso_llm: bool = False


# =====================================================================
# == PASO 1: Abrir base y modelo — se crean en la primera pregunta ==
# =====================================================================

@lru_cache(maxsize=1)
def _base_por_defecto() -> Chroma:
    return abrir_base()


@lru_cache(maxsize=1)
def _llm_por_defecto() -> BaseChatModel:
    return crear_llm()


# =====================================================================
# == PASO 2: Responder — búsqueda, umbral y LLM ==
# =====================================================================

def responder_con_detalle(
    pregunta: str,
    *,
    base: Chroma | None = None,
    llm: BaseChatModel | None = None,
    k: int = K,
    umbral: float = UMBRAL_DISTANCIA,
) -> Respuesta:
    """Responde y devuelve también las fuentes y distancias (para evaluar)."""
    # 2.1 Pregunta vacía: saludo, sin buscar ni gastar
    pregunta = (pregunta or "").strip()
    if not pregunta:
        return Respuesta(MENSAJE_VACIO)

    # 2.2 Buscar fragmentos (retrieval)
    resultados = buscar(pregunta, base or _base_por_defecto(), k)
    distancias = [round(d, 3) for _, d in resultados]

    # 2.3 Guardrail: solo los relevantes; si no hay, no se llama al LLM
    relevantes = filtrar_relevantes(resultados, umbral)
    if not relevantes:
        return Respuesta(MENSAJE_SIN_INFO, distancias=distancias)

    # 2.4 Llamar al LLM con reglas + contexto + pregunta (prompts, llm)
    salida = (llm or _llm_por_defecto()).invoke(armar_mensajes(pregunta, relevantes))
    texto = extraer_texto(salida) or MENSAJE_SIN_INFO
    fuentes = list(dict.fromkeys(d.metadata.get("fuente", "?") for d in relevantes))
    return Respuesta(texto, fuentes=fuentes, distancias=distancias, uso_llm=True)


# =====================================================================
# == CONTRATO CON api/: la única función que usa la capa de entrada ==
# =====================================================================

def responder(pregunta: str) -> str:
    """Recibe el texto del cliente y devuelve la respuesta.

    Puede lanzar excepciones (OpenAI caído, timeout, base inexistente):
    api/ las captura y envía el mensaje de respaldo.
    """
    return responder_con_detalle(pregunta).texto
