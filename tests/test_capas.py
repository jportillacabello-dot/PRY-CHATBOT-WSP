"""Reglas de dependencias (instrucciones/estructura-proyecto-rag.md, sección 3)."""

import ast
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
SRC = RAIZ / "src"

CANAL = {"fastapi", "twilio", "flask"}          # librerías que solo puede usar api/
PASOS = ["ingestion", "chunking", "embeddings", "vectordb", "retrieval", "prompts", "llm"]
ARRIBA = {"src.pipeline", "src.evaluation", "src.api"}


def _imports(archivo: Path) -> set[str]:
    """Módulos importados por un archivo, con su ruta completa (p. ej. 'src.utils.config')."""
    modulos = set()
    for nodo in ast.walk(ast.parse(archivo.read_text(encoding="utf-8"))):
        if isinstance(nodo, ast.Import):
            modulos |= {a.name for a in nodo.names}
        elif isinstance(nodo, ast.ImportFrom) and nodo.module:
            modulos.add(nodo.module)
    return modulos


def _archivos(carpeta: str) -> list[Path]:
    return sorted((SRC / carpeta).glob("*.py"))


def _raices(modulos: set[str]) -> set[str]:
    return {m.split(".")[0] for m in modulos}


@pytest.mark.parametrize("carpeta", PASOS + ["pipeline", "evaluation", "utils"])
def test_solo_api_usa_librerias_del_canal(carpeta):
    for archivo in _archivos(carpeta):
        assert not _raices(_imports(archivo)) & CANAL, archivo.name


@pytest.mark.parametrize("carpeta", PASOS + ["pipeline", "evaluation", "utils"])
def test_nadie_importa_api(carpeta):
    for archivo in _archivos(carpeta):
        assert not any(m.startswith("src.api") for m in _imports(archivo)), archivo.name


@pytest.mark.parametrize("carpeta", PASOS)
def test_los_pasos_no_importan_capas_de_arriba(carpeta):
    for archivo in _archivos(carpeta):
        assert not any(m.startswith(tuple(ARRIBA)) for m in _imports(archivo)), archivo.name


def test_utils_no_importa_otras_carpetas():
    for archivo in _archivos("utils"):
        otras = {m for m in _imports(archivo) if m.startswith("src.") and not m.startswith("src.utils")}
        assert not otras, archivo.name


def test_todas_las_carpetas_son_paquetes():
    for carpeta in PASOS + ["pipeline", "evaluation", "api", "utils"]:
        assert (SRC / carpeta / "__init__.py").exists(), carpeta
