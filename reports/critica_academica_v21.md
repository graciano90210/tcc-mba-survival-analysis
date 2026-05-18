# Crítica Académica — TCC V21: Análise de Sobrevivência em Microcrédito de Alta Frequência

**Revisão:** Prof. Dr. [Revisor Senior], ICMC/USP  
**Data:** 2026-05-18  
**Documento analisado:** `Projeto_Pesquisa_TCC_V21_Completo.docx` (Graciano Pinzón, 2026)  
**Orientador:** Prof. Dr. Vicente Garibay Cancho

---

## Síntese Geral

O trabalho apresenta uma contribuição metodológica genuína: adaptar o modelo de Counting Process de Anderson-Gill (1982) a dados de microcrédito de alta frequência (snapshots de 10 dias), construindo um pipeline ETL-MLOps completo com Selenium RPA, tratamento de 28.386 créditos e 425 eventos de default. A definição operacional do evento — `dias_sem_pagar ≥ 120` — está corretamente motivada e alinhada com a prática operacional da entidade ("castigo de cartera"). O documento é robusto em engenharia; as oportunidades de melhoria estão sobretudo na validade estatística e nos limites de inferência.

---

## Oportunidades de Melhoria

### 1. Viés de Sobrevivência na Extração (Crítico)

**O problema:** O scraping via Selenium captura créditos *ativos no momento da extração* (2020–2026). Créditos castigados antes de 2020 e removidos do sistema LISTO são invisíveis para o pipeline. Isso significa que a amostra observada é condicionada à sobrevivência até o início do estudo — o exemplo textbook de viés de sobrevivência.

**Consequência quantitativa:** A taxa de default observada (1,50%, 425/28.386) subestima a taxa real da carteira histórica completa da entidade. Se os créditos castigados pré-2020 tivessem taxa de default sistematicamente maior (o que é esperado, pois saíram do sistema), os modelos Cox e DeepSurv treinados na amostra disponível superestimarão S(t) para novos créditos.

**Recomendação:** Quantificar o período de cobertura efetiva (número de créditos originados por semestre) e adicionar uma seção de "Limitações" explicitando que as estimativas de S(t) têm validade interna mas não generalizabilidade histórica completa. Se houver registros externos de castigos pré-2020, incorporá-los como créditos com `evento=1` e `t_stop` estimado.

---

### 2. Censura Informativa — Violação de Missing At Random (Crítico)

**O problema:** A análise de sobrevivência padrão (KM, Cox) assume que a censura é *não-informativa* (ou seja, um crédito censurado tem a mesma função de risco futura que um crédito que continua sendo observado). No contexto de microcrédito, essa suposição é violada de duas formas:

1. **Pagamento antecipado voluntário:** Clientes que liquidam o crédito antes do vencimento saem da observação como "censurados", mas seu perfil de risco é *inferior* ao da população geral.
2. **Abandono silencioso:** Clientes que simplesmente desaparecem do sistema LISTO sem acumular 120 dias de inatividade também aparecem como censurados, mas seu risco real é elevado.

**Consequência:** Cox e KM produzem estimativas de S(t) viesadas; o C-index pode estar inflado.

**Recomendação:** (a) Distinguir tipos de censura no dataset: `censura_tipo ∈ {pagamento_antecipado, vigente, inativo}`. (b) Para Sprint 3, considerar o estimador de Aalen-Johansen se as taxas de saída puderem ser estratificadas por causa. (c) Ao reportar limitações, citar Scharfstein et al. (1999) sobre censura informativa.

---

### 3. Clustering a Nível de Cliente — Violação de Independência (Importante)

**O problema:** Um mesmo cliente pode ter múltiplos créditos simultâneos ou sequenciais na base de dados. O pipeline atual trata cada `CÓDIGO CRÉDITO` como unidade independente, mas dois créditos do mesmo cliente compartilham covariáveis não observadas (histórico de pagamento pessoal, capacidade de renda, relação com o cobrador) — o que viola a suposição de independência do modelo de Cox.

**Consequência:** Erros padrão dos coeficientes são subestimados → intervalos de confiança muito estreitos → resultados "significativos" que na realidade não são.

**Recomendação:** (a) Verificar se existem clientes com múltiplos créditos: `df.groupby('cliente_id')['CÓDIGO CRÉDITO'].nunique()`. (b) Para Sprint 3, usar `cluster` robust standard errors no Cox (`lifelines.CoxTimeVaryingFitter(robust=True, cluster_col='cliente_id')`). (c) Considerar um modelo de frailty (frailty model) com efeito aleatório por cliente se a quantidade de clusters for suficiente.

---

### 4. Variáveis Macroeconômicas Ausentes (Importante)

**O problema:** O diferencial de taxa de default entre escritórios — OFI_44 (3,50%) vs. OFI_23 (0,90%) — é atribuído implicitamente a características operacionais da oficina, mas o log-rank p=0,775 não rejeita que as diferenças sejam ruído amostral. Uma hipótese mais plausível é que os escritórios estão geograficamente localizados em municípios com diferentes ciclos econômicos.

**Covariáveis macroeconômicas ausentes com alta relevância:**
- Taxa SELIC trimestral (proxy de custo de crédito)
- IPCA acumulado (erosão do poder de compra dos mutuários)
- Taxa de desemprego municipal (IBGE — CAGED)
- PIB per capita do município (IBGE)

**Consequência:** O modelo Cox atual omite confundidores externos, gerando coeficientes viesados para `ofi_id` e covariáveis correlacionadas com o ciclo econômico.

**Recomendação:** Para Sprint 3, incorporar pelo menos a taxa de desemprego municipal como variável tempo-variante. Os dados estão disponíveis gratuitamente via API do IBGE (SIDRA). Isso transforma o modelo em análise de riscos competitivos contextualizados.

---

### 5. Efeito Cobrador Confundido com Zona Geográfica (Moderado)

**O problema:** A variável `rta_id` (responsável de cobro) captura simultaneamente dois efeitos não separáveis: (a) a zona geográfica atribuída ao cobrador e (b) a eficácia individual do cobrador para prevenir defaults. Um cobrador excepcionalmente eficaz em uma zona de alto risco reduzirá artificialmente a taxa de default dessa zona, fazendo com que o modelo interprete a "zona" como de baixo risco.

**Consequência:** Os coeficientes de `rta_id` no Cox não têm interpretação causal limpa.

**Recomendação:** (a) Verificar se cobradores mudam de zona ao longo do tempo (dados de RH). (b) Se possível, decompor `rta_id` em `zona_id` (geográfico, fixo) + `cobrador_id` (pessoa, pode variar). (c) Ao reportar, nomear explicitamente este confundimento e sua direção de viés.

---

### 6. Artefato na Curva KM — S(t) = 1,0 até o Dia 120 (Moderado)

**O problema:** A curva KM global mostra S(t) = 1,000 para t < 120 dias, o que parece indicar que nenhum crédito defaulta nos primeiros 4 meses. Isso não é um achado empírico — é uma consequência *matemática direta* da definição do evento: `dias_sem_pagar ≥ 120` implica que nenhum evento pode ocorrer antes de t=120.

**Risco:** Leitores sem contexto podem interpretar S(t)=1,0 até t=120 como evidência de que microcréditos são extremamente seguros no curto prazo, quando na realidade é apenas um artefato da definição.

**Recomendação:** Adicionar uma nota de rodapé ou callout explícito no §4.6.3 (Curva KM) e na Figura 2 explicando: "O platô S(t)=1,0 para t<120 dias é uma consequência direta da definição operacional do evento (dias_sem_pagar ≥ 120) e não representa ausência de risco nos primeiros quatro meses." Isso demonstra rigor metodológico e antecipa a crítica da banca.

---

### 7. Desbalanceamento Extremo para DeepSurv (Importante para Sprint 3)

**O problema:** Com 98,50% de registros censurados (27.961 de 28.386 créditos), a rede neural DeepSurv/RNN-Survival enfrenta um problema de desbalanceamento severo. A função de perda padrão (Negative Partial Log-Likelihood de Breslow) dará peso implicitamente muito maior aos 97.961 créditos censurados, podendo fazer com que a rede aprenda a ignorar os 425 eventos e prediga S(t) ≈ 1,0 para todos os créditos.

**Consequência:** C-index artificialmente alto (modelo constantemente prediz "sem risco" → acerta para 98,5% dos casos) sem valor preditivo real.

**Recomendação para Sprint 3:**
- Usar *weighted Negative Partial Log-Likelihood*: atribuir peso `w_evento / w_censurado = (1-p) / p` onde `p = 0,015` → peso ≈ 66× para créditos com evento.
- Implementar via parâmetro `event_weight` em pycox ou via loss customizada no PyTorch.
- Reportar C-index *separadamente* para E=1 e E=0 (discrimination by subgroup).
- Considerar *data augmentation* por bootstrapping dos 425 eventos antes do treinamento.

---

### 8. Riscos Competitivos — Pagamento Antecipado vs. Default (Moderado para Sprint 3)

**O problema:** O modelo atual trata a saída da observação como binária: `evento=1` (default) ou `censurado`. Mas existem pelo menos dois motivos distintos de saída: (a) default por inatividade ≥120 dias e (b) liquidação antecipada voluntária (o cliente paga o saldo total antes do vencimento). Misturar ambos sob "censurado" viola a suposição de independência de causas.

**Consequência:** Em análise de riscos competitivos, a função de risco causa-específica `h₁(t)` (default) é distorcida pela presença de créditos que saem por liquidação antecipada (causa 2). KM e Cox de causa única produzem estimativas de S(t) pessimistas para a causa de default.

**Recomendação:**
- Para Sprint 3, identificar créditos com `SALDO = 0` no último snapshot como *liquidados* e atribuir `censura_tipo = 'liquidado'`.
- Ajustar um modelo de riscos competitivos Fine-Gray (`lifelines.AalenJohansenFitter` ou `sksurv.nonparametric.kaplan_meier_estimator` com `competing_risk=True`).
- Reportar Cumulative Incidence Function (CIF) para default separada da CIF para liquidação.

---

## Tabela de Prioridades

| # | Oportunidade | Severidade | Quando abordar |
|---|---|---|---|
| 1 | Viés de sobrevivência na extração | **Crítico** | §5 Limitações (Sprint 3) |
| 2 | Censura informativa (violação MAR) | **Crítico** | §5 Limitações + análise sensibilidade |
| 3 | Clustering por cliente | **Importante** | Sprint 3 (robust SE no Cox) |
| 4 | Variáveis macroeconômicas ausentes | **Importante** | Sprint 3 (API IBGE) |
| 5 | Efeito cobrador confundido | Moderado | §5 Limitações |
| 6 | Artefato KM S(t)=1,0 até dia 120 | Moderado | §4.6.3 (nota imediata no V22) |
| 7 | Desbalanceamento para DeepSurv | **Importante** | Sprint 3 (weighted loss) |
| 8 | Riscos competitivos (prepago vs. default) | Moderado | Sprint 3-4 |

---

## Pontos Fortes do Trabalho

1. **Pipeline ETL-MLOps completo e reproduzível** — Selenium RPA + chunked CSV loading (5.000 linhas/chunk, evita crash de 6 GB RAM) + formato Counting Process em um único fluxo automatizado é uma contribuição de engenharia genuína, rara em TCC de pós-graduação.

2. **Definição operacional rigorosa do evento** — A correção de `CUOTAS_ATRASADAS ≥ 120` (impossível: máximo observado = 34) para `dias_sem_pagar ≥ 120` demonstra domínio do negócio e rigor metodológico. O alinhamento com o "castigo de cartera" operacional da entidade dá validade de constructo à variável.

3. **Cronômetro de inatividade com forward-fill** — A lógica de `fecha_ultimo_pago_efectivo` (semeada em `FECHA_CRÉDITO`, atualizada a `fecha_fin_bloque` quando `dias_con_abono > 0`) é matematicamente correta e operacionalmente coerente. Distingue mora transitória de abandono real.

4. **Correção de left truncation** — `t_start = max(0, fecha_ini_bloque - FECHA_CRÉDITO)` para o primeiro intervalo, com `t_start[k] = t_stop[k-1]` para continuidade via `shift()` — implementação textbook do Counting Process.

5. **Dataset de alta granularidade** — Snapshots de 10 dias permitem detectar recuperações e recaídas intracrédito que dados mensais não capturariam, explorando adequadamente a estrutura temporal rica do sistema LISTO.

6. **Rastreabilidade completa** — Cada arquivo `matriz_maestra.csv` preserva `archivo_origen` com datas início/fim do bloque, permitindo auditoria e reprocessamento independente de qualquer janela temporal.

---

## Referências da Crítica

- Anderson, P. K., & Gill, R. D. (1982). Cox's regression model for counting processes. *The Annals of Statistics*, 10(4), 1100–1120.
- Fine, J. P., & Gray, R. J. (1999). A proportional hazards model for the subdistribution of a competing risk. *JASA*, 94(446), 496–509.
- Scharfstein, D. O., Rotnitzky, A., & Robins, J. M. (1999). Adjusting for nonignorable drop-out using semiparametric nonresponse models. *JASA*, 94(448), 1096–1120.
- Therneau, T. M., & Grambsch, P. M. (2000). *Modeling Survival Data: Extending the Cox Model*. Springer.
- Katzman, J. L. et al. (2018). DeepSurv: Personalized treatment recommender system using a Cox proportional hazards deep neural network. *BMC Medical Research Methodology*, 18(1), 24.
