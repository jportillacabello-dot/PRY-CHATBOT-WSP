"""Tests de la ingesta (ingestion, chunking, vectordb, pipeline de ingesta).

Usan embeddings falsos: no llaman a OpenAI ni cuestan nada.
"""

import zipfile
from pathlib import Path

import pytest
from langchain_core.embeddings import DeterministicFakeEmbedding

import main
from src.chunking.chunker import trocear
from src.ingestion.loader import cargar_documentos, limpiar_paginas
from src.pipeline.ingest_pipeline import ingestar
from src.vectordb.vector_store import construir_base

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
    assert limpiar_paginas(paginas) == [f"Contenido de la página {n}" for n in range(1, 5)]


def test_limpieza_no_toca_documentos_cortos():
    # Con menos de 3 páginas no se puede saber qué es encabezado.
    assert limpiar_paginas(["Título\nTexto  con   espacios"]) == ["Título\nTexto con espacios"]


# ------------------------------------------------------------------ carga

def test_carga_los_documentos_de_ejemplo():
    documentos = cargar_documentos(EJEMPLO)
    assert {d.metadata["fuente"] for d in documentos} == {"faq.md", "politicas.txt", "carta.pdf"}
    carta = next(d for d in documentos if d.metadata["fuente"] == "carta.pdf")
    assert "Capuchino" in carta.page_content
    assert carta.metadata["pagina"] == 1


def test_carga_docx_e_ignora_formatos_no_soportados(tmp_path):
    _crear_docx(tmp_path / "horarios.docx", "Abrimos a las 8")
    (tmp_path / "precios.xlsx").write_bytes(b"no soportado")
    (tmp_path / ".gitkeep").write_text("")
    documentos = cargar_documentos(tmp_path)
    assert [d.metadata["fuente"] for d in documentos] == ["horarios.docx"]
    assert "Abrimos a las 8" in documentos[0].page_content


def test_carpeta_inexistente_da_error_claro(tmp_path):
    with pytest.raises(FileNotFoundError):
        cargar_documentos(tmp_path / "no-existe")


# --------------------------------------------------------------- troceado

def test_trocear_respeta_el_tamano_y_numera_fragmentos():
    fragmentos = trocear(cargar_documentos(EJEMPLO), chunk_size=300, chunk_overlap=30)
    assert all(len(f.page_content) <= 300 for f in fragmentos)
    faq = [f.metadata["fragmento"] for f in fragmentos if f.metadata["fuente"] == "faq.md"]
    assert faq == list(range(len(faq))) and len(faq) > 1


# ---------------------------------------------------------- base vectorial

def test_construir_base_es_idempotente(tmp_path, embeddings):
    fragmentos = trocear(cargar_documentos(EJEMPLO))
    destino = tmp_path / "chroma_db"

    construir_base(fragmentos, embeddings, destino)
    base = construir_base(fragmentos, embeddings, destino)  # segunda corrida

    assert base._collection.count() == len(fragmentos)  # sin duplicados
    assert base._collection.metadata["hnsw:space"] == "cosine"
    resultado = base.similarity_search("horario", k=2)
    assert len(resultado) == 2 and "fuente" in resultado[0].metadata


def test_pipeline_de_ingesta_completo(tmp_path, embeddings):
    preparado = ingestar(EJEMPLO, tmp_path / "db", embeddings=embeddings)
    assert preparado.archivos == 3 and preparado.fragmentos
    assert (tmp_path / "db" / "chroma.sqlite3").exists()


def test_main_ingestar_sin_api_key_falla_con_mensaje(monkeypatch, tmp_path, capsys):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr("dotenv.load_dotenv", lambda *a, **k: False)
    codigo = main.main(["ingestar", "--docs", str(EJEMPLO), "--destino", str(tmp_path / "db")])
    assert codigo == 1
    assert "OPENAI_API_KEY" in capsys.readouterr().out
