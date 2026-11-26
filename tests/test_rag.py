"""Tests de rag.py y probar_busqueda.py con embeddings y LLM falsos (sin costo)."""

from pathlib import Path

import pytest
from langchain_core.embeddings import DeterministicFakeEmbedding
from langchain_core.language_models.fake_chat_models import FakeListChatModel

import ingesta
import probar_busqueda
import rag

RAIZ = Path(__file__).resolve().parent.parent
EJEMPLO = RAIZ / "ejemplo"


class LLMEspia(FakeListChatModel):
    """LLM falso que guarda los mensajes que recibe."""

    recibido: list = []

    def invoke(self, mensajes, *args, **kwargs):
        self.recibido.append(mensajes)
        return super().invoke(mensajes, *args, **kwargs)


@pytest.fixture
def base(tmp_path):
    embeddings = DeterministicFakeEmbedding(size=64)
    fragmentos = ingesta.trocear(ingesta.cargar_documentos(EJEMPLO / "docs"))
    ingesta.construir_base(fragmentos, embeddings, tmp_path / "db")
    return rag.abrir_base(tmp_path / "db", embeddings)


@pytest.fixture
def llm():
    espia = LLMEspia(responses=["Abrimos de 9 a 2 los domingos."])
    espia.recibido = []
    return espia


# ------------------------------------------------------------------- prompt

def test_prompt_reemplaza_el_mensaje_sin_info_y_tiene_las_reglas():
    prompt = rag.cargar_prompt()
    assert "{sin_info}" not in prompt
    assert rag.MENSAJE_SIN_INFO in prompt
    assert "CONTEXTO" in prompt and "instrucciones" in prompt


# ------------------------------------------------------------------ responder

def test_con_contexto_relevante_llama_al_llm_con_contexto_y_pregunta(base, llm):
    r = rag.responder_con_detalle("¿A qué hora abren los domingos?", base=base, llm=llm, umbral=2.0)
    assert r.uso_llm and r.texto == "Abrimos de 9 a 2 los domingos."
    assert r.fuentes and len(r.distancias) == rag.K
    sistema, humano = llm.recibido[0]
    assert "Reglas" in sistema.content
    assert "CONTEXTO:" in humano.content and "¿A qué hora abren los domingos?" in humano.content


def test_sin_contexto_relevante_no_llama_al_llm(base, llm):
    r = rag.responder_con_detalle("¿Quién ganó el mundial?", base=base, llm=llm, umbral=0.0)
    assert r.texto == rag.MENSAJE_SIN_INFO
    assert not r.uso_llm and llm.recibido == []


def test_pregunta_vacia_no_busca_ni_llama_al_llm(llm):
    assert rag.responder_con_detalle("   ", base=None, llm=llm).texto == rag.MENSAJE_VACIO
    assert llm.recibido == []


def test_respuesta_vacia_del_llm_se_convierte_en_sin_info(base):
    r = rag.responder_con_detalle("hola", base=base, llm=FakeListChatModel(responses=[""]), umbral=2.0)
    assert r.texto == rag.MENSAJE_SIN_INFO


def test_abrir_base_inexistente_da_error_claro(tmp_path):
    with pytest.raises(FileNotFoundError, match="python src/ingesta.py"):
        rag.abrir_base(tmp_path / "no-existe", DeterministicFakeEmbedding(size=8))


# ------------------------------------------------------------ probar_busqueda

def _resultado(distancia, esperada="faq.md", fuentes=("faq.md",)):
    return probar_busqueda.Resultado("p", esperada, list(fuentes), distancia)


def test_umbral_separable_usa_el_punto_medio():
    resultados = [_resultado(0.4), _resultado(0.6), _resultado(0.9, esperada="")]
    assert probar_busqueda.sugerir_umbral(resultados) == (0.75, True)


def test_umbral_no_separable_no_descarta_preguntas_validas():
    resultados = [_resultado(0.4), _resultado(0.64), _resultado(0.55, esperada="")]
    umbral, separa = probar_busqueda.sugerir_umbral(resultados)
    assert umbral == 0.69 and not separa


def test_evaluar_marca_aciertos_con_las_preguntas_de_ejemplo(base):
    filas = probar_busqueda.leer_preguntas(EJEMPLO / "preguntas_prueba.csv")
    assert len(filas) == 20
    resultados = probar_busqueda.evaluar(filas, base, k=5)  # k = todos los fragmentos
    con_respuesta = [r for r in resultados if r.tiene_respuesta]
    assert len(con_respuesta) == 18 and all(r.acierto for r in con_respuesta)


def test_csv_sin_columna_fuente_esperada_da_error(tmp_path):
    ruta = tmp_path / "p.csv"
    ruta.write_text("pregunta,respuesta_esperada\n¿Hola?,Hola\n", encoding="utf-8")
    with pytest.raises(ValueError, match="fuente_esperada"):
        probar_busqueda.leer_preguntas(ruta)
