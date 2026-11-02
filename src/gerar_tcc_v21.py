"""
gerar_tcc_v21.py — Gerador do TCC V21 no formato oficial USP MBA Ciência de Dados.

Integra:
  - Todo o conteúdo do V20 (zero cortes)
  - §4 expandido: fundamentos teóricos + EDA real (28.386 créditos, 425 eventos)
  - Correção crítica: evento redefinido de CUOTAS_ATRASADAS → dias_sem_pagar ≥ 120
  - Formato USP: Arial, margens 3/2 cm, NBR 14724:2024

Output: documentotcc/Projeto_Pesquisa_TCC_V21_Completo.docx
"""

from pathlib import Path
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import copy

# ── Caminhos ────────────────────────────────────────────────────────────────
BASE   = Path(__file__).parent.parent
OUTPUT = BASE / "documentotcc" / "Projeto_Pesquisa_TCC_V21_Completo.docx"


# ── Helpers de formatação USP ────────────────────────────────────────────────

def _set_spacing(paragraph, multiple=1.5):
    pf = paragraph.paragraph_format
    pf.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
    pf.line_spacing      = multiple
    pf.space_before      = Pt(0)
    pf.space_after       = Pt(6)


def _set_font(run, size=12, bold=False, italic=False):
    run.font.name  = "Arial"
    run.font.size  = Pt(size)
    run.font.bold  = bold
    run.font.italic = italic


def add_body(doc, text, align=WD_ALIGN_PARAGRAPH.JUSTIFY, indent_first=True):
    """Parágrafo de corpo: Arial 12pt, espaçamento 1.5, justificado."""
    p = doc.add_paragraph()
    _set_spacing(p)
    p.alignment = align
    if indent_first:
        p.paragraph_format.first_line_indent = Cm(1.25)
    run = p.add_run(text)
    _set_font(run)
    return p


def add_heading(doc, text, level=1):
    """Títulos USP. Nível 1 = 16pt Bold MAIÚSCULAS; 2 = 14pt Bold; 3+ = 12pt Bold."""
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    _set_spacing(p, multiple=1.0)
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after  = Pt(6)
    p.paragraph_format.first_line_indent = Cm(0)

    sizes = {1: 16, 2: 14, 3: 12, 4: 12, 5: 12}
    size = sizes.get(level, 12)
    label = text.upper() if level == 1 else text
    run = p.add_run(label)
    _set_font(run, size=size, bold=True)
    return p


def add_centered(doc, text, size=12, bold=False, spacing=1.5):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _set_spacing(p, multiple=spacing)
    p.paragraph_format.first_line_indent = Cm(0)
    run = p.add_run(text)
    _set_font(run, size=size, bold=bold)
    return p


def add_table_data(doc, headers, rows, caption_text, table_num):
    """Tabela com etiqueta 'Tabela X –' ACIMA (NBR 14724)."""
    cap = doc.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.LEFT
    _set_spacing(cap, multiple=1.0)
    cap.paragraph_format.first_line_indent = Cm(0)
    run = cap.add_run(f"Tabela {table_num} – {caption_text}")
    _set_font(run, size=10, bold=False, italic=True)

    table = doc.add_table(rows=len(rows) + 1, cols=len(headers))
    table.style = "Table Grid"

    # Header row
    hdr_cells = table.rows[0].cells
    for i, h in enumerate(headers):
        hdr_cells[i].text = h
        for run in hdr_cells[i].paragraphs[0].runs:
            run.font.name = "Arial"
            run.font.size = Pt(10)
            run.font.bold = True

    # Data rows
    for r_idx, row_data in enumerate(rows):
        cells = table.rows[r_idx + 1].cells
        for c_idx, val in enumerate(row_data):
            cells[c_idx].text = str(val)
            for run in cells[c_idx].paragraphs[0].runs:
                run.font.name = "Arial"
                run.font.size = Pt(10)

    doc.add_paragraph()  # espaço após tabela
    return table


def add_formula(doc, formula_text):
    """Fórmula matemática em Unicode, centralizada."""
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _set_spacing(p, multiple=1.0)
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after  = Pt(6)
    p.paragraph_format.first_line_indent = Cm(0)
    run = p.add_run(formula_text)
    _set_font(run, size=11, italic=True)
    return p


def add_bullet(doc, text, level=0):
    p = doc.add_paragraph(style="List Bullet")
    p.paragraph_format.first_line_indent = Cm(0)
    _set_spacing(p)
    run = p.add_run(text)
    _set_font(run)
    return p


def add_figure(doc, img_path, caption, fig_num):
    """Figura com legenda ABAIXO (NBR 14724) — insere só se o arquivo existir."""
    path = Path(img_path)
    if not path.exists():
        p = doc.add_paragraph()
        _set_spacing(p, multiple=1.0)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(f"[FIGURA {fig_num} — arquivo não encontrado: {path.name}]")
        _set_font(run, size=10, italic=True)
        return

    p_img = doc.add_paragraph()
    p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_img.paragraph_format.first_line_indent = Cm(0)
    run = p_img.add_run()
    try:
        run.add_picture(str(path), width=Cm(14))
    except Exception:
        run.add_picture(str(path))

    cap = doc.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _set_spacing(cap, multiple=1.0)
    cap.paragraph_format.first_line_indent = Cm(0)
    cap.paragraph_format.space_after = Pt(12)
    r = cap.add_run(f"Figura {fig_num} – {caption}")
    _set_font(r, size=10, italic=True)


def page_break(doc):
    doc.add_page_break()


# ── Configuração do documento ────────────────────────────────────────────────

def configure_doc(doc):
    for section in doc.sections:
        section.left_margin   = Cm(3)
        section.right_margin  = Cm(2)
        section.top_margin    = Cm(3)
        section.bottom_margin = Cm(2)
    style = doc.styles["Normal"]
    style.font.name = "Arial"
    style.font.size = Pt(12)


# ── PRÉ-TEXTUAIS ─────────────────────────────────────────────────────────────

def build_capa(doc):
    add_centered(doc, "UNIVERSIDADE DE SÃO PAULO", size=14, bold=True, spacing=1.0)
    add_centered(doc, "Instituto de Ciências Matemáticas e de Computação – ICMC", size=12, bold=True, spacing=1.0)
    add_centered(doc, "MBA em Ciência de Dados", size=12, bold=False, spacing=1.0)
    for _ in range(6):
        add_centered(doc, "", size=12, spacing=1.0)
    add_centered(doc, "Juan Fernando Graciano Pinzón", size=13, bold=True, spacing=1.0)
    for _ in range(4):
        add_centered(doc, "", size=12, spacing=1.0)
    add_centered(
        doc,
        "Modelagem de Risco de Crédito Dinâmico para Microempreendedores: "
        "Uma Abordagem via Análise de Sobrevivência em Fluxos de Alta Frequência sob Censura",
        size=17, bold=True, spacing=1.5,
    )
    for _ in range(4):
        add_centered(doc, "", size=12, spacing=1.0)
    add_centered(doc, "Orientador: Prof. Dr. Vicente Garibay Cancho", size=12, bold=False, spacing=1.0)
    add_centered(doc, "Área de concentração: Ciência de Dados", size=12, bold=False, spacing=1.0)
    for _ in range(4):
        add_centered(doc, "", size=12, spacing=1.0)
    add_centered(doc, "São Paulo / São Carlos, 2026", size=11, bold=False, spacing=1.0)
    page_break(doc)


def build_resumo(doc):
    add_heading(doc, "RESUMO", level=1)
    resumo = (
        "GRACIANO PINZÓN, Juan Fernando. Modelagem de Risco de Crédito Dinâmico para "
        "Microempreendedores: Uma Abordagem via Análise de Sobrevivência em Fluxos de Alta "
        "Frequência sob Censura. 2026. Trabalho de Conclusão de Curso – MBA em Ciência de Dados, "
        "Instituto de Ciências Matemáticas e de Computação, Universidade de São Paulo, "
        "São Paulo/São Carlos, 2026."
    )
    add_body(doc, resumo, indent_first=False)
    doc.add_paragraph()
    texto = (
        "A concessão de crédito para o segmento de microempreendedores no Brasil enfrenta severa "
        "assimetria de informação, com modelos tradicionais baseados em dados estáticos que "
        "ignoram a dinâmica de pagamento em tempo real. Esta pesquisa desenvolve um modelo "
        "preditivo de risco de crédito dinâmico utilizando Análise de Sobrevivência com "
        "covariáveis dependentes do tempo, fundamentado em dados de alta frequência de uma "
        "instituição de microcrédito de pagamento diário. Um pipeline de extração automatizado "
        "(RPA com Selenium) coletou 3.962 planilhas Excel do Sistema ATLAS, cobrindo três "
        "escritórios e 17 rotas no período 2020–2026, resultando em uma Matriz Mestra de 344.869 "
        "linhas e 2.358 colunas. Após engenharia de características no formato Counting Process "
        "(Anderson e Gill, 1982), o dataset de sobrevivência final contém 28.386 créditos únicos, "
        "301.434 intervalos temporais e 425 eventos de castigo de carteira (taxa de inadimplência "
        "de 1,50%). O evento é definido como dias_sem_pagar ≥ 120 dias calendário — equivalente "
        "a quatro meses consecutivos sem qualquer abono. A análise exploratória revelou que a "
        "curva de Kaplan-Meier permanece em S(t) = 1,0 até o 120° dia, caindo para S(180) = 0,68 "
        "e S(365) = 0,17, indicando que créditos de longa permanência concentram o risco. A etapa "
        "seguinte compreende o ajuste do Modelo de Riscos Proporcionais de Cox com covariáveis "
        "tempo-variantes e a implementação de arquiteturas de Deep Learning para sobrevivência "
        "(DeepSurv), com comparação via C-index de Harrell e Brier Score temporal. O pipeline "
        "ETL é estruturado sob a metodologia CRISP-DS e princípios MLOps, garantindo rastreabilidade "
        "total (Data Lineage) e reprodutibilidade dos resultados."
    )
    add_body(doc, texto, indent_first=False)
    p = doc.add_paragraph()
    _set_spacing(p)
    run = p.add_run(
        "Palavras-chave: análise de sobrevivência; microcrédito; Modelo de Cox; DeepSurv; "
        "alta frequência; processo de contagem; inadimplência."
    )
    _set_font(run, bold=False)
    page_break(doc)


def build_abstract(doc):
    add_heading(doc, "ABSTRACT", level=1)
    ref = (
        "GRACIANO PINZÓN, Juan Fernando. Dynamic Credit Risk Modeling for Microentrepreneurs: "
        "A Survival Analysis Approach on High-Frequency Flows under Censoring. 2026. Final Course "
        "Work – MBA in Data Science, Institute of Mathematics and Computer Science, University of "
        "São Paulo, São Paulo/São Carlos, 2026."
    )
    add_body(doc, ref, indent_first=False)
    doc.add_paragraph()
    texto = (
        "Lending to the micro-entrepreneur segment in Brazil faces severe information asymmetry, "
        "with traditional models based on static data that ignore real-time payment dynamics. This "
        "research develops a dynamic credit risk prediction model using Survival Analysis with "
        "time-varying covariates, grounded in high-frequency data from a daily-payment microcredit "
        "institution. An automated extraction pipeline (RPA with Selenium) collected 3,962 Excel "
        "spreadsheets from the ATLAS System, covering three offices and 17 routes over the period "
        "2020–2026, resulting in a Master Matrix of 344,869 rows and 2,358 columns. After feature "
        "engineering in the Counting Process format (Anderson and Gill, 1982), the final survival "
        "dataset contains 28,386 unique credits, 301,434 time intervals, and 425 write-off events "
        "(default rate: 1.50%). The event is defined as days_without_payment ≥ 120 calendar days — "
        "equivalent to four consecutive months without any payment. Exploratory analysis revealed "
        "that the Kaplan-Meier curve remains at S(t) = 1.0 until day 120, then drops to "
        "S(180) = 0.68 and S(365) = 0.17, indicating that long-standing credits concentrate the "
        "risk. The next phase includes fitting a Cox Proportional Hazards model with time-varying "
        "covariates and implementing Deep Learning survival architectures (DeepSurv), with "
        "comparison via Harrell's C-index and temporal Brier Score. The ETL pipeline is structured "
        "under CRISP-DS methodology and MLOps principles, ensuring full traceability (Data Lineage) "
        "and reproducibility of results."
    )
    add_body(doc, texto, indent_first=False)
    p = doc.add_paragraph()
    _set_spacing(p)
    run = p.add_run(
        "Keywords: survival analysis; microcredit; Cox model; DeepSurv; high-frequency data; "
        "counting process; default."
    )
    _set_font(run)
    page_break(doc)


def build_listas(doc):
    # Lista de Ilustrações
    add_heading(doc, "LISTA DE ILUSTRAÇÕES", level=1)
    figs = [
        ("1", "Distribuição do evento de default: proporção, taxa por escritório e por rota"),
        ("2", "Curva de Kaplan-Meier global do portfólio com tabela de n em risco"),
        ("3", "Curvas de Kaplan-Meier por escritório com teste de log-rank"),
        ("4", "Distribuição do tempo de seguimento (t_stop) e número de intervalos por crédito"),
        ("5", "Distribuição de dias_sem_pagar: global, zoom 0-150 dias e máximo por crédito"),
        ("6", "Distribuição das covariáveis: Default (E=1) versus Censurado (E=0)"),
        ("7", "Perfil econômico do portfólio: prazo, montante e boxplot por evento"),
        ("8", "Mapa de calor de correlações das covariáveis do modelo de sobrevivência"),
        ("9", "Trajetórias individuais: 5 créditos em default versus 5 censurados"),
    ]
    for num, desc in figs:
        p = doc.add_paragraph()
        _set_spacing(p, multiple=1.0)
        p.paragraph_format.first_line_indent = Cm(0)
        run = p.add_run(f"Figura {num} – {desc}")
        _set_font(run, size=12)
    page_break(doc)

    # Lista de Tabelas
    add_heading(doc, "LISTA DE TABELAS", level=1)
    tabs = [
        ("1",  "Componentes e volume do Data Lake extraído"),
        ("2",  "Dimensões da Matriz Mestra após consolidação"),
        ("3",  "Filtro de coorte diária: critério e créditos retidos"),
        ("4",  "Variáveis de tempo e evento do dataset de sobrevivência"),
        ("5",  "Covariáveis tempo-variantes e suas fórmulas"),
        ("6",  "Covariáveis estáticas do modelo"),
        ("7",  "Caracterização geral do dataset de sobrevivência"),
        ("8",  "Taxa de default por escritório"),
        ("9",  "Valores da curva de Kaplan-Meier global"),
        ("10", "Resultado do teste de log-rank (OFI_23 vs. OFI_44)"),
        ("11", "Estatísticas do tempo de seguimento e intervalos por crédito"),
        ("12", "Estatísticas do cronômetro dias_sem_pagar"),
        ("13", "Correlações das covariáveis com o evento"),
        ("14", "Montante do crédito por grupo de evento"),
        ("15", "Validação do formato Counting Process"),
    ]
    for num, desc in tabs:
        p = doc.add_paragraph()
        _set_spacing(p, multiple=1.0)
        p.paragraph_format.first_line_indent = Cm(0)
        run = p.add_run(f"Tabela {num} – {desc}")
        _set_font(run, size=12)
    page_break(doc)

    # Lista de Abreviaturas
    add_heading(doc, "LISTA DE ABREVIATURAS E SIGLAS", level=1)
    abrevs = [
        ("ABNT",    "Associação Brasileira de Normas Técnicas"),
        ("CRISP-DS","Cross Industry Standard Process for Data Science"),
        ("EDA",     "Análise Exploratória de Dados (Exploratory Data Analysis)"),
        ("ETL",     "Extract, Transform, Load"),
        ("KM",      "Kaplan-Meier"),
        ("LGPD",    "Lei Geral de Proteção de Dados Pessoais"),
        ("LSTM",    "Long Short-Term Memory"),
        ("MAR",     "Missing At Random"),
        ("MBA",     "Master of Business Administration"),
        ("MLOps",   "Machine Learning Operations"),
        ("RAM",     "Random Access Memory"),
        ("RPA",     "Robotic Process Automation"),
        ("TCC",     "Trabalho de Conclusão de Curso"),
        ("USP",     "Universidade de São Paulo"),
    ]
    for sigla, desc in abrevs:
        p = doc.add_paragraph()
        _set_spacing(p, multiple=1.0)
        p.paragraph_format.first_line_indent = Cm(0)
        run = p.add_run(f"{sigla} – {desc}")
        _set_font(run, size=12)
    page_break(doc)


def build_sumario(doc):
    add_heading(doc, "SUMÁRIO", level=1)
    entries = [
        (1, "1", "INTRODUÇÃO E CONTEXTUALIZAÇÃO DO PROBLEMA"),
        (2, "2", "OBJETIVOS"),
        (2, "2.1", "Objetivo Geral"),
        (2, "2.2", "Objetivos Específicos"),
        (1, "3", "ARQUITETURA DE DADOS E PIPELINE DE EXTRAÇÃO INDUSTRIAL (ETL)"),
        (2, "3.1", "Contexto e Resolução de Barreiras via Automação (RPA)"),
        (2, "3.2", "Escalabilidade Corporativa e Descoberta Automática"),
        (2, "3.3", "Processamento Batch, Filtro Anti-Zero e Persistência"),
        (2, "3.4", "Arquitetura do Data Lake, Pipeline de Consolidação e CRISP-DS"),
        (1, "4", "ENGENHARIA DE VARIÁVEIS E DEFINIÇÃO DO EVENTO TARGET"),
        (2, "4.1", "Fundamentos Teóricos da Análise de Sobrevivência"),
        (3, "4.1.1", "Função de Sobrevivência e Função de Risco"),
        (3, "4.1.2", "Tipos de Censura e Truncação à Esquerda"),
        (3, "4.1.3", "Estimador de Kaplan-Meier"),
        (3, "4.1.4", "Teste de Log-Rank"),
        (3, "4.1.5", "Processo de Contagem de Anderson-Gill"),
        (2, "4.2", "Definição Operacional da Inadimplência na Alta Frequência"),
        (2, "4.3", "Estrutura Bimodal de Atributos e Estratégia de Proxy"),
        (2, "4.4", "Formatação Anderson-Gill (Counting Process)"),
        (2, "4.5", "Construção do Dataset de Sobrevivência"),
        (3, "4.5.1", "Fonte de Dados: Sistema ATLAS e Data Lake"),
        (3, "4.5.2", "Filtro de Coorte Diária"),
        (3, "4.5.3", "Cronômetro de Inatividade Financeira (forward-fill)"),
        (3, "4.5.4", "Correções do Formato Counting Process"),
        (3, "4.5.5", "Variáveis Covariadas"),
        (2, "4.6", "Análise Exploratória de Dados (EDA)"),
        (3, "4.6.1", "Caracterização Geral do Dataset"),
        (3, "4.6.2", "Distribuição do Evento de Default"),
        (3, "4.6.3", "Curva de Kaplan-Meier Global"),
        (3, "4.6.4", "Análise Estratificada por Escritório (Teste de Log-Rank)"),
        (3, "4.6.5", "Tempo de Seguimento e Granularidade Longitudinal"),
        (3, "4.6.6", "Cronômetro dias_sem_pagar"),
        (3, "4.6.7", "Análise de Covariáveis: Default vs. Censurado"),
        (3, "4.6.8", "Perfil Econômico do Portfólio"),
        (3, "4.6.9", "Estrutura de Correlações"),
        (3, "4.6.10", "Análise de Trajetórias Individuais"),
        (2, "4.7", "Síntese e Validação do Dataset"),
        (1, "5", "MODELAGEM MATEMÁTICA E COMPUTACIONAL"),
        (2, "5.1", "Baseline Clássico (Modelo de Cox)"),
        (2, "5.2", "O Desafio da Censura à Direita em Arquiteturas Neurais"),
        (2, "5.3", "Abordagem Estado da Arte (Deep Learning sob Censura)"),
        (1, "6", "VALIDAÇÃO"),
        (1, "7", "CRONOGRAMA INTEGRADO DE PESQUISA"),
        (1, "REFERÊNCIAS", "REFERÊNCIAS BIBLIOGRÁFICAS"),
    ]
    for level, num, title in entries:
        p = doc.add_paragraph()
        _set_spacing(p, multiple=1.0)
        p.paragraph_format.first_line_indent = Cm(0)
        indent = Cm((level - 1) * 0.75)
        p.paragraph_format.left_indent = indent
        label = f"{num}  {title}" if num != "REFERÊNCIAS" else title
        run = p.add_run(label)
        _set_font(run, size=12, bold=(level == 1))
    page_break(doc)


# ── SEÇÃO 1 ──────────────────────────────────────────────────────────────────

def build_secao_1(doc):
    add_heading(doc, "1  INTRODUÇÃO E CONTEXTUALIZAÇÃO DO PROBLEMA", level=1)
    add_body(doc,
        "A concessão de crédito para o segmento microempresarial (especificamente o nicho "
        "Subprime ou Thin-File) no Brasil e em toda a América Latina enfrenta uma severa "
        "assimetria de informação. As instituições financeiras tradicionais baseiam seus modelos "
        "de risco em dados estáticos e históricos defasados (como apontamentos em birôs de "
        "crédito, scores estáticos ou balanços anuais). Essa abordagem frequentemente penaliza "
        "o microempreendedor por eventos passados, ignorando sua real e atual capacidade de "
        "geração de caixa."
    )
    add_body(doc,
        "Diante desse cenário, esta pesquisa propõe uma mudança de paradigma: a utilização de "
        "dados dinâmicos e de alta frequência, especificamente o registro interno de pagamentos "
        "diários (abonos) e suas respectivas modalidades de liquidação, para avaliar a saúde "
        "financeira do negócio em tempo real. O estudo será viabilizado através do uso de uma "
        "base de dados estratégica fornecida por uma empresa parceira especializada em microcrédito "
        "para o setor informal. O grande diferencial desta abordagem reside em observar a liquidez "
        "diária e a intensidade desses pagamentos parciais, modelando o risco de default não como "
        "um evento binário e estático, mas como um processo dinâmico e contínuo no tempo."
    )


# ── SEÇÃO 2 ──────────────────────────────────────────────────────────────────

def build_secao_2(doc):
    add_heading(doc, "2  OBJETIVOS", level=1)
    add_heading(doc, "2.1  Objetivo Geral", level=2)
    add_body(doc,
        "Desenvolver um modelo preditivo de risco de crédito baseado em Análise de Sobrevivência "
        "(Survival Analysis) para estimar o tempo exato até a ruptura do fluxo de caixa e da "
        "capacidade de pagamento (inadimplência técnica) de microempreendedores, integrando "
        "variáveis estáticas demográficas e dados longitudinais de fluxo transacional de alta "
        "frequência."
    )
    add_heading(doc, "2.2  Objetivos Específicos", level=2)
    items = [
        ("Engenharia de Dados (ETL/RPA):",
         "Projetar e implementar um sistema robusto de ingestão massiva capaz de contornar "
         "limitações de sistemas legados, extraindo e organizando o histórico transacional de "
         "múltiplas unidades de negócio em um Data Lake."),
        ("Data Stitching e MLOps:",
         "Unificar os snapshots temporais em uma Matriz Mestra (Silver Layer) com rastreabilidade "
         "total (Data Lineage) e otimização computacional de memória."),
        ("Tratamento e EDA:",
         "Aplicar o estimador não-paramétrico de Kaplan-Meier para análise exploratória do tempo "
         "de sobrevivência da capacidade de pagamento da carteira, e extrair covariáveis "
         "espaço-temporais (clusters de rotas)."),
        ("Modelagem de Baseline Clássico:",
         "Treinar e ajustar o Modelo de Riscos Proporcionais de Cox para quantificar a inferência "
         "e o impacto das covariáveis estáticas e dependentes do tempo (time-varying covariates) "
         "na função de risco basal."),
        ("Inovação e Aporte Acadêmico (Deep Learning):",
         "Comparar a performance preditiva e a explicabilidade do modelo paramétrico de Cox com "
         "arquiteturas contemporâneas de Deep Learning adaptadas para dados de sobrevivência "
         "(como DeepSurv ou Recurrent Neural Networks — RNNs), incorporando tratamento para "
         "censura (Negative Partial Log-Likelihood)."),
        ("Comparativo Classificatório:",
         "Avaliar os ganhos marginais da abordagem de sobrevivência contra os modelos tradicionais "
         "de Credit Scoring de classificação binária."),
    ]
    for label, text in items:
        p = doc.add_paragraph()
        _set_spacing(p)
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.first_line_indent = Cm(1.25)
        r1 = p.add_run(label + " ")
        _set_font(r1, bold=True)
        r2 = p.add_run(text)
        _set_font(r2)


# ── SEÇÃO 3 ──────────────────────────────────────────────────────────────────

def build_secao_3(doc):
    add_heading(doc, "3  ARQUITETURA DE DADOS E PIPELINE DE EXTRAÇÃO INDUSTRIAL (ETL)", level=1)

    add_heading(doc, "3.1  Contexto e Resolução de Barreiras via Automação (RPA)", level=2)
    add_body(doc,
        "A construção de modelos de análise de sobrevivência exige séries longitudinais precisas. "
        "A fonte primária é o Sistema corporativo ATLAS que não expõe APIs REST e restringe "
        "extrações a janelas de 10 dias em uma interface web baseada em frames aninhados e "
        "autenticação complexa. Para contornar isso, desenvolveu-se a classe orientada a objetos "
        "AtlasDataExtractor em Python 3.12 (Selenium WebDriver). O robô gerencia dinamicamente o "
        "switching entre iframes, injetando JavaScript diretamente no DOM para ignorar bloqueios, "
        "e implementa um mecanismo de retry com três tentativas para lidar com erros de elemento "
        "obsoleto (StaleElementReferenceException) nos controles SELECT2."
    )

    add_heading(doc, "3.2  Escalabilidade Corporativa e Descoberta Automática", level=2)
    add_body(doc,
        "O pipeline evoluiu para um sistema de Ingestão Massiva que opera de forma autônoma. Um "
        "algoritmo de Auto-Discovery navega pela hierarquia de escritórios e rotas mapeando todas "
        "as dependências sem intervenção humana. A infraestrutura detectou automaticamente três "
        "Escritórios e 17 Rotas geográficas, gerando uma extração de 3.962 arquivos Excel com "
        "histórico de 2020 a 2026."
    )

    add_heading(doc, "3.3  Processamento Batch, Filtro Anti-Zero e Persistência", level=2)
    add_body(doc,
        "Devido ao limite de 10 dias por extração do sistema, o algoritmo de paginação temporal "
        "divide o horizonte de aproximadamente seis anos em blocos estritos. O pipeline implementa "
        "três mecanismos de qualidade: (1) Validação de UI — antes de baixar, o robô inspeciona "
        "os campos HTML e aborta o download se os dados retornam nulos, prevenindo viés na curva "
        "de risco basal; (2) Smart Wait — monitoramento assíncrono detecta arquivos temporários "
        "(.crdownload) e renomeia semanticamente cada lote no padrão "
        "planilla_abonos_YYYYMMDD_YYYYMMDD.xlsx; (3) Checkpointing — mecanismo de persistência "
        "de estado em JSON permite que, em caso de falha, a extração seja retomada no exato "
        "último bloco processado com sucesso."
    )
    add_body(doc,
        "A gestão de riscos do pipeline seguiu as sete categorias identificadas na literatura "
        "de gerenciamento de projetos de Ciência de Dados (Louzada Neto, 2026): qualidade dos "
        "dados, orçamento, comprometimento, recursos humanos, fornecedores, segurança da "
        "informação e expectativas de tempo de execução. A estratégia de redução de dependência "
        "de fornecedores foi implementada através de solução in-house de web scraping, eliminando "
        "licenças externas e garantindo controle total sobre o pipeline."
    )

    add_heading(doc, "3.4  Arquitetura do Data Lake, Pipeline de Consolidação e CRISP-DS", level=2)
    add_body(doc,
        "Os arquivos ingeridos alimentam uma hierarquia rígida de diretórios que garante "
        "rastreabilidade total (Data Lineage): data/raw/OFI_{id}/RTA_{id}/planilha.xlsx. "
        "A etapa de consolidação (Data Stitching) transforma os recortes temporais fragmentados "
        "em um gigantesco Painel de Dados Longitudinal contínuo (Silver Layer), apto para os "
        "algoritmos de Sobrevivência."
    )
    add_body(doc,
        "O pipeline é estruturado sob a metodologia CRISP-DS (Cross Industry Standard Process "
        "for Data Science), cujas seis fases mapeiam diretamente às etapas do projeto: "
        "(1) Entendimento do Negócio → definição do evento de castigo de carteira; "
        "(2) Entendimento dos Dados → EDA do dataset de sobrevivência; "
        "(3) Preparação dos Dados → Feature Engineering no formato Counting Process; "
        "(4) Modelagem → Modelo de Cox e DeepSurv; "
        "(5) Avaliação → C-index de Harrell e Brier Score temporal; "
        "(6) Implantação → modelo em produção para scoring dinâmico. "
        "Esta estrutura, independente de ferramenta e setor (Louzada Neto, 2026), garante "
        "que cada fase contribua para as demais de forma iterativa."
    )
    add_body(doc,
        "Para garantir a governança, o pipeline faz o Data Stitching usando o 'Código de "
        "Crédito' como chave, extraindo metadados topológicos (identificadores de rotas e "
        "escritórios) diretamente da hierarquia de diretórios e injetando-os como covariáveis "
        "categóricas em cada registro transacional. Um algoritmo de otimização de memória via "
        "downcasting numérico e categorização de strings reduziu o footprint em RAM em até 49%, "
        "viabilizando o processamento da Matriz Mestra de 882 MB sem erros de Out-of-Memory."
    )


# ── SEÇÃO 4 ──────────────────────────────────────────────────────────────────

def build_secao_4(doc):
    add_heading(doc, "4  ENGENHARIA DE VARIÁVEIS E DEFINIÇÃO DO EVENTO TARGET", level=1)

    # ── 4.1 Fundamentos Teóricos ────────────────────────────────────────────
    add_heading(doc, "4.1  Fundamentos Teóricos da Análise de Sobrevivência", level=2)
    add_body(doc,
        "A análise de sobrevivência compreende um conjunto de técnicas estatísticas projetadas "
        "para modelar o tempo até a ocorrência de um evento de interesse (Kalbfleisch e Prentice, "
        "2002). Diferentemente da regressão logística — que estima a probabilidade de default em "
        "um ponto fixo do tempo —, a análise de sobrevivência incorpora explicitamente a dimensão "
        "temporal, distinguindo entre indivíduos que experimentaram o evento e aqueles observados "
        "sem experimentá-lo (censurados)."
    )

    add_heading(doc, "4.1.1  Função de Sobrevivência e Função de Risco", level=3)
    add_body(doc,
        "Sejam as definições fundamentais para uma variável aleatória contínua não negativa T que "
        "representa o tempo até o evento. A função de sobrevivência é:"
    )
    add_formula(doc, "S(t) = P(T > t) = 1 − F(t)")
    add_body(doc,
        "em que F(t) é a função de distribuição acumulada de T. S(t) representa a probabilidade "
        "de que o indivíduo não tenha experimentado o evento até o tempo t. A função de risco "
        "(hazard function), também denominada taxa de falha instantânea, é:"
    )
    add_formula(doc, "h(t) = lim[Δt→0] P(t ≤ T < t+Δt | T ≥ t) / Δt = f(t) / S(t)")
    add_body(doc,
        "h(t) mede a taxa condicional de ocorrência do evento no instante t, dado que o "
        "indivíduo sobreviveu até aquele momento. É o componente central do modelo de regressão "
        "de Cox. A relação fundamental entre S(t) e h(t) é:"
    )
    add_formula(doc, "S(t) = exp(−∫₀ᵗ h(u) du) = exp(−H(t))")
    add_body(doc,
        "em que H(t) é a função de risco acumulado (cumulative hazard function). Esta relação "
        "mostra que a função de sobrevivência fica completamente determinada pela função de risco."
    )

    add_heading(doc, "4.1.2  Tipos de Censura e Truncação à Esquerda", level=3)
    add_body(doc,
        "Um aspecto crítico da análise de sobrevivência é o tratamento de observações em que o "
        "evento não é observado dentro do período de estudo. A censura à direita (right "
        "censoring) ocorre quando o evento não ocorreu antes do fim da observação — o tipo mais "
        "comum, aplicável aos créditos ativos no corte do estudo (15 de maio de 2026). A "
        "truncação à esquerda (left truncation) ocorre quando o indivíduo entra no estudo em "
        "um momento posterior à origem de risco — no presente trabalho, quando o primeiro "
        "snapshot disponível de um crédito corresponde a uma data posterior ao seu desembolso. "
        "O tratamento correto de ambos os fenômenos — implementado mediante o formato Counting "
        "Process — é condição necessária para a validade estatística do modelo de Cox "
        "(Therneau e Grambsch, 2000)."
    )

    add_heading(doc, "4.1.3  Estimador de Kaplan-Meier", level=3)
    add_body(doc,
        "O estimador de Kaplan-Meier (Kaplan e Meier, 1958) é o estimador não paramétrico "
        "padrão da função de sobrevivência. Sejam t₁ < t₂ < ... < tₖ os tempos distintos em "
        "que ocorreram eventos. Em cada tempo de evento tⱼ, sejam dⱼ o número de eventos e "
        "nⱼ o número de indivíduos em risco. O estimador é:"
    )
    add_formula(doc, "Ŝ(t) = ∏[j: tⱼ ≤ t] (1 − dⱼ/nⱼ)")
    add_body(doc,
        "Suas propriedades principais são: (1) Consistência — converge em probabilidade para "
        "S(t) verdadeiro quando n → ∞; (2) Não paramétrico — não assume nenhuma distribuição "
        "para T; (3) Correção automática por censura — os indivíduos censurados contribuem ao "
        "denominador nⱼ até o momento de sua censura, mas não ao numerador dⱼ. O intervalo de "
        "confiança é obtido pela transformação de Greenwood: "
        "Var[Ŝ(t)] = Ŝ(t)² × Σ[dⱼ / (nⱼ(nⱼ−dⱼ))]."
    )

    add_heading(doc, "4.1.4  Teste de Log-Rank", level=3)
    add_body(doc,
        "O teste de log-rank (Mantel, 1966) compara as curvas de sobrevivência de dois ou mais "
        "grupos sem assumir uma forma paramétrica. A hipótese nula é H₀: S₁(t) = S₂(t) para "
        "todo t. O estatístico Q segue uma distribuição χ² com (k−1) graus de liberdade sob "
        "H₀, onde k é o número de grupos. O teste pondera igualmente todos os tempos de evento "
        "(pesos wⱼ = 1 na versão padrão), sendo mais sensível a diferenças na cauda da "
        "distribuição de sobrevivência."
    )

    add_heading(doc, "4.1.5  Processo de Contagem de Anderson-Gill", level=3)
    add_body(doc,
        "O modelo clássico de Cox assume covariáveis fixas no tempo. Quando as covariáveis "
        "mudam ao longo do seguimento — como o saldo devedor, o número de parcelas atrasadas "
        "ou os dias sem pagar —, é necessário adotar o marco do Processo de Contagem de "
        "Anderson e Gill (1982). Em lugar de uma única observação por indivíduo (T, δ, X), "
        "o indivíduo i é representado mediante uma sequência de intervalos:"
    )
    add_formula(doc, "(t_start₁, t_stop₁, δ₁, X_{i1}), (t_start₂, t_stop₂, δ₂, X_{i2}), ...")
    add_body(doc,
        "As restrições do formato são: (1) os intervalos devem ser contíguos e não sobrepostos: "
        "t_start[k] = t_stop[k−1] exatamente; (2) o evento δ = 1 só pode ocorrer no último "
        "intervalo de cada indivíduo; (3) os intervalos são abertos pela esquerda e fechados "
        "pela direita: (t_start, t_stop]. Este formato — implementado em "
        "lifelines.CoxTimeVaryingFitter e nos modelos de sobrevivência neuronal do pycox — "
        "permite que as covariáveis variem em cada snapshot de observação, capturando dinâmicas "
        "de risco que modelos estáticos não conseguem detectar."
    )

    # ── 4.2 Definição Operacional ────────────────────────────────────────────
    add_heading(doc, "4.2  Definição Operacional da Inadimplência na Alta Frequência", level=2)
    add_body(doc,
        "Diferente do varejo bancário tradicional (onde 1 cota = 30 dias), o modelo operacional "
        "da instituição parceira baseia-se em ciclos diários. A calibração matemática do evento "
        "foi definida sob os seguintes parâmetros:"
    )
    items_42 = [
        ("Equivalência Temporal:",
         "Adota-se a premissa fundamental de que 1 parcela atrasada equivale a 1 dia de atraso real."),
        ("Evento de Falha/Ruptura (E=1):",
         "Definido inicialmente como o atingimento do campo CUOTAS_ATRASADAS igual a 120. "
         "Contudo, a execução empírica do pipeline revelou que esta variável tem teto operacional "
         "equivalente a CUOTAS_PACTADAS (máximo de 40 dias para a coorte diária), "
         "impossibilitando o atingimento de 120 cotas atrasadas — o que produziria exatamente "
         "zero eventos. A definição foi, portanto, revisada para: E=1 quando "
         "dias_sem_pagar ≥ 120 dias calendário. Este limiar representa o denominado 'castigo "
         "de carteira' operativo da instituição: aproximadamente 4 meses de mora ininterrupta "
         "em um crédito cuja vida útil total é de 20 a 40 dias, onde a probabilidade de "
         "recuperação se torna nula. A distinção conceitual central é entre mora transitória "
         "(o cliente atrasa alguns dias mas retoma os pagamentos, reiniciando o cronômetro) e "
         "abandono real (o cliente cessa completamente os pagamentos por mais de 4 meses)."),
        ("Tempo de Sobrevivência (T):",
         "Mensura o número de dias desde o desembolso do microcrédito até o atingimento de "
         "dias_sem_pagar = 120. Clientes ativos, quitados ou com inatividade inferior a 120 dias "
         "no encerramento da base são tratados mediante Censura à Direita (E=0)."),
        ("Critério de Pureza Temporal:",
         "Para garantir a integridade da análise e a convergência dos algoritmos de Deep "
         "Learning, o pipeline aplica um filtro de exclusão para créditos com periodicidade "
         "semanal ou esporádica. O universo de estudo é restrito à coorte de pagamentos "
         "diários (planos de 20, 24, 30 e 40 parcelas), eliminando o ruído transacional."),
    ]
    for label, text in items_42:
        p = doc.add_paragraph()
        _set_spacing(p)
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.first_line_indent = Cm(1.25)
        r1 = p.add_run(label + " ")
        _set_font(r1, bold=True)
        r2 = p.add_run(text)
        _set_font(r2)

    # ── 4.3 Estrutura Bimodal ────────────────────────────────────────────────
    add_heading(doc, "4.3  Estrutura Bimodal de Atributos e Estratégia de Proxy", level=2)
    for txt in [
        "Variáveis Estáticas: Parâmetros do crédito (Valor de Crédito, Valor de Parcela, "
        "Cotas Pactadas).",
        "Geodemographic Proxy: Diante da informalidade do setor e da ausência de variáveis "
        "demográficas estruturadas (como idade exata ou CNAE setorial), o modelo utiliza a "
        "localização geográfica (IDs de Rota e Escritório) como covariáveis de controle. "
        "Assume-se que a geografia atua como um proxy socioeconômico robusto para capturar o "
        "comportamento de risco local da rede comercial.",
        "Variáveis Dinâmicas (Heartbeat): O vetor longitudinal de pagamentos, parcelas em "
        "atraso no tempo t, intensidade transacional de abonos "
        "(Valor do Último Abono / Valor da Parcela) e dias com abono, capturando a verdadeira "
        "'frequência cardíaca' financeira do empreendedor.",
    ]:
        add_body(doc, txt)

    # ── 4.4 Formatação Anderson-Gill ─────────────────────────────────────────
    add_heading(doc, "4.4  Formatação Anderson-Gill (Counting Process)", level=2)
    add_body(doc,
        "Para o modelamento correto das covariáveis dependentes do tempo, a matriz transacional "
        "é transformada em intervalos longitudinais contínuos (t_start, t_stop]. A engenharia "
        "de features resolveu dois desafios matemáticos críticos:"
    )
    for label, text in [
        ("Left Truncation:",
         "Créditos que se originam dentro de uma janela de observação ativa têm seu tempo de "
         "início corrigido via função max(0, dias), prevenindo tempos de vida negativos que "
         "colapsariam a função de verossimilhança. A fórmula aplicada é: "
         "t_start(primeira linha) = max(0, data_ini_bloco − DATA_CRÉDITO) em dias."),
        ("Continuidade de Markov:",
         "A transição entre intervalos garante estritamente que t_start[n] = t_stop[n−1] "
         "através de funções de janela (shift), eliminando gaps temporais que fariam o modelo "
         "assumir o desaparecimento artificial do cliente. O t_stop sempre provém do nome do "
         "arquivo Excel (data de fim do bloco de 10 dias)."),
    ]:
        p = doc.add_paragraph()
        _set_spacing(p)
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.first_line_indent = Cm(1.25)
        r1 = p.add_run(label + " ")
        _set_font(r1, bold=True)
        r2 = p.add_run(text)
        _set_font(r2)

    # ── 4.5 Construção do Dataset ────────────────────────────────────────────
    add_heading(doc, "4.5  Construção do Dataset de Sobrevivência", level=2)

    add_heading(doc, "4.5.1  Fonte de Dados: Sistema ATLAS e Data Lake", level=3)
    add_body(doc,
        "O Sistema ATLAS é a "
        "plataforma de gestão creditícia da instituição parceira. Os dados brutos foram "
        "extraídos mediante o pipeline ETL automatizado com Selenium WebDriver, baixando "
        "relatórios Excel (Planilha de Abonos) para cada combinação de escritório e rota "
        "em blocos de 10 dias calendário."
    )
    add_table_data(
        doc,
        ["Componente", "Volume"],
        [
            ["Arquivos Excel baixados", "3.962 arquivos"],
            ["Escritórios cobertos", "3 (OFI_23 São Paulo, OFI_31 Soc. Brasil, OFI_44 Cabo Frio)"],
            ["Rotas cobertas", "17"],
            ["Período de cobertura", "2020-01-01 → 2026-05-15"],
            ["Tamanho do Data Lake (bruto)", "~14 GB"],
        ],
        "Componentes e volume do Data Lake extraído",
        table_num=1,
    )
    add_table_data(
        doc,
        ["Métrica", "Valor"],
        [
            ["Linhas (observações)", "344.869"],
            ["Colunas totais", "2.358"],
            ["Colunas de pagamentos diários", "~2.330"],
            ["Colunas estáticas do crédito", "28"],
            ["Tamanho em disco", "882 MB"],
            ["Tamanho em RAM (expandido)", "~6 GB"],
        ],
        "Dimensões da Matriz Mestra após consolidação",
        table_num=2,
    )
    add_body(doc,
        "A escala do dataset impossibilita sua carga completa em memória. Por esta razão, o "
        "pipeline de engenharia de características implementa leitura por chunks de 5.000 "
        "linhas com máscara vetorizada NumPy (n_linhas × n_colunas_pagamento) para calcular "
        "os agregados de pagamento em tempo real sem materializar as ~2.330 colunas de data "
        "em RAM, processando aproximadamente 5.000 linhas por segundo."
    )

    add_heading(doc, "4.5.2  Filtro de Coorte Diária", level=3)
    add_body(doc,
        "O portfólio da instituição contém créditos com frequências de pagamento heterogêneas: "
        "diária, semanal, quinzenal e mensal. Para garantir a homogeneidade do grupo sob análise "
        "e a correta interpretação do cronômetro de inatividade, aplica-se o seguinte critério "
        "de inclusão: créditos de pagamento diário são aqueles cujo número de cotas pactuadas "
        "(CUOTAS_PACTADAS) é ≤ 40. A justificativa operativa é que créditos com mais de 40 "
        "cotas são de modalidade semanal ou quinzenal, e seus padrões de mora não são "
        "diretamente comparáveis com os créditos diários."
    )
    add_table_data(
        doc,
        ["Coorte", "Critério", "Créditos"],
        [
            ["Diária (incluída)", "CUOTAS_PACTADAS ≤ 40", "28.386"],
            ["Semanal/quinzenal/mensal (excluída)", "CUOTAS_PACTADAS > 40", "—"],
        ],
        "Filtro de coorte diária: critério e créditos retidos",
        table_num=3,
    )

    add_heading(doc, "4.5.3  Cronômetro de Inatividade Financeira (forward-fill)", level=3)
    add_body(doc,
        "O cálculo de dias_sem_pagar segue uma lógica de forward-fill sobre a data do último "
        "pagamento efetivo: (1) Inicializar data_ultimo_pagamento_efetivo = DATA_CRÉDITO; "
        "(2) Para cada bloco (snapshot) t: se dias_com_abono > 0, atualizar "
        "data_ultimo_pagamento_efetivo = data_fim_bloco; caso contrário, manter o valor do "
        "bloco anterior; (3) dias_sem_pagar[t] = (data_fim_bloco − data_ultimo_pagamento_efetivo).dias."
    )
    add_body(doc,
        "Esta lógica possui as seguintes propriedades: (a) Semente correta — o crédito arranca "
        "com dias_sem_pagar = 0 na data de desembolso; (b) Reinicialização automática — qualquer "
        "abono, mesmo que mínimo, reinicia o cronômetro a zero; (c) Acumulação contínua — a "
        "inatividade se acumula ao longo de múltiplos blocos consecutivos sem pagamento; "
        "(d) Clipagem inferior — dias_sem_pagar é definido como max(0, dias calculados) para "
        "evitar valores negativos por dessincronização de datas."
    )

    add_heading(doc, "4.5.4  Correções do Formato Counting Process", level=3)
    add_body(doc,
        "Após a ocorrência do evento (dias_sem_pagar ≥ 120), a trajetória do crédito é "
        "truncada: os snapshots posteriores ao evento são eliminados. Esta regra garante que "
        "o evento de default seja o último intervalo observado de cada crédito, respeitando "
        "a condição de absorção do modelo de sobrevivência. A fórmula do t_stop e a herança "
        "do t_start via shift garantem a cadeia perfeita exigida pelo modelo de Cox:"
    )
    add_formula(doc, "t_stop[t] = (data_fim_bloco[t] − DATA_CRÉDITO).dias + 1")
    add_formula(doc, "t_start[t] = t_stop[t−1]  para  t > 1")

    add_heading(doc, "4.5.5  Variáveis Covariadas", level=3)
    add_table_data(
        doc,
        ["Variável", "Tipo", "Descrição"],
        [
            ["t_start", "Contínua", "Início do intervalo (dias desde o desembolso)"],
            ["t_stop",  "Contínua", "Fim do intervalo (dias desde o desembolso)"],
            ["evento",  "Binária",  "1 = default (dias_sem_pagar ≥ 120), 0 = censura"],
            ["dias_sem_pagar", "Discreta", "Cronômetro de inatividade financeira"],
        ],
        "Variáveis de tempo e evento do dataset de sobrevivência",
        table_num=4,
    )
    add_table_data(
        doc,
        ["Variável", "Fórmula", "Interpretação"],
        [
            ["cuotas_atrasadas",        "CUOTAS_ATRASADAS",                    "Dias em mora no snapshot"],
            ["pago_promedio_diario",    "Σ(pagamentos_bloco) / dias_bloco",    "Fluxo médio de pagamentos (BRL)"],
            ["dias_con_abono",          "#{dias com abono > 0} no bloco",      "Frequência de pagamento no período"],
            ["intensidade_recuperacao","VALOR_ÚLTIMO_ABONO / VALOR_COTA",      "Fração da cota paga (clip [0,10])"],
            ["ratio_atraso",            "CUOTAS_ATRASADAS / CUOTAS_PACTADAS", "Fração do prazo em mora (clip [0,1])"],
            ["saldo_relativo",          "SALDO / TOTAL_CRÉDITO",               "Fração do crédito pendente (clip [0,1])"],
        ],
        "Covariáveis tempo-variantes e suas fórmulas",
        table_num=5,
    )
    add_table_data(
        doc,
        ["Variável", "Descrição"],
        [
            ["total_credito",    "Montante original do crédito (BRL)"],
            ["valor_cota",       "Valor da cota diária pactuada (BRL)"],
            ["cotas_pactadas",   "Prazo do crédito em dias"],
            ["ofi_id",           "Identificador de escritório (proxy geográfico)"],
            ["rta_id",           "Identificador de rota (proxy de zona/cobrador)"],
        ],
        "Covariáveis estáticas do modelo",
        table_num=6,
    )

    # ── 4.6 EDA ──────────────────────────────────────────────────────────────
    add_heading(doc, "4.6  Análise Exploratória de Dados (EDA)", level=2)
    add_body(doc,
        "A análise exploratória foi desenvolvida no notebook notebooks/01_eda_survival.ipynb, "
        "gerando nove figuras de diagnóstico (Figuras 1–9) documentadas nas subseções seguintes."
    )

    add_heading(doc, "4.6.1  Caracterização Geral do Dataset", level=3)
    add_table_data(
        doc,
        ["Métrica", "Valor"],
        [
            ["Créditos únicos",              "28.386"],
            ["Intervalos totais (linhas)",   "301.434"],
            ["Eventos (E=1)",                "425"],
            ["Taxa de default (nível crédito)", "1,50%"],
            ["Créditos censurados (E=0)",    "27.961 (98,50%)"],
            ["Escritórios",                  "3"],
            ["Rotas",                        "17"],
            ["Período de observação",        "2020-01-01 → 2026-05-15 (~6,4 anos)"],
        ],
        "Caracterização geral do dataset de sobrevivência",
        table_num=7,
    )
    add_body(doc,
        "O baixo índice de default (1,50%) reflete a dinâmica operativa do microcrédito de "
        "pagamento diário: a instituição realiza gestão de cobrança intensiva por meio do "
        "cobrador de rota (gestora), reduzindo significativamente a incidência de abandono "
        "total. A maioria dos inadimplentes é de caráter transitório e se resolve antes de "
        "atingir os 120 dias de inatividade."
    )

    add_heading(doc, "4.6.2  Distribuição do Evento de Default", level=3)
    add_figure(doc, BASE / "reports" / "fig01_distribucion_evento.png",
               "Distribuição do evento de default: proporção (pie), taxa por escritório e taxa por rota", 1)
    add_table_data(
        doc,
        ["Escritório", "Créditos", "Eventos", "Taxa de Default"],
        [
            ["OFI_23 (São Paulo)",     "14.031", "126", "0,90%"],
            ["OFI_31 (Soc. Brasil)",    "7.333",  "53",  "0,72%"],
            ["OFI_44 (Cabo Frio)",      "7.022",  "246", "3,50%"],
        ],
        "Taxa de default por escritório",
        table_num=8,
    )
    add_body(doc,
        "O escritório OFI_44 (Cabo Frio) apresenta uma taxa de default quase quatro vezes "
        "superior às demais oficinas (3,50% vs. 0,72–0,90%). Esta heterogeneidade geográfica "
        "é estatisticamente relevante para o modelo de Cox: ofi_id e rta_id atuam como "
        "variáveis proxy do contexto socioeconômico local, a intensidade de supervisão do "
        "cobrador e a composição do portfólio de clientes. A distribuição da taxa de default "
        "por rota (Figura 1) revela heterogeneidade adicional: algumas rotas dentro de OFI_44 "
        "concentram a maioria dos eventos, sugerindo que o risco é fortemente localizado a "
        "nível de cobrador/zona de cobrança."
    )

    add_heading(doc, "4.6.3  Curva de Kaplan-Meier Global", level=3)
    add_figure(doc, BASE / "reports" / "fig02_kaplan_meier_global.png",
               "Curva de Kaplan-Meier global do portfólio com tabela de n em risco", 2)
    add_table_data(
        doc,
        ["Tempo (dias)", "S(t)", "Risco Acumulado"],
        [
            ["30",  "1,0000", "0,00%"],
            ["60",  "1,0000", "0,00%"],
            ["90",  "1,0000", "0,00%"],
            ["120", "1,0000", "0,00%"],
            ["180", "0,6815", "31,85%"],
            ["270", "0,6788", "32,12%"],
            ["365", "0,1673", "83,27%"],
            ["540", "0,0908", "90,92%"],
        ],
        "Valores da curva de Kaplan-Meier global",
        table_num=9,
    )
    add_body(doc,
        "Os quatro primeiros pontos da curva — todos com S(t) = 1,0 — não implicam que não "
        "existam defaults antes do dia 120. Implicam que, entre os créditos que sobrevivem "
        "além desses prazos, nenhum experimentou o evento ainda. Isto é consistente com a "
        "definição do evento: dias_sem_pagar ≥ 120 é impossível antes de o crédito ter pelo "
        "menos ~120 dias de antiguidade."
    )
    add_body(doc,
        "O salto brusco entre o dia 120 e o dia 180 — de S = 1,0 para S = 0,68 — reflete que "
        "os créditos que atingem os 120–180 dias de antiguidade têm um perfil de risco "
        "radicalmente diferente da maioria: são créditos que persistiram muito além do seu "
        "prazo original (20–40 dias), evidenciando que permanecem no portfólio por renovações "
        "sucessivas ou por incapacidade de encerramento. Para o dia 365, o 83,3% dos créditos "
        "que atingiram esse horizonte temporal experimentaram o evento de castigo. Esta "
        "estrutura temporal — risco nulo no curto prazo, risco elevado em horizontes longos — "
        "caracteriza os microcreditos de pagamento diário e justifica o uso da análise de "
        "sobrevivência sobre a regressão logística."
    )

    add_heading(doc, "4.6.4  Análise Estratificada por Escritório (Teste de Log-Rank)", level=3)
    add_figure(doc, BASE / "reports" / "fig03_kaplan_meier_oficinas.png",
               "Curvas de Kaplan-Meier por escritório com teste de log-rank (OFI_23 vs. OFI_44)", 3)
    add_table_data(
        doc,
        ["Estatístico", "Valor"],
        [
            ["χ² (log-rank)", "0,0817"],
            ["p-valor",       "0,7750"],
        ],
        "Resultado do teste de log-rank (OFI_23 vs. OFI_44)",
        table_num=10,
    )
    add_body(doc,
        "O p-valor de 0,775 indica que não se pode rejeitar a hipótese nula de igualdade de "
        "curvas de sobrevivência entre OFI_23 e OFI_44 ao nível de significância de 5%. "
        "Este resultado — aparentemente contraditório com a marcada diferença nas taxas brutas "
        "de default (0,90% vs. 3,50%) — pode ser explicado por: (1) diferença no timing do "
        "evento — o teste de log-rank compara a função de sobrevivência em cada ponto do tempo; "
        "se OFI_44 e OFI_23 experimentam seus eventos em momentos similares, o teste não "
        "detecta diferença; (2) créditos em risco — a horizontes temporais longos, o número de "
        "créditos em risco se reduz drasticamente, diminuindo o poder estatístico do teste. "
        "Esta limitação do teste não paramétrico motiva o uso do modelo de Cox, que pode "
        "controlar simultaneamente por múltiplas covariáveis e capturar o efeito marginal de "
        "ofi_id ajustando pelas diferenças no perfil dos clientes."
    )

    add_heading(doc, "4.6.5  Tempo de Seguimento e Granularidade Longitudinal", level=3)
    add_figure(doc, BASE / "reports" / "fig04_tiempo_seguimiento.png",
               "Distribuição do tempo de seguimento (t_stop) e número de intervalos por crédito", 4)
    add_table_data(
        doc,
        ["Estatístico", "t_stop (dias)", "n_intervalos"],
        [
            ["Mediana",      "29 dias", "3"],
            ["Média",        "36 dias", "10,6"],
            ["Percentil 25", "24 dias", "—"],
            ["Percentil 75", "35 dias", "—"],
            ["Máximo",       "815 dias", "233"],
        ],
        "Estatísticas do tempo de seguimento e intervalos por crédito",
        table_num=11,
    )
    add_body(doc,
        "A mediana de 29 dias reflete que a maioria dos créditos do portfólio são de curto "
        "prazo (20–30 dias) e têm poucas renovações. No entanto, a distribuição apresenta uma "
        "cauda direita pronunciada: alguns créditos acumulam até 815 dias de seguimento e 233 "
        "snapshots de 10 dias, correspondendo a clientes com múltiplas renovações consecutivas "
        "ou que permaneceram no portfólio sem encerrar durante anos. Esta estrutura bimodal — "
        "maioria de créditos curtos + cauda de créditos de longa permanência — é típica do "
        "microcrédito de pagamento diário e justifica o uso da análise de sobrevivência."
    )

    add_heading(doc, "4.6.6  Cronômetro dias_sem_pagar", level=3)
    add_figure(doc, BASE / "reports" / "fig05_dias_sin_pagar.png",
               "Distribuição de dias_sem_pagar: global, zoom 0–150 dias e máximo por crédito", 5)
    add_table_data(
        doc,
        ["Estatístico", "Valor"],
        [
            ["Mediana",      "0 dias"],
            ["Percentil 75", "0 dias"],
            ["Percentil 95", "0 dias"],
            ["Percentil 99", "26 dias"],
            ["Máximo",       "400 dias"],
        ],
        "Estatísticas do cronômetro dias_sem_pagar",
        table_num=12,
    )
    add_body(doc,
        "O cronômetro de inatividade apresenta uma distribuição fortemente concentrada em zero: "
        "em mais de 95% de todos os intervalos observados, o crédito tem dias_sem_pagar = 0, "
        "ou seja, o cliente realizou pelo menos um abono durante o bloco de 10 dias. Os valores "
        "altos (> 26 dias) são estatisticamente raros (< 1% dos intervalos) e correspondem "
        "quase exclusivamente aos créditos que eventualmente experimentam o evento de default. "
        "A correlação de Pearson entre dias_sem_pagar e evento é r = 0,680 — a correlação mais "
        "alta do conjunto de covariáveis com a variável alvo — confirmando que o cronômetro "
        "captura eficazmente o sinal preditivo do abandono creditício."
    )

    add_heading(doc, "4.6.7  Análise de Covariáveis: Default vs. Censurado", level=3)
    add_figure(doc, BASE / "reports" / "fig06_covariables_evento.png",
               "Distribuição das covariáveis por grupo: Default (E=1) versus Censurado (E=0)", 6)
    add_table_data(
        doc,
        ["Covariável", "r com evento", "Direção"],
        [
            ["dias_sem_pagar",           "+0,6796", "Cronômetro direto do evento"],
            ["saldo_relativo",           "−0,0350", "Maior saldo → menor probabilidade de default"],
            ["dias_con_abono",           "−0,0217", "Mais dias com abono → menor risco"],
            ["ratio_atraso",             "−0,0176", "Contra-intuitivo; explicado por composição"],
            ["cuotas_atrasadas",         "−0,0166", "Idem"],
            ["pago_promedio_diario",     "−0,0152", "Mais pagamentos → menor risco"],
            ["intensidade_recuperacao",  "+0,0071", "Efeito misto"],
        ],
        "Correlações das covariáveis com o evento",
        table_num=13,
    )
    add_body(doc,
        "As correlações das covariáveis de mora e pagamento com o evento são negativas, mas de "
        "magnitude muito baixa. Isto não implica ausência de efeito preditivo, mas que as "
        "correlações lineares de Pearson não capturam a relação não linear e dinâmica entre "
        "essas variáveis e o risco no contexto do Counting Process. O modelo de Cox de hazard "
        "proporcional poderá quantificar esses efeitos corretamente."
    )

    add_heading(doc, "4.6.8  Perfil Econômico do Portfólio", level=3)
    add_figure(doc, BASE / "reports" / "fig07_perfil_credito.png",
               "Perfil econômico do portfólio: distribuição do prazo, montante e boxplot por evento", 7)
    add_table_data(
        doc,
        ["Estatístico", "Valor"],
        [
            ["Mediana",      "R$ 1.200"],
            ["Média",        "R$ 1.491"],
            ["Percentil 10", "R$ 540"],
            ["Percentil 90", "R$ 3.000"],
        ],
        "Montante do crédito por grupo de evento",
        table_num=14,
    )
    add_body(doc,
        "Os créditos são de baixo montante (mediana R$ 1.200), confirmando o perfil de "
        "microcrédito de pagamento diário destinado a trabalhadores informais e "
        "microempreendedores com necessidades de liquidez de curto prazo. A distribuição do "
        "prazo está altamente concentrada em três valores discretos: 20 dias (17.812 créditos, "
        "62,7%) — o produto principal; 24 dias (8.330 créditos, 29,3%) — segunda opção padrão; "
        "30 dias (1.488 créditos, 5,2%) — prazo estendido. Esta concentração em modalidades "
        "padrão reflete que os prazos são produtos pré-definidos pela instituição, não "
        "negociados individualmente. A grande maioria do portfólio (92,0%) tem prazo de 20 "
        "ou 24 dias."
    )

    add_heading(doc, "4.6.9  Estrutura de Correlações", level=3)
    add_figure(doc, BASE / "reports" / "fig08_correlaciones.png",
               "Mapa de calor de correlações das covariáveis do modelo de sobrevivência (triângulo inferior)", 8)
    add_body(doc,
        "O mapa de calor de correlações (Figura 8, triângulo inferior) revela as seguintes "
        "relações significativas entre covariáveis: (1) ratio_atraso ↔ cuotas_atrasadas "
        "(r ≈ +0,90): correlação esperada, já que ratio_atraso = cuotas_atrasadas / "
        "cotas_pactadas — ambas as variáveis medem essencialmente a mesma coisa em escalas "
        "diferentes; no modelo de Cox final, deverá ser incluída apenas uma das duas para "
        "evitar multicolinearidade; (2) dias_sem_pagar ↔ evento (r = 0,68): cronômetro direto "
        "do evento; (3) pago_promedio_diario ↔ dias_con_abono: correlação positiva esperada. "
        "A ausência de correlações altas (> 0,7) entre as demais covariáveis indica que o "
        "conjunto de variáveis selecionado não apresenta problemas graves de multicolinearidade."
    )

    add_heading(doc, "4.6.10  Análise de Trajetórias Individuais", level=3)
    add_figure(doc, BASE / "reports" / "fig09_trayectorias.png",
               "Trajetórias individuais de dias_sem_pagar: 5 créditos em default versus 5 censurados", 9)
    add_body(doc,
        "A visualização de trajetórias individuais — 5 créditos em default e 5 censurados "
        "(Figura 9) — permite validar qualitativamente a lógica do cronômetro. Nos créditos em "
        "default, o cronômetro dias_sem_pagar cresce monotonicamente durante os últimos blocos "
        "de observação, cruzando o limiar de 120 dias exatamente no intervalo marcado como "
        "evento (E=1). Nos créditos censurados, o cronômetro permanece em zero ou próximo de "
        "zero durante toda a trajetória, com eventuais subidas breves seguidas de reinicialização "
        "imediata ao ocorrer um abono. Isto confirma que o mecanismo de forward-fill captura "
        "corretamente a mora transitória."
    )

    # ── 4.7 Síntese e Validação ──────────────────────────────────────────────
    add_heading(doc, "4.7  Síntese e Validação do Dataset", level=2)
    add_table_data(
        doc,
        ["Validação", "Resultado"],
        [
            ["t_stop > t_start em todos os intervalos",  "✓ Verificado"],
            ["Cadeia perfeita t_start[k] = t_stop[k−1]", "✓ Verificado (via shift)"],
            ["Evento E=1 apenas no último intervalo",     "✓ Aplicado pela regra de censura"],
            ["Sem valores nulos em colunas-chave",        "✓ Verificado"],
            ["Número de eventos > 100",                   "✓ 425 eventos"],
            ["Covariáveis numéricas em faixa esperada",  "✓ Clip aplicado a todas as razões"],
        ],
        "Validação do formato Counting Process",
        table_num=15,
    )
    add_body(doc,
        "A definição do evento como dias_sem_pagar ≥ 120 demonstrou ser operacionalmente válida "
        "e estatisticamente estável, produzindo uma taxa de default de 1,50% coerente com as "
        "referências de microcrédito de pagamento diário em economias emergentes (Schreiner, "
        "2002; Banerjee e Duflo, 2007). O dataset fica preparado para a etapa seguinte: ajuste "
        "do Modelo de Cox de Riscos Proporcionais com covariáveis tempo-variantes."
    )


# ── SEÇÃO 5 ──────────────────────────────────────────────────────────────────

def build_secao_5(doc):
    add_heading(doc, "5  MODELAGEM MATEMÁTICA E COMPUTACIONAL (O DESAFIO DA CENSURA)", level=1)

    add_heading(doc, "5.1  Baseline Clássico (Modelo de Cox)", level=2)
    add_body(doc,
        "A fase inicial aplicará o Modelo de Riscos Proporcionais de Cox para estabelecer o "
        "marco regulatório de interpretabilidade e quantificar o impacto das covariáveis "
        "estáticas e dinâmicas (Hazard Ratios). A análise dos Resíduos de Schoenfeld servirá "
        "como diagnóstico para validar as limitações da proporcionalidade em dados de alta "
        "frequência. [RESULTADO PENDENTE — Etapa de modelagem em andamento]"
    )

    add_heading(doc, "5.2  O Desafio da Censura à Direita em Arquiteturas Neurais", level=2)
    add_body(doc,
        "Diferentemente da regressão logística convencional que utiliza o Erro Quadrático "
        "Médio (MSE) ou a Entropia Cruzada, arquiteturas de Deep Learning tradicionais falham "
        "ao ignorar a informação contida nos registros censurados à direita (clientes que "
        "continuam ativos ao fim do período de extração e não alcançaram o evento de falha). "
        "Descartar ou classificar essas observações como zeros introduz um viés severo e "
        "subestima o tempo real de sobrevivência."
    )

    add_heading(doc, "5.3  Abordagem Estado da Arte (Deep Learning sob Censura)", level=2)
    add_body(doc,
        "Para contornar as limitações estritas da proporcionalidade e incorporar o aprendizado "
        "sequencial sem perder as observações censuradas, a pesquisa implementará redes neurais "
        "recorrentes (como LSTM ou GRU) integradas à Análise de Sobrevivência "
        "(DeepSurv/RNN-Survival). O avanço metodológico fundamental desta proposta consiste em "
        "substituir as funções de perda convencionais pela otimização direta da Verossimilhança "
        "Parcial Negativa (Negative Partial Log-Likelihood) na última camada da rede. Dessa "
        "forma, a arquitetura de IA aprenderá os padrões complexos e as dependências não "
        "lineares da memória temporal de pagamentos diários, respeitando e incorporando "
        "matematicamente o tempo de sobrevivência acumulado dos clientes sob censura. "
        "[IMPLEMENTAÇÃO PENDENTE — Sprint 3]"
    )


# ── SEÇÃO 6 ──────────────────────────────────────────────────────────────────

def build_secao_6(doc):
    add_heading(doc, "6  VALIDAÇÃO", level=1)
    add_body(doc,
        "Testes de performance compararão o modelo de sobrevivência clássico com as técnicas "
        "de Deep Learning, utilizando métricas específicas para dados censurados: C-index de "
        "Harrell (concordance index), Brier Score temporal e Teste de Log-Rank. "
        "[RESULTADOS PENDENTES — Sprint 4]"
    )


# ── SEÇÃO 7 ──────────────────────────────────────────────────────────────────

def build_secao_7(doc):
    add_heading(doc, "7  CRONOGRAMA INTEGRADO DE PESQUISA", level=1)
    add_body(doc,
        "O projeto é estruturado em quatro sprints Scrum (Louzada Neto, 2026), com entregas "
        "iterativas que permitem ajustes de escopo sem comprometer o prazo final:"
    )
    sprints = [
        ("Sprint 1 (Jan–Mar 2026) — ETL/Pipeline [CONCLUÍDO]:",
         "Desenvolvimento do extrator Selenium (AtlasDataExtractor), extração de 3.962 "
         "arquivos Excel (3 escritórios, 17 rotas, 2020–2026), consolidação da Matriz "
         "Mestra (344.869 × 2.358) e otimização de memória (−49% RAM)."),
        ("Sprint 2 (Mar–Mai 2026) — Feature Engineering + EDA [CONCLUÍDO]:",
         "Definição e implementação do cronômetro dias_sem_pagar, construção do dataset "
         "de sobrevivência no formato Counting Process (28.386 créditos, 301.434 intervalos, "
         "425 eventos), análise exploratória completa com 9 figuras de diagnóstico e "
         "elaboração do relatório metodológico (Seção 4 do TCC)."),
        ("Sprint 3 (Jun–Ago 2026) — Modelagem Cox + DeepSurv [PENDENTE]:",
         "Ajuste do Modelo de Riscos Proporcionais de Cox com covariáveis tempo-variantes, "
         "diagnóstico de resíduos de Schoenfeld, implementação de DeepSurv/RNN-Survival com "
         "Negative Partial Log-Likelihood e comparação de Hazard Ratios."),
        ("Sprint 4 (Set–Nov 2026) — Avaliação + Redação final [PENDENTE]:",
         "Cálculo do C-index de Harrell, Brier Score temporal e Teste de Log-Rank entre "
         "modelos, comparativo com Credit Scoring binário (regressão logística), redação "
         "das seções de Resultados, Discussão e Conclusão do TCC."),
    ]
    for label, text in sprints:
        p = doc.add_paragraph()
        _set_spacing(p)
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.first_line_indent = Cm(1.25)
        r1 = p.add_run(label + " ")
        _set_font(r1, bold=True)
        r2 = p.add_run(text)
        _set_font(r2)


# ── REFERÊNCIAS ───────────────────────────────────────────────────────────────

def build_referencias(doc):
    add_heading(doc, "REFERÊNCIAS BIBLIOGRÁFICAS", level=1)
    refs = [
        "ALTMAN, E. I.; SABATO, G. Modeling Credit Risk for SMEs: Evidence from the US Market. "
        "Abacus, v. 43, n. 3, p. 332–357, 2007.",

        "ANDERSON, P. K.; GILL, R. D. Cox's regression model for counting processes: a large "
        "sample study. The Annals of Statistics, v. 10, n. 4, p. 1100–1120, 1982.",

        "BANERJEE, A. V.; DUFLO, E. The economic lives of the poor. Journal of Economic "
        "Perspectives, v. 21, n. 1, p. 141–167, 2007.",

        "KALBFLEISCH, J. D.; PRENTICE, R. L. The Statistical Analysis of Failure Time Data. "
        "2. ed. New York: Wiley, 2002.",

        "KAPLAN, E. L.; MEIER, P. Nonparametric estimation from incomplete observations. "
        "Journal of the American Statistical Association, v. 53, n. 282, p. 457–481, 1958.",

        "KATZMAN, J. L. et al. DeepSurv: personalized treatment recommender system using a Cox "
        "proportional hazards deep neural network. BMC Medical Research Methodology, v. 18, "
        "n. 24, 2018.",

        "KIM, Jong-Min. Deep Learning in Survival Analysis: Recent Advances and Multimodal "
        "Approaches. 2026.",

        "KLEIN, J. P.; MOESCHBERGER, M. L. Survival Analysis: Techniques for Censored and "
        "Truncated Data. 2. ed. New York: Springer, 2003.",

        "LOUZADA NETO, F. Gestão de Projetos de Ciência de Dados e Inteligência Artificial. "
        "Material didático — MBA em Ciência de Dados. ICMC/USP, São Carlos, 2026.",

        "MANTEL, N. Evaluation of survival data and two new rank order statistics arising in "
        "its consideration. Cancer Chemotherapy Reports, v. 50, n. 3, p. 163–170, 1966.",

        "SCHREINER, M. Aspects of outreach: a framework for discussion of the social benefits "
        "of microfinance. Journal of International Development, v. 14, n. 5, p. 591–603, 2002.",

        "THERNEAU, T. M.; GRAMBSCH, P. M. Modeling Survival Data: Extending the Cox Model. "
        "New York: Springer, 2000.",
    ]
    for ref in refs:
        p = doc.add_paragraph()
        _set_spacing(p, multiple=1.0)
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.first_line_indent = Cm(0)
        p.paragraph_format.left_indent = Cm(0)
        p.paragraph_format.space_after  = Pt(6)
        run = p.add_run(ref)
        _set_font(run, bold=True)


# ── MAIN — gera versão PT e chama o gerador ES ───────────────────────────────

def build_doc():
    """Gera a versão em Português."""
    doc = Document()
    configure_doc(doc)

    build_capa(doc)
    build_resumo(doc)
    build_abstract(doc)
    build_listas(doc)
    build_sumario(doc)

    build_secao_1(doc)
    build_secao_2(doc)
    build_secao_3(doc)
    build_secao_4(doc)
    build_secao_5(doc)
    build_secao_6(doc)
    build_secao_7(doc)
    build_referencias(doc)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUTPUT)
    print(f"\n[PT] V21 gerado com sucesso: {OUTPUT}")
    print(f"     Tamanho: {OUTPUT.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    import subprocess, sys

    # 1. Versão em Português
    build_doc()

    # 2. Versão em Espanhol (script separado)
    es_script = Path(__file__).parent / "gerar_tcc_v21_es.py"
    if es_script.exists():
        print("\n[ES] Gerando versão em Espanhol...")
        result = subprocess.run([sys.executable, str(es_script)], capture_output=True, text=True)
        print(result.stdout)
        if result.returncode != 0:
            print("ERRO:", result.stderr)
    else:
        print(f"\n[ES] Script não encontrado: {es_script}")
