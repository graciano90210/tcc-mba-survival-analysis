# Modelagem de Risco de Crédito Dinâmico para Microempreendedores
### Uma Abordagem via Análise de Sobrevivência em Fluxos de Alta Frequência

> **Trabalho de Conclusão de Curso (TCC)** · MBA em Ciência de Dados · ICMC/USP
> **Autor:** Juan Fernando Graciano Pinzon · **Orientador:** Prof. Dr. Vicente Garibay Cancho

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/Selenium-RPA%20Pipeline-43B02A?style=for-the-badge&logo=selenium&logoColor=white"/>
  <img src="https://img.shields.io/badge/ETL-Em%20Execução-orange?style=for-the-badge"/>
  <img src="https://img.shields.io/badge/Lifelines-Sobrevivência-2ecc71?style=for-the-badge"/>
  <img src="https://img.shields.io/badge/LGPD-Compliant-e74c3c?style=for-the-badge"/>
</p>

---

## Resumo Executivo

Este projeto desenvolve um motor de **Credit Scoring Dinâmico** para o segmento de microcrédito informal — historicamente excluído do sistema financeiro tradicional. A hipótese central sustenta que os **fluxos de caixa diários de alta frequência** constituem proxies robustas de solvência, superando em poder preditivo as variáveis socioeconômicas estáticas dos modelos convencionais.

A abordagem metodológica baseia-se na **Análise de Sobrevivência**, modelando o tempo até a inadimplência crítica (T ≥ 120 dias consecutivos) por meio do Modelo de Riscos Proporcionais de Cox e arquiteturas de Deep Learning (DeepSurv/RNNs) para covariáveis variantes no tempo.

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
│   │   ├── planilla_abonos_*.xlsx        # RTA_82 JUAN — 233 arquivos (113 MB) ✓
│   │   ├── OFI_23/                       # São Paulo
│   │   │   ├── RTA_96/                   # Francisco Morato
│   │   │   ├── RTA_423/
│   │   │   ├── RTA_136/
│   │   │   ├── RTA_367/
│   │   │   ├── RTA_448/
│   │   │   └── RTA_494/
│   │   ├── OFI_31/                       # Sociedades Brasil
│   │   │   ├── RTA_415/ RTA_68/
│   │   │   ├── RTA_338/ RTA_347/ RTA_389/
│   │   └── OFI_44/                       # Cabo Frio
│   │       ├── RTA_114/ RTA_439/
│   │       └── RTA_396/ RTA_420/ RTA_511/
│   └── processed/
│       └── matriz_maestra.csv            # Produto do Data Stitching
│
├── src/
│   ├── listo_extractor.py                # ETL Piloto — OFI_23/RTA_82 (JUAN) ✓
│   ├── listo_masivo.py                   # ETL Corporativo — 17 rotas (em execução)
│   └── consolidar_datos.py               # Data Stitching → matriz_maestra.csv
│
├── notebooks/                            # (agendado — Mês 2/3)
├── .env                                  # Credenciais — NUNCA versionar
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Estado da Extração de Dados (ETL)

| Oficina | ID | Rotas | Período | Status |
|---|---|---|---|---|
| São Paulo — RTA_82 (JUAN) | OFI_23 | 1/7 | 01/01/2020 → 14/05/2026 | **✓ 100% — 233 lotes / 113 MB** |
| São Paulo — demais rotas | OFI_23 | 6/7 | 01/01/2020 → hoje | Em execução |
| Sociedades Brasil | OFI_31 | 5/5 | 01/01/2020 → hoje | Aguardando |
| Cabo Frio | OFI_44 | 5/5 | 01/01/2020 → hoje | Aguardando |

**Mapa corporativo descoberto automaticamente:** 3 oficinas · 17 rotas · ~3.961 lotes totais estimados.

---

## Pipeline ETL — Implementação Técnica

### Classe `ListoDataExtractor` (`src/listo_extractor.py`)

Robot piloto de extração da rota JUAN (OFI_23/RTA_82). Resolve os seguintes desafios técnicos do Sistema LISTO (v3.288.45):

| Desafio | Solução Implementada |
|---|---|
| Sem API REST | Selenium WebDriver + ChromeDriver automático |
| Login bifásico com select2 | DOM native `dispatchEvent('change')` em vez de jQuery |
| Modal bootbox bloqueando frameset | `find_elements` + JS click dentro do iframe correto |
| Frameset aninhado (`leftFrame`/`mainFrame`) | Sequência precisa de `switch_to.frame()` |
| Menu com tags `<op>` não-padrão | XPath `//op[normalize-space()='...']` + JS click |
| Campo de data readonly (datepicker) | Injeção de valor via `arguments[0].value` JS |
| Popup "descargar varios archivos" | `automatic_downloads: 1` nas prefs do Chrome |
| Blocos com dados ausentes | Validação via `<object id="ebReportePantalla">` |

### Classe `ListoMasivoExtractor` (`src/listo_masivo.py`)

Herda `ListoDataExtractor` e adiciona capacidade corporativa:

- **Auto-Discovery:** lê dinamicamente todas as oficinas e rotas do DOM do formulário via AJAX
- **Data Lake hierárquico:** organiza em `data/raw/OFI_{id}/RTA_{id}/`
- **Filtro anti-zero:** inspeciona `<object id="ebReportePantalla">` — se não renderizou PDF, o bloco é classificado como inativo e ignorado
- **Checkpoint JSON:** persiste o estado em `.checkpoint.json` para retomada após falhas
- **Pausa inter-rota:** 10 s entre rutas para limpeza de cache do navegador

### Fluxo de Extração Batch

```
cursor = 01/01/2020
loop por oficina → ruta → tempo:
    ├── Injetar dtFechaIni via JS (bypassa datepicker)
    ├── JS click btnAceptar → aguardar 10 s
    ├── Validar ebReportePantalla (PDF visível?)
    │   ├── Não → [SKIP] rota inativa nesse período
    │   └── Sim → JS click btnExcel
    │           → monitorar .crdownload em data/raw/
    │           → mover para OFI_XX/RTA_YY/planilla_abonos_YYYYMMDD_YYYYMMDD.xlsx
    │           → salvar checkpoint
    └── cursor += 10 dias
```

---

## Metodologia Analítica

```
Sistema LISTO (janela: 10 dias)
        │ Selenium RPA
        ▼
data/raw/ (Data Lake hierárquico)
        │ consolidar_datos.py (Data Stitching)
        ▼
data/processed/matriz_maestra.csv
        │ Feature Engineering (covariáveis tempo-variantes)
        ▼
    ┌───┴───┐
    │       │
  Cox PH  DeepSurv/RNN
    │       │
    └───┬───┘
        │
  Credit Score Dinâmico
```

### Definição Formal

| Notação | Definição |
|---|---|
| **T** | Dias desde o desembolso até a inadimplência crítica |
| **E = 1** | 120 dias consecutivos de atraso (limiar empírico de não-retorno) |
| **E = 0** | Censura à direita — cliente ativo, quitado ou atraso < 120 dias |
| **S(t)** | P(T > t) — probabilidade de permanecer adimplente além do dia t |
| **h(t)** | Taxa instantânea de falha no instante t |

---

## Stack Tecnológico

| Categoria | Tecnologia | Finalidade |
|---|---|---|
| **Linguagem** | Python 3.12 | Core do projeto |
| **RPA / ETL** | `selenium`, `webdriver-manager` | Download automatizado do LISTO |
| **Credenciais** | `python-dotenv` | Gestão segura de segredos |
| **Sobrevivência** | `lifelines` | Cox PH, Kaplan-Meier, Nelson-Aalen |
| **Manipulação** | `pandas`, `numpy` | Data Stitching e feature engineering |
| **ML Clássico** | `scikit-learn` | Pré-processamento e validação cruzada |
| **Visualização** | `matplotlib`, `seaborn` | Curvas KM, EDA, diagnóstico |
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
cp .env.example .env   # preencher LISTO_USER, LISTO_PASS, LISTO_RUTA

# 5. ETL — rota piloto (OFI_23/RTA_82)
python src/listo_extractor.py

# 6. ETL — extração corporativa completa (17 rotas)
python src/listo_masivo.py

# 7. Data Stitching → matriz_maestra.csv
python src/consolidar_datos.py
```

> **Pré-requisito:** Google Chrome instalado. O ChromeDriver é gerenciado automaticamente via `webdriver-manager`.

---

## Dados e Conformidade com a LGPD

Os dados em `data/raw/` e `data/processed/` são **omitidos do versionamento** via `.gitignore` em conformidade com a **LGPD (Lei nº 13.709/2018)**. Os arquivos contêm informações financeiras individuais de microempreendedores, classificadas como dados sensíveis. As credenciais de acesso ao sistema LISTO são gerenciadas via arquivo `.env`, também excluído do versionamento.

---

## Cronograma

| Fase | Descrição | Status |
|---|---|---|
| Mês 1 | Revisão bibliográfica e fundamentação teórica | **Concluído** |
| Mês 2 | Pipeline ETL massivo, Data Lake e EDA | **Em Execução** |
| Consolidação | Data Stitching — matriz mestra longitudinal | Pronto para início |
| Mês 3 | Modelagem: Cox PH + DeepSurv/RNN | Agendado |
| Mês 4 | Validação, análise crítica e primeira versão do TCC | Agendado |
| Mês 5 | Revisão final ABNT/USP e defesa | Agendado |

---

## Referências

- **Cox, D. R.** (1972). Regression models and life-tables. *JRSS-B*, 34(2), 187–202.
- **Klein, J. P.; Moeschberger, M. L.** (2003). *Survival Analysis: Techniques for Censored and Truncated Data*. 2nd ed. Springer.
- **Hosmer, D. W.; Lemeshow, S.; May, S.** (2008). *Applied Survival Analysis*. 2nd ed. Wiley.
- **Thomas, L. C.** (2009). *Consumer Credit Models*. Oxford University Press.
- **Kvamme, H. et al.** (2019). Time-to-event prediction with neural networks and Cox regression. *JMLR*, 20(129).
- **Davidson-Pilon, C.** (2019). lifelines: survival analysis in Python. *JOSS*, 4(40), 1317.
- **Kim, Jong-Min** — Literatura seminal em Deep Learning para Análise de Sobrevivência (recomendada pela orientação).

---

<p align="center">
  <sub>MBA em Ciência de Dados · ICMC/USP · 2025–2026</sub><br>
  <sub>Dados brutos protegidos pela LGPD — propriedade da instituição financeira parceira</sub>
</p>
