"""Base vectorial: crear, reconstruir y abrir la colección de ChromaDB.

Única parte del proyecto que conoce ChromaDB.

Pasos:
    1. Conectar         cliente persistente en disco
    2. Construir        borrar la colección anterior y guardar los fragmentos
    3. Abrir            la colección ya creada, para buscar
"""

from __future__ import annotations

from pathlib import Path

import chromadb
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from src.embeddings.embedder import crear_embeddings
from src.utils.config import CONFIG, ruta
from src.utils.helpers import mostrar


# =====================================================================
# == CONFIGURACIÓN: carpeta, colección y distancia ==
# =====================================================================

CHROMA_DIR = ruta("chroma")
COLECCION = CONFIG["vectordb"]["coleccion"]
# Distancia coseno: el umbral de retrieval se calcula sobre ella.
METADATA_COLECCION = {"hnsw:space": CONFIG["vectordb"]["distancia"]}


# =====================================================================
# == PASO 1: Conectar — cliente persistente en disco ==
# =====================================================================

def _cliente(destino: Path) -> chromadb.ClientAPI:
    return chromadb.PersistentClient(
        path=str(destino),
        settings=chromadb.config.Settings(anonymized_telemetry=False),
    )


# =====================================================================
# == PASO 2: Construir — reconstruir la colección desde cero ==
# =====================================================================

def construir_base(
    fragmentos: list[Document],
    embeddings: Embeddings,
    destino: Path = CHROMA_DIR,
    coleccion: str = COLECCION,
) -> Chroma:
    """Borra la colección (si existe) y la vuelve a crear con los fragmentos."""
    cliente = _cliente(destino)

    # 2.1 Borrar la colección anterior para no duplicar fragmentos
    if coleccion in [c.name for c in cliente.list_collections()]:
        cliente.delete_collection(coleccion)

    # 2.2 Crear la colección con distancia coseno y guardar los fragmentos
    base = Chroma(
        client=cliente,
        collection_name=coleccion,
        embedding_function=embeddings,
        collection_metadata=METADATA_COLECCION,
    )
    ids = [f"{f.metadata['fuente']}#p{f.metadata['pagina']}#f{f.metadata['fragmento']}" for f in fragmentos]
    if fragmentos:
        base.add_documents(fragmentos, ids=ids)  # aquí se llama a OpenAI
    return base


# =====================================================================
# == PASO 3: Abrir — la colección que creó la ingesta ==
# =====================================================================

def abrir_base(destino: Path = CHROMA_DIR, embeddings: Embeddings | None = None) -> Chroma:
    destino = Path(destino)
    if not (destino / "chroma.sqlite3").exists():
        raise FileNotFoundError(f"No existe la base en {mostrar(destino)}/. Corre primero: python main.py ingestar")
    return Chroma(
        client=_cliente(destino),
        collection_name=COLECCION,
        embedding_function=embeddings or crear_embeddings(),
    )
