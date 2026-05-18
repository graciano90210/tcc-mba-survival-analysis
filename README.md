# Modelagem de Risco de Crédito Dinâmico para Microempreendedores
### Uma Abordagem via Análise de Sobrevivência em Fluxos de Alta Frequência

> **Trabalho de Conclusão de Curso (TCC)** · MBA em Ciência de Dados · ICMC/USP  
> **Autor:** Juan Fernando Graciano Pinzón · **Orientador:** Prof. Dr. Vicente Garibay Cancho

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/Selenium-RPA%20Pipeline-43B02A?style=for-the-badge&logo=selenium&logoColor=white"/>
  <img src="https://img.shields.io/badge/ETL-Concluído-brightgreen?style=for-the-badge"/>
  <img src="https://img.shields.io/badge/EDA-Concluído-brightgreen?style=for-the-badge"/>
  <img src="https://img.shields.io/badge/Lifelines-Sobrevivência-2ecc71?style=for-the-badge"/>
  <img src="https://img.shields.io/badge/TCC-V21%20Gerado-blue?style=for-the-badge"/>
  <img src="https://img.shields.io/badge/LGPD-Compliant-e74c3c?style=for-the-badge"/>
</p>

---

## Resumo Executivo

Este projeto desenvolve um motor de **Credit Scoring Dinâmico** para o segmento de microcrédito informal — historicamente excluído do sistema financeiro tradicional. A hipótese central sustenta que os **fluxos de caixa diários de alta frequência** constituem proxies robustas de solvência, superando em poder preditivo as variáveis socioeconômicas estáticas dos modelos convencionais.

A abordagem metodológica baseia-se na **Análise de Sobrevivência**, modelando o tempo até a inadimplência crítica (`dias_sem_pagar ≥ 120`) por meio do Modelo de Riscos Proporcionais de Cox com covariáveis tempo-variantes (formato Counting Process de Anderson-Gill) e arquiteturas de Deep Learning (DeepSurv/RNNs).

**Dataset atual:** 28.386 créditos · 425 eventos de default (1,50%) · 3 oficinas · 17 rotas · 2020–2026.

---

## Estado do Projeto (Sprint 2 concluído)

| Sprint | Descrição | Status |
|---|---|---|
| **Sprint 1** | ETL Selenium + Data Lake + Data Stitching | **✓ Concluído** |
| **Sprint 2** | Feature Engineering + EDA + TCC V21 | **✓ Concluído** |
| Sprint 3 | Modelagem: Cox PH + DeepSurv | Agendado |
| Sprint 4 | Validação, análise crítica e defesa | Agendado |

---

## Problema e Solução

| Dimensão | Abordagem Tradicional | Abordagem Proposta |
|---|---|---|
| **Dados de entrada** | Score estático, renda declarada | Fluxo de pagamentos diários (6 anos) |
| **Frequência** | Mensal / Anual | Diária (alta frequência) |
| **Cobertura** | Bancarizados com histórico | Microempreendedores sub-bancarizados |
| **Modelo** | Regressão Logística / Score fixo | Cox PH + DeepSurv (tempo-variante) |
| **Variável alvo** | Binário: inadimplente / adimplente | T (dias de sobrevivência) + E (evento) |

---

## Arquitetura do Projeto

```
TCC/
├── data/
│   ├── raw/                              # Ignorado pelo .gitignore (LGPD)
│   │   ├── OFI_23/                       # São Paulo (7 rotas)
│   │   ├── OFI_31/                       # Sociedades Brasil (5 rotas)
│   │   └── OFI_44/                       # Cabo Frio (5 rotas)
│   └── processed/
│       ├── matriz_maestra.csv            # Produto do Data Stitching (~6 GB)
│       └── survival_dataset.csv          # Counting Process (28.386 créditos)
│
├── src/
│   ├── listo_extractor.py                # ETL Piloto — OFI_23/RTA_82 ✓
│   ├── listo_masivo.py                   # ETL Corporativo — 17 rotas ✓
│   ├── consolidar_datos.py               # Data Stitching → matriz_maestra.csv ✓
│   ├── feature_engineering.py            # Counting Process + cronômetro forward-fill ✓
│   ├── gerar_tcc_v21.py                  # Gerador TCC V21 Português (NBR 14724:2024) ✓
│   └── gerar_tcc_v21_es.py               # Gerador TCC V21 Español ✓
│
├── notebooks/
│   └── 01_eda_survival.ipynb             # EDA completo — 9 figuras diagnósticas ✓
│
├── reports/
│   ├── fig01_default_distribution.png    # Distribuição do evento de default
│   ├── fig02_km_global.png               # Curva KM global com tabela de risco
│   ├── fig03_km_por_oficina.png          # KM por oficina + teste log-rank
│   ├── fig04_followup_distribution.png   # Tempo de seguimento e intervalos
│   ├── fig05_dias_sem_pagar.png          # Cronômetro dias_sem_pagar (3 painéis)
│   ├── fig06_covariables_evento.png      # Covariáveis: Default vs. Censurado
│   ├── fig07_perfil_economico.png        # Perfil econômico do portfólio
│   ├── fig08_correlacao_heatmap.png      # Mapa de calor de correlações
│   ├── fig09_trajetorias.png             # Trajetórias individuais (5+5)
│   ├── informe_metodologia_eda.md        # Relatório teórico-empírico completo (ES)
│   └── critica_academica_v21.md          # 8 oportunidades de melhoria (revisão senior)
│
├── documentotcc/
│   ├── Projeto_Pesquisa_TCC_V21_Completo.docx   # TCC V21 em Português (700 KB) ✓
│   └── TCC_V21_Español_Completo.docx            # TCC V21 em Español (695 KB) ✓
│
├── .env                                  # Credenciais — NUNCA versionar
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Resultados do EDA (Sprint 2)

| Métrica | Valor |
|---|---|
| Créditos únicos | 28.386 |
| Eventos de default (E=1) | 425 (1,50%) |
| Créditos censurados (E=0) | 27.961 (98,50%) |
| Oficinas | 3 (OFI_23, OFI_31, OFI_44) |
| KM — S(180 dias) | 0,6815 |
| KM — S(365 dias) | 0,1673 |
| Log-rank (OFI_23 vs OFI_44) | p = 0,775 (não significativo) |
| Taxa de default OFI_44 | 3,50% |
| Taxa de default OFI_23 | 0,90% |
| Mediana de seguimento | ~183 dias |
| Definição do evento | `dias_sem_pagar ≥ 120` |

---

## Definição Formal do Evento

| Notação | Definição |
|---|---|
| **T** | Dias desde o desembolso até a inadimplência crítica |
| **E = 1** | `dias_sem_pagar ≥ 120` — 4 meses de inatividade financeira total ("castigo de cartera") |
| **E = 0** | Censura à direita — crédito ativo, quitado ou atraso < 120 dias |
| **S(t)** | P(T > t) — probabilidade de permanecer adimplente além do dia t |
| **h(t)** | Taxa instantânea de falha no instante t |
| **t_start / t_stop** | Formato Counting Process (Anderson-Gill 1982) |

> **Correção crítica V20 → V21:** A definição anterior (`CUOTAS_ATRASADAS = 120`) era operacionalmente impossível — o máximo observado na cohorte diária é 34. Corrigido para `dias_sem_pagar ≥ 120` com cronômetro de inatividade via forward-fill.

---

## Pipeline ETL

### Fluxo de Extração Batch

```
Sistema LISTO (janela: 10 dias)
        │ Selenium RPA
        ▼
data/raw/OFI_XX/RTA_YY/
        │ consolidar_datos.py (Data Stitching)
        ▼
data/processed/matriz_maestra.csv (~6 GB)
        │ feature_engineering.py (Counting Process)
        ▼
data/processed/survival_dataset.csv
        │
    ┌───┴───┐
    │       │
  Cox PH  DeepSurv/RNN       ← Sprint 3
    │       │
    └───┬───┘
        │
  Credit Score Dinâmico
```

### Desafios Técnicos Resolvidos no Sistema LISTO (v3.288.45)

| Desafio | Solução |
|---|---|
| Sem API REST | Selenium WebDriver + ChromeDriver automático |
| Login bifásico com select2 | DOM native `dispatchEvent('change')` |
| Modal bootbox bloqueando frameset | `find_elements` + JS click dentro do iframe correto |
| Campo de data readonly | Injeção de valor via `arguments[0].value` JS |
| Matriz de 6 GB em RAM | Leitura em chunks de 5.000 linhas com máscara NumPy vetorizada |

---

## Documentos TCC Gerados

| Versão | Idioma | Arquivo | Tamanho |
|---|---|---|---|
| V21 | Português | `Projeto_Pesquisa_TCC_V21_Completo.docx` | 700 KB |
| V21 | Español | `TCC_V21_Español_Completo.docx` | 695 KB |

**Formato:** NBR 14724:2024 (USP) — Arial, margens 3/2 cm, interlineado 1,5.  
**Conteúdo:** 8 seções + pré-textuais (RESUMO, ABSTRACT, SUMÁRIO) + 9 figuras EDA + 15 tabelas.

---

## Stack Tecnológico

| Categoria | Tecnologia | Finalidade |
|---|---|---|
| **Linguagem** | Python 3.12 | Core do projeto |
| **RPA / ETL** | `selenium`, `webdriver-manager` | Download automatizado do LISTO |
| **Credenciais** | `python-dotenv` | Gestão segura de segredos |
| **Sobrevivência** | `lifelines` | Cox PH, Kaplan-Meier, Nelson-Aalen |
| **Deep Learning** | `pycox`, `torch` | DeepSurv / RNN-Survival (Sprint 3) |
| **Manipulação** | `pandas`, `numpy` | Data Stitching e feature engineering |
| **Visualização** | `matplotlib`, `seaborn` | Curvas KM, EDA, diagnóstico |
| **Documentos** | `python-docx` | Geração programática do TCC (ABNT) |
| **Ambiente** | `venv` | Isolamento de dependências |

---

## Instalação e Execução

```bash
# 1. Clone o repositório
git clone git@github.com:graciano90210/tcc-mba-survival-analysis.git
cd tcc-mba-survival-analysis

# 2. Crie e ative o ambiente virtual
python3 -m venv venv
source venv/bin/activate

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Configure as credenciais (nunca versionar este arquivo)
cp .env.example .env   # preencher LISTO_USER e LISTO_PASS

# 5. ETL corporativo (17 rotas · ~3.961 lotes)
python src/listo_masivo.py

# 6. Data Stitching → matriz_maestra.csv
python src/consolidar_datos.py

# 7. Feature Engineering → survival_dataset.csv
python src/feature_engineering.py

# 8. EDA (gera 9 figuras em reports/)
jupyter nbconvert --to notebook --execute notebooks/01_eda_survival.ipynb \
    --output 01_eda_survival.ipynb --output-dir notebooks/

# 9. Gerar documentos TCC V21 (PT + ES)
python src/gerar_tcc_v21.py
```

> **Pré-requisito:** Google Chrome instalado. ChromeDriver gerenciado automaticamente via `webdriver-manager`.

---

## Dados e Conformidade com a LGPD

Os dados em `data/raw/` e `data/processed/` são **omitidos do versionamento** via `.gitignore` em conformidade com a **LGPD (Lei nº 13.709/2018)**. Os arquivos contêm informações financeiras individuais de microempreendedores, classificadas como dados sensíveis. As credenciais de acesso ao sistema LISTO são gerenciadas via arquivo `.env`, também excluído do versionamento.

---

## Referências

- **Anderson, P. K.; Gill, R. D.** (1982). Cox's regression model for counting processes. *The Annals of Statistics*, 10(4), 1100–1120.
- **Cox, D. R.** (1972). Regression models and life-tables. *JRSS-B*, 34(2), 187–202.
- **Kaplan, E. L.; Meier, P.** (1958). Nonparametric estimation from incomplete observations. *JASA*, 53(282), 457–481.
- **Katzman, J. L. et al.** (2018). DeepSurv: personalized treatment recommender system using a Cox proportional hazards deep neural network. *BMC Medical Research Methodology*, 18(1), 24.
- **Klein, J. P.; Moeschberger, M. L.** (2003). *Survival Analysis: Techniques for Censored and Truncated Data*. 2nd ed. Springer.
- **Kvamme, H. et al.** (2019). Time-to-event prediction with neural networks and Cox regression. *JMLR*, 20(129).
- **Mantel, N.** (1966). Evaluation of survival data and two new rank order statistics. *Cancer Chemotherapy Reports*, 50(3), 163–170.
- **Schreiner, M.** (2002). Scoring: The next breakthrough in microcredit? *CGAP Occasional Paper*, 7.
- **Thomas, L. C.** (2009). *Consumer Credit Models*. Oxford University Press.
- **Davidson-Pilon, C.** (2019). lifelines: survival analysis in Python. *JOSS*, 4(40), 1317.

---

<p align="center">
  <sub>MBA em Ciência de Dados · ICMC/USP · 2025–2026</sub><br>
  <sub>Dados brutos protegidos pela LGPD — propriedade da instituição financeira parceira</sub>
</p>
