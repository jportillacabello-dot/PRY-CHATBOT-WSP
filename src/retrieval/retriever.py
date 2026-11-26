"""Retrieval: buscar los fragmentos relevantes para una pregunta.

Pasos:
    1. Buscar    los K fragmentos más parecidos, con su distancia coseno
    2. Filtrar   guardrail de relevancia: solo los que pasan el umbral
"""

from __future__ import annotations

from langchain_chroma import Chroma
from langchain_core.documents import Document

from src.utils.config import CONFIG


# =====================================================================
# == CONFIGURACIÓN: cuántos fragmentos y qué tan parecidos ==
# =====================================================================

K = CONFIG["retrieval"]["k"]
# Distancia coseno máxima para considerar un fragmento relevante.
# Calibrar con: python main.py probar-busqueda
UMBRAL_DISTANCIA = CONFIG["retrieval"]["umbral_distancia"]


# =====================================================================
# == PASO 1: Buscar — los K fragmentos más parecidos ==
# =====================================================================

def buscar(pregunta: str, base: Chroma, k: int = K) -> list[tuple[Document, float]]:
    """Los k fragmentos más parecidos con su distancia coseno (menor = más parecido)."""
    return base.similarity_search_with_score(pregunta, k=k)


# =====================================================================
# == PASO 2: Filtrar — guardrail de relevancia ==
# =====================================================================

def filtrar_relevantes(
    resultados: list[tuple[Document, float]],
    umbral: float = UMBRAL_DISTANCIA,
) -> list[Document]:
    """Se queda con los fragmentos cuya distancia no supera el umbral."""
    return [doc for doc, distancia in resultados if distancia <= umbral]
