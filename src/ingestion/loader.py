"""Ingesta: leer los documentos del negocio y limpiar su texto.

Pasos:
    1. Leer archivos       PDF, Word, TXT y Markdown -> texto por página
    2. Limpiar texto       quitar encabezados, pies, números de página y espacios
    3. Cargar documentos   recorrer la carpeta y armar un Document por página
"""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

from langchain_core.documents import Document

from src.utils.config import CONFIG


# =====================================================================
# == CONFIGURACIÓN: formatos aceptados y patrón de números de página ==
# =====================================================================

EXTENSIONES = set(CONFIG["ingesta"]["extensiones"])

# Números de página sueltos: "3", "Página 3", "3 de 10", "3/10".
_NUMERO_PAGINA = re.compile(r"^(p[áa]g(ina)?\.?\s*)?\d+(\s*(de|/)\s*\d+)?$", re.IGNORECASE)


# =====================================================================
# == PASO 1: Leer archivos — sacar el texto de cada formato ==
# =====================================================================
# Cada lector devuelve una lista de textos: una entrada por página en los
# PDF y una sola entrada para los demás formatos.

def _leer_pdf(ruta: Path) -> list[str]:
    from pypdf import PdfReader

    return [pagina.extract_text() or "" for pagina in PdfReader(ruta).pages]


def _leer_docx(ruta: Path) -> list[str]:
    import docx2txt

    return [docx2txt.process(str(ruta)) or ""]


def _leer_texto(ruta: Path) -> list[str]:
    return [ruta.read_text(encoding="utf-8")]


_LECTORES = {".pdf": _leer_pdf, ".docx": _leer_docx, ".txt": _leer_texto, ".md": _leer_texto}


# =====================================================================
# == PASO 2: Limpiar texto — quitar ruido que confunde la búsqueda ==
# =====================================================================

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
    # 2.1 Detectar líneas repetidas en casi todas las páginas (encabezados y pies)
    repetidas: set[str] = set()
    if len(paginas) >= 3:
        conteo = Counter(
            linea.strip()
            for pagina in paginas
            for linea in set(pagina.splitlines())
            if linea.strip()
        )
        repetidas = {linea for linea, n in conteo.items() if n >= 0.6 * len(paginas)}

    # 2.2 Quitar esas líneas y los números de página, y normalizar espacios
    limpias = []
    for pagina in paginas:
        lineas = [
            linea
            for linea in pagina.splitlines()
            if linea.strip() not in repetidas and not _NUMERO_PAGINA.match(linea.strip())
        ]
        limpias.append(normalizar("\n".join(lineas)))
    return limpias


# =====================================================================
# == PASO 3: Cargar documentos — recorrer la carpeta y armar Documents ==
# =====================================================================

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
        # 3.1 Saltar ocultos (.gitkeep), temporales de Office (~$) y formatos no soportados
        if not ruta.is_file() or ruta.name.startswith((".", "~$")):
            continue
        extension = ruta.suffix.lower()
        if extension not in EXTENSIONES:
            print(f"  [omitido] {ruta.relative_to(carpeta)}: formato no soportado")
            continue

        # 3.2 Leer (PASO 1) y limpiar (PASO 2)
        paginas = limpiar_paginas(_LECTORES[extension](ruta))
        fuente = ruta.relative_to(carpeta).as_posix()
        if not any(paginas):
            print(f"  [aviso] {fuente}: no tiene texto (¿PDF escaneado?)")
            continue

        # 3.3 Un Document por página, con su origen en la metadata
        for numero, texto in enumerate(paginas, start=1):
            if texto:
                documentos.append(Document(page_content=texto, metadata={"fuente": fuente, "pagina": numero}))
    return documentos
