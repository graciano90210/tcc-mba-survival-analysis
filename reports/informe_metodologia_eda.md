# Ingeniería de Características y Análisis Exploratorio del Dataset de Supervivencia  
**TCC — Análisis de Riesgo de Crédito por Análisis de Supervivencia**  
**Juan Fernando Graciano Pinzón — MBA Data Science ICMC/USP**

---

## 4. METODOLOGÍA: DEL PANEL DE DATOS AL DATASET DE SUPERVIVENCIA

### 4.1 Fundamentos Teóricos del Análisis de Supervivencia

El análisis de supervivencia comprende un conjunto de técnicas estadísticas diseñadas para modelar el tiempo hasta la ocurrencia de un evento de interés (Kalbfleisch & Prentice, 2002). A diferencia de la regresión logística — que estima la probabilidad de default en un punto fijo del tiempo —, el análisis de supervivencia incorpora explícitamente la dimensión temporal, distinguiendo entre individuos que experimentaron el evento y aquellos que fueron observados sin experimentarlo (censurados).

#### 4.1.1 Función de Supervivencia y Función de Riesgo

Sean las definiciones fundamentales para una variable aleatoria continua no negativa *T* que representa el tiempo hasta el evento:

**Función de supervivencia:**

$$S(t) = P(T > t) = 1 - F(t)$$

donde *F(t)* es la función de distribución acumulada de *T*. *S(t)* representa la probabilidad de que el individuo no haya experimentado el evento hasta el tiempo *t*.

**Función de densidad de probabilidad condicional (hazard):**

$$h(t) = \lim_{\Delta t \to 0} \frac{P(t \leq T < t + \Delta t \mid T \geq t)}{\Delta t} = \frac{f(t)}{S(t)}$$

La función de riesgo *h(t)* — también denominada tasa de fallo instantánea — mide la tasa condicional de ocurrencia del evento en el instante *t*, dado que el individuo sobrevivió hasta ese momento. Es el componente central del modelo de regresión de Cox.

**Relación fundamental:**

$$S(t) = \exp\left(-\int_0^t h(u) \, du\right) = \exp(-H(t))$$

donde *H(t)* es la función de riesgo acumulado (*cumulative hazard function*). Esta relación muestra que la función de supervivencia queda completamente determinada por la función de riesgo.

#### 4.1.2 Tipos de Censura

Un aspecto crítico del análisis de supervivencia es el tratamiento de observaciones en las que el evento no se observa dentro del período de estudio:

- **Censura a la derecha (right censoring):** El evento no ocurrió antes del fin de la observación. Es el tipo más común y el que aplica a los créditos activos al corte del estudio (15 de mayo de 2026).
- **Truncación por la izquierda (left truncation):** El individuo entra al estudio en un momento posterior al origen de riesgo. En el presente trabajo, ocurre cuando el primer snapshot disponible de un crédito corresponde a una fecha posterior a su fecha de desembolso.

El tratamiento correcto de ambos fenómenos — implementado mediante el formato Counting Process — es condición necesaria para la validez estadística del modelo de Cox (Therneau & Grambsch, 2000).

#### 4.1.3 Estimador de Kaplan-Meier

El estimador de Kaplan-Meier (Kaplan & Meier, 1958) es el estimador no paramétrico estándar de la función de supervivencia. Sea *t₁ < t₂ < ... < tₖ* el conjunto de tiempos distintos en que ocurrieron eventos. En cada tiempo de evento *tⱼ*, sean *dⱼ* el número de eventos y *nⱼ* el número de individuos en riesgo. El estimador es:

$$\hat{S}(t) = \prod_{j: t_j \leq t} \left(1 - \frac{d_j}{n_j}\right)$$

Sus propiedades principales son:
- **Consistencia:** converge en probabilidad a *S(t)* verdadera cuando *n → ∞*.
- **No paramétrico:** no asume ninguna distribución para *T*.
- **Corrección automática por censura:** los individuos censurados contribuyen al denominador *nⱼ* hasta el momento de su censura, pero no al numerador *dⱼ*.

El intervalo de confianza se obtiene mediante la transformación de Greenwood:

$$\text{Var}[\hat{S}(t)] = \hat{S}(t)^2 \sum_{j: t_j \leq t} \frac{d_j}{n_j(n_j - d_j)}$$

#### 4.1.4 Prueba de Log-Rank

La prueba de log-rank (Mantel, 1966) compara las curvas de supervivencia de dos o más grupos sin asumir una forma paramétrica. La hipótesis nula es *H₀: S₁(t) = S₂(t) ∀t*. El estadístico es:

$$Q = \frac{\left(\sum_j w_j (d_{1j} - e_{1j})\right)^2}{\sum_j w_j^2 \frac{n_{1j} n_{2j} d_j (n_j - d_j)}{n_j^2 (n_j-1)}}$$

donde *e₁ⱼ = n₁ⱼ dⱼ / nⱼ* es el número esperado de eventos bajo *H₀* y *wⱼ = 1* (log-rank estándar). Bajo *H₀*, *Q* sigue una distribución χ² con (k-1) grados de libertad.

#### 4.1.5 Representación en Proceso de Conteo (Anderson-Gill)

El modelo clásico de Cox asume covariables fijas en el tiempo. Cuando las covariables cambian a lo largo del seguimiento — como el saldo deudor, el número de cuotas atrasadas o los días sin pagar — es necesario adoptar el marco del Proceso de Conteo de Anderson-Gill (Anderson & Gill, 1982).

En lugar de una única observación por individuo *(T, δ, **X**)*, el individuo *i* es representado mediante una secuencia de intervalos:

$$(t_{start,1}, t_{stop,1}, \delta_1, \mathbf{X}_{i1}), \quad (t_{start,2}, t_{stop,2}, \delta_2, \mathbf{X}_{i2}), \quad \ldots$$

Las restricciones del formato son:

1. Los intervalos deben ser **contiguos** y **no solapados**: *t_start[k] = t_stop[k-1]* exactamente.
2. El evento *δ = 1* solo puede ocurrir en el **último intervalo** de cada individuo.
3. Los intervalos deben ser **abiertos por la izquierda y cerrados por la derecha**: *(t_start, t_stop]*.

Este formato — implementado en `lifelines.CoxTimeVaryingFitter` y en los modelos de supervivencia neuronal de `pycox` — permite que las covariables varíen en cada snapshot de observación, capturando dinámicas de riesgo que modelos estáticos no pueden detectar.

---

### 4.2 Construcción del Dataset de Supervivencia

#### 4.2.1 Fuente de Datos: Sistema ATLAS

El Sistema ATLAS es la plataforma de gestión crediticia de la entidad. Los datos brutos fueron extraídos mediante un pipeline ETL automatizado con Selenium WebDriver, descargando informes Excel (*Planilla de Abonos*) para cada combinación de oficina y ruta en bloques de 10 días calendarios.

El **Data Lake** resultante comprende:

| Componente | Volumen |
|---|---|
| Archivos Excel descargados | 3,962 archivos |
| Oficinas cubiertas | 3 (OFI_23 São Paulo, OFI_31 Soc. Brasil, OFI_44 Cabo Frio) |
| Rutas cubiertas | 17 |
| Período de cobertura | 2020-01-01 → 2026-05-15 |
| Tamaño del Data Lake (bruto) | ~14 GB |

Tras el proceso de consolidación (*Data Stitching*), la **Matriz Maestra** resultante tiene las siguientes dimensiones:

| Métrica | Valor |
|---|---|
| Filas (observaciones) | 344,869 |
| Columnas totales | 2,358 |
| Columnas de pagos diarios | ~2,330 |
| Columnas estáticas del crédito | 28 |
| Tamaño en disco | 882 MB |
| Tamaño en RAM (expandido) | ~6 GB |

La escala del dataset imposibilita su carga completa en memoria. Por esta razón, el pipeline de ingeniería de características implementa **lectura por chunks de 5,000 filas** con máscara vectorizada NumPy **(n_filas × n_columnas_pago)** para calcular los agregados de pago al vuelo sin materializar las ~2,330 columnas de fecha en RAM.

#### 4.2.2 Filtro de Cohorte Diaria

El portafolio de la entidad contiene créditos con frecuencias de pago heterogéneas: diaria, semanal, quincenal y mensual. Para garantizar la homogeneidad del grupo bajo análisis y la correcta interpretación del cronómetro de inactividad, se aplica el siguiente criterio de inclusión:

**Créditos de pago diario:** aquellos cuyo número de cuotas pactadas (*CUOTAS_PACTADAS*) es ≤ 40.

La justificación operativa es que, en la entidad estudiada, los créditos con más de 40 cuotas son de modalidad semanal (52 semanas/año ≈ 208 días de seguimiento para 4 meses) o quincenal, y sus patrones de mora no son directamente comparables con los créditos diarios.

| Cohorte | Criterio | Créditos |
|---|---|---|
| Diaria (incluida) | CUOTAS_PACTADAS ≤ 40 | 28,386 |
| Semanal/quincenal/mensual (excluida) | CUOTAS_PACTADAS > 40 | — |

#### 4.2.3 Definición Operacional del Evento de Default

La definición del evento de incumplimiento requirió una revisión crítica del indicador disponible en el sistema.

**Por qué NO se usó CUOTAS_ATRASADAS ≥ 120:**

La variable *CUOTAS_ATRASADAS* registra el número de cuotas diarias que el cliente tiene pendientes de pago en la fecha del snapshot. Para un crédito con plazo de 20 días, el máximo teórico de *CUOTAS_ATRASADAS* es exactamente 20. Para un crédito de 40 días, el máximo es 40. Por lo tanto, el umbral de 120 cuotas atrasadas es **operacionalmente imposible** para cualquier crédito de la cohorte diaria, lo que produciría exactamente cero eventos y haría el análisis de supervivencia inviable.

**Definición adoptada: castigo de cartera operativo:**

$$E_i = \mathbf{1}\left[\text{dias\_sin\_pagar}_{it} \geq 120\right]$$

Esta definición captura el concepto de **castigo de cartera** (*write-off*) utilizado operativamente por la entidad: un crédito es declarado en default cuando transcurren 120 días calendario sin que el cliente realice ningún abono. Este umbral equivale a 4 meses de inactividad financiera total, considerando que los créditos tienen plazos de 20 a 40 días y se renuevan periódicamente.

La distinción conceptual central es entre:
- **Mora transitoria:** el cliente atrasa algunos días pero retoma los pagos. El cronómetro se reinicia con cada abono.
- **Abandono real:** el cliente cesa completamente los pagos por más de 4 meses, evidenciando incapacidad o voluntad nula de pago.

#### 4.2.4 Cronómetro de Inactividad Financiera

El cálculo de *dias_sin_pagar* sigue una lógica de **forward-fill** sobre la fecha del último pago efectivo:

```
Para cada crédito i, ordenado por fecha_ini_bloque:
  1. Inicializar: fecha_ultimo_pago_efectivo = FECHA_CRÉDITO
  2. Para cada bloque (snapshot) t:
     - Si dias_con_abono > 0: actualizar fecha_ultimo_pago_efectivo = fecha_fin_bloque
     - Si dias_con_abono = 0: mantener fecha_ultimo_pago_efectivo del bloque anterior
  3. dias_sin_pagar[t] = (fecha_fin_bloque - fecha_ultimo_pago_efectivo).days
```

Esta lógica tiene las siguientes propiedades:
- **Semilla correcta:** el crédito arranca con *dias_sin_pagar = 0* en la fecha de desembolso.
- **Reinicio automático:** cualquier abono — aunque sea mínimo — reinicia el cronómetro a cero.
- **Acumulación continua:** la inactividad se acumula a lo largo de múltiples bloques consecutivos sin pago.
- **Clipeo inferior:** *dias_sin_pagar* se define como *max(0, días calculados)* para evitar valores negativos por desincronización de fechas.

#### 4.2.5 Correcciones del Formato Counting Process

**Corrección de Left Truncation:**

Un crédito puede estar activo en el primer snapshot disponible pero haber sido desembolsado antes del inicio de ese bloque. Sin corrección, el intervalo inicial tendría *t_start* negativo. La corrección aplicada es:

$$t_{start,\text{primera fila}} = \max\left(0, \; \text{fecha\_ini\_bloque} - \text{FECHA\_CRÉDITO}\right)_{\text{días}}$$

**Corrección de continuidad (shift):**

Para garantizar la cadena perfecta *t_start[k] = t_stop[k-1]* que el modelo de Cox exige, el *t_start* de cada intervalo se hereda del *t_stop* del intervalo anterior mediante un desplazamiento (`shift(1)`). Solo la primera fila de cada crédito usa la corrección de left truncation. El *t_stop* siempre proviene del nombre del archivo Excel (fecha de fin del bloque de 10 días):

$$t_{stop,t} = \left(\text{fecha\_fin\_bloque}_t - \text{FECHA\_CRÉDITO}\right)_{\text{días}} + 1$$
$$t_{start,t} = t_{stop,t-1} \quad \text{para } t > 1$$

Esta implementación elimina los *gaps* de 1 día que de otra forma aparecerían entre bloques consecutivos y que el algoritmo de Cox interpretaría como intervalos de observación faltante.

**Regla de censura:**

Tras la ocurrencia del evento (*dias_sin_pagar ≥ 120*), la trayectoria del crédito se trunca: los snapshots posteriores al evento son eliminados. Esta regla garantiza que el evento de default sea el **último intervalo observado** de cada crédito, respetando la condición de absorción del modelo de supervivencia.

#### 4.2.6 Variables Covariadas

El dataset final contiene las siguientes variables:

**Variables de tiempo y evento:**

| Variable | Tipo | Descripción |
|---|---|---|
| `t_start` | Continua | Inicio del intervalo (días desde desembolso) |
| `t_stop` | Continua | Fin del intervalo (días desde desembolso) |
| `evento` | Binaria | 1 = default (dias_sin_pagar ≥ 120), 0 = censura |
| `dias_sin_pagar` | Discreta | Cronómetro de inactividad financiera |

**Covariables tiempo-variantes (varían en cada snapshot):**

| Variable | Fórmula | Interpretación |
|---|---|---|
| `cuotas_atrasadas` | CUOTAS_ATRASADAS | Días en mora en el snapshot |
| `pago_promedio_diario` | Σ(pagos_bloque) / días_bloque | Flujo de pagos diario promedio (BRL) |
| `dias_con_abono` | #{días con abono > 0} en el bloque | Frecuencia de pago en el período |
| `intensidad_recuperacion` | VALOR_ÚLTIMO_ABONO / VALOR_CUOTA | Qué fracción de la cuota pagó el cliente (clip [0, 10]) |
| `ratio_atraso` | CUOTAS_ATRASADAS / CUOTAS_PACTADAS | Fracción del plazo en mora (clip [0, 1]) |
| `saldo_relativo` | SALDO / TOTAL_CRÉDITO | Fracción del crédito pendiente de pago (clip [0, 1]) |

**Covariables estáticas (replicadas en cada fila del crédito):**

| Variable | Descripción |
|---|---|
| `total_credito` | Monto original del crédito (BRL) |
| `valor_cuota` | Valor de la cuota diaria pactada (BRL) |
| `cuotas_pactadas` | Plazo del crédito en días |
| `ofi_id` | Identificador de oficina (proxy geográfico) |
| `rta_id` | Identificador de ruta (proxy de zona/cobrador) |

---

### 4.3 Análisis Exploratorio de Datos (EDA)

El análisis exploratorio se desarrolló en el notebook `notebooks/01_eda_survival.ipynb`, generando nueve figuras de diagnóstico que se documentan a continuación.

#### 4.3.1 Caracterización General del Dataset

| Métrica | Valor |
|---|---|
| Créditos únicos | 28,386 |
| Intervalos totales (filas) | 301,434 |
| Eventos (E=1) | 425 |
| Tasa de default (nivel crédito) | **1.50%** |
| Créditos censurados (E=0) | 27,961 (98.50%) |
| Oficinas | 3 |
| Rutas | 17 |
| Período de observación | 2020-01-01 → 2026-05-15 (~6.4 años) |

El **bajo índice de default (1.50%)** refleja la dinámica operativa del microcréditode pago diario: la entidad realiza gestión de cobro intensiva a través del cobrador de ruta (*gestora*), reduciendo significativamente la incidencia de abandono total. La mayoría de los incumplimientos son de carácter transitorio y se resuelven antes de alcanzar los 120 días de inactividad.

#### 4.3.2 Distribución del Evento de Default

**Por oficina:**

| Oficina | Créditos | Eventos | Tasa de Default |
|---|---|---|---|
| OFI_23 (São Paulo) | 14,031 | 126 | **0.90%** |
| OFI_31 (Soc. Brasil) | 7,333 | 53 | **0.72%** |
| OFI_44 (Cabo Frio) | 7,022 | 246 | **3.50%** |

La oficina OFI_44 (Cabo Frio) presenta una tasa de default casi **cuatro veces superior** a las demás oficinas (3.50% vs. 0.72–0.90%). Esta heterogeneidad geográfica es estadísticamente relevante para el modelo de Cox: `ofi_id` y `rta_id` actúan como variables proxy del contexto socioeconómico local, la intensidad de supervisión del cobrador y la composición del portafolio de clientes.

La distribución de la tasa de default por ruta (fig01) revela heterogeneidad adicional: algunas rutas dentro de OFI_44 concentran la mayoría de los eventos, sugiriendo que el riesgo es fuertemente localizado a nivel de cobrador/zona de cobranza.

*(Ver Figura 1: Distribución del evento — Pie, tasa por oficina, tasa por ruta)*

#### 4.3.3 Curva de Kaplan-Meier Global

La curva de Kaplan-Meier global exhibe un patrón altamente informativo sobre la dinámica de riesgo del portafolio:

| Tiempo (días) | S(t) | Riesgo Acumulado |
|---|---|---|
| 30 | 1.0000 | 0.00% |
| 60 | 1.0000 | 0.00% |
| 90 | 1.0000 | 0.00% |
| 120 | 1.0000 | 0.00% |
| 180 | 0.6815 | **31.85%** |
| 270 | 0.6788 | 32.12% |
| 365 | 0.1673 | **83.27%** |
| 540 | 0.0908 | 90.92% |

**Interpretación del patrón:**

Los cuatro primeros puntos de la curva — todos con S(t) = 1.0 — no implican que no existan defaults antes del día 120. Implican que, entre los créditos que **sobreviven más allá de esos plazos**, ninguno ha experimentado el evento todavía. Esto es consistente con la definición del evento: *dias_sin_pagar ≥ 120* es imposible antes de que el crédito tenga al menos ~120 días de antigüedad.

El salto brusco entre el día 120 y el día 180 — de S = 1.0 a S = 0.68 — refleja que los créditos que alcanzan los 120-180 días de antigüedad tienen un perfil de riesgo radicalmente diferente al de la mayoría: son créditos que **persistieron mucho más allá de su plazo original** (20-40 días), evidenciando que permanecen en el portafolio por renovaciones sucesivas o por incapacidad de cierre. Para el día 365, el 83.3% de los créditos que alcanzaron ese horizonte temporal han experimentado el evento de castigo.

Esta estructura temporal — riesgo nulo en el corto plazo, riesgo elevado en horizontes largos — caracteriza a los microcreditos de pago diario: el riesgo de default no se distribuye uniformemente en el tiempo sino que se concentra en créditos de larga permanencia.

*(Ver Figura 2: Curva de Kaplan-Meier global con tabla de n en riesgo)*

#### 4.3.4 Análisis Estratificado por Oficina (Log-Rank Test)

Las curvas de Kaplan-Meier estratificadas por oficina permiten comparar visualmente las funciones de supervivencia de OFI_23, OFI_31 y OFI_44.

La prueba de log-rank entre OFI_23 y OFI_44 — las oficinas con mayor diferencia en tasa bruta de default — produce:

| Estadístico | Valor |
|---|---|
| χ² (log-rank) | 0.0817 |
| p-valor | **0.7750** |

El **p-valor de 0.775** indica que **no se puede rechazar la hipótesis nula** de igualdad de curvas de supervivencia entre OFI_23 y OFI_44 al nivel de significancia del 5%.

Este resultado — aparentemente contradictorio con la marcada diferencia en tasas brutas de default (0.90% vs. 3.50%) — puede explicarse por:

1. **Diferencia en el *timing* del evento:** La prueba de log-rank compara la función de supervivencia en cada punto del tiempo; si OFI_44 y OFI_23 experimentan sus eventos en momentos similares, la prueba no detecta diferencia aunque las tasas brutas difieran.
2. **Créditos en riesgo:** A horizontes temporales largos (donde ocurren los eventos), el número de créditos en riesgo se reduce drásticamente, disminuyendo el poder estadístico de la prueba.
3. **Heterogeneidad intra-oficina:** La variabilidad entre rutas dentro de cada oficina puede dominar la variabilidad entre oficinas, diluyendo la señal.

Esta limitación del test no paramétrico motiva el uso del modelo de Cox, que puede controlar simultáneamente por múltiples covariables y capturar el efecto marginal de `ofi_id` ajustando por las diferencias en el perfil de los clientes.

*(Ver Figura 3: Curvas KM por oficina con log-rank test)*

#### 4.3.5 Tiempo de Seguimiento y Granularidad Longitudinal

| Estadístico | t_stop (días) | n_intervalos |
|---|---|---|
| Mediana | **29 días** | 3 |
| Media | 36 días | 10.6 |
| Percentil 25 | 24 días | — |
| Percentil 75 | 35 días | — |
| Máximo | **815 días** | 233 |

La **mediana de 29 días** refleja que la mayoría de los créditos del portafolio son de corto plazo (20-30 días) y tienen pocas renovaciones, resultando en un seguimiento breve. Sin embargo, la distribución presenta una **cola derecha pronunciada**: algunos créditos acumulan hasta 815 días de seguimiento y 233 snapshots de 10 días, correspondiendo a clientes con múltiples renovaciones consecutivas o que permanecieron en el portafolio sin cerrar durante años.

Esta estructura bimodal — mayoría de créditos cortos + cola de créditos de larga permanencia — es típica del microcréditode pago diario y justifica el uso del análisis de supervivencia sobre la regresión logística: el tiempo de permanencia en riesgo es informativo per se.

*(Ver Figura 4: Distribución de t_stop e intervalos por crédito)*

#### 4.3.6 Cronómetro de Inactividad Financiera (dias_sin_pagar)

| Estadístico | Valor |
|---|---|
| Mediana | 0 días |
| Percentil 75 | 0 días |
| Percentil 95 | 0 días |
| Percentil 99 | 26 días |
| Máximo | **400 días** |

El cronómetro de inactividad presenta una distribución **fuertemente concentrada en cero**: en más del 95% de todos los intervalos observados, el crédito tiene *dias_sin_pagar = 0*, es decir, el cliente realizó al menos un abono durante el bloque de 10 días. Los valores altos (> 26 días) son estadísticamente raros (< 1% de los intervalos) y corresponden casi exclusivamente a los créditos que eventualmente experimentan el evento de default.

La correlación de Pearson entre *dias_sin_pagar* y *evento* es **r = 0.680** — la correlación más alta del conjunto de covariables con la variable objetivo — confirmando que el cronómetro captura de manera efectiva la señal predictiva del abandono crediticio.

*(Ver Figura 5: Distribución de dias_sin_pagar — global, zoom 0-150, máximo por crédito)*

#### 4.3.7 Análisis de Covariables: Default vs. Censurado

El análisis comparativo de las distribuciones de covariables entre grupos (E=1 vs. E=0) revela patrones consistentes con la teoría del riesgo crediticio:

**Correlaciones con el evento (Pearson):**

| Covariable | r con evento | Dirección |
|---|---|---|
| `dias_sin_pagar` | **+0.6796** | Cronómetro directo del evento |
| `saldo_relativo` | −0.0350 | Mayor saldo → menor probabilidad de default |
| `dias_con_abono` | −0.0217 | Más días con abono → menor riesgo |
| `ratio_atraso` | −0.0176 | Contra-intuitivo; explicado por composición |
| `cuotas_atrasadas` | −0.0166 | Ídem |
| `pago_promedio_diario` | −0.0152 | Más pagos → menor riesgo |
| `intensidad_recuperacion` | +0.0071 | Efecto mixto |

Las correlaciones de las covariables de mora y pago con el evento son negativas pero de muy baja magnitud. Esto no implica ausencia de efecto predictivo, sino que las correlaciones lineales de Pearson no capturan la relación no lineal y dinámica entre estas variables y el riesgo en el contexto del Counting Process. El modelo de Cox de hazard proporcional podrá cuantificar estos efectos correctamente.

La variable `dias_sin_pagar` domina las correlaciones lineales porque **define directamente el evento**: en los intervalos donde el cliente está próximo al umbral de 120 días, *dias_sin_pagar* es necesariamente alto. Esta variable se incluirá como covariable explicativa en el modelo Cox dada su doble rol: es tanto el cronómetro del evento como un predictor dinámico del riesgo residual.

*(Ver Figura 6: Histogramas comparativos de covariables — Default vs. Censurado)*

#### 4.3.8 Perfil Económico del Portafolio

**Monto del crédito (total_credito):**

| Estadístico | Valor |
|---|---|
| Mediana | R$ 1,200 |
| Media | R$ 1,491 |
| Percentil 10 | R$ 540 |
| Percentil 90 | R$ 3,000 |

Los créditos son de bajo monto (mediana R$ 1,200), confirmando el perfil de microcréditode pago diario destinado a trabajadores informales y microempresarios con necesidades de liquidez de corto plazo.

**Plazo del crédito (cuotas_pactadas = días de plazo):**

La distribución del plazo está altamente concentrada en tres valores discretos:
- **20 días:** 17,812 créditos (62.7%) — el producto principal
- **24 días:** 8,330 créditos (29.3%) — segunda opción estándar
- **30 días:** 1,488 créditos (5.2%) — plazo extendido

Esta concentración en modalidades estándar refleja que los plazos son productos pre-definidos por la entidad, no negociados individualmente. La gran mayoría del portafolio (92.0%) tiene un plazo de 20 o 24 días.

*(Ver Figura 7: Distribución de plazo, monto y boxplot por evento)*

#### 4.3.9 Estructura de Correlaciones entre Covariables

El mapa de calor de correlaciones (triángulo inferior) revela las siguientes relaciones significativas entre covariables:

- **ratio_atraso ↔ cuotas_atrasadas** (r ≈ +0.90): correlación esperada, ya que `ratio_atraso = cuotas_atrasadas / cuotas_pactadas` — ambas variables miden essencialmente lo mismo en escalas diferentes. En el modelo de Cox final, deberá considerarse incluir solo una de las dos para evitar multicolinealidad.
- **dias_sin_pagar ↔ evento** (r = 0.68): cronómetro directo del evento.
- **pago_promedio_diario ↔ dias_con_abono** (r > 0): coherente — más días con pago implica mayor flujo promedio.
- **saldo_relativo ↔ total_credito**: correlación moderada, refleja que créditos de mayor monto tienden a tener saldos relativos mayores al inicio del período de observación.

La ausencia de correlaciones altas (> 0.7) entre las covariables de pago, mora y saldo — con la excepción del par ratio_atraso/cuotas_atrasadas — indica que el conjunto de variables seleccionado no presenta problemas graves de multicolinealidad, condición favorable para la estabilidad de los coeficientes del modelo de Cox.

*(Ver Figura 8: Mapa de calor de correlaciones)*

#### 4.3.10 Análisis de Trayectorias Individuales

La visualización de trayectorias individuales — 5 créditos en default y 5 créditos censurados — permite validar cualitativamente la lógica del cronómetro:

- **Créditos en default:** el cronómetro *dias_sin_pagar* crece monotónicamente durante los últimos bloques de observación, cruzando el umbral de 120 días exactamente en el intervalo marcado como evento (E=1). Confirmado que la regla de censura trunca correctamente la trayectoria tras el primer evento.
- **Créditos censurados:** el cronómetro permanece en cero o cerca de cero durante toda la trayectoria, con eventuales subidas breves seguidas de reinicio inmediato al producirse un abono. Esto confirma que el mecanismo de forward-fill captura correctamente la mora transitoria.

*(Ver Figura 9: Trayectorias de 5 créditos en default vs. 5 censurados)*

---

### 4.4 Síntesis y Validación del Dataset

El dataset de supervivencia resultante cumple con todos los requisitos del formato Counting Process de Anderson-Gill para ser procesado por `lifelines.CoxTimeVaryingFitter`:

| Validación | Resultado |
|---|---|
| t_stop > t_start en todos los intervalos | ✓ Verificado |
| Cadena perfecta t_start[k] = t_stop[k-1] | ✓ Verificado (via shift) |
| Evento E=1 solo en el último intervalo | ✓ Aplicado por regla de censura |
| Sin valores nulos en columnas clave | ✓ Verificado |
| Número de eventos > 100 | ✓ 425 eventos |
| Covariables numéricas en rango esperado | ✓ Clip aplicado a todas las ratios |

**Resumen final del dataset:**

```
══════════════════════════════════════════════════════
DATASET DE SUPERVIVENCIA — ESTADÍSTICAS FINALES
══════════════════════════════════════════════════════
  Período:           2020-01-01 → 2026-05-15
  Oficinas:          3 | Rutas: 17
  Créditos únicos:   28,386
  Intervalos (filas):301,434
  Eventos (E=1):     425   (tasa: 1.50%)
  Censurados (E=0):  27,961 (98.50%)
  T mediana:         29 días | T máximo: 815 días
  S(180 días):       68.15% | S(365 días): 16.73%
  Monto mediano:     R$ 1,200 | Plazo modal: 20 días
══════════════════════════════════════════════════════
```

La definición del evento como *dias_sin_pagar ≥ 120* demostró ser operacionalmente válida y estadísticamente estable, produciendo una tasa de default de 1.50% coherente con las referencias del microcréditode pago diario en economías emergentes (Schreiner, 2002; Banerjee & Duflo, 2007). El dataset queda preparado para la siguiente etapa: ajuste del modelo de Cox de Riesgos Proporcionales con covariables tiempo-variantes.

---

### Referencias

- Anderson, P. K., & Gill, R. D. (1982). Cox's regression model for counting processes: A large sample study. *The Annals of Statistics*, 10(4), 1100–1120.
- Banerjee, A. V., & Duflo, E. (2007). The economic lives of the poor. *Journal of Economic Perspectives*, 21(1), 141–167.
- Kalbfleisch, J. D., & Prentice, R. L. (2002). *The Statistical Analysis of Failure Time Data* (2nd ed.). Wiley.
- Kaplan, E. L., & Meier, P. (1958). Nonparametric estimation from incomplete observations. *Journal of the American Statistical Association*, 53(282), 457–481.
- Mantel, N. (1966). Evaluation of survival data and two new rank order statistics arising in its consideration. *Cancer Chemotherapy Reports*, 50(3), 163–170.
- Schreiner, M. (2002). Aspects of outreach: A framework for discussion of the social benefits of microfinance. *Journal of International Development*, 14(5), 591–603.
- Therneau, T. M., & Grambsch, P. M. (2000). *Modeling Survival Data: Extending the Cox Model*. Springer.
