# Projeto de Pesquisa — MBA em Ciência de Dados
## ICMC/USP — Instituto de Ciências Matemáticas e de Computação

---

## Título do Projeto de Pesquisa

**Modelagem de Risco de Crédito Dinâmico para Microempreendedores: Uma Abordagem via Análise de Sobrevivência em Fluxos de Alta Frequência**

---

## Nome do Aluno

Juan Fernando Graciano Pinzón

---

## Nome do Orientador

Prof. Dr. Vicente Garibay Cancho
Instituto de Ciências Matemáticas e de Computação – ICMC/USP

---

## Justificativas e Importância do Projeto de Pesquisa em Termos de Relevância para a Área

A concessão de crédito ao segmento microempresarial — em especial ao nicho *Subprime* ou *Thin-File* — no Brasil e em toda a América Latina enfrenta uma severa assimetria de informação. As instituições financeiras tradicionais baseiam seus modelos de risco em dados estáticos e históricos defasados, como apontamentos em birôs de crédito, *scores* estáticos ou balanços anuais. Essa abordagem frequentemente penaliza o microempreendedor por eventos passados, ignorando sua capacidade real e atual de geração de caixa (ALTMAN; SABATO, 2007; BAESENS; VAN GESTEL, 2009).

O segmento de microcrédito de pagamento diário apresenta uma estrutura longitudinal única: cada crédito gera um registro diário de abono (pagamento parcial) ou ausência de pagamento, configurando um fluxo transacional de alta frequência que os modelos tradicionais de *Credit Scoring* são incapazes de explorar. A inovação central desta pesquisa consiste em utilizar esse histórico de pagamentos diários como proxy do "fôlego financeiro" do empreendedor, capturando em tempo real a dinâmica de liquidez do negócio.

Do ponto de vista metodológico, existe uma lacuna relevante na literatura: há escassez de estudos que apliquem a Análise de Sobrevivência com covariáveis dependentes do tempo a dados de microcrédito de pagamento diário, particularmente no contexto latino-americano. O dataset utilizado nesta pesquisa — construído a partir de dados reais de uma instituição parceira — compreende 28.386 créditos únicos, 301.434 intervalos temporais e 425 eventos de castigo de carteira (taxa de inadimplência de 1,50%), cobrindo o período de janeiro de 2020 a maio de 2026 (~6,4 anos). A heterogeneidade geográfica observada — taxa de 3,50% no escritório de Cabo Frio (OFI_44) contra 0,90% no escritório de São Paulo (OFI_23) — evidencia que modelos populacionais agregados são insuficientes e que o risco de crédito varia significativamente por contexto territorial, o que demanda modelos com covariáveis tempo-variantes capazes de capturar essa dinâmica espacial.

A Análise de Sobrevivência, e em particular o Modelo de Riscos Proporcionais de Cox (COX, 1972) e o *Processo de Contagem* de Anderson e Gill (1982), oferece o arcabouço estatístico adequado para modelar o tempo até a inadimplência técnica incorporando simultaneamente censura à direita, truncação à esquerda e covariáveis que evoluem ao longo do seguimento. A extensão desse paradigma para arquiteturas de *Deep Learning* — DeepSurv e redes neurais recorrentes com *Negative Partial Log-Likelihood* (KATZMAN et al., 2018) — representa a fronteira atual da área e constitui o principal aporte acadêmico desta pesquisa.

---

## Objetivos Gerais e Específicos do Projeto de Pesquisa

### Objetivo Geral

Desenvolver um modelo preditivo de risco de crédito dinâmico baseado em Análise de Sobrevivência para estimar o tempo exato até a ruptura do fluxo de caixa e da capacidade de pagamento — caracterizada como inadimplência técnica — de microempreendedores, integrando variáveis estáticas demográficas e dados longitudinais de fluxo transacional de alta frequência.

### Objetivos Específicos

1. **Engenharia de Dados (ETL/RPA):** Projetar e implementar um sistema robusto de ingestão massiva capaz de contornar as limitações de sistemas legados sem API REST, extraindo e organizando o histórico transacional de múltiplas unidades de negócio em um Data Lake hierárquico, com mecanismo de *checkpoint* para resiliência a falhas.

2. **Data Stitching e MLOps:** Unificar os 3.962 *snapshots* temporais em uma Matriz Mestra (*Silver Layer*) de 344.869 linhas × 2.358 colunas, com rastreabilidade total (*Data Lineage*) e otimização computacional de memória via *chunked loading* com máscara NumPy vetorizada.

3. **Análise Exploratória e Kaplan-Meier:** Aplicar o estimador não paramétrico de Kaplan-Meier para análise exploratória do tempo de sobrevivência da capacidade de pagamento da carteira e extrair covariáveis espaço-temporais (*clusters* de rotas geográficas) para uso no modelo de Cox.

4. **Modelagem de Baseline Clássico (Cox):** Treinar e ajustar o Modelo de Riscos Proporcionais de Cox com covariáveis dependentes do tempo (`lifelines.CoxTimeVaryingFitter`) para quantificar o impacto de cada covariável na função de risco basal mediante *Hazard Ratios*, validando a suposição de proporcionalidade via resíduos de Schoenfeld.

5. **Inovação e Aporte Acadêmico (Deep Learning sob Censura):** Implementar arquiteturas DeepSurv e RNN-*Survival* (LSTM/GRU) com otimização da *Negative Partial Log-Likelihood* (`pycox`/PyTorch), comparando sua performance preditiva com o baseline de Cox.

6. **Avaliação Comparativa:** Avaliar os ganhos marginais da abordagem de Análise de Sobrevivência frente aos modelos tradicionais de *Credit Scoring* de classificação binária, utilizando o C-*index* de Harrell, o *Brier Score* temporal e a área sob a curva ROC (AUC) como métricas comparativas.

---

## Metodologia a ser Utilizada no Projeto de Pesquisa

A pesquisa segue a metodologia CRISP-DS (*Cross Industry Standard Process for Data Science*), estruturada em quatro etapas técnicas interdependentes:

### 1. Arquitetura de Dados — Pipeline ETL/RPA

A fonte primária de dados é o Sistema LISTO (versão 3.288.45), plataforma de gestão creditícia sem exposição de APIs REST. A extração automatizada foi implementada em Python 3.12 com Selenium WebDriver (*Robotic Process Automation*), superando seis barreiras técnicas específicas da interface: autenticação bifásica com widget jQuery SELECT2, navegação em *frameset* aninhado de três níveis, campo de data *readonly* (datepicker bypass via JavaScript), modal bootbox dinâmico e descarga silenciosa de múltiplos arquivos. Um cursor temporal percorre blocos estritos de 10 dias calendário de 2020 a 2026 (~233 iterações por rota), gerando 3.962 planilhas Excel organizadas hierarquicamente em `data/raw/OFI_{id}/RTA_{id}/`. O sistema de *checkpoint* JSON persiste o estado após cada bloco bem-sucedido, garantindo retomada exata após interrupções. O volume total extraído é de aproximadamente 14 GB de dados brutos.

O processo de *Data Stitching* consolida os 3.962 arquivos em uma Matriz Mestra de 344.869 linhas × 2.358 colunas (882 MB em disco, ~6 GB em RAM), processada em *chunks* de 5.000 linhas com máscara NumPy vetorizada de *broadcasting* (*n_linhas × n_colunas_pagamento*) para evitar erros de *Out-of-Memory*, com redução de consumo de RAM de aproximadamente 49% via *downcasting* para `float32`.

### 2. Engenharia de Características — Formato Counting Process

A Matriz Mestra é transformada no formato *Counting Process* de Anderson e Gill (1982), em que cada crédito *i* é representado por uma sequência de intervalos contíguos: `(t_start, t_stop, evento, X_it)`. O evento de inadimplência é definido operacionalmente como `E_i = 𝟙[dias_sem_pagar ≥ 120 dias calendário]`, equivalente a quatro meses de inatividade financeira total — critério de castigo de carteira da instituição parceira. O cronômetro `dias_sem_pagar` é implementado por *forward-fill* e reiniciado a zero a cada pagamento (abono > 0) detectado no bloco. Dois ajustes matemáticos são aplicados: (a) correção de truncação à esquerda — `t_start = max(0, data_ini_bloco − DATA_CRÉDITO)` — para evitar tempos de vida negativos; (b) continuidade de Markov via `shift()` — `t_start[k] = t_stop[k−1]` — para eliminar lacunas temporais artificiais entre snapshots.

O dataset final de sobrevivência, restrito à coorte diária (CUOTAS_PACTADAS ≤ 40), contém 28.386 créditos únicos, 301.434 intervalos temporais e 425 eventos (taxa de inadimplência de 1,50%). As sete covariáveis tempo-variantes incluem: `dias_sem_pagar`, `cuotas_atrasadas`, `pago_promedio_diario`, `dias_con_abono`, `intensidade_recuperacion`, `ratio_atraso` e `saldo_relativo`.

### 3. Modelagem

**Baseline — Modelo de Cox:** O Modelo de Riscos Proporcionais de Cox é ajustado com covariáveis dependentes do tempo via `lifelines.CoxTimeVaryingFitter`. Os *Hazard Ratios* quantificarão o impacto individual de cada covariável na função de risco basal. Os resíduos de Schoenfeld servirão como diagnóstico para verificar a suposição de proporcionalidade.

**Aporte Acadêmico — Deep Learning sob Censura:** Arquiteturas de redes neurais recorrentes (LSTM/GRU) integradas à Análise de Sobrevivência (DeepSurv/RNN-*Survival*), treinadas com otimização da *Negative Partial Log-Likelihood*, que respeita matematicamente o tempo de sobrevivência acumulado dos registros censurados à direita, evitando o viés severo introduzido pelo descarte dessas observações.

### 4. Validação e Avaliação Comparativa

Os modelos serão comparados via: C-*index* de Harrell (concordância entre o risco predito e o tempo observado), *Brier Score* temporal integrado (acurácia calibrada ao longo do tempo) e comparativo de AUC vs. C-*index* frente a modelos de classificação binária (*Logistic Regression*, *Random Forest*, *XGBoost*). O diagnóstico de proporcionalidade do Cox será realizado pelos resíduos de Schoenfeld.

Toda a infraestrutura de dados atende à Lei Geral de Proteção de Dados Pessoais (LGPD, Lei n.º 13.709/2018): dados brutos excluídos do controle de versão (`.gitignore`), credenciais em variáveis de ambiente (`.env`), pseudonimização por `CÓDIGO CRÉDITO` como chave primária e minimização de dados na *Silver Layer*.

---

## Relação Itemizada das Atividades Previstas, em Ordem Sequencial e Temporal

| Mês | Atividade | Situação |
|:---:|-----------|:--------:|
| 1–2 | Revisão bibliográfica sistemática: Análise de Sobrevivência, *Credit Scoring*, DeepSurv, Processo de Contagem de Anderson-Gill | Concluído |
| 3–4 | Desenvolvimento do pipeline ETL/RPA: autenticação Selenium, extração dos 3.962 xlsx (3 escritórios, 17 rotas, 2020–2026), Data Lake ~14 GB, sistema de *checkpoint* JSON | Concluído |
| 5   | *Data Stitching*: consolidação da Matriz Mestra (344.869 × 2.358), *chunked loading* NumPy, redução de RAM (~49%), coluna de rastreabilidade `arquivo_origen` | Concluído |
| 6   | Feature Engineering: cronômetro `dias_sem_pagar`, correção de truncação à esquerda, continuidade de Markov, filtro de coorte diária; Análise Exploratória de Dados completa (9 figuras diagnósticas, curva KM global, teste de log-rank) | Concluído |
| 7   | Ajuste do Modelo de Riscos Proporcionais de Cox com covariáveis tempo-variantes (`lifelines.CoxTimeVaryingFitter`); diagnóstico de resíduos de Schoenfeld; interpretação dos *Hazard Ratios* | Pendente |
| 8   | Implementação das arquiteturas DeepSurv e RNN-*Survival* (LSTM/GRU) com `pycox`/PyTorch; treinamento com *Negative Partial Log-Likelihood*; *hyperparameter tuning* | Pendente |
| 9   | Avaliação comparativa: C-*index* de Harrell, *Brier Score* temporal integrado, comparativo AUC vs. C-*index* frente a classificadores binários tradicionais | Pendente |
| 10  | Redação das seções de Resultados, Discussão e Conclusão do TCC; elaboração das tabelas e figuras finais | Pendente |
| 11  | Revisão crítica pelo orientador Prof. Dr. Vicente Garibay Cancho; ajustes de conteúdo, formatação ABNT (NBR 14724:2024) e revisão de referências | Pendente |
| 12  | Entrega final do TCC à plataforma da USP/ICMC; apresentação e defesa perante a banca examinadora | Pendente |

---

## Relação dos Resultados ou Produtos que se Espera Obter após o Término da Pesquisa

1. **Dataset longitudinal inédito de microcrédito diário:** painel de alta frequência com 28.386 créditos únicos, 301.434 intervalos temporais e 425 eventos de castigo de carteira, no formato *Counting Process* de Anderson-Gill, disponível para reprodução e extensão por pesquisadores da área.

2. **Modelo de Cox calibrado com covariáveis tempo-variantes:** estimativas dos *Hazard Ratios* para cada covariável dinâmica (dias sem pagamento, intensidade de recuperação, saldo relativo etc.), com diagnóstico de proporcionalidade e intervalo de confiança de 95%, fornecendo interpretabilidade clínica ao gestor de risco.

3. **Arquitetura DeepSurv/RNN-*Survival* treinada:** rede neural recorrente com *Negative Partial Log-Likelihood*, capaz de superar o baseline de Cox em C-*index* (meta: C-*index* > 0,70), com tratamento formal da censura à direita e suporte a covariáveis tempo-variantes.

4. **Comparativo quantitativo:** análise sistemática dos ganhos marginais da Análise de Sobrevivência (C-*index*, *Brier Score*) frente aos modelos tradicionais de *Credit Scoring* de classificação binária (AUC do *Logistic Regression*, *Random Forest* e *XGBoost*), contribuindo para a literatura de benchmarking em risco de crédito dinâmico.

5. **Motor de risco escalável em Python:** código-fonte modular e documentado (ETL, *Feature Engineering*, Cox, DeepSurv) disponibilizado como repositório *open-source* no GitHub, com *pipeline* de atualização periódica das covariáveis tempo-variantes para *scoring* dinâmico de novos créditos em produção.

6. **Trabalho de Conclusão de Curso aprovado:** entrega e defesa do TCC perante a banca examinadora do MBA em Ciência de Dados da Universidade de São Paulo (USP/ICMC), 2026.

7. **Artigo científico:** submissão de artigo derivado dos resultados a periódico indexado da área, como *Journal of Machine Learning Research* (JMLR), *Risk Analysis* ou *Journal of Credit Risk*, visando a difusão acadêmica dos achados sobre modelagem de sobrevivência em microcrédito de alta frequência.

---

## Relação Itemizada das Referências que Subsidiam a Proposta de Pesquisa

ALTMAN, E. I.; SABATO, G. Modeling Credit Risk for SMEs: Evidence from the US Market. **Abacus**, v. 43, n. 3, p. 332–357, 2007.

ANDERSON, P. K.; GILL, R. D. Cox's regression model for counting processes: a large sample study. **The Annals of Statistics**, v. 10, n. 4, p. 1100–1120, 1982.

BAESENS, B.; VAN GESTEL, T. **Credit Risk Management: Basic Concepts**. Oxford: Oxford University Press, 2009.

KALBFLEISCH, J. D.; PRENTICE, R. L. **The Statistical Analysis of Failure Time Data**. 2. ed. New York: Wiley, 2002.

KAPLAN, E. L.; MEIER, P. Nonparametric estimation from incomplete observations. **Journal of the American Statistical Association**, v. 53, n. 282, p. 457–481, 1958.

KATZMAN, J. L. et al. DeepSurv: personalized treatment recommender system using a Cox proportional hazards deep neural network. **BMC Medical Research Methodology**, v. 18, n. 24, 2018.

KLEIN, J. P.; MOESCHBERGER, M. L. **Survival Analysis: Techniques for Censored and Truncated Data**. 2. ed. New York: Springer, 2003.

MANTEL, N. Evaluation of survival data and two new rank order statistics arising in its consideration. **Cancer Chemotherapy Reports**, v. 50, n. 3, p. 163–170, 1966.

SCHREINER, M. Aspects of outreach: a framework for discussion of the social benefits of microfinance. **Journal of International Development**, v. 14, n. 5, p. 591–603, 2002.

THERNEAU, T. M.; GRAMBSCH, P. M. **Modeling Survival Data: Extending the Cox Model**. New York: Springer, 2000.
