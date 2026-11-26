"""Punto de entrada del chatbot RAG. Se corre siempre desde la raíz del proyecto.

Uso:
    python main.py ingestar                              # docs/ -> chroma_db/
    python main.py ingestar --docs ejemplo/docs          # con el negocio de ejemplo
    python main.py probar-busqueda                       # data/preguntas_prueba.csv
    python main.py probar-busqueda --preguntas ejemplo/preguntas_prueba.csv
    python main.py preguntar "¿A qué hora abren?"        # una pregunta
    python main.py preguntar                             # conversación
    python main.py preguntar --csv ejemplo/preguntas_prueba.csv

Servidor (Fase 3): uvicorn src.api.routes:app

Solo lee argumentos, llama al pipeline o a la evaluación e imprime.
"""

from __future__ import annotations

import argparse
import csv
import sys
import time
from pathlib import Path

from src.utils.helpers import consola_utf8, mostrar


# =====================================================================
# == COMANDO 1: ingestar — documentos a la base vectorial ==
# =====================================================================

def cmd_ingestar(args: argparse.Namespace) -> int:
    from src.pipeline.ingest_pipeline import guardar, preparar

    # 1.1 Cargar, limpiar y trocear (sin costo)
    print(f"Leyendo documentos de {mostrar(args.docs)}/")
    try:
        preparado = preparar(args.docs, args.chunk_size, args.overlap)
    except (FileNotFoundError, ValueError) as error:
        print(f"ERROR: {error}")
        return 1
    print(f"  {preparado.archivos} archivos, {len(preparado.documentos)} páginas, {len(preparado.fragmentos)} fragmentos")

    # 1.2 Embeddings y guardado en ChromaDB (llama a OpenAI)
    try:
        guardar(preparado, args.destino)
    except RuntimeError as error:
        print(f"ERROR: {error}")
        return 1
    print(f"Base guardada en {mostrar(args.destino)}/. Costo aprox.: ${preparado.costo_aprox:.4f}")
    return 0


# =====================================================================
# == COMANDO 2: probar-busqueda — medir la búsqueda sin LLM ==
# =====================================================================

def cmd_probar_busqueda(args: argparse.Namespace) -> int:
    from src.evaluation.search_eval import evaluar, imprimir_informe, leer_preguntas
    from src.vectordb.vector_store import abrir_base

    try:
        # 2.1 Leer las preguntas
        filas = leer_preguntas(args.preguntas)
        if not filas:
            print(f"ERROR: {mostrar(args.preguntas)} no tiene preguntas. Complétalo o usa --preguntas ejemplo/preguntas_prueba.csv")
            return 1
        # 2.2 Buscar cada pregunta
        resultados = evaluar(filas, abrir_base(), args.k)
    except (FileNotFoundError, ValueError, RuntimeError) as error:
        print(f"ERROR: {error}")
        return 1
    # 2.3 Informe (código de salida 1 si no se cumple la meta)
    return 0 if imprimir_informe(resultados, args.k) else 1


# =====================================================================
# == COMANDO 3: preguntar — probar el bot completo en consola ==
# =====================================================================

def cmd_preguntar(args: argparse.Namespace) -> int:
    from src.pipeline.rag_pipeline import responder_con_detalle

    def correr(pregunta: str, esperada: str | None = None) -> float:
        inicio = time.perf_counter()
        r = responder_con_detalle(pregunta, k=args.k, umbral=args.umbral)
        segundos = time.perf_counter() - inicio
        print(f"\nP: {pregunta}")
        if esperada is not None:
            print(f"Esperada: {esperada or '(no está en los documentos)'}")
        print(f"R: {r.texto}")
        llm = "sí" if r.uso_llm else "no (umbral)"
        print(f"   fuentes={r.fuentes} distancias={r.distancias} llm={llm} tiempo={segundos:.1f}s")
        return segundos

    try:
        # 3.1 Todas las preguntas de un CSV
        if args.csv:
            with open(args.csv, encoding="utf-8", newline="") as archivo:
                filas = [f for f in csv.DictReader(archivo) if f.get("pregunta", "").strip()]
            tiempos = [correr(f["pregunta"], f.get("respuesta_esperada", "")) for f in filas]
            if tiempos:
                print(f"\n{len(tiempos)} preguntas · tiempo promedio {sum(tiempos) / len(tiempos):.1f}s · máximo {max(tiempos):.1f}s")
                print("Marca cada respuesta como correcta o incorrecta (meta: ≥ 18/20).")
        # 3.2 Una sola pregunta
        elif args.pregunta:
            correr(args.pregunta)
        # 3.3 Conversación hasta Enter vacío
        else:
            print("Escribe una pregunta (Enter vacío para salir).")
            while pregunta := input("\n> ").strip():
                correr(pregunta)
    except (FileNotFoundError, RuntimeError) as error:
        print(f"ERROR: {error}")
        return 1
    return 0


# =====================================================================
# == EJECUCIÓN: leer el subcomando y despachar ==
# =====================================================================

def crear_parser() -> argparse.ArgumentParser:
    from src.chunking.chunker import CHUNK_OVERLAP, CHUNK_SIZE
    from src.retrieval.retriever import K, UMBRAL_DISTANCIA
    from src.utils.config import ruta

    parser = argparse.ArgumentParser(description="Chatbot RAG en WhatsApp.")
    sub = parser.add_subparsers(dest="comando", required=True)

    p = sub.add_parser("ingestar", help="carga los documentos en ChromaDB")
    p.add_argument("--docs", type=Path, default=ruta("docs"), help="carpeta de documentos (por defecto: docs)")
    p.add_argument("--destino", type=Path, default=ruta("chroma"), help="carpeta de ChromaDB (por defecto: chroma_db)")
    p.add_argument("--chunk-size", type=int, default=CHUNK_SIZE)
    p.add_argument("--overlap", type=int, default=CHUNK_OVERLAP)
    p.set_defaults(funcion=cmd_ingestar)

    p = sub.add_parser("probar-busqueda", help="mide si la búsqueda trae el fragmento correcto")
    p.add_argument("--preguntas", type=Path, default=ruta("preguntas"))
    p.add_argument("--k", type=int, default=K)
    p.set_defaults(funcion=cmd_probar_busqueda)

    p = sub.add_parser("preguntar", help="responde en consola (una pregunta, conversación o CSV)")
    p.add_argument("pregunta", nargs="?", help="pregunta a responder (sin ella, modo conversación)")
    p.add_argument("--csv", type=Path, help="CSV con columnas pregunta y respuesta_esperada")
    p.add_argument("--k", type=int, default=K)
    p.add_argument("--umbral", type=float, default=UMBRAL_DISTANCIA)
    p.set_defaults(funcion=cmd_preguntar)
    return parser


def main(argv: list[str] | None = None) -> int:
    consola_utf8()
    args = crear_parser().parse_args(argv)
    return args.funcion(args)


if __name__ == "__main__":
    sys.exit(main())
