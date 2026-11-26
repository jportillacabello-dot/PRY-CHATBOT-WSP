"""Cadena RAG: pregunta -> fragmentos de ChromaDB -> gpt-5-mini -> respuesta.

Capa de lógica: no importa FastAPI ni Twilio. app.py solo usa responder().

Uso en consola:
    python src/rag.py "¿A qué hora abren?"
    python src/rag.py                                      # modo conversación
    python src/rag.py --csv ejemplo/preguntas_prueba.csv   # responde todas las preguntas

Pasos:
    1. Abrir base y modelo   ChromaDB (creada por ingesta.py) y gpt-5-mini
    2. Buscar                los K fragmentos más parecidos a la pregunta
    3. Armar el prompt       reglas (prompt.txt) + fragmentos + pregunta
    4. Responder             umbral de relevancia y, si pasa, llamada al LLM
"""

from __future__ import annotations

import argparse
import csv
import sys
import time
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

import chromadb
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage

import ingesta


# =====================================================================
# == CONFIGURACIÓN: modelo, búsqueda, umbral y mensajes fijos ==
# =====================================================================

MODELO_LLM = "gpt-5-mini"
K = 4  # fragmentos que se buscan por pregunta
# Distancia coseno máxima para considerar un fragmento relevante. Calibrar con
# probar_busqueda.py sobre los documentos y preguntas reales.
UMBRAL_DISTANCIA = 0.75
TIMEOUT_LLM = 10  # segundos; Twilio corta el webhook a los 15
MAX_TOKENS = 600
PROMPT_PATH = Path(__file__).with_name("prompt.txt")

MENSAJE_SIN_INFO = "Lo siento, no tengo esa información."
MENSAJE_VACIO = "¡Hola! Escríbeme tu consulta y te ayudo."


@dataclass
class Respuesta:
    """Resultado completo de una consulta (para evaluar y depurar)."""

    texto: str
    fuentes: list[str] = field(default_factory=list)
    distancias: list[float] = field(default_factory=list)
    uso_llm: bool = False


# =====================================================================
# == PASO 1: Abrir la base y el modelo — una sola vez por proceso ==
# =====================================================================

def abrir_base(destino: Path = ingesta.CHROMA_DIR, embeddings: Embeddings | None = None) -> Chroma:
    """Abre la base que creó ingesta.py."""
    destino = Path(destino)
    if not (destino / "chroma.sqlite3").exists():
        raise FileNotFoundError(f"No existe la base en {ingesta.mostrar(destino)}/. Corre primero: python src/ingesta.py")
    cliente = chromadb.PersistentClient(
        path=str(destino),
        settings=chromadb.config.Settings(anonymized_telemetry=False),
    )
    return Chroma(
        client=cliente,
        collection_name=ingesta.COLECCION,
        embedding_function=embeddings or ingesta.crear_embeddings(),
    )


def crear_llm() -> BaseChatModel:
    """gpt-5-mini con razonamiento mínimo para responder rápido."""
    from langchain_openai import ChatOpenAI

    ingesta.verificar_clave()
    return ChatOpenAI(
        model=MODELO_LLM,
        reasoning_effort="minimal",
        max_tokens=MAX_TOKENS,
        timeout=TIMEOUT_LLM,
        max_retries=1,
    )


# lru_cache: la base y el modelo se crean en la primera pregunta y se reutilizan.
@lru_cache(maxsize=1)
def _base_por_defecto() -> Chroma:
    return abrir_base()


@lru_cache(maxsize=1)
def _llm_por_defecto() -> BaseChatModel:
    return crear_llm()


# =====================================================================
# == PASO 2: Buscar — los fragmentos más parecidos a la pregunta ==
# =====================================================================

def buscar(pregunta: str, base: Chroma, k: int = K) -> list[tuple[Document, float]]:
    """Los k fragmentos más parecidos con su distancia coseno (menor = más parecido)."""
    return base.similarity_search_with_score(pregunta, k=k)


# =====================================================================
# == PASO 3: Armar el prompt — reglas + fragmentos + pregunta ==
# =====================================================================

def cargar_prompt(ruta: Path = PROMPT_PATH) -> str:
    """Reglas del bot. {sin_info} se reemplaza por MENSAJE_SIN_INFO."""
    return Path(ruta).read_text(encoding="utf-8").replace("{sin_info}", MENSAJE_SIN_INFO)


def armar_contexto(documentos: list[Document]) -> str:
    """Une los fragmentos, cada uno con el nombre de su archivo entre corchetes."""
    return "\n\n".join(f"[{d.metadata.get('fuente', '?')}]\n{d.page_content}" for d in documentos)


def armar_mensajes(pregunta: str, documentos: list[Document]) -> list[BaseMessage]:
    """Mensaje de sistema (reglas) + mensaje del cliente (contexto y pregunta)."""
    return [
        SystemMessage(cargar_prompt()),
        HumanMessage(f"CONTEXTO:\n{armar_contexto(documentos)}\n\nPREGUNTA DEL CLIENTE:\n{pregunta}"),
    ]


# =====================================================================
# == PASO 4: Responder — umbral de relevancia y llamada al LLM ==
# =====================================================================

def _texto(mensaje: BaseMessage) -> str:
    """Extrae el texto de la respuesta del LLM (puede venir como texto o por bloques)."""
    contenido = mensaje.content
    if isinstance(contenido, str):
        return contenido.strip()
    partes = [b.get("text", "") if isinstance(b, dict) else str(b) for b in contenido]
    return "".join(partes).strip()


def responder_con_detalle(
    pregunta: str,
    *,
    base: Chroma | None = None,
    llm: BaseChatModel | None = None,
    k: int = K,
    umbral: float = UMBRAL_DISTANCIA,
) -> Respuesta:
    """Responde y devuelve también las fuentes y distancias (para evaluar)."""
    # 4.1 Pregunta vacía: saludo, sin buscar ni gastar
    pregunta = (pregunta or "").strip()
    if not pregunta:
        return Respuesta(MENSAJE_VACIO)

    # 4.2 Buscar fragmentos (PASO 2)
    resultados = buscar(pregunta, base or _base_por_defecto(), k)
    distancias = [round(d, 3) for _, d in resultados]

    # 4.3 Guardrail: quedarse solo con los relevantes; si no hay, no se llama al LLM
    relevantes = [doc for doc, distancia in resultados if distancia <= umbral]
    if not relevantes:
        return Respuesta(MENSAJE_SIN_INFO, distancias=distancias)

    # 4.4 Llamar al LLM con el prompt armado (PASO 3)
    salida = (llm or _llm_por_defecto()).invoke(armar_mensajes(pregunta, relevantes))
    texto = _texto(salida) or MENSAJE_SIN_INFO
    fuentes = list(dict.fromkeys(d.metadata.get("fuente", "?") for d in relevantes))
    return Respuesta(texto, fuentes=fuentes, distancias=distancias, uso_llm=True)


# =====================================================================
# == CONTRATO CON app.py: la única función que usa la capa de entrada ==
# =====================================================================

def responder(pregunta: str) -> str:
    """Contrato con app.py: recibe el texto del cliente y devuelve la respuesta.

    Puede lanzar excepciones (OpenAI caído, timeout, base inexistente):
    app.py las captura y envía el mensaje de respaldo.
    """
    return responder_con_detalle(pregunta).texto


# =====================================================================
# == EJECUCIÓN: probar la cadena desde la consola ==
# =====================================================================

def _imprimir(pregunta: str, r: Respuesta, segundos: float, esperada: str | None = None) -> None:
    print(f"\nP: {pregunta}")
    if esperada is not None:
        print(f"Esperada: {esperada or '(no está en los documentos)'}")
    print(f"R: {r.texto}")
    llm = "sí" if r.uso_llm else "no (umbral)"
    print(f"   fuentes={r.fuentes} distancias={r.distancias} llm={llm} tiempo={segundos:.1f}s")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Prueba la cadena RAG en consola.")
    parser.add_argument("pregunta", nargs="?", help="pregunta a responder (sin ella, modo conversación)")
    parser.add_argument("--csv", type=Path, help="CSV con columnas pregunta y respuesta_esperada")
    parser.add_argument("--k", type=int, default=K)
    parser.add_argument("--umbral", type=float, default=UMBRAL_DISTANCIA)
    args = parser.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    def correr(pregunta: str, esperada: str | None = None) -> float:
        inicio = time.perf_counter()
        r = responder_con_detalle(pregunta, k=args.k, umbral=args.umbral)
        segundos = time.perf_counter() - inicio
        _imprimir(pregunta, r, segundos, esperada)
        return segundos

    try:
        # Modo 1: todas las preguntas de un CSV
        if args.csv:
            with open(args.csv, encoding="utf-8", newline="") as archivo:
                filas = [f for f in csv.DictReader(archivo) if f.get("pregunta", "").strip()]
            tiempos = [correr(f["pregunta"], f.get("respuesta_esperada", "")) for f in filas]
            if tiempos:
                print(f"\n{len(tiempos)} preguntas · tiempo promedio {sum(tiempos) / len(tiempos):.1f}s · máximo {max(tiempos):.1f}s")
                print("Marca cada respuesta como correcta o incorrecta (meta: ≥ 18/20).")
        # Modo 2: una sola pregunta
        elif args.pregunta:
            correr(args.pregunta)
        # Modo 3: conversación hasta Enter vacío
        else:
            print("Escribe una pregunta (Enter vacío para salir).")
            while pregunta := input("\n> ").strip():
                correr(pregunta)
    except (FileNotFoundError, RuntimeError) as error:
        print(f"ERROR: {error}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
