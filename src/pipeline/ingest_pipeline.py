"""Pipeline de ingesta: docs/ -> fragmentos -> embeddings -> ChromaDB.

Cada ejecución reconstruye la colección desde cero, así que se puede correr
todas las veces que cambien los documentos sin duplicar fragmentos.

Pasos:
    1. Preparar    cargar y limpiar (ingestion) y trocear (chunking)
    2. Guardar     embeddings (embeddings) y base vectorial (vectordb)
    3. Ingestar    los dos pasos seguidos
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from src.chunking.chunker import CHUNK_OVERLAP, CHUNK_SIZE, trocear
from src.embeddings.embedder import crear_embeddings
from src.ingestion.loader import cargar_documentos
from src.utils.config import CONFIG, ruta
from src.vectordb.vector_store import CHROMA_DIR, construir_base


# =====================================================================
# == CONFIGURACIÓN: carpeta de documentos y costo de los embeddings ==
# =====================================================================

DOCS_DIR = ruta("docs")
COSTO_POR_MILLON = CONFIG["embeddings"]["costo_por_millon"]


@dataclass
class Preparado:
    """Resultado del PASO 1, antes de gastar en embeddings."""

    documentos: list[Document]
    fragmentos: list[Document]

    @property
    def archivos(self) -> int:
        return len({d.metadata["fuente"] for d in self.documentos})

    @property
    def costo_aprox(self) -> float:
        # Aproximación: 1 token ≈ 4 caracteres.
        caracteres = sum(len(f.page_content) for f in self.fragmentos)
        return caracteres / 4 / 1_000_000 * COSTO_POR_MILLON


# =====================================================================
# == PASO 1: Preparar — cargar, limpiar y trocear (sin costo) ==
# =====================================================================

def preparar(
    docs: Path = DOCS_DIR,
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
) -> Preparado:
    documentos = cargar_documentos(docs)
    if not documentos:
        raise ValueError("No se encontró texto. Agrega PDF, Word, TXT o Markdown a la carpeta.")
    return Preparado(documentos, trocear(documentos, chunk_size, chunk_overlap))


# =====================================================================
# == PASO 2: Guardar — embeddings y base vectorial (llama a OpenAI) ==
# =====================================================================

def guardar(
    preparado: Preparado,
    destino: Path = CHROMA_DIR,
    embeddings: Embeddings | None = None,
) -> None:
    construir_base(preparado.fragmentos, embeddings or crear_embeddings(), destino)


# =====================================================================
# == PASO 3: Ingestar — preparar y guardar seguidos ==
# =====================================================================

def ingestar(
    docs: Path = DOCS_DIR,
    destino: Path = CHROMA_DIR,
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
    embeddings: Embeddings | None = None,
) -> Preparado:
    preparado = preparar(docs, chunk_size, chunk_overlap)
    guardar(preparado, destino, embeddings)
    return preparado
