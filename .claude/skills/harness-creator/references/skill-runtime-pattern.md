# Patrón de skills

Usa este patrón cuando quieras empaquetar un comportamiento reutilizable del agente como una skill, en lugar de repetir instrucciones largas en cada repositorio.

## Qué va en una skill

- Flujos de trabajo reutilizables que sirven en varios proyectos.
- Procedimientos de decisión de un dominio concreto.
- Plantillas, checklists y material de referencia que el agente carga cuando lo necesita.
- Scripts auxiliares pequeños, si son estables y seguros de ejecutar.

## Qué NO va en una skill

- Datos de arquitectura de un proyecto concreto, que deben vivir en ese repositorio.
- Secretos, tokens, URLs privadas o credenciales del usuario.
- Manuales largos que el agente tendría que leer siempre antes de actuar.
- Comandos con efectos destructivos, salvo que estén claramente documentados y pidan aprobación explícita del usuario.

## Forma de una skill

Una skill de producción usa revelación progresiva:

1. El frontmatter de `SKILL.md` explica cuándo debe activarse la skill.
2. El cuerpo da el flujo de trabajo fiable más corto posible.
3. `references/` contiene material más profundo que solo se carga cuando es relevante.
4. `templates/` contiene artefactos listos para copiar.
5. `evals/` recoge chequeos de calidad representativos.

## Reglas de diseño

- Mantén el archivo de entrada lo bastante corto para leerlo de un vistazo.
- Prefiere checklists concretas antes que consejos abstractos.
- Enlaza cada archivo incluido que menciones y verifica que existe.
- Las instrucciones de instalación deben decir claramente el repositorio, el nombre de la skill y el agente destino.
- Trata los scripts como ayudas opcionales, no como comportamiento oculto.

## Checklist de validación

- [ ] `SKILL.md` existe y tiene un frontmatter válido.
- [ ] Todo archivo referenciado existe dentro de la carpeta de la skill.
- [ ] Las plantillas se pueden copiar sin riesgo a un repositorio destino.
- [ ] El comando de instalación se probó con `skills add --list` o equivalente.
- [ ] La skill no depende de rutas locales privadas.
