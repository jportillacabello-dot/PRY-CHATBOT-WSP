"""Flujo 1: documentos del negocio -> fragmentos -> embeddings -> ChromaDB.

Capa de datos: no importa FastAPI ni Twilio (ver CLAUDE.md).

Uso:
    python ingesta.py                       # lee docs/ y crea chroma_db/
    python ingesta.py --docs ejemplo/docs   # con el negocio de ejemplo

Cada ejecución reconstruye la colección desde cero, así que se puede correr
todas las veces que cambien los documentos sin duplicar fragmentos.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from collections import Counter
from pathlib import Path

import chromadb
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

DOCS_DIR = Path("docs")
CHROMA_DIR = Path("chroma_db")
COLECCION = "negocio"
MODELO_EMBEDDINGS = "text-embedding-3-small"
CHUNK_SIZE = 800
CHUNK_OVERLAP = 100
EXTENSIONES = {".pdf", ".docx", ".txt", ".md"}
# Distancia coseno: el umbral de relevancia de rag.py se calcula sobre ella.
METADATA_COLECCION = {"hnsw:space": "cosine"}

# Números de página sueltos: "3", "Página 3", "3 de 10", "3/10".
_NUMERO_PAGINA = re.compile(r"^(p[áa]g(ina)?\.?\s*)?\d+(\s*(de|/)\s*\d+)?$", re.IGNORECASE)


# ---------------------------------------------------------------- limpieza

def normalizar(texto: str) -> str:
    """Quita espacios repetidos y deja como máximo una línea en blanco seguida."""
    lineas = [re.sub(r"[ \t ]+", " ", linea).strip() for linea in texto.splitlines()]
    texto = "\n".join(lineas)
    return re.sub(r"\n{3,}", "\n\n", texto).strip()


def limpiar_paginas(paginas: list[str]) -> list[str]:
    """Quita encabezados, pies y números de página de un documento de varias páginas.

    Una línea que aparece en al menos el 60 % de las páginas (con 3 o más
    páginas) se considera encabezado o pie y se elimina.
    """
    repetidas: set[str] = set()
    if len(paginas) >= 3:
        conteo = Counter(
            linea.strip()
            for pagina in paginas
            for linea in set(pagina.splitlines())
            if linea.strip()
        )
        repetidas = {linea for linea, n in conteo.items() if n >= 0.6 * len(paginas)}

    limpias = []
    for pagina in paginas:
        lineas = [
            linea
            for linea in pagina.splitlines()
            if linea.strip() not in repetidas and not _NUMERO_PAGINA.match(linea.strip())
        ]
        limpias.append(normalizar("\n".join(lineas)))
    return limpias


# ------------------------------------------------------------------ carga

def _leer_pdf(ruta: Path) -> list[str]:
    from pypdf import PdfReader

    return [pagina.extract_text() or "" for pagina in PdfReader(ruta).pages]


def _leer_docx(ruta: Path) -> list[str]:
    import docx2txt

    return [docx2txt.process(str(ruta)) or ""]


def _leer_texto(ruta: Path) -> list[str]:
    return [ruta.read_text(encoding="utf-8")]


_LECTORES = {".pdf": _leer_pdf, ".docx": _leer_docx, ".txt": _leer_texto, ".md": _leer_texto}


def cargar_documentos(carpeta: Path) -> list[Document]:
    """Lee los PDF, Word, TXT y Markdown de la carpeta (y subcarpetas).

    Devuelve un Document por página (PDF) o por archivo (los demás), con la
    metadata `fuente` (ruta relativa) y `pagina` (empieza en 1).
    """
    carpeta = Path(carpeta)
    if not carpeta.is_dir():
        raise FileNotFoundError(f"No existe la carpeta de documentos: {carpeta}")

    documentos: list[Document] = []
    for ruta in sorted(carpeta.rglob("*")):
        if not ruta.is_file() or ruta.name.startswith((".", "~$")):
            continue
        extension = ruta.suffix.lower()
        if extension not in EXTENSIONES:
            print(f"  [omitido] {ruta.relative_to(carpeta)}: formato no soportado")
            continue

        paginas = limpiar_paginas(_LECTORES[extension](ruta))
        fuente = ruta.relative_to(carpeta).as_posix()
        if not any(paginas):
            print(f"  [aviso] {fuente}: no tiene texto (¿PDF escaneado?)")
            continue
        for numero, texto in enumerate(paginas, start=1):
            if texto:
                documentos.append(Document(page_content=texto, metadata={"fuente": fuente, "pagina": numero}))
    return documentos


# ---------------------------------------------------------------- troceado

def trocear(
    documentos: list[Document],
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
) -> list[Document]:
    """Corta los documentos en fragmentos y numera cada uno dentro de su fuente."""
    separador = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    fragmentos = separador.split_documents(documentos)
    por_fuente: Counter[str] = Counter()
    for fragmento in fragmentos:
        fuente = fragmento.metadata["fuente"]
        fragmento.metadata["fragmento"] = por_fuente[fuente]
        por_fuente[fuente] += 1
    return fragmentos


# ---------------------------------------------------------- base vectorial

def construir_base(
    fragmentos: list[Document],
    embeddings: Embeddings,
    destino: Path = CHROMA_DIR,
    coleccion: str = COLECCION,
) -> Chroma:
    """Borra la colección (si existe) y la vuelve a crear con los fragmentos."""
    cliente = chromadb.PersistentClient(
        path=str(destino),
        settings=chromadb.config.Settings(anonymized_telemetry=False),
    )
    if coleccion in [c.name for c in cliente.list_collections()]:
        cliente.delete_collection(coleccion)

    base = Chroma(
        client=cliente,
        collection_name=coleccion,
        embedding_function=embeddings,
        collection_metadata=METADATA_COLECCION,
    )
    ids = [f"{f.metadata['fuente']}#p{f.metadata['pagina']}#f{f.metadata['fragmento']}" for f in fragmentos]
    if fragmentos:
        base.add_documents(fragmentos, ids=ids)
    return base


def verificar_clave() -> None:
    """Carga .env y falla con un mensaje claro si no hay OPENAI_API_KEY."""
    from dotenv import load_dotenv

    load_dotenv()
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("Falta OPENAI_API_KEY. Copia .env.example como .env y pega tu clave.")


def crear_embeddings() -> Embeddings:
    """Embeddings de OpenAI. Necesita OPENAI_API_KEY en .env."""
    from langchain_openai import OpenAIEmbeddings

    verificar_clave()
    return OpenAIEmbeddings(model=MODELO_EMBEDDINGS)


# ------------------------------------------------------------------ main

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Carga los documentos del negocio en ChromaDB.")
    parser.add_argument("--docs", type=Path, default=DOCS_DIR, help="carpeta de documentos (por defecto: docs)")
    parser.add_argument("--destino", type=Path, default=CHROMA_DIR, help="carpeta de ChromaDB (por defecto: chroma_db)")
    parser.add_argument("--chunk-size", type=int, default=CHUNK_SIZE)
    parser.add_argument("--overlap", type=int, default=CHUNK_OVERLAP)
    args = parser.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")  # tildes correctas también en Git Bash

    print(f"Leyendo documentos de {args.docs.as_posix()}/")
    try:
        documentos = cargar_documentos(args.docs)
    except FileNotFoundError as error:
        print(f"ERROR: {error}")
        return 1
    if not documentos:
        print("ERROR: no se encontró texto. Agrega PDF, Word, TXT o Markdown a la carpeta.")
        return 1

    fragmentos = trocear(documentos, args.chunk_size, args.overlap)
    fuentes = sorted({d.metadata["fuente"] for d in documentos})
    caracteres = sum(len(f.page_content) for f in fragmentos)
    print(f"  {len(fuentes)} archivos, {len(documentos)} páginas, {len(fragmentos)} fragmentos")

    try:
        embeddings = crear_embeddings()
    except RuntimeError as error:
        print(f"ERROR: {error}")
        return 1

    construir_base(fragmentos, embeddings, args.destino)
    # Aproximación: 1 token ≈ 4 caracteres; text-embedding-3-small cuesta $0.02 por 1M tokens.
    costo = caracteres / 4 / 1_000_000 * 0.02
    print(f"Base guardada en {args.destino.as_posix()}/ (colección '{COLECCION}'). Costo aprox.: ${costo:.4f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
