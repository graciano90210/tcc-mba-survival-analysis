# Pendientes de la V27 (lista de control)

La V27 (`src/gerar_tcc_v27.py`) parte de la V26 y recibe los resultados del Sprint 4.

Todo lo que se dejó "para después" mientras revisamos el TCC página por página.
Se marca con [x] cuando queda resuelto. Última actualización: 04/11/2026.

## Pre-textuales
- [x] Portada: texto vertical USP/ICMC nítido (fuente real).
- [ ] Portada (opcional): redibujar el fondo (líneas del cubo) en vectorial.
- [x] Portada: subtítulo con coma en vez de guion largo.
- [ ] Ficha catalográfica: pedir una nueva a la Biblioteca ICMC al final (cambian páginas y palabras clave).
- [ ] Título: proponer al Prof. Vicente "...Análise de Sobrevivência com Riscos Competitivos em Fluxos de Alta Frequência" (en vez de "...em Fluxos de Alta Frequência sob Censura"); si aprueba, cambiarlo al final (portada, folha de rosto, resumo, abstract, README) junto con la ficha nueva.
- [x] Folha de rosto, Resumo y Abstract alineados con el modelo oficial del MBA (Monografia, Ciências de Dados, USP – São Carlos, número de folhas automático). 03/11. Confirmado en cemeai.icmc.usp.br: "MBA em Ciências de Dados".
- [x] Dedicatória sin título, abajo a la derecha.
- [ ] Agradecimentos: decidir si se incluye (borrador ofrecido).
- [x] Resumo y Abstract en lenguaje simple, sin símbolos.
- [x] Resumo y Abstract: cifras actualizadas (28.149 créditos, 200 defaults) y frase del resultado (02/11)
      (Fine-Gray landmark día 21: AUC 0,93, 81% de los volados en el 10% de mayor riesgo).
- [x] Sumário, Lista de Ilustrações y Lista de Tabelas automáticas con página.
- [x] Lista de Siglas automática (solo las usadas en el texto).
- [x] **Lista de Símbolos revisada (05/11).** Quitar
      "t_start, t_stop" (nombres de código), "E_i", "p" y "r"; dejar solo los símbolos de
      las fórmulas que queden (S(t), h(t), H(t), F(t), T…).
- [x] Números de página desde la Introdução (contando desde la folha de rosto).

## Corpo del texto
- [x] Introdução reescrita (fuentes Mapa de Empresas y Sebrae 2026).
- [x] Revisão Bibliográfica reescrita (06/11): 5 secciones, 12 referencias nuevas confirmadas por Juan, Referências en orden alfabético automático.
- [ ] Confirmar y agregar Ishwaran et al. (2008, RSF) y Granzotto (2008, UFSCar, fração de cura).
- [ ] Títulos de figuras y tablas: quitar "vs.", "—", nombres de código (se corrige al reescribir cada sección).
- [x] "Fonte:" debajo de cada figura y tabla (02/11, automático; por defecto "Elaborada pelo autor (2026)."). Título de figura arriba (NBR 14724).
- [ ] Revisar si cada capítulo (sección primaria) debe empezar en página nueva.
- [x] Quitar guiones largos, flechas, "×", "≥", "✓" del texto (02/11: 87 guiones y ~60 símbolos; solo quedan dentro de las fórmulas). El texto nuevo se escribe sin ellos.
- [ ] Usar "comerciante" para describir al cliente; producto descrito de forma neutral (sin cobrador ni tasa).
- [ ] Recomendaciones de la clase de Metodologia (ver `notas_analise_socioeconomica.md`, §6).

## Adelanto para Isadora (enviar el domingo 08/11/2026)
Recomendaciones de Isadora y dónde se atienden:
- [x] 1. Resumo simple (V26); barreras de la extracción explicadas sin jerga y *Data Stitching* definido (§4.1 y §4.2, 02/11).
- [x] 2. Justificar granularidad diaria contra mensual (§5.3, 02/11): 7 días alerta antes que 10 (73% contra 61%
      en el día 14); lo mensual no ve pago incompleto ni domingos/feriados.
- [x] 3. Referencias recientes y contexto brasileño en el cap. 2 (06/11: Mapa de Empresas, Sebrae, BCB 2025, CMN 4.966). Clases sociales: análisis por renta en el Sprint 5. (antes: regiones
      por DDD ya disponibles, clases con CNEFE/renta como trabajo en curso).
- [x] 4. Reducir travessões (hecho el 02/11 en toda la V27).
- [x] 5. Artículos contemporáneos (Dirick 2017, Frydman 2022, Blumenstock 2022) y métricas/regulación después de 2002 (Uno 2011, CMN 4.966) en el cap. 2 (06/11).
- [x] 6. Sentido práctico de covariables que cambian por bloque: riesgo actualizado cada semana (§5.3, 02/11).
- [x] 7. Tratamiento de datos ausentes o inconsistentes: §4.3 con tabla de auditoría (02/11).
- [x] 8. Itálico automático en términos extranjeros (07/11): lista ESTRANGEIROS en el generador; nombres propios y siglas en redondo.
- [x] 9. Párrafo de transición del EDA a los modelos (§6.6, 02/11).
- [x] Nota para Isadora redactada (07/11): reports/nota_isadora_adiantamento.md.
- [x] PDF final generado (07/11): documentotcc/TCC_Juan_Graciano_Adiantamento_V27.pdf (49 págs). Juan lo envía por Moodle y email el 07/11.
- [ ] Referencias: Claude las busca (título, autor, año, enlace) y Juan confirma (vie 6).

## Materias del MBA aplicadas al TCC (revisión 02/11/2026)
Para el adelanto (enriquecen las secciones de esta semana):
- [x] §4.3: técnicas de Técnicas Avançadas de Captura e Tratamento (missing values, outliers,
      class imbalance, normalization, web scraping); responde la recomendación 7 de Isadora.
- [ ] §3: diagrama conceptual del ETL, como en Processamento Massivo (Modelagem Conceitual de ETL/ELT);
      responde la recomendación 1 de Isadora.
- [ ] §4: organizar la metodología por las fases de CRISP-DM (Gestão Ágil) y presentar la logística como
      GLM (Estatística para CD, Modelos Lineares Generalizados).
- [ ] §4: mencionar el cure fraction model (mixture cure model) como trabajo en curso.
- [ ] §2 (vie 6): buscar referencias con el método de revisión sistemática (Metodologia II) e incluir
      Granzotto (2008), "Seleção de modelos de tempos com longa-duração para dados de finanças", UFSCar
      (lectura recomendada en Aprendizado Dinâmico, módulo Análise de Sobrevivência).
- [ ] Juan: confirmar en el Currículo Lattes del Prof. Vicente si trabaja con cure rate models y llevar
      la pregunta a la próxima reunión.
Para los sprints siguientes (ya en el cronograma §8 de la V27):
- [ ] Sprint 5: cure fraction model como benchmark (Aprendizado Dinâmico, notebook AD-08, última sección).
- [ ] Sprint 5: Random Survival Forest (Aprendizado de Máquina, florestas aleatórias).
- [ ] Sprint 5: covariables macro con lo de series de tiempo (Aprendizado Dinâmico), estacionalidad.
- [ ] Sprint 6: DeepHit con embeddings de ruta y oficina (APIAG, MLP e Feature Embeddings) y variante con
      LSTM sobre la secuencia diaria de pagos (APIAG, Redes Neurais para dados sequenciais).
- [ ] Sprint 7: sección corta de ética y LGPD (Introdução à CD, Questões Éticas) y storytelling en las
      figuras de resultados (Reporte dos Resultados).
- [ ] Actualizar las menciones a sprints dentro del texto (§4 y §5 todavía dicen DeepSurv/pycox en el
      Sprint 4-5); se corrige al reescribir esas secciones.

## Sección 4 (ETL) reescrita el 02/11
- [x] De 10 a ~5 páginas, sin código; detalle técnico en el Apêndice A. Figura del flujo (7 días, Fine-Gray).
- [x] Numeración automática de tablas y figuras: en el texto usar {tab:clave} / {fig:clave}.
- [x] §4.5 Gestão do Projeto: fases CRISP-DS actualizadas (02/11).
- [ ] Diagrama conceptual del ETL (Processamento Massivo): opcional, la Figura 1 ya cumple esa función.

## Revisión página por página (iniciada 03/11)
- [x] Portada, folha de rosto (modelo oficial: Monografia, Ciências de Dados, USP – São Carlos), dedicatoria
      (alineada a la izquierda), Resumo y Abstract (sin "robô", sin regiones, con resultado del historial y conclusión),
      listas de figuras, tablas y siglas.
- [x] Lista de Símbolos y Sumário (05/11): sumário como el modelo oficial (sin sangría, apéndice sin subsecciones),
      REFERÊNCIAS, APÊNDICE A en minúsculas, cap. 8 = CONSIDERAÇÕES FINAIS (8.1 conclusiones parciales, 8.2 cronograma).
- [x] Introdução, Objetivos, cap. 4 completo y §5.1–5.2 revisados (05/11).
- [x] Revisión página por página del cuerpo completa (06/11): §5.3 con tabla de ejemplo semanal, §6.6, §7.4 (SHR), cap. 8 y cronograma reescritos.
- [ ] Revisar el Apêndice A (opcional) y la versión en español actualizada al final.

## Revisión externa (otra ventana de Claude, 04/11)
- [x] Abstract con frase rota, Anderson a Andersen, §2.2 con snapshots de 10 días, "Seção 3.6", cap. 1 con
      los capítulos 6 y 7, CRISP-DM en el Sprint 7, Sprint 4 "enviado" en futuro.
- [x] Regras simples como baseline (cox_v2.py, REGRAS_SIMPLES): Fine-Gray +8 pp de captura sobre la mejor
      regla, mejor en 15/15 particiones (día 14) y 13/15 (día 21). Desvío de la captura en la tabla.
- [x] Explicado qué aporta supervivencia frente a la logística (censurados y el "cuándo").
- [ ] **Validación temporal (entrenar 2020 a 2024, probar 2025 y 2026): prioridad del Sprint 5, antes que DeepHit.**
- [ ] Figura de incidencia acumulada de default por grupo de riesgo previsto (muestra el "cuándo").
- [x] Ética: §4.4 dice que el dueño de la institución autorizó y suministró el acceso a los datos (confirmado por Juan 04/11).
- [ ] "45 f." contra "46 p." de la ficha: se resuelve con la ficha nueva al final.

## Análisis socioeconómico mejor (decidido 04/11; Juan no está convencido del análisis por DDD)
- [x] §6.2 (05/11): tabla de regiones por DDD quitada; párrafo anuncia el análisis por renta del setor censitário (opción a)
      o (b) dejarla como primera aproximación.
- [ ] Juan: descargar del IBGE la malha de setores censitários 2022 de SP, RJ y SC y la renta por setor
      (Agregados por Setores Censitários, rendimento do responsável; si no hay 2022, Censo 2010 Básico V005 + malha 2010).
- [ ] Cruce local GPS del cliente (3.781 de 4.024, 94%) con el setor censitário (geopandas, sin servicios externos):
      quintiles de renta, tasa de abandono por quintil y renta como variable del modelo (Sprint 5).
- [ ] Opcional: actividad del negocio a partir del nombre (1/3 identificable): belleza 6,6%, alimentación 5,3%,
      vestuario 1,8% de clientes que se volaron.

## Capítulos 5, 6 y 7 reescritos el 02/11
- [x] Cap. 5: conceptos (pocas fórmulas), desfechos, granularidad de 7 días, variables.
- [x] Cap. 6: EDA nueva (src/fig_eda_v27.py, 6 figuras, tablas de oficina y región por DDD).
      Ojo: el AalenJohansenFitter de lifelines mete ruido en los tiempos; se usa un estimador propio.
- [x] Cap. 7: estrategia landmark, validación, resultados (tablas de AUC/top 10%, 7 contra 10 días,
      razones de riesgo de Fine-Gray) y limitaciones. Objetivos (cap. 3) alineados.
- [x] Lista de Símbolos rehecha (05/11): S(t), P, T, t, h(t), en orden de aparición y sin guion.
- [x] Cap. 2 sin DeepSurv ni referencias viejas (06/11).
- [ ] Citar Ishwaran et al. (2008) para el RSF cuando se confirme la referencia.

## Sprint 4 en el texto (V27)
- [ ] §3: dataset reconstruido (vales excluidos, calendario de cobro, cuota de 1 real = renegociación,
      abonos después del cierre). Quitar números de la V25 (273 eventos, 0,96%).
- [ ] §4: bloques de 7 días con 10 como sensibilidad; landmark + Fine-Gray; logística de comparación;
      validación cruzada por cliente; por qué el Cox cause-specific no sirve para ordenar en el landmark.
- [ ] §5: tablas y figuras nuevas (CIF por oficina, AUC/captura por día y bloque, razones de riesgo).
- [ ] §5.8 Auditoría: reescribir con las trampas encontradas (campos del día de descarga, limpiezas, vales,
      cuota de 1 real, cuadres).
- [ ] Fine-Gray formal con pesos de censura (hoy aproximado: 2,7% de censura).
- [ ] Confirmar fechas de los partidos de Brasil en la Copa 2022 (gov.br) y artículo de la Res. CMN 4.966.
- [ ] Repositorio: decidir privado o limpieza antes del push (nombre real del sistema, URL, rutas, usuario de limpieza, término del producto).

## Referencias
- [ ] Referencia ANTHROPIC: confirmar modelo y fecha de acceso.
- [ ] Agregar las referencias nuevas de la revisión bibliográfica cuando estén confirmadas.
