"""Tarea 1.3: ¿la búsqueda trae el fragmento correcto para cada pregunta de prueba?

No llama al LLM: solo mide la búsqueda en ChromaDB y sugiere un umbral de
relevancia para rag.py.

Uso:
    python src/probar_busqueda.py                                  # data/preguntas_prueba.csv
    python src/probar_busqueda.py --preguntas ejemplo/preguntas_prueba.csv --k 3

El CSV necesita las columnas `pregunta` y `fuente_esperada` (nombre del archivo
donde está la respuesta; vacía si la respuesta no está en los documentos).

Pasos:
    1. Leer preguntas      el CSV de prueba
    2. Buscar              los K fragmentos de cada pregunta y marcar aciertos
    3. Sugerir umbral      a partir de las distancias de ambos grupos
    4. Informe             tabla, % de aciertos y umbral sugerido
"""

from __future__ import annotations

import argparse
import csv
import sys
from dataclasses import dataclass
from pathlib import Path

from langchain_chroma import Chroma

import ingesta
import rag


# =====================================================================
# == CONFIGURACIÓN: archivo de preguntas, meta y margen del umbral ==
# =====================================================================

PREGUNTAS = ingesta.RAIZ / "data" / "preguntas_prueba.csv"
META_ACIERTO = 0.9  # 18 de 20
MARGEN_UMBRAL = 0.05


@dataclass
class Resultado:
    """Lo que trajo la búsqueda para una pregunta."""

    pregunta: str
    fuente_esperada: str  # "" = la respuesta no está en los documentos
    fuentes: list[str]
    distancia: float  # del fragmento más cercano

    @property
    def tiene_respuesta(self) -> bool:
        return bool(self.fuente_esperada)

    @property
    def acierto(self) -> bool:
        return self.fuente_esperada in self.fuentes


# =====================================================================
# == PASO 1: Leer preguntas — el CSV con la fuente esperada ==
# =====================================================================

def leer_preguntas(ruta: Path) -> list[dict]:
    with open(ruta, encoding="utf-8", newline="") as archivo:
        filas = [f for f in csv.DictReader(archivo) if (f.get("pregunta") or "").strip()]
    if filas and "fuente_esperada" not in filas[0]:
        raise ValueError(f"{ruta} no tiene la columna fuente_esperada")
    return filas


# =====================================================================
# == PASO 2: Buscar — los K fragmentos de cada pregunta ==
# =====================================================================

def evaluar(filas: list[dict], base: Chroma, k: int = rag.K) -> list[Resultado]:
    resultados = []
    for fila in filas:
        encontrados = rag.buscar(fila["pregunta"], base, k)  # misma búsqueda que usa el bot
        resultados.append(
            Resultado(
                pregunta=fila["pregunta"].strip(),
                fuente_esperada=(fila.get("fuente_esperada") or "").strip(),
                fuentes=[d.metadata.get("fuente", "?") for d, _ in encontrados],
                distancia=round(encontrados[0][1], 3) if encontrados else 2.0,
            )
        )
    return resultados


# =====================================================================
# == PASO 3: Sugerir umbral — separar preguntas con y sin respuesta ==
# =====================================================================

def sugerir_umbral(resultados: list[Resultado]) -> tuple[float | None, bool]:
    """Devuelve (umbral, separa_bien).

    El umbral no debe descartar ninguna pregunta válida. Si las preguntas sin
    respuesta quedan todas por encima de las válidas, se usa el punto medio
    entre ambos grupos; si no, el umbral solo puede ser la distancia válida
    máxima más un margen, y las preguntas sin respuesta que queden debajo
    tiene que cubrirlas el prompt.
    """
    validas = [r.distancia for r in resultados if r.tiene_respuesta]
    sin_respuesta = [r.distancia for r in resultados if not r.tiene_respuesta]
    if not validas:
        return None, False
    # Caso 1: los grupos no se tocan -> punto medio
    if sin_respuesta and min(sin_respuesta) > max(validas):
        return round((max(validas) + min(sin_respuesta)) / 2, 2), True
    # Caso 2: se mezclan -> no perder ninguna válida
    return round(max(validas) + MARGEN_UMBRAL, 2), False


# =====================================================================
# == PASO 4: Informe — tabla, % de aciertos y umbral sugerido ==
# =====================================================================

def imprimir_informe(resultados: list[Resultado], k: int) -> bool:
    """Imprime la tabla y el resumen. Devuelve True si se cumple la meta."""
    # 4.1 Una línea por pregunta: OK, NO o -- (sin respuesta esperada)
    for r in resultados:
        if r.tiene_respuesta:
            marca = "OK" if r.acierto else "NO"
        else:
            marca = "--"
        print(f"{marca}  dist={r.distancia:.3f}  top={r.fuentes[0] if r.fuentes else '-':<16} {r.pregunta}")

    # 4.2 Porcentaje de aciertos contra la meta
    con_respuesta = [r for r in resultados if r.tiene_respuesta]
    aciertos = sum(r.acierto for r in con_respuesta)
    tasa = aciertos / len(con_respuesta) if con_respuesta else 0.0
    cumple = tasa >= META_ACIERTO

    print(f"\nFuente correcta entre los {k} primeros: {aciertos}/{len(con_respuesta)} ({tasa:.0%}) · meta ≥ {META_ACIERTO:.0%}: {'cumple' if cumple else 'NO cumple'}")
    for r in con_respuesta:
        if not r.acierto:
            print(f"  Falla: «{r.pregunta}» esperaba {r.fuente_esperada}, trajo {r.fuentes}")

    # 4.3 Rangos de distancia de cada grupo
    validas = [r.distancia for r in con_respuesta]
    sin_respuesta = [r for r in resultados if not r.tiene_respuesta]
    if validas:
        print(f"Distancia del más cercano, preguntas con respuesta: {min(validas):.2f} – {max(validas):.2f}")
    if sin_respuesta:
        d = [r.distancia for r in sin_respuesta]
        print(f"Distancia del más cercano, preguntas sin respuesta: {min(d):.2f} – {max(d):.2f}")

    # 4.4 Umbral sugerido (PASO 3) y qué preguntas tendrá que cubrir el prompt
    umbral, separa = sugerir_umbral(resultados)
    if umbral is not None:
        print(f"Umbral sugerido para rag.py: {umbral} (actual: {rag.UMBRAL_DISTANCIA})")
        if not separa and sin_respuesta:
            debajo = [r.pregunta for r in sin_respuesta if r.distancia <= umbral]
            print(f"  El umbral no filtra {len(debajo)} pregunta(s) sin respuesta; las debe cubrir el prompt: {debajo}")
    return cumple


# =====================================================================
# == EJECUCIÓN: correr los pasos 1 a 4 desde la consola ==
# =====================================================================

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Mide si la búsqueda trae el fragmento correcto.")
    parser.add_argument("--preguntas", type=Path, default=PREGUNTAS)
    parser.add_argument("--k", type=int, default=rag.K)
    args = parser.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    try:
        # PASO 1: leer preguntas
        filas = leer_preguntas(args.preguntas)
        if not filas:
            print(f"ERROR: {ingesta.mostrar(args.preguntas)} no tiene preguntas. Complétalo o usa --preguntas ejemplo/preguntas_prueba.csv")
            return 1
        # PASO 2: buscar cada pregunta
        resultados = evaluar(filas, rag.abrir_base(), args.k)
    except (FileNotFoundError, ValueError, RuntimeError) as error:
        print(f"ERROR: {error}")
        return 1
    # PASOS 3 y 4: umbral e informe (código de salida 1 si no se cumple la meta)
    return 0 if imprimir_informe(resultados, args.k) else 1


if __name__ == "__main__":
    sys.exit(main())
