# Pendientes de la V27 (lista de control)

La V27 (`src/gerar_tcc_v27.py`) parte de la V26 y recibe los resultados del Sprint 4.

Todo lo que se dejó "para después" mientras revisamos el TCC página por página.
Se marca con [x] cuando queda resuelto. Última actualización: 02/11/2026.

## Pre-textuales
- [x] Portada: texto vertical USP/ICMC nítido (fuente real).
- [ ] Portada (opcional): redibujar el fondo (líneas del cubo) en vectorial.
- [x] Portada: subtítulo con coma en vez de guion largo.
- [ ] Ficha catalográfica: pedir una nueva a la Biblioteca ICMC al final (cambian páginas y palabras clave).
- [ ] Resumo/Abstract: lugar "São Paulo/São Carlos" → dejar igual a la ficha catalográfica nueva.
- [x] Dedicatória sin título, abajo a la derecha.
- [ ] Agradecimentos: decidir si se incluye (borrador ofrecido).
- [x] Resumo y Abstract en lenguaje simple, sin símbolos.
- [x] Resumo y Abstract: cifras actualizadas (28.149 créditos, 200 defaults) y frase del resultado (02/11)
      (Fine-Gray landmark día 21: AUC 0,93, 81% de los volados en el 10% de mayor riesgo).
- [x] Sumário, Lista de Ilustrações y Lista de Tabelas automáticas con página.
- [x] Lista de Siglas automática (solo las usadas en el texto).
- [ ] **Lista de Símbolos: revisarla cuando reescribamos las fórmulas de la §5.** Quitar
      "t_start, t_stop" (nombres de código), "E_i", "p" y "r"; dejar solo los símbolos de
      las fórmulas que queden (S(t), h(t), H(t), F(t), T…).
- [x] Números de página desde la Introdução (contando desde la folha de rosto).

## Corpo del texto
- [x] Introdução reescrita (fuentes Mapa de Empresas y Sebrae 2026).
- [ ] Revisão Bibliográfica: nueva estructura + referencias que Juan debe buscar (ver chat 16/10).
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
- [ ] 3. Referencias recientes, contexto socioeconómico, comparación entre clases sociales (§2, vie 6; regiones
      por DDD ya disponibles, clases con CNEFE/renta como trabajo en curso).
- [x] 4. Reducir travessões (hecho el 02/11 en toda la V27).
- [ ] 5. Artículos contemporáneos de supervivencia y métricas de crédito después de 2002 (§2, vie 6).
- [x] 6. Sentido práctico de covariables que cambian por bloque: riesgo actualizado cada semana (§5.3, 02/11).
- [x] 7. Tratamiento de datos ausentes o inconsistentes: §4.3 con tabla de auditoría (02/11).
- [ ] 8. Itálico en todos los términos extranjeros (sáb 7).
- [x] 9. Párrafo de transición del EDA a los modelos (§6.6, 02/11).
- [ ] Nota corta para Isadora en portugués (cuerpo del email y de Moodle): qué se cambió por cada recomendación (sáb 7).
- [ ] Exportar la V27 a PDF y enviarla por Moodle y por email (dom 8).
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

## Capítulos 5, 6 y 7 reescritos el 02/11
- [x] Cap. 5: conceptos (pocas fórmulas), desfechos, granularidad de 7 días, variables.
- [x] Cap. 6: EDA nueva (src/fig_eda_v27.py, 6 figuras, tablas de oficina y región por DDD).
      Ojo: el AalenJohansenFitter de lifelines mete ruido en los tiempos; se usa un estimador propio.
- [x] Cap. 7: estrategia landmark, validación, resultados (tablas de AUC/top 10%, 7 contra 10 días,
      razones de riesgo de Fine-Gray) y limitaciones. Objetivos (cap. 3) alineados.
- [ ] Lista de Símbolos: hoy solo quedan S(t), P y T en el texto; rehacer la lista.
- [ ] Cap. 2 (Revisão Bibliográfica) todavía menciona DeepSurv y "Seção 8"; se reescribe el viernes.
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
