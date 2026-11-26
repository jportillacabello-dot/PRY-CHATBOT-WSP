# Guía de formato: diagramas de arquitectura IA (proyectos personales)

> Para proyectos propios, sin marca institucional. **Usar junto con [plantilla.html](plantilla.html)**: adjuntar ambos al LLM y pedirle que cambie solo el contenido.

## 1. Estructura de la página
1. **Cabecera:** nombre del proyecto + una línea de qué hace. Sin logos.
2. **Leyenda:** solo los tipos de elemento usados.
3. **Diagrama:** un solo SVG escrito directamente en el HTML (sin librerías).
4. **Notas (opcional):** 3–6 tarjetas con decisiones clave o dudas abiertas.

## 2. Zonas del diagrama
| Zona | Qué va |
|---|---|
| **Arriba** | Entrada: usuario, archivo, API o evento |
| **Centro** | Pasos del pipeline en orden vertical |
| **Izquierda** | Modelos de IA (LLM, embeddings, reranker) |
| **Derecha** | Datos: índices, memoria, archivos |
| **Abajo** | Salida + monitoreo/evaluación |

Gateway, red team o decisiones humanas solo si el proyecto los tiene. Si una zona no aplica, se omite.

## 3. Paleta neutra (tinta + verde azulado)
| Rol | Claro | Oscuro |
|---|---|---|
| Fondo | `#FAFAF9` | `#111413` |
| Texto | `#1C1F1E` | `#E8ECEA` |
| Texto secundario | `#6B7270` | `#9AA3A0` |
| Acento (pasos, flechas clave) | `#0F766E` | `#2DD4BF` |
| Paso del pipeline (fondo) | `#E6F2F0` | `#16302C` |
| Decisión humana | `#FDF1E3` borde `#C2410C` | `#3A2414` borde `#FB923C` |
| Modelo de IA | `#F1F2F1` borde gris | `#1B1F1E` borde gris |
| Datos (cilindros) | `#EEF2F8` borde `#475569` | `#1A2230` borde `#94A3B8` |
| Memoria / aprendizaje | fondo de paso, borde acento grueso | ídem |

Definir todo como variables CSS (`:root` + bloque oscuro con `prefers-color-scheme`).

## 4. Formas y flechas
| Elemento | Forma |
|---|---|
| Paso | Caja con esquinas apenas redondeadas |
| Guardrail | Píldora con candado |
| Datos / memoria | Cilindro |
| Acción interactiva | Píldora rellena con acento |

| Flecha | Significado |
|---|---|
| Sólida | Flujo principal o lectura |
| Rayas | Llamada a modelo o excepción |
| Puntos | Telemetría |
| Color acento | Bucle de aprendizaje |

La punta indica hacia dónde va el dato. Etiquetas cortas o ninguna.

## 5. Texto
- **Inter** para texto y **Space Grotesk** para títulos (Google Fonts).
- Título de caja ≤ ~25 caracteres; el detalle va en una segunda línea gris.

## 6. Revisión rápida
- [ ] Nada se sale de su caja ni cruza bordes.
- [ ] Flechas en la dirección correcta.
- [ ] Se ve en tema claro y oscuro.
- [ ] Una sola vista por diagrama (pipeline, contenedores o infraestructura).

## 7. Pedirlo a un LLM
> Te adjunto una guía y una plantilla HTML. Crea un diagrama de arquitectura de IA **copiando el diseño de la plantilla** (medidas, formas, colores) y cambiando solo el contenido.
> Proyecto: [nombre y objetivo]. Vista: [pipeline / contenedores / infraestructura]. Nivel: [sin tecnologías / con herramientas concretas].
> Contenido: [entradas, pasos, modelos, datos, salida].
