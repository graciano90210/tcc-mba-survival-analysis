# Pendientes de la V27 (lista de control)

La V27 (`src/gerar_tcc_v27.py`) parte de la V26 y recibe los resultados del Sprint 4.

Todo lo que se dejó "para después" mientras revisamos el TCC página por página.
Se marca con [x] cuando queda resuelto. Última actualización: 02/11/2026.

## Pre-textuales
- [x] Portada: texto vertical USP/ICMC nítido (fuente real).
- [ ] Portada (opcional): redibujar el fondo (líneas del cubo) en vectorial.
- [ ] Portada: subtítulo "Trabalho de Conclusão de Curso — MBA…" cambiar el guion largo por coma.
- [ ] Ficha catalográfica: pedir una nueva a la Biblioteca ICMC al final (cambian páginas y palabras clave).
- [ ] Resumo/Abstract: lugar "São Paulo/São Carlos" → dejar igual a la ficha catalográfica nueva.
- [x] Dedicatória sin título, abajo a la derecha.
- [ ] Agradecimentos: decidir si se incluye (borrador ofrecido).
- [x] Resumo y Abstract en lenguaje simple, sin símbolos.
- [ ] Resumo y Abstract: actualizar cifras (28.149 créditos, 200 defaults) y agregar la frase del resultado
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
- [ ] Agregar "Fonte:" debajo de cada figura y tabla (ABNT; hoy no hay ninguna).
- [ ] Revisar si cada capítulo (sección primaria) debe empezar en página nueva.
- [ ] Quitar guiones largos, flechas, "×", "≥", "✓" del resto del texto (hoy ~105 guiones largos).
- [ ] Usar "comerciante" para describir al cliente; producto descrito de forma neutral (sin cobrador ni tasa).
- [ ] Recomendaciones de la clase de Metodologia (ver `notas_analise_socioeconomica.md`, §6).

## Adelanto para Isadora (enviar el domingo 08/11/2026)
Recomendaciones de Isadora y dónde se atienden:
- [ ] 1. Resumo simple; explicar cómo se superaron las barreras de la extracción; definir *Data Stitching* (§3, mar 3).
- [ ] 2. Justificar granularidad diaria contra mensual (§4, mié 4): 7 días alerta antes que 10 (73% contra 61%
      en el día 14); lo mensual no ve pago incompleto ni domingos/feriados.
- [ ] 3. Referencias recientes, contexto socioeconómico, comparación entre clases sociales (§2, vie 6; regiones
      por DDD ya disponibles, clases con CNEFE/renta como trabajo en curso).
- [ ] 4. Reducir travessões (todo el texto, sáb 7).
- [ ] 5. Artículos contemporáneos de supervivencia y métricas de crédito después de 2002 (§2, vie 6).
- [ ] 6. Sentido práctico de covariables que cambian por bloque: riesgo actualizado cada semana (§4, mié 4).
- [ ] 7. Tratamiento de datos ausentes o inconsistentes en el pipeline (§3, mar 3): auditoría.
- [ ] 8. Itálico en todos los términos extranjeros (sáb 7).
- [ ] 9. Párrafo de transición del EDA a los modelos (§5, jue 5).
- [ ] Nota corta para Isadora en portugués (cuerpo del email y de Moodle): qué se cambió por cada recomendación (sáb 7).
- [ ] Exportar la V27 a PDF y enviarla por Moodle y por email (dom 8).
- [ ] Referencias: Claude las busca (título, autor, año, enlace) y Juan confirma (vie 6).

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
