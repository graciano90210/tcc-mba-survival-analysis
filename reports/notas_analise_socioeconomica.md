# Notas de trabajo: análisis socioeconómico, KPIs y ciclos económicos

Documento vivo. Se va actualizando a medida que avanzamos. Origen: feedback de la
evaluación de *Metodologia e Projeto II* (Isadora Ferrão, 9,80/10, 24/09/2026), que
pide contexto socioeconómico brasileño reciente y comparación entre clases sociales.

Última actualización: 28/09/2026.

---

## 1. Rutas: ciudad de operación

Fuente: encabezado de los reportes ATLAS (`Ruta: ...`) + confirmación de la operación,
contrastado con el DDD y las coordenadas de los clientes de cada ruta.

| rta_id | Oficina | Ruta | Ciudad | Evidencia |
|---|---|---|---|---|
| 82 | 23 São Paulo | 01.01. JUAN SP | São Paulo | nombre, DDD 11 (93%) |
| 96 | 23 São Paulo | 01.02. FRANCISCO MORATO | Francisco Morato | nombre, DDD 11 |
| 423 | 23 São Paulo | 01.03. DIADEMA | Diadema | nombre, DDD 11 |
| 136 | 23 São Paulo | 01.04. PINDA | Pindamonhangaba | nombre, DDD 12 |
| 367 | 23 São Paulo | 01.07. SANTOS | Santos | nombre, DDD 13 |
| 448 | 23 São Paulo | 01.08. GUARULHOS | Guarulhos | nombre, DDD 11 |
| 494 | 23 São Paulo | 01.09. VAMPI SJ | São José dos Campos | operación, DDD 12 (93%) |
| 415 | 31 Soc. Brasil | 01.06. CAMPINAS | Campinas | nombre, DDD 19 |
| 68 | 31 Soc. Brasil | 04.01. BILLY | Petrópolis / Rio de Janeiro | operación dijo "Rio"; DDD 24 (59%) y 21 (40%), coordenadas en Petrópolis |
| 338 | 31 Soc. Brasil | 04.02. BLUMENAU | Blumenau | nombre, DDD 47 |
| 347 | 31 Soc. Brasil | 04.03. CAMBORIU | Balneário Camboriú | nombre, DDD 47 |
| 389 | 31 Soc. Brasil | 04.04. CANTI | Rio de Janeiro | operación, DDD 21 (100%) |
| 114 | 44 Cabo Frio | 02.01. RIO | Rio de Janeiro | nombre, DDD 21 (98%) |
| 439 | 44 Cabo Frio | 02.02. COSTEÑO | Cabo Frio | operación dijo "creo que SP/Francisco Morato"; **datos dicen Cabo Frio** (DDD 22 88%) |
| 396 | 44 Cabo Frio | 02.03. CRISTIAN | Cabo Frio | operación, DDD 22 (91%) |
| 420 | 44 Cabo Frio | 02.04. CRUZ | Rio das Ostras | operación dijo "creo que Santos/Praia Grande"; **datos dicen Região dos Lagos** (DDD 22 100%, coords Rio das Ostras) |
| 511 | 44 Cabo Frio | 02.05. LUIS ALFONSO CF | Cabo Frio | nombre, DDD 22 |

**Las rutas son carteras de un cobrador y el cobrador puede cambiar de ciudad**
(confirmado por la operación: COSTEÑO trabajó en Rio antes de ir a São Paulo).
Composición por DDD a lo largo del tiempo (fecha del crédito):

- COSTEÑO: solo tiene créditos entre 2025 T2 y 2026 T2, todos DDD 22 → en nuestros datos
  es Região dos Lagos. Su etapa en São Paulo, si existe, es posterior a la descarga.
- CRUZ: solo entre 2025 T4 y 2026 T2, 100% DDD 22 → Região dos Lagos.
- BILLY: 2021 a 2023 T2 casi todo DDD 24 (Petrópolis/Serrana); desde 2023 T3 mitad
  DDD 24 y mitad DDD 21 (expansión a Rio capital).

**Regla para el análisis:** la ciudad se asigna **por cliente** (DDD y dirección), no por
ruta. La ruta queda como efecto del cobrador/cartera. En São Paulo hay varias rutas;
algunas llevan nombre de barrio o de cobrador.

## 2. Información demográfica disponible

| Campo | Cobertura | Utilidad |
|---|---|---|
| DDD del celular/teléfono | 83% de clientes | región/UF del cliente (11 = São Paulo, 21 = Rio, 22 = Região dos Lagos, 24 = Serrana/Sul Fluminense, 47 = Norte de SC…) |
| LATITUD/LONGITUD | 93% de clientes | **cuidado:** en varias rutas casi todos caen en un mismo punto (CANTI 90%, CAMBORIU 88%, COSTEÑO 81%, LUIS ALFONSO 72%). Probablemente es la posición del celular del cobrador al registrar, no del negocio del cliente. Útil solo donde hay dispersión (JUAN SP, FRANCISCO MORATO, RIO, BILLY). |
| DIRECCIÓN | 100%; 66% con tipo de vía + número | la mejor fuente para ubicar al cliente a nivel de sector censal |
| BARRIO | inútil | solo 3 valores ("CENTRO", "SANTA INES", "1_POR DEFINIR") |
| Oficina / ruta | 100% | ciudad de operación (tabla 1) |
| Edad, sexo, ingreso, actividad | **no existe** en los reportes | preguntar si la ficha del cliente en ATLAS tiene más campos |

**No inferir sexo por el nombre**: impreciso y sensible bajo la LGPD.

### Ubicación del cliente por DDD (fuente preferida, confirmado por la operación)

`kpis_clientes.csv` trae `regiao_cliente` (DDD; sin DDD, ciudad de la ruta),
`fonte_regiao` y `migrante_ddd` (DDD de un estado distinto al de la ruta). Límites: el DDD
da región, no barrio; algunos clientes conservan el número de su estado de origen.

Primeros resultados (% de clientes que se volaron al menos una vez):

| Región (DDD) | Clientes | % volaron |
|---|---|---|
| Vale do Itajaí / Litoral Norte SC (47) | 307 | **19,9** |
| Baixada Santista (13) | 212 | 7,1 |
| Rio de Janeiro metrópole (21) | 672 | 4,0 |
| Grande São Paulo (11) | 973 | 3,3 |
| Vale do Paraíba (12) | 343 | 2,6 |
| Campinas (19) | 121 | 2,5 |
| Serrana / Sul Fluminense (24) | 167 | 1,8 |
| Região dos Lagos (22) | 543 | 1,1 |

- **Clientes sin DDD válido** se vuelan más: 9,2% en la ruta Rio, 11,7% en BILLY,
  5,4% en JUAN SP. Tener un teléfono válido registrado puede ser una variable en sí misma.
- Migrantes por DDD: 5,8% contra 4,7% (solo 69 clientes, diferencia no concluyente).

### Plan para "clase social"

1. Geocodificar la DIRECCIÓN **sin enviarla a servicios externos** (LGPD). Opción: el
   CNEFE del IBGE (Cadastro Nacional de Endereços para Fins Estatísticos), que es
   público, trae coordenadas y sector censal por dirección y se puede cruzar localmente.
2. Asociar a cada cliente la renta media del **sector censal** (Censo IBGE).
3. Clasificar por franjas de renta (clases A–E o quintiles) y comparar tasa de volados,
   puntualidad, ticket y renovación entre clases.
4. Donde no haya dirección geocodificable: usar la ciudad (ruta/DDD) con indicadores
   municipales (renta per cápita, IDHM, Gini).

## 3. KPIs ya calculados (`src/kpis_clientes.py`)

Salidas en `data/processed/` (fuera de git): `kpis_clientes.csv`, `kpis_rutas.csv`.

- Por cliente: n.º de créditos, antigüedad, intervalo entre renovaciones, ticket,
  cuota, plazo, puntualidad, razón plazo real/pactado, si se voló, pérdida, intereses
  cobrados, resultado, oficina, ruta, ciudad, DDD, UF, coordenadas.
- Resultados iniciales (cohorte de `reconstruir_dataset.py`):
  - 4.108 clientes; **201 (4,9%) se volaron al menos una vez**.
  - Capital prestado R$ 35,1 millones; intereses cobrados R$ 6,8 millones; pérdidas
    R$ 114 mil (0,32%). **Revisar:** la pérdida parece baja.
  - **Santa Catarina concentra el riesgo:** Camboriú 2,9% de default por crédito (18%
    de sus clientes se voló alguna vez), Blumenau 2,3% (20%). São Paulo y Rio entre
    0,3% y 0,8%.

## 4. Ciclos económicos y choques locales (a incorporar como covariables)

Periodo de los datos: ene. 2020 a may. 2026.

### Nacionales
| Periodo | Evento | Fuente para fechar/medir |
|---|---|---|
| 2020 T1–T2 | Recesión por COVID-19 (fechada por el CODACE/FGV: pico 2019 T4, valle 2020 T2) | CODACE (FGV IBRE), PIB trimestral IBGE |
| mar. 2020 → 2021 | Cuarentenas, cierre de comercio, Auxílio Emergencial | decretos estatales/municipales, datos de Auxílio |
| 2021–2022 | Inflación alta y ciclo de alza de la Selic (2% → 13,75%) | BCB SGS (Selic, IPCA) |
| 2024–2025 | Nuevo ciclo de alza de la Selic | BCB SGS |

### Locales (**verificar fechas antes de usarlas**)
| Ciudad/ruta | Evento | A verificar |
|---|---|---|
| Petrópolis (BILLY) | Lluvias y deslizamientos de feb. 2022 | fecha exacta y área afectada |
| Blumenau / Camboriú | Inundaciones en SC (fines de 2023) | fechas y municipios |
| Todas | Estacionalidad: fin de año, carnaval, regreso a clases, temporada de verano en ciudades de playa (Cabo Frio, Camboriú, Santos) | construir dummies |

### Domingos y festivos (nacionales, estaduales y municipales)

El cobrador no pasa los domingos ni, en buena parte, los festivos. Un día sin abono en
esas fechas **no es mora**. Evidencia en los datos (abonos por día):

- Lunes a viernes ≈ 245; sábado ≈ 214; **domingo ≈ 10**.
- Festivos nacionales, relativo a un día hábil típico: Natal 2%, N.S. Aparecida 26%,
  Independência 28%, Tiradentes y Finados 33%, Dia do Trabalho 35%, República 47%,
  Consciência Negra 48%.
- Festivos locales (caen menos porque solo afectan a la parte de la cartera en esa
  ciudad o estado): aniversario de São Paulo (25/01) 51%, Revolução Constitucionalista
  SP (09/07) 57%, São Sebastião Rio (20/01) 72%, São Jorge RJ (23/04) 91%.
- Faltan festivos móviles (Carnaval, Sexta-feira Santa, Corpus Christi) y municipales
  de las demás ciudades.

**Cómo incorporarlo:**
1. Calendario de días de cobro por UF y ciudad: librería `holidays` (Brasil, con
   subdivisiones por estado; no está instalada) + festivos municipales a mano.
2. Puntualidad y `dias_con_abono_prev` sobre **días de cobro esperados** (sin domingos ni
   festivos), no sobre días calendario.
3. Covariable del intervalo: n.º de festivos/días sin cobro en el bloque de 10 días.
4. La regla de default se mantiene en 120 días calendario (definición del negocio).

**Implementado (02/11/2026, `src/calendario_cobro.py`, librería `holidays` 0.107).**
Validación con los abonos 2020–2026 (abonos por día, SP / RJ / SC; día hábil = 132 / 101 / 22):
domingo 0,4 / 0,4 / 0,1 (**la operación confirma: los domingos no se trabaja**); feriado
nacional 30 / 25 / 3,7; feriado estadual 43 / 36; Corpus Christi 38 / 27 / 0,7;
víspera de Año Nuevo 28 / 45 / 5; Carnaval 64 / 68 / 12; sábado 108 / 93 / 19.
Días sin cobro = domingo, feriados nacionales y estaduales, Carnaval, Corpus Christi,
vísperas de Navidad y Año Nuevo. Faltan los feriados municipales (la librería no los trae).
Nuevas covariables en el dataset: `dias_cobro_sin_pagar`, `dias_sin_cobro_bloque`, y el
atraso (`ratio_atraso`) ya se mide en días de cobro.

### Grandes eventos sociales (pedido de Isadora: "aspectos sociales")
- **Copa del Mundo 2022 (Qatar)**: días de partido de Brasil 24/11, 28/11, 02/12, 05/12 y
  09/12/2022 (ponto facultativo; **Juan debe confirmar las fechas en una fuente oficial,
  p. ej. el decreto del Ministério da Gestão / gov.br**). Abonos: 220–241 contra 270–297 en
  días normales vecinos, **caída de 15–20%**. Menor que un feriado; queda como análisis
  descriptivo. La Copa 2026 empieza en junio, después del corte (15/05/2026).
- **COVID-19**: abonos por mes 563 (mar. 2020), **83 (abr.) y 50 (may.)**, 102 (jun.),
  vuelta a ~490 en dic. 2020. Choque mucho mayor que cualquier feriado.
- **Gobiernos** (idea de Juan, 02/11): 2020–2022 gobierno Bolsonaro, 2023–2026 gobierno Lula.
  Problema: el primer periodo coincide con COVID y con el ciclo de alza de la Selic, así que
  no se puede atribuir un efecto al gobierno. Propuesta: tratarlo como **periodos de
  política económica** medidos con variables concretas (Selic, IPCA, desempleo y
  transferencias de renta: Auxílio Emergencial 2020–2021, nuevo Bolsa Família desde 2023),
  sin la etiqueta derecha/izquierda en el texto. **Consultar con el orientador.**

### Series para medir el efecto
- **Nacional:** Selic, IPCA, IBC-Br (BCB SGS, mensual).
- **Estatal:** IBC-R (actividad regional, BCB), desempleo PNAD Contínua (IBGE, trimestral).
- **Municipal:** empleo formal CAGED (mensual por municipio), PIB municipal (anual, con
  2 años de rezago).

### Cómo entra al modelo
Covariables tiempo-variantes asignadas a cada intervalo del crédito según la fecha
calendario y la ciudad de la ruta. Preguntas a responder: ¿sube el riesgo de volarse en
recesión o con Selic alta? ¿Afectan igual a todas las ciudades? ¿Explican los choques
locales (p. ej. Petrópolis 2022) picos de default en esas rutas?

## 5. Hallazgos de datos que cambian el TCC (auditoría del 28/09/2026)

- La regla de la V25 medía el silencio según los reportes de 10 días. Los volados no
  aparecen en los reportes mientras están en silencio: 183 volados quedaban como "cura".
- 250 créditos sin ningún abono y SALDO 0 aparecían en todos los reportes y quedaban como
  default. **Decisión: excluidos** (`creditos_sin_movimiento.csv`).
- SALDO, CUOTAS ATRASADAS y VALOR ÚLTIMO ABONO son el estado del día de la descarga
  (leakage si se usan como covariables).
- Reglas confirmadas: default = 120 días sin pagar desde el último pago real (o desde el
  desembolso si nunca pagó); la limpieza de volados siempre llega después, a los 6–12
  meses; el sistema solo cierra el crédito cuando el último abono deja saldo 0.
- Resultado de `src/reconstruir_dataset.py`: 28.294 créditos, **202 defaults (0,71%)**,
  93.953 intervalos, validaciones OK.

## 5b. Sprint 4 (02/11/2026): datos de la operación y primeros modelos

**De la operación (Juan):**
- Plazos: 20, 24, 30, 40 o 50 días.
- **Vales**: el campo CLIENTE empieza con "VALE" (150 créditos, 63 nombres). Son préstamos de
  la empresa a sus trabajadores, sin intereses y a muchos días; **no son créditos de clientes
  y se excluyen** (`PATRON_VALE` en `reconstruir_dataset.py`). Solo 2 terminaban en default.
- **Cuota de 1 real = renegociación en el MISMO crédito** (Juan, 02/11): el comerciante cierra
  el negocio a mitad del crédito, desaparece unos días, después llama y acuerda pagar semanal o
  quincenal; se le alarga el plazo y la cuota queda en 1 real por día para que no pese en el
  cobro diario de la ruta. A esos clientes no se les da crédito nuevo y la mayoría se pierde.
  269 créditos (más de 50 cuotas). En 204 el cliente pagó la cuota normal en los primeros días:
  VALOR CUOTA y CUOTAS PACTADAS son el estado del día de la descarga (igual que SALDO), así que
  la marca de 1 real es **leakage** si entra al modelo. Corrección: cuota original estimada
  como TOTAL / 20 (`_cuota_original` en `reconstruir_dataset.py`) y la marca queda solo para lo
  descriptivo. Error mío corregido: el par 64997 → 65298 era una renovación normal (abono alto
  para renovar), no un traslado de deuda.
- Desenlace de los 269 con la regla de 120 días: 41 default, 196 cura, 32 censura. De las 196
  curas, 101 cierran con abono pequeño tras menos de 15 días sin pagar; 92 cierran con un abono
  grande (mediana 40 a 58% del total) tras 15 a 119 días sin pagar. **Regla confirmada por Juan:
  se voló solo si pasó 4 meses o más sin pagar nada y después vino el abono de todo lo que
  debía**; esos 92 no llegan a 4 meses, así que se mantienen como cura (el cliente volvió).
- La limpieza de volados ya está tratada: el default se marca en el día 120 y el abono de
  limpieza posterior nunca cuenta como pago (182 volado_limpiado).
- Valores prestados: hasta 15.000 (pocos clientes 20.000 o más). **Hay créditos al 15% y otras
  tasas** (confirmado): `kpis_clientes.py` supone 20% para separar capital e intereses, así que
  pérdida e intereses de los KPIs son aproximados (limitación a declarar). El modelo no se afecta
  (usa el total).
- **Abonos después del cierre ("cuadres")**: 89 créditos reciben más de 1,2 veces el total (varios
  exactamente el doble). Ej.: 87206 completa 1.200 el 07/07/2023 y recibe 1.200 más hasta el 15/07;
  124775 (Juan: "no es un cliente normal, es otro cuadre"). El crédito se paga normal y después el
  código se usa para un cuadre. No afecta: desenlace, covariables, historial y KPIs usan solo
  pagos hasta el día del cierre. Se mantienen.
- El cliente "apretado" se nota en los créditos anteriores: parcela incompleta, atraso, y al
  final un abono alto solo para cerrar y renovar. Implementado en `src/historial_cliente.py`.
- El modelo debe considerar el plazo y la cuota diaria para saber si paga incompleto:
  `plazo_dias`, `pago_relativo_prev` (pago diario / cuota) y `pct_abono_incompleto`.

**Historial del cliente (tasa de default del crédito actual según el anterior):**
puntualidad ≤ 70% 1,22% contra > 95% 0,39%; demoró > 1,2 veces el plazo 1,00% contra 0,38%
dentro del plazo; último abono > 9 cuotas 0,86% contra ≤ 1,5 cuotas 0,23%; primer crédito
1,41% contra 0,60% con historial.

**Hallazgo metodológico:** en el Cox tempo-variante el default "se anuncia" durante los
16 bloques de silencio previos al día 120 (en el último bloque dias_sin_pagar = 113–119).
C-index 0,98 con esa variable, 0,87 sin ella: buena parte es mecánica. Además el Cox
cause-specific compara, en el día 120, a los que se vuelan con los créditos lentos que
siguen abiertos (los buenos ya se curaron), y en un landmark da AUC 0,55.
La pregunta útil, "¿este crédito terminará en default?", se responde con la **incidencia
acumulada** (Fine-Gray) en un landmark.

**Resultados sin vales (28.149 créditos, 200 defaults; validación cruzada por cliente,
5 particiones × 3 repeticiones; `src/cox_v2.py`, `reports/modelagem_v2/`):**

| Modelo (bloque 7 días) | Día 14 AUC | Día 14 top 10% | Día 21 AUC | Día 21 top 10% |
|---|---|---|---|---|
| Fine-Gray landmark, crédito actual + historial | 0,913 ± 0,018 | 78% | 0,936 ± 0,012 | 83% |
| Logística landmark, igual | 0,913 ± 0,018 | 77% | 0,934 ± 0,012 | 83% |
| Logística, solo historial y contrato (≈ al desembolso) | 0,814 | 49% | 0,801 | 48% |
| Cox tempo-variante B (sin días sin pagar) | 0,699 | 46% | 0,778 | 52% |

Bloque 7 contra 10 días (Fine-Gray, día 14): AUC 0,913 contra 0,884, top 10% 78% contra 68%;
en el día 21 se igualan (0,936 contra 0,934). **El bloque de 7 días da la alerta antes.** Odds ratios (logística, día 14):
ratio_atraso 1,84; dias_con_abono_prev 0,55; primeiro_credito 1,25; ult_log_pago_final 1,23
(el abono alto para renovar sube el riesgo, como dijo la operación); ofi_31 1,68.
**Cifras de la tabla anteriores a la corrección del leakage de la cuota de 1 real.** Después de
corregir (sin plano_flexivel, cuota original estimada), bloque 7 días: Fine-Gray AUC 0,896 y
top 10% 73% en el día 14; AUC 0,930 y top 10% 81% en el día 21; solo historial 0,758 / 36%.
Pendiente: Fine-Gray formal con pesos de censura (hay 2,7% de censura), comparar con RSF y
DeepHit en los mismos landmarks, y validación temporal.

## 6. Recomendaciones de la clase en vivo (Plantões Metodologia, Victor Hugo Barella, 29/09/2026)

Ejemplo analizado: TCC de Bruno Pimentel (90 págs.).

1. **No poner tanto código en el TCC.** Si el evaluador quiere verlo, va al repositorio
   y al notebook. Estado en la V26: 4 bloques de código (§4.2, §4.3 y §4.5, máscara NumPy)
   y unos 19 fragmentos técnicos en tablas (XPath, `switch_to.frame`, `dispatchEvent`,
   `execute_script`). Acción: quitar los bloques, describir las soluciones en lenguaje
   conceptual y citar el repositorio y el notebook. Así también se reduce la §4, que
   ocupaba ~28% del documento. **Antes de citar el repo público hay que limpiarlo de
   datos sensibles.**
   **Coincide con Isadora** (feedback Metodologia II): simplificar la descripción del
   pipeline de extracción, explicar de forma didáctica cómo se superaron las barreras y
   definir términos como *Data Stitching* antes de usarlos. Plan para la V26:
   - Resumo: una sola frase sobre la extracción, sin lista de barreras técnicas.
   - §4 de ~11 páginas a ~3–4: por qué no había API, qué se automatizó, cómo se
     garantizó que no se perdieran datos (checkpoints) y cómo se unieron los archivos.
     Tabla de barreras solo con problema y solución conceptual.
   - El detalle técnico va al repositorio (o a un Apêndice corto).
2. Tabla de eventos por tipo con total al pie: usarla para los desenlaces
   (default / cura / censura).
3. Sección propia de "Pré-processamento dos dados", sistemática y reproducible (script,
   versión de Python y bibliotecas): describir ahí `reconstruir_dataset.py` y sus reglas.
   Responde al pedido de la tutora sobre datos ausentes o inconsistentes.

4. **Ventanas temporales explicadas en lenguaje simple** (ej.: ventanas antes/después del
   evento, "respeitando a cronologia dos dados"). En nuestro caso: explicar los bloques
   de 10 días y decir explícitamente que cada covariable usa solo información disponible
   al inicio del bloque (prevención de leakage), que es una de las correcciones de la
   reconstrucción.
5. **Conjuntos de atributos con nombre** (orig, orig_stats…, mega_full) para comparar
   modelos. Aplicarlo en el Sprint 6 como estudio de ablación: (A) comportamiento de
   pago; (B) A + contexto macro y festivos; (C) B + región/socioeconómico. Comparar
   C-index/Brier por conjunto muestra cuánto aporta cada fuente de información.
6. El ejemplo balancea clases al construir las ventanas. Nosotros tenemos 0,71% de
   default: justificar el tratamiento del desbalance (ya previsto para DeepHit).

7. **Tablas autoexplicativas.** El profesor dijo que la tabla de instancias por tipo de
   evento y fuente (reales/simuladas/desenhadas) no le quedó clara. Regla para la V26:
   cada tabla debe (a) decir la unidad (crédito, cliente o intervalo), (b) definir cada
   categoría en el texto o en una nota al pie de la tabla, y (c) ir seguida de un
   párrafo que diga qué conclusión sacar de ella y cómo afecta al análisis.
   Caso crítico nuestro: la tabla de desenlaces por motivo. "Cura por cierre del
   sistema" (435 créditos cuyo abono final se completa con la FECHA ÚLTIMO ABONO) es el
   equivalente a datos "no observados directamente" y hay que explicarlo con claridad,
   igual que los 255 créditos excluidos.

9. **Diagrama del flujo metodológico** (el profesor mostró uno: pré-processamento →
   extração/ETL → processamento → modelagem). Borrador hecho:
   `src/fig_fluxo_metodologico.py` → `reports/fig00_fluxo_metodologico.png` (6 etapas en
   3 grupos). Va al inicio de la metodología en la V26, antes de la §4; al insertarlo
   se renumeran las figuras.
10. **¿Por qué bloques de 10 días?** Origen: ATLAS solo permitía descargar ventanas de
    10 días. Tras la reconstrucción, los bloques se arman desde el desembolso con pagos
    diarios y el evento se fecha al día exacto: el largo del bloque solo define cada
    cuánto se actualizan las covariables. Argumento a favor de **7 días**: el cobro es
    lunes a sábado; un bloque de 7 días siempre tiene 6 días de cobro, uno de 10 tiene
    8 o 9 según los domingos (exposición variable); plazos de 20/24 días ≈ 3–4 semanas.
    Tamaño: ~94 mil intervalos con 10 días, ~134 mil con 7 (manejable).
    **Decisión (29/09/2026, Juan): 7 días como bloque principal**, pero igual se compara
    con 10 días en el Sprint 4 (constante `DIAS_BLOQUE`) y se reporta en el TCC como
    análisis de sensibilidad.
    Quitar de la V26 la analogía con el teorema de muestreo (débil).
11. **Diccionario de variables con unidad** (el ejemplo tiene "Nome | Descrição |
    Unidade"). En la V26: una sola tabla con todas las variables del dataset
    reconstruido (nombre en el código, descripción en portugués, unidad: dias, R$,
    proporção 0–1, contagem) y si es estática o tempo-variante. Hoy las Tablas 11 y 12
    dan fórmula pero no unidad, mezclan nombres en español y aún listan variables de la
    V25 que ya no existen (p. ej. intensidad del día de la descarga).
12. **"Construção de variáveis" con notación formal y nombres sistemáticos** (ejemplo:
    ventana X ∈ ℝ^{T×D}, valor x_{t,j}; modos de atributos incrementales Instante,
    Básico, Forma, Dinâmico…; nombres `<Sensor>_<estatística>` pensados para SHAP).
    Aplicación en la V26:
    - Notación: crédito i, pago diario y_i(d), intervalo k = (s_k, s_k + 7], vector de
      covariables x_i(s_k) calculado solo con la historia hasta s_k (deja formalizada la
      prevención de leakage).
    - Nombres en portugués con patrón `<fonte>_<medida>_<janela>`: p. ej.
      `pag_media_7d`, `pag_dias_7d`, `pag_cv_7d`, `saldo_rel`, `atraso_cotas`,
      `silencio_dias`, `macro_selic`, `reg_ddd`, `cal_feriados_7d`. Hoy el código usa
      nombres en español (`dias_sin_pagar`, `pago_promedio_diario_prev`).
    - Grupos incrementales = conjuntos A/B/C del punto 5.
    - Explicabilidad: hazard ratios en el Cox y SHAP para supervivencia (p. ej.
      SurvSHAP(t)) en el DeepHit, con los mismos nombres de variables.
13. **Tabla resumen de los modos de construcción de variables** (Modo | Qtd. |
    Principais estatísticas | Objetivo). Versión adaptada a la serie de pagos diarios
    (ventana = bloque de 7 días y/o últimas 4 semanas), cada grupo con su objetivo de
    negocio:

    | Modo | Estadísticas | Objetivo |
    |---|---|---|
    | Estado | días de silencio, saldo relativo, cuotas atrasadas al inicio del bloque | dónde está el crédito hoy |
    | Básico | media, desvío, mín., máx. del abono diario; días con abono / días de cobro | nivel y regularidad del pago |
    | Parcialidad | abono / valor de la cuota (media, % de abonos parciales) | si paga la cuota completa o en abonos pequeños |
    | Tendencia | EMA de abonos (α = 0,1 y 0,3), pendiente en 4 semanas | deterioro o recuperación reciente |
    | Estrés | mayor racha sin pagar, % de días de cobro sin abono, máximo déficit acumulado frente al cronograma (análogo al *max drawdown*) | señales tempranas de volarse |
    | Contexto | feriados en el bloque, Selic/IPCA, región (DDD) | efectos externos al cliente |

    **Cuidado:** con 202 defaults, el Cox debe ser parsimonioso (regla de ~10 eventos por
    variable → como máximo ~20 variables). Los conjuntos ricos van al DeepHit con
    regularización; el Cox usa un subconjunto justificado.
14. **Sección "Algoritmos" con una subsección por modelo** (ejemplo: 10 clasificadores;
    cada uno con descripción + referencia, ventajas/limitaciones y **espacio de búsqueda
    de hiperparámetros** en lista; Grid Search con validación cruzada estratificada
    k = 10; métrica principal Recall, justificada por el dominio). Aplicación:
    - Modelos a describir así: regresión logística (credit scoring binario de
      referencia), Cox cause-specific, **Random Survival Forest** (lo sugirió Vicente;
      barato con scikit-survival) y DeepHit.
    - Espacios de búsqueda, p. ej. Cox: `penalizer` ∈ {0; 0,01; 0,1}, `l1_ratio` ∈
      {0; 0,5; 1}; RSF: `n_estimators`, `min_samples_leaf`, `max_features`; DeepHit:
      capas, neuronas, dropout, α, σ, tasa de aprendizaje, tamaño de lote.
    - **Diferencia clave con el ejemplo:** no sirve la validación cruzada aleatoria
      estratificada. Un cliente tiene varios créditos y los datos son temporales →
      validación **agrupada por cliente** (GroupKFold) y un corte **fuera del periodo**
      (entrenar hasta una fecha, probar después). Explicarlo como prevención de
      leakage.
    - Métrica principal justificada por el negocio: C-index dependiente del tiempo y
      Brier (IPCW) + una métrica operativa, p. ej. % de los volados de los próximos
      30 días que quedan en el 10% de mayor riesgo (costo asimétrico: perder capital
      pesa más que dejar de prestar).
    - Formato observado (Logistic Regression, SVC, AdaBoost…): párrafo de 3–4 líneas por
      modelo (qué hace, cita, una ventaja, una limitación) + 3 hiperparámetros en
      viñetas. Nosotros: menos modelos (4) pero cada limitación conectada a nuestro
      problema (censura, riesgos competitivos, pocos eventos, interpretabilidad).
15. **Tabla consolidada "Algoritmo | Valores do Grid Search"** — el profesor la
    **recomienda explícitamente**. Borrador para nuestros modelos (agregar una columna
    "Valor escolhido" después del ajuste):

    | Algoritmo | Valores da busca |
    |---|---|
    | Regressão logística | penalty = {l1, l2}; C = {0,01; 0,1; 1}; class_weight = {None, balanced} |
    | Cox cause-specific (lifelines) | penalizer = {0; 0,01; 0,1}; l1_ratio = {0; 0,5; 1} |
    | Random Survival Forest (scikit-survival) | n_estimators = {200, 500}; min_samples_leaf = {10, 30, 50}; max_features = {sqrt, 0,3}; max_depth = {None, 10} |
    | DeepHit (pycox) | camadas = {[32,32], [64,64]}; dropout = {0,1; 0,3}; α = {0,2; 0,5}; σ = {0,1; 0,5}; lr = {1e-3, 1e-4}; batch = {256, 1024} |

    Ojo: RSF, DeepHit y la logística no aceptan covariables tempo-variantes en formato
    Counting Process. Para compararlos con el Cox se usa **landmarking**: en cada punto de
    referencia (p. ej. semanas 1, 2, 3, 4 del crédito) se toma la foto de las covariables
    hasta ese momento y se predice el desenlace en el horizonte siguiente.
16. **Interpretabilidad como argumento de adopción** (el ejemplo justifica el Decision
    Tree porque facilita la aceptación del modelo por los ingenieros de proceso).
    Equivalente nuestro: que el gestor de cartera y el cobrador entiendan por qué un
    cliente es de alto riesgo. Refuerzo legal: la **LGPD (art. 20)** da derecho a pedir
    revisión de decisiones tomadas solo por tratamiento automatizado, incluido el perfil
    de crédito → la explicabilidad no es opcional. Opción: un **árbol de supervivencia**
    simple (scikit-survival `SurvivalTree`, poca profundidad) como modelo de reglas
    legibles ("más de X días sin pagar y abonos parciales → alto riesgo"), junto a los
    hazard ratios del Cox y SHAP del DeepHit.
17. **Normalización dentro de cada fold** (z-score con media y desvío estimados solo
    en el entrenamiento, con fórmula, para evitar *data leakage*). Aplicar igual: el
    escalador se ajusta en el entrenamiento de cada partición (por cliente / por tiempo)
    y solo se aplica al teste. **Verificar en el Sprint 4** si `modelagem_riscos_competitivos.py`
    estandariza con el dataset completo antes de separar.
18. **SMOTE (opcional en el ejemplo, solo en el treino de cada fold).** En nuestro caso
    **justificar por qué no se usa**: en supervivencia, un caso sintético necesita un
    tiempo, un tipo de desenlace y una trayectoria de intervalos coherentes, y la
    interpolación de SMOTE rompe esa estructura (y la del Counting Process). Además,
    la verosimilitud parcial del Cox compara cada evento con su conjunto de riesgo,
    así que el desbalance no la sesga como a un clasificador. Alternativas: pesos por
    clase en la pérdida del DeepHit y muestreo estratificado de lotes (ya previstos).
19. **Optimización interna de hiperparámetros (validación anidada)** con fórmula:
    θ* = argmax_{θ∈Θ} (1/K) Σ_m métrica^(m)(θ); luego se reajusta con todo el treino del
    fold y se evalúa en el teste. Nuestra versión:
    - Externo: corte temporal (treino hasta una fecha, teste después) y/o GroupKFold
      por cliente.
    - Interno: GroupKFold por cliente dentro del treino (K = 5).
    - θ* = argmax (1/5) Σ_m C_td^(m)(θ) (C-index dependiente del tiempo); desempate por
      menor Brier integrado.
    - **Detalle observado en el ejemplo:** el texto dice k = 5 pero la sumatoria va de
      m = 1 a 3. Lección: revisar que cada fórmula coincida con el texto.
20. **Cada métrica con fórmula + ventaja + limitación** (el ejemplo lo hace con F1 y
    AUC, y advierte que la AUC puede salir alta solo por la gran cantidad de verdaderos
    negativos en datos desbalanceados). Nuestra sección de métricas:
    - **C-index de Harrell**: fórmula de pares concordantes; ventaja: intuitivo;
      limitación: depende de la censura y no mide calibración.
    - **C de Uno / AUC(t) dependiente del tiempo** (ponderado por IPCW): corrige la
      censura; se reporta en horizontes de negocio (p. ej. 30, 60, 120 días).
    - **Brier(t) e Brier integrado (IPCW), sobre la CIF de default**: mide calibración;
      limitación: depende del modelo de censura.
    - **Advertencia equivalente a la del ejemplo:** con 0,71% de default, C-index y AUC
      pueden verse altos por la masa de créditos que nunca se vuelan → complementar con
      una métrica centrada en los eventos: precisión/recall en el horizonte y % de
      volados capturados en el 10% de mayor riesgo (punto 14).
21. **Sección propia de "Técnica de interpretabilidade"** (3.7 en el ejemplo), separada
    de las métricas. Contenido nuestro: hazard ratios del Cox, SHAP para supervivencia
    en el DeepHit y árbol de supervivencia de reglas (puntos 12 y 16).
22. **Figura didáctica de SHAP** ("Visão geral da metodologia": entradas → modelo caja
    negra → explicación con barras + / −, "Fonte: adaptado de shap.readthedocs.io").
    Hacer nuestra propia versión con un crédito de ejemplo: días sin pagar = 12,
    abonos parciales = 60%, saldo = 45%, región = SC → modelo → riesgo de volarse en
    30 días = 0,18 → barras de contribución. Citar Lundberg e Lee (2017). Resultados de
    SHAP en gráficos beeswarm y de barras.
23. **ABNT: toda figura y tabla lleva "Fonte:" debajo** (el ejemplo lo hace). **La V26
    no tiene ninguna línea de Fonte** → agregar en `add_figure` y `add_table_data`
    ("Fonte: elaborado pelo autor (2026)" o la fuente real, p. ej. "Fonte: dados da
    pesquisa").
24. **Capítulo de Experimentos/Resultados**: abre diciendo que todo se implementó en
    Python para reproducibilidad, **da el link del repositorio** (código, gráficos y
    artefactos) y anuncia cómo se organizan las secciones de resultados (4.1 análisis
    de medias entre modos de representación, 4.2 ganancia…). Nuestra versión:
    4.1 desenlaces y EDA del dataset reconstruido, 4.2 Cox cause-specific,
    4.3 comparación de modelos (landmarking), 4.4 conjuntos de atributos A/B/C,
    4.5 interpretabilidad, 4.6 análisis socioeconómico y regional.
25. **El profesor aclaró que el TCC de ejemplo tiene puntos de mejora** (no es un modelo
    a copiar al pie de la letra). Detectados hasta ahora: tabla de instancias poco clara
    (punto 7), k = 5 en el texto contra sumatoria hasta 3 (punto 19). En la sección de
    SHAP (pág. 52–53): **el título de la Figura 4 dice "Visão geral da metodologia
    proposta" pero la figura muestra un ejemplo de SHAP** (título que no corresponde al
    contenido) y hay un error de tipeo ("pode meio" en lugar de "por meio"). Lecciones:
    el título de cada figura describe exactamente lo que muestra; revisión ortográfica
    final completa. *(Completar con los que mencione el profesor.)*
    Para nuestro SHAP: la fórmula del valor de Shapley es la misma, pero en supervivencia
    se explica el riesgo en un horizonte (p. ej. P(volarse en 30 días)) o se usa
    SurvSHAP(t), no la salida de un clasificador.
8. *(Observación propia, no de la clase.)* Ejemplo concreto en la V25 (pág. 21, §4.3): dos bloques de código (datepicker y
   "filtro anti-zero") + detalle de `.crdownload`. Se reemplaza por un párrafo
   conceptual (borrador en la conversación del 29/09). **Corregir además la
   justificación del filtro anti-zero:** decía que evitaba falsos defaults en
   `dias_sem_pagar`, pero con la reconstrucción el silencio se mide entre fechas reales
   de abono; su papel ahora es solo evitar archivos vacíos.

### Preguntas pendientes para el próximo plantão o para el orientador (Vicente)

La clase del 29/09 terminó antes de poder hacerlas. En orden de prioridad:

1. **Correção dos dados** (la más importante): "Na auditoria encontrei erros de
   rotulagem do evento e os números mudaram bastante em relação à versão entregue (de
   273 para 202 eventos). Onde apresentar essa correção: na metodologia, como etapa de
   pré-processamento, ou nos resultados e limitações?"
2. **Código e dados confidenciais**: "Meus dados são de uma instituição financeira e
   estão sob LGPD. Posso citar um repositório público só com o código, sem dados, ou é
   melhor deixar o código em um apêndice?"
3. **Comparação justa entre modelos**: "Uso Cox com covariáveis tempo-variantes e quero
   comparar com Random Survival Forest e DeepHit, que não aceitam esse formato. Usar
   landmarking para comparar todos no mesmo esquema é aceitável?"
4. **Métricas com desbalanceamento (0,7%)**: "Além do C-index e do Brier, vocês esperam
   uma métrica de negócio, como a proporção de inadimplentes capturados no top 10% de
   risco?"
5. **Classe social**: "Não tenho renda dos clientes. Usar a renda média do setor
   censitário do IBGE a partir do endereço como proxy de classe social é aceitável?"

## 6b. Fuentes que Juan debe verificar/descargar (para la Introdução)

| Dato | Dónde buscar | Qué traer |
|---|---|---|
| Empresas activas y MEI | gov.br, buscar "Mapa de Empresas" (Ministério do Empreendedorismo, da Microempresa e da Empresa de Pequeno Porte) → boletín más reciente | total de empresas activas, total de MEI, periodo y fecha del boletín, PDF |
| Acceso a crédito de pequeños negocios | sebrae.com.br o datasebrae.com.br, buscar "Financiamento dos Pequenos Negócios 2025" | % que pidió crédito y lo obtuvo, principales obstáculos, año, PDF |
| (Opcional) Morosidad de empresas | serasaexperian.com.br, "Indicador de Inadimplência das Empresas" | n.º de MPE en mora y fecha |

**Confirmado por Juan en el painel oficial (16/10/2026):** 25.418.820 empresas activas y
13.581.677 MEI activos, datos del CNPJ actualizados hasta julio/2026. Fuente:
https://www.gov.br/empresas-e-negocios/pt-br/mapa-de-empresas/painel-mapa-de-empresas
(acceso 16 out. 2026). Painel de Sócios con filtro MEI: 55,1% hombres y 44,9% mujeres.

**Confirmado por Juan (16/10/2026), Agência Sebrae, 15/09/2026** (Carlos Abreu, "Inadimplência
de pequenos negócios cai, e aprovação de crédito atinge maior nível desde 2022", 13ª ed.
Pulso dos Pequenos Negócios): pequenos negócios con deudas en atraso 28% (1º tri) → 25%
(julio/2026); 46% de los que buscaron crédito en los últimos 3 meses fueron aprobados (máximo
de la serie iniciada en 2022). URL:
https://agenciasebrae.com.br/dados/inadimplencia-de-pequenos-negocios-cai-e-aprovacao-de-credito-atinge-maior-nivel-desde-2022/
Ya no hace falta Serasa ni IBGE informalidad en la introducción.

Borrador provisorio anterior con cifras de prensa: 24,2 mi empresas activas y 12,6 mi MEI
(2º quadrimestre 2025); 48% obtuvo crédito en 2025 (Sebrae). Confirmar en la fuente oficial.

## 7. Preguntas abiertas para la operación

1. ¿Quién es "JHONJA G"? (registra parte de los abonos de limpieza)
2. ¿Cómo se registran los clientes de dos veces por semana?
3. ¿La ficha del cliente en ATLAS tiene edad, sexo, actividad o ingreso?
4. Confirmar ciudad de COSTEÑO, CRUZ y BILLY (ver tabla 1).
