"""Chunking: cortar los documentos en fragmentos para la búsqueda.

Pasos:
    1. Cortar     respetando párrafos, líneas, frases y palabras
    2. Numerar    cada fragmento dentro de su archivo (ids estables)
"""

from __future__ import annotations

from collections import Counter

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.utils.config import CONFIG


# =====================================================================
# == CONFIGURACIÓN: tamaño y solapamiento de los fragmentos ==
# =====================================================================

CHUNK_SIZE = CONFIG["ingesta"]["chunk_size"]
CHUNK_OVERLAP = CONFIG["ingesta"]["chunk_overlap"]


# =====================================================================
# == PASO 1 y 2: Trocear — cortar y numerar los fragmentos ==
# =====================================================================

def trocear(
    documentos: list[Document],
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
) -> list[Document]:
    """Corta los documentos en fragmentos y numera cada uno dentro de su fuente."""
    # 1. Cortar respetando primero párrafos, luego líneas, frases y palabras
    separador = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    fragmentos = separador.split_documents(documentos)

    # 2. Numerar los fragmentos de cada archivo (sirve para armar ids estables)
    por_fuente: Counter[str] = Counter()
    for fragmento in fragmentos:
        fuente = fragmento.metadata["fuente"]
        fragmento.metadata["fragmento"] = por_fuente[fuente]
        por_fuente[fuente] += 1
    return fragmentos
