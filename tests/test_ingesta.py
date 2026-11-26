"""Tests de ingesta.py. Usan embeddings falsos: no llaman a OpenAI ni cuestan nada."""

import ast
import zipfile
from pathlib import Path

import pytest
from langchain_core.embeddings import DeterministicFakeEmbedding

import ingesta

RAIZ = Path(__file__).resolve().parent.parent
EJEMPLO = RAIZ / "ejemplo" / "docs"


@pytest.fixture
def embeddings():
    return DeterministicFakeEmbedding(size=64)


def _crear_docx(ruta: Path, texto: str) -> None:
    """Crea un .docx mínimo (solo word/document.xml) sin depender de python-docx."""
    xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        f"<w:body><w:p><w:r><w:t>{texto}</w:t></w:r></w:p></w:body></w:document>"
    )
    with zipfile.ZipFile(ruta, "w") as z:
        z.writestr("word/document.xml", xml)


# --------------------------------------------------------------- limpieza

def test_limpieza_quita_encabezados_pies_y_numeros_de_pagina():
    paginas = [
        f"PASTELERÍA DULCE AROMA\nContenido de la página {n}\nPágina {n} de 4"
        for n in range(1, 5)
    ]
    limpias = ingesta.limpiar_paginas(paginas)
    assert limpias == [f"Contenido de la página {n}" for n in range(1, 5)]


def test_limpieza_no_toca_documentos_cortos():
    # Con menos de 3 páginas no se puede saber qué es encabezado.
    assert ingesta.limpiar_paginas(["Título\nTexto  con   espacios"]) == ["Título\nTexto con espacios"]


# ------------------------------------------------------------------ carga

def test_carga_los_documentos_de_ejemplo():
    documentos = ingesta.cargar_documentos(EJEMPLO)
    fuentes = {d.metadata["fuente"] for d in documentos}
    assert fuentes == {"faq.md", "politicas.txt", "carta.pdf"}
    carta = next(d for d in documentos if d.metadata["fuente"] == "carta.pdf")
    assert "Capuchino" in carta.page_content
    assert carta.metadata["pagina"] == 1


def test_carga_docx_e_ignora_formatos_no_soportados(tmp_path):
    _crear_docx(tmp_path / "horarios.docx", "Abrimos a las 8")
    (tmp_path / "precios.xlsx").write_bytes(b"no soportado")
    (tmp_path / ".gitkeep").write_text("")
    documentos = ingesta.cargar_documentos(tmp_path)
    assert [d.metadata["fuente"] for d in documentos] == ["horarios.docx"]
    assert "Abrimos a las 8" in documentos[0].page_content


def test_carpeta_inexistente_da_error_claro(tmp_path):
    with pytest.raises(FileNotFoundError):
        ingesta.cargar_documentos(tmp_path / "no-existe")


# --------------------------------------------------------------- troceado

def test_trocear_respeta_el_tamano_y_numera_fragmentos():
    documentos = ingesta.cargar_documentos(EJEMPLO)
    fragmentos = ingesta.trocear(documentos, chunk_size=300, chunk_overlap=30)
    assert all(len(f.page_content) <= 300 for f in fragmentos)
    faq = [f.metadata["fragmento"] for f in fragmentos if f.metadata["fuente"] == "faq.md"]
    assert faq == list(range(len(faq))) and len(faq) > 1


# ---------------------------------------------------------- base vectorial

def test_construir_base_es_idempotente(tmp_path, embeddings):
    fragmentos = ingesta.trocear(ingesta.cargar_documentos(EJEMPLO))
    destino = tmp_path / "chroma_db"

    ingesta.construir_base(fragmentos, embeddings, destino)
    base = ingesta.construir_base(fragmentos, embeddings, destino)  # segunda corrida

    assert base._collection.count() == len(fragmentos)  # sin duplicados
    assert base._collection.metadata["hnsw:space"] == "cosine"
    resultado = base.similarity_search("horario", k=2)
    assert len(resultado) == 2 and "fuente" in resultado[0].metadata


def test_main_sin_api_key_falla_con_mensaje(monkeypatch, tmp_path, capsys):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr("dotenv.load_dotenv", lambda *a, **k: False)
    codigo = ingesta.main(["--docs", str(EJEMPLO), "--destino", str(tmp_path / "db")])
    assert codigo == 1
    assert "OPENAI_API_KEY" in capsys.readouterr().out


# ------------------------------------------------------------------ capas

def test_ingesta_no_importa_la_capa_de_entrada():
    arbol = ast.parse((RAIZ / "ingesta.py").read_text(encoding="utf-8"))
    modulos = set()
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            modulos |= {a.name.split(".")[0] for a in nodo.names}
        elif isinstance(nodo, ast.ImportFrom) and nodo.module:
            modulos.add(nodo.module.split(".")[0])
    assert not modulos & {"fastapi", "twilio", "app"}
