# Modelagem de Risco de Crédito Dinâmico para Microempreendedores
### Uma Abordagem via Análise de Sobrevivência em Fluxos de Alta Frequência sob Censura

> **Trabalho de Conclusão de Curso (TCC)** · MBA em Ciências de Dados · ICMC/USP · CeMEAI
> **Autor:** Juan Fernando Graciano Pinzón · **Orientador:** Prof. Dr. Vicente Garibay Cancho

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/lifelines-Sobrevivência-2ecc71?style=for-the-badge"/>
  <img src="https://img.shields.io/badge/Riscos-Competitivos-8e44ad?style=for-the-badge"/>
  <img src="https://img.shields.io/badge/Sprint-4%20concluído-brightgreen?style=for-the-badge"/>
  <img src="https://img.shields.io/badge/TCC-V27%20em%20construção-blue?style=for-the-badge"/>
  <img src="https://img.shields.io/badge/LGPD-dados%20fora%20do%20git-e74c3c?style=for-the-badge"/>
</p>

---

## Resumo

O projeto estuda o risco de crédito de comerciantes, formais e informais, atendidos por
uma instituição de microcrédito com créditos de curta duração (20 a 50 dias) e pagamentos
registrados diariamente. A pergunta de pesquisa é: **com o comportamento de pagamento das
primeiras semanas do crédito e o histórico do cliente, é possível antecipar quem vai
abandonar o crédito, meses antes de a perda se confirmar?**

Cada crédito pode terminar de duas formas que competem entre si: **default** (o cliente
abandona) ou **quitação** (o cliente paga tudo). Por isso o trabalho usa análise de
sobrevivência com **riscos competitivos** e compara modelos clássicos (Cox, Fine-Gray,
regressão logística) com modelos de aprendizado de máquina (Random Survival Forest e
DeepHit, próximos sprints).

---

## Dados

| Item | Valor |
|---|---|
| Período | jan. 2020 a 15 mai. 2026 |
| Créditos de clientes | 28.149 |
| Default | 200 (0,71%) |
| Quitação | 27.191 (96,60%) |
| Censura (abertos no corte) | 758 (2,69%) |
| Escritórios / rotas | 3 / 17 (SP, RJ e SC) |
| Pagamentos diários | ≈ 470 mil |

Os dados brutos e processados **não estão no repositório** (LGPD, Lei nº 13.709/2018).
O sistema de gestão da instituição aparece no texto do TCC com o pseudônimo **ATLAS**.

### Definição dos desfechos

| Desfecho | Regra (confirmada com a operação) |
|---|---|
| **Default** | 120 dias corridos sem nenhum pagamento, contados do último pagamento real (ou do desembolso, se nunca pagou) |
| **Quitação** | Pagamento acumulado de pelo menos 98% do total antes de qualquer silêncio de 120 dias |
| **Censura** | Nenhum dos dois até a data de corte |

A baixa contábil dos créditos abandonados (um abono pelo saldo seguido de uma saída de
caixa, meses depois) nunca é contada como pagamento: o default já está marcado no dia 120.

### Cuidados com os dados (auditoria)

- **Campos do dia da descarga:** saldo, parcelas em atraso, valor da parcela e prazo
  refletem o estado de maio de 2026, não o histórico. Usá-los como covariáveis seria
  *leakage*; tudo é reconstruído a partir dos pagamentos diários.
- **Renegociação com parcela de 1 real:** quando o comerciante fecha o negócio, o prazo é
  alongado no mesmo crédito e a parcela passa a 1 real por dia. Como o campo mostra o estado
  final, esses 269 créditos usam a parcela original estimada.
- **Vales de trabalhadores:** empréstimos internos sem juros, excluídos (150).
- **Créditos sem movimento** (sem nenhum abono e saldo zero) excluídos (255), e créditos
  não diários ou anteriores a 2020 fora da coorte.
- **Domingos e feriados:** não há cobrança aos domingos e ela cai para 20% a 30% nos
  feriados; o atraso é medido em dias de cobrança, por estado.

---

## Estado do projeto

| Sprint | Período | Entrega | Situação |
|---|---|---|---|
| 1 | 2025–2026 | Extração automatizada e consolidação dos relatórios | Concluído |
| 2 | 2026 | Engenharia de atributos, EDA e projeto de pesquisa | Concluído |
| 3 | set. 2026 | Reconstrução do dataset pelos pagamentos diários (eventos corrigidos) | Concluído |
| 4 | até 02/11/2026 | Blocos de 7 dias, calendário de cobrança, histórico do cliente, Cox e Fine-Gray | Concluído |
| 5 | nov. 2026 | Variáveis macroeconômicas e sociais, RSF e DeepHit | Em andamento |
| 6 | nov. 2026 | Avaliação comparativa, interpretabilidade (SHAP) | Planejado |
| 7 | até 18/12/2026 | Redação final do TCC | Planejado |

Entrega oficial: fevereiro de 2027.

---

## Resultados do Sprint 4

Modelo *landmark*: no dia 14 ou 21 do crédito, com a informação disponível naquele dia,
ordena-se os créditos ainda abertos pelo risco de terminar em default. Validação cruzada
agrupada por cliente (5 partições, 3 repetições; nenhum cliente em treino e teste ao
mesmo tempo). Blocos de 7 dias.

| Modelo | AUC dia 14 | Defaults no top 10% (dia 14) | AUC dia 21 | Defaults no top 10% (dia 21) |
|---|---|---|---|---|
| **Fine-Gray** (crédito atual + histórico) | **0,90** | **73%** | **0,93** | **81%** |
| Regressão logística (comparação) | 0,90 | 73% | 0,93 | 81% |
| Só histórico e contrato (perto do desembolso) | 0,76 | 36% | 0,75 | 35% |

- Blocos de **7 dias** dão o alerta antes que os de 10 dias (dia 14: 73% contra 61% dos
  defaults no top 10%).
- O Cox *cause-specific* tempo-variante tem C-index de 0,98, mas é quase mecânico: no último
  bloco antes do default o cliente já está com 113 a 119 dias sem pagar. Por isso o modelo
  principal é o Fine-Gray em *landmark*.
- Sinais do histórico do cliente que aumentam o risco: primeiro crédito, baixa pontualidade
  e atraso no crédito anterior, e abono final alto só para renovar.

---

## Estrutura

```
TCC/
├── data/                          # fora do git (LGPD)
│   ├── raw/                       # relatórios de 10 dias por escritório e rota
│   └── processed/                 # matriz consolidada e datasets de sobrevivência
├── src/
│   ├── atlas_extractor.py         # extração automatizada (Selenium), piloto
│   ├── atlas_masivo.py            # extração das 17 rotas
│   ├── consolidar_datos.py        # consolidação → matriz_maestra.csv
│   ├── reconstruir_dataset.py     # desfechos e Counting Process (blocos de 7 e 10 dias)
│   ├── calendario_cobro.py        # dias de cobrança por estado (domingos e feriados)
│   ├── historial_cliente.py       # comportamento do cliente nos créditos anteriores
│   ├── kpis_clientes.py           # KPIs por cliente e rota (análise socioeconômica)
│   ├── cox_v2.py                  # Cox tempo-variante, Fine-Gray e logística em landmark
│   ├── fig_fluxo_metodologico.py  # figura do fluxo metodológico
│   └── gerar_tcc_v27.py           # gerador do documento do TCC (ABNT, python-docx)
├── notebooks/                     # EDA
├── reports/
│   ├── modelagem_v2/              # métricas e coeficientes do Sprint 4
│   └── pendientes_v27.md          # lista de controle do texto
└── documentotcc/                  # versões do TCC (.docx)
```

Versões antigas (`feature_engineering.py`, `modelagem_riscos_competitivos.py`,
`gerar_tcc_v21` a `v26`) são mantidas para rastreabilidade.

---

## Como executar

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# extração (precisa das credenciais em .env, nunca versionado)
python src/atlas_masivo.py
python src/consolidar_datos.py

# dataset e modelos
python src/reconstruir_dataset.py   # survival_dataset_v2_b7.csv, _b10.csv, desenlaces_v2.csv
python src/historial_cliente.py     # historial_cliente.csv
python src/kpis_clientes.py         # kpis_clientes.csv, kpis_rutas.csv
python src/cox_v2.py                # reports/modelagem_v2/

# documento
python src/gerar_tcc_v27.py
```

---

## Stack

| Uso | Ferramentas |
|---|---|
| Extração | `selenium`, `webdriver-manager`, `python-dotenv` |
| Dados | `pandas`, `numpy`, `pyarrow` |
| Sobrevivência | `lifelines` (Cox, Aalen-Johansen), `scikit-learn` |
| Calendário | `holidays` (feriados nacionais e estaduais) |
| Visualização | `matplotlib`, `seaborn` |
| Documento | `python-docx`, LibreOffice (PDF) |

---

## Referências principais

- Andersen, P. K.; Gill, R. D. (1982). Cox's regression model for counting processes: a large sample study. *The Annals of Statistics*, 10(4), 1100–1120.
- Cox, D. R. (1972). Regression models and life-tables. *Journal of the Royal Statistical Society B*, 34(2), 187–202.
- Fine, J. P.; Gray, R. J. (1999). A proportional hazards model for the subdistribution of a competing risk. *Journal of the American Statistical Association*, 94(446), 496–509.
- Putter, H.; Fiocco, M.; Geskus, R. B. (2007). Tutorial in biostatistics: competing risks and multi-state models. *Statistics in Medicine*, 26(11), 2389–2430.
- van Houwelingen, H. C. (2007). Dynamic prediction by landmarking in event history analysis. *Scandinavian Journal of Statistics*, 34(1), 70–85.
- Thomas, L. C. (2009). *Consumer Credit Models*. Oxford University Press.
- Davidson-Pilon, C. (2019). lifelines: survival analysis in Python. *Journal of Open Source Software*, 4(40), 1317.

---

<p align="center">
  <sub>MBA em Ciências de Dados · ICMC/USP · 2025–2026</sub><br>
  <sub>Dados protegidos pela LGPD, de propriedade da instituição parceira</sub>
</p>
