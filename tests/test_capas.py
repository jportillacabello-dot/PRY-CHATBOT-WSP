"""Regla de capas (CLAUDE.md): la lógica y los datos no importan la capa de entrada."""

import ast
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
CAPA_ENTRADA = {"fastapi", "twilio", "app"}


def _modulos_importados(archivo: Path) -> set[str]:
    arbol = ast.parse(archivo.read_text(encoding="utf-8"))
    modulos = set()
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            modulos |= {a.name.split(".")[0] for a in nodo.names}
        elif isinstance(nodo, ast.ImportFrom) and nodo.module:
            modulos.add(nodo.module.split(".")[0])
    return modulos


@pytest.mark.parametrize("archivo", ["ingesta.py", "rag.py", "probar_busqueda.py"])
def test_no_importa_la_capa_de_entrada(archivo):
    assert not _modulos_importados(RAIZ / archivo) & CAPA_ENTRADA


def test_ingesta_no_importa_la_logica():
    assert "rag" not in _modulos_importados(RAIZ / "ingesta.py")
