"""
gerar_tcc_v22_es.py — Generador del TCC V22 (Español).

Mirror de gerar_tcc_v22.py con todo el contenido traducido al español.
Novedades vs. V21_es:
  - §3 completamente expandida: 6 subsecciones con detalle técnico completo
    del pipeline ETL (autenticación, frameset, batch, auto-discovery, Data Lake,
    checkpoint, Data Stitching, chunked loading NumPy, LGPD, CRISP-DS)
  - 8 nuevas tablas en §3 (total: 21 tablas en el documento)
  - SUMARIO y LISTA DE TABLAS actualizados

Output: documentotcc/TCC_V22_Espanol_Completo.docx
"""

from pathlib import Path
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING

BASE   = Path(__file__).parent.parent
OUTPUT = BASE / "documentotcc" / "TCC_V22_Espanol_Completo.docx"
REPORTS = BASE / "reports"


# ── Helpers de formato USP ────────────────────────────────────────────────────

def _set_spacing(paragraph, multiple=1.5):
    pf = paragraph.paragraph_format
    pf.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
    pf.line_spacing      = multiple
    pf.space_before      = Pt(0)
    pf.space_after       = Pt(6)


def _set_font(run, size=12, bold=False, italic=False):
    run.font.name   = "Arial"
    run.font.size   = Pt(size)
    run.font.bold   = bold
    run.font.italic = italic


def add_body(doc, text, align=WD_ALIGN_PARAGRAPH.JUSTIFY, indent_first=True):
    p = doc.add_paragraph()
    _set_spacing(p)
    p.alignment = align
    if indent_first:
        p.paragraph_format.first_line_indent = Cm(1.25)
    run = p.add_run(text)
    _set_font(run)
    return p


def add_heading(doc, text, level=1):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    _set_spacing(p, multiple=1.0)
    p.paragraph_format.space_before      = Pt(12)
    p.paragraph_format.space_after       = Pt(6)
    p.paragraph_format.first_line_indent = Cm(0)
    sizes = {1: 16, 2: 14, 3: 12, 4: 12}
    label = text.upper() if level == 1 else text
    run = p.add_run(label)
    _set_font(run, size=sizes.get(level, 12), bold=True)
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
    cap = doc.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.LEFT
    _set_spacing(cap, multiple=1.0)
    cap.paragraph_format.first_line_indent = Cm(0)
    run = cap.add_run(f"Tabla {table_num} – {caption_text}")
    _set_font(run, size=10, italic=True)

    table = doc.add_table(rows=len(rows) + 1, cols=len(headers))
    table.style = "Table Grid"
    hdr_cells = table.rows[0].cells
    for i, h in enumerate(headers):
        hdr_cells[i].text = h
        for r in hdr_cells[i].paragraphs[0].runs:
            r.font.name = "Arial"; r.font.size = Pt(10); r.font.bold = True
    for r_idx, row_data in enumerate(rows):
        cells = table.rows[r_idx + 1].cells
        for c_idx, val in enumerate(row_data):
            cells[c_idx].text = str(val)
            for r in cells[c_idx].paragraphs[0].runs:
                r.font.name = "Arial"; r.font.size = Pt(10)
    doc.add_paragraph()
    return table


def add_formula(doc, formula_text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _set_spacing(p, multiple=1.0)
    p.paragraph_format.space_before      = Pt(6)
    p.paragraph_format.space_after       = Pt(6)
    p.paragraph_format.first_line_indent = Cm(0)
    run = p.add_run(formula_text)
    _set_font(run, size=11, italic=True)
    return p


def add_code(doc, code_text):
    """Bloque de código en Courier New con sangría."""
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    _set_spacing(p, multiple=1.0)
    p.paragraph_format.first_line_indent = Cm(0)
    p.paragraph_format.left_indent       = Cm(1.0)
    p.paragraph_format.space_before      = Pt(4)
    p.paragraph_format.space_after       = Pt(4)
    run = p.add_run(code_text)
    run.font.name = "Courier New"
    run.font.size = Pt(9)
    return p


def add_figure(doc, img_path, caption, fig_num):
    path = Path(img_path)
    if not path.exists():
        p = doc.add_paragraph()
        _set_spacing(p, multiple=1.0)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(f"[FIGURA {fig_num} — archivo no encontrado: {path.name}]")
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
    cap.paragraph_format.space_after       = Pt(12)
    r = cap.add_run(f"Figura {fig_num} – {caption}")
    _set_font(r, size=10, italic=True)


def add_labeled(doc, label, text):
    """Párrafo con etiqueta en negrita seguida de texto normal."""
    p = doc.add_paragraph()
    _set_spacing(p)
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.first_line_indent = Cm(1.25)
    r1 = p.add_run(label + " ")
    _set_font(r1, bold=True)
    r2 = p.add_run(text)
    _set_font(r2)


def page_break(doc):
    doc.add_page_break()


def configure_doc(doc):
    for section in doc.sections:
        section.left_margin   = Cm(3)
        section.right_margin  = Cm(2)
        section.top_margin    = Cm(3)
        section.bottom_margin = Cm(2)
    style = doc.styles["Normal"]
    style.font.name = "Arial"
    style.font.size = Pt(12)


# ── PORTADA Y PRE-TEXTUALES ───────────────────────────────────────────────────

def build_portada(doc):
    add_centered(doc, "UNIVERSIDADE DE SÃO PAULO", size=14, bold=True, spacing=1.0)
    add_centered(doc, "Instituto de Ciências Matemáticas e de Computação – ICMC", size=12, bold=True, spacing=1.0)
    add_centered(doc, "MBA em Ciência de Dados", size=12, spacing=1.0)
    for _ in range(6): add_centered(doc, "", size=12, spacing=1.0)
    add_centered(doc, "Juan Fernando Graciano Pinzón", size=13, bold=True, spacing=1.0)
    for _ in range(4): add_centered(doc, "", size=12, spacing=1.0)
    add_centered(doc,
        "Modelización del Riesgo de Crédito Dinámico para Microempresarios: "
        "Un Enfoque mediante Análisis de Supervivencia en Flujos de Alta Frecuencia bajo Censura",
        size=17, bold=True, spacing=1.5)
    for _ in range(4): add_centered(doc, "", size=12, spacing=1.0)
    add_centered(doc, "Director: Prof. Dr. Vicente Garibay Cancho", size=12, spacing=1.0)
    add_centered(doc, "Área de concentración: Ciencia de Datos", size=12, spacing=1.0)
    for _ in range(4): add_centered(doc, "", size=12, spacing=1.0)
    add_centered(doc, "São Paulo / São Carlos, 2026", size=11, spacing=1.0)
    page_break(doc)


def build_resumen(doc):
    add_heading(doc, "RESUMEN", level=1)
    add_body(doc,
        "GRACIANO PINZÓN, Juan Fernando. Modelización del Riesgo de Crédito Dinámico para "
        "Microempresarios: Un Enfoque mediante Análisis de Supervivencia en Flujos de Alta "
        "Frecuencia bajo Censura. 2026. Trabajo de Conclusión de Curso – MBA en Ciencia de Datos, "
        "Instituto de Ciências Matemáticas e de Computação, Universidade de São Paulo, "
        "São Paulo/São Carlos, 2026.", indent_first=False)
    doc.add_paragraph()
    add_body(doc,
        "La concesión de crédito al segmento de microempresarios en Brasil enfrenta severa "
        "asimetría de información, con modelos tradicionales basados en datos estáticos que ignoran "
        "la dinámica de pago en tiempo real. Esta investigación desarrolla un modelo predictivo de "
        "riesgo de crédito dinámico mediante Análisis de Supervivencia con covariables dependientes "
        "del tiempo, fundamentado en datos de alta frecuencia de una institución de microcrédito de "
        "pago diario. Un pipeline de extracción automatizado (RPA con Selenium WebDriver) superó las "
        "barreras técnicas del Sistema ATLAS — sin API REST, frameset anidado, SELECT2, datepicker "
        "readonly y modales dinámicos — recolectando 3.962 planillas Excel de tres oficinas y 17 rutas "
        "en el período 2020–2026, totalizando ~14 GB de datos brutos. El Data Stitching consolidó los "
        "snapshots en una Matriz Maestra de 344.869 filas × 2.358 columnas (882 MB en disco, ~6 GB en "
        "RAM), procesada en chunks de 5.000 filas con máscara NumPy vectorizada (n_filas × n_columnas_pago) "
        "para evitar errores de Out-of-Memory. Tras ingeniería de características en formato Counting "
        "Process (Anderson y Gill, 1982), el dataset de supervivencia final contiene 28.386 créditos "
        "únicos, 301.434 intervalos temporales y 425 eventos de castigo de cartera (tasa de morosidad "
        "del 1,50%), con el evento definido como dias_sem_pagar ≥ 120 días calendario. El análisis "
        "exploratorio reveló que la curva de Kaplan-Meier cae de S(t) = 1,0 a S(180) = 0,68 y "
        "S(365) = 0,17. La etapa siguiente comprende el ajuste del Modelo de Cox y la implementación "
        "de arquitecturas DeepSurv, con comparación mediante el C-index de Harrell.", indent_first=False)
    p = doc.add_paragraph()
    _set_spacing(p)
    run = p.add_run(
        "Palabras clave: análisis de supervivencia; microcrédito; Modelo de Cox; DeepSurv; "
        "alta frecuencia; proceso de conteo; morosidad; RPA; ETL.")
    _set_font(run)
    page_break(doc)


def build_abstract(doc):
    add_heading(doc, "ABSTRACT", level=1)
    add_body(doc,
        "GRACIANO PINZÓN, Juan Fernando. Dynamic Credit Risk Modeling for Microentrepreneurs: "
        "A Survival Analysis Approach on High-Frequency Flows under Censoring. 2026. Final Course "
        "Work – MBA in Data Science, Institute of Mathematics and Computer Science, University of "
        "São Paulo, São Paulo/São Carlos, 2026.", indent_first=False)
    doc.add_paragraph()
    add_body(doc,
        "Lending to the micro-entrepreneur segment in Brazil faces severe information asymmetry, "
        "with traditional models based on static data that ignore real-time payment dynamics. This "
        "research develops a dynamic credit risk prediction model using Survival Analysis with "
        "time-varying covariates, grounded in high-frequency data from a daily-payment microcredit "
        "institution. An automated extraction pipeline (RPA with Selenium WebDriver) overcame the "
        "technical barriers of the ATLAS System — no REST API, nested frameset, SELECT2, readonly "
        "datepicker, and dynamic modals — collecting 3,962 Excel spreadsheets from three offices "
        "and 17 routes over the period 2020–2026, totaling ~14 GB of raw data. Data Stitching "
        "consolidated the snapshots into a Master Matrix of 344,869 rows × 2,358 columns (882 MB "
        "on disk, ~6 GB in RAM), processed in 5,000-row chunks with a vectorized NumPy mask "
        "(n_rows × n_payment_columns) to avoid Out-of-Memory errors. After feature engineering in "
        "the Counting Process format (Anderson and Gill, 1982), the final survival dataset contains "
        "28,386 unique credits, 301,434 time intervals, and 425 write-off events (default rate: "
        "1.50%), with the event defined as days_without_payment ≥ 120 calendar days. The next phase "
        "includes fitting a Cox Proportional Hazards model and implementing DeepSurv architectures, "
        "with comparison via Harrell's C-index.", indent_first=False)
    p = doc.add_paragraph()
    _set_spacing(p)
    run = p.add_run(
        "Keywords: survival analysis; microcredit; Cox model; DeepSurv; high-frequency data; "
        "counting process; default; RPA; ETL.")
    _set_font(run)
    page_break(doc)


def build_listas(doc):
    # Lista de Ilustraciones
    add_heading(doc, "LISTA DE ILUSTRACIONES", level=1)
    figs = [
        ("1",  "Distribución del evento de morosidad: proporción, tasa por oficina y por ruta"),
        ("2",  "Curva de Kaplan-Meier global del portafolio con tabla de n en riesgo"),
        ("3",  "Curvas de Kaplan-Meier por oficina con prueba de log-rank"),
        ("4",  "Distribución del tiempo de seguimiento (t_stop) y número de intervalos por crédito"),
        ("5",  "Distribución de dias_sem_pagar: global, zoom 0–150 días y máximo por crédito"),
        ("6",  "Distribución de covariables: Moroso (E=1) versus Censurado (E=0)"),
        ("7",  "Perfil económico del portafolio: plazo, monto y boxplot por evento"),
        ("8",  "Mapa de calor de correlaciones de las covariables del modelo de supervivencia"),
        ("9",  "Trayectorias individuales: 5 créditos en default versus 5 censurados"),
    ]
    for num, desc in figs:
        p = doc.add_paragraph()
        _set_spacing(p, multiple=1.0)
        p.paragraph_format.first_line_indent = Cm(0)
        run = p.add_run(f"Figura {num} – {desc}")
        _set_font(run, size=12)
    page_break(doc)

    # Lista de Tablas — V22 tiene 21 tablas
    add_heading(doc, "LISTA DE TABLAS", level=1)
    tabs = [
        ("1",  "Barreras técnicas del Sistema ATLAS y soluciones implementadas"),
        ("2",  "Secuencia de navegación en el frameset anidado del Sistema ATLAS"),
        ("3",  "Mapa corporativo detectado: oficinas y rutas del Sistema ATLAS"),
        ("4",  "Volumetría final del Data Lake extraído"),
        ("5",  "Estructura del archivo de checkpoint JSON de resiliencia"),
        ("6",  "Dimensiones de la Matriz Maestra tras consolidación (Data Stitching)"),
        ("7",  "Estrategia de chunked loading con máscara NumPy vectorizada"),
        ("8",  "Conformidad LGPD y gobernanza de datos en el pipeline ETL"),
        ("9",  "Filtro de cohorte diaria: criterio y créditos retenidos"),
        ("10", "Variables de tiempo y evento del dataset de supervivencia"),
        ("11", "Covariables tiempo-variantes y sus fórmulas"),
        ("12", "Covariables estáticas del modelo"),
        ("13", "Caracterización general del dataset de supervivencia"),
        ("14", "Tasa de morosidad por oficina"),
        ("15", "Valores de la curva de Kaplan-Meier global"),
        ("16", "Resultado de la prueba de log-rank (OFI_23 vs. OFI_44)"),
        ("17", "Estadísticas del tiempo de seguimiento e intervalos por crédito"),
        ("18", "Estadísticas del cronómetro dias_sem_pagar"),
        ("19", "Correlaciones de las covariables con el evento"),
        ("20", "Monto del crédito por grupo de evento"),
        ("21", "Validación del formato Counting Process"),
    ]
    for num, desc in tabs:
        p = doc.add_paragraph()
        _set_spacing(p, multiple=1.0)
        p.paragraph_format.first_line_indent = Cm(0)
        run = p.add_run(f"Tabla {num} – {desc}")
        _set_font(run, size=12)
    page_break(doc)

    # Lista de Abreviaturas
    add_heading(doc, "LISTA DE ABREVIATURAS Y SIGLAS", level=1)
    abrevs = [
        ("ABNT",    "Asociación Brasileña de Normas Técnicas"),
        ("CRISP-DS","Cross Industry Standard Process for Data Science"),
        ("DOM",     "Document Object Model"),
        ("EDA",     "Análisis Exploratorio de Datos (Exploratory Data Analysis)"),
        ("ETL",     "Extract, Transform, Load"),
        ("KM",      "Kaplan-Meier"),
        ("LGPD",    "Lei Geral de Proteção de Dados Pessoais (Ley General de Protección de Datos)"),
        ("LSTM",    "Long Short-Term Memory"),
        ("MAR",     "Missing At Random"),
        ("MBA",     "Master of Business Administration"),
        ("MLOps",   "Machine Learning Operations"),
        ("RAM",     "Random Access Memory"),
        ("RPA",     "Robotic Process Automation"),
        ("TCC",     "Trabalho de Conclusão de Curso (Trabajo Final de Curso)"),
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
    add_heading(doc, "SUMARIO", level=1)
    entries = [
        (1, "1",    "INTRODUCCIÓN Y CONTEXTUALIZACIÓN DEL PROBLEMA"),
        (1, "2",    "OBJETIVOS"),
        (2, "2.1",  "Objetivo General"),
        (2, "2.2",  "Objetivos Específicos"),
        (1, "3",    "ARQUITECTURA DE DATOS Y PIPELINE DE EXTRACCIÓN INDUSTRIAL (ETL)"),
        (2, "3.1",  "El Sistema ATLAS: Contexto y Barreras Técnicas de la Extracción"),
        (2, "3.2",  "Autenticación Bifásica y Navegación en el Frameset Anidado"),
        (2, "3.3",  "Extracción Batch: Paginación Temporal y Filtro Anti-Cero"),
        (2, "3.4",  "Escalabilidad Corporativa: Auto-Discovery, Data Lake Jerárquico y Resiliencia"),
        (2, "3.5",  "Consolidación de la Matriz Maestra y Optimización de Memoria (Data Stitching)"),
        (2, "3.6",  "Gobernanza de Datos, Conformidad LGPD y Metodología CRISP-DS"),
        (1, "4",    "INGENIERÍA DE VARIABLES Y DEFINICIÓN DEL EVENTO TARGET"),
        (2, "4.1",  "Fundamentos Teóricos del Análisis de Supervivencia"),
        (3, "4.1.1","Función de Supervivencia y Función de Riesgo"),
        (3, "4.1.2","Tipos de Censura y Truncación por la Izquierda"),
        (3, "4.1.3","Estimador de Kaplan-Meier"),
        (3, "4.1.4","Prueba de Log-Rank"),
        (3, "4.1.5","Proceso de Conteo de Anderson-Gill"),
        (2, "4.2",  "Definición Operacional de la Morosidad en Alta Frecuencia"),
        (2, "4.3",  "Estructura Bimodal de Atributos y Estrategia de Proxy"),
        (2, "4.4",  "Formato Anderson-Gill (Counting Process)"),
        (2, "4.5",  "Construcción del Dataset de Supervivencia"),
        (2, "4.6",  "Análisis Exploratorio de Datos (EDA)"),
        (2, "4.7",  "Síntesis y Validación del Dataset"),
        (1, "5",    "MODELAMIENTO MATEMÁTICO Y COMPUTACIONAL"),
        (2, "5.1",  "Baseline Clásico (Modelo de Cox)"),
        (2, "5.2",  "El Desafío de la Censura por la Derecha en Arquitecturas Neurales"),
        (2, "5.3",  "Enfoque Estado del Arte (Deep Learning bajo Censura)"),
        (1, "6",    "VALIDACIÓN"),
        (1, "7",    "CRONOGRAMA INTEGRADO DE INVESTIGACIÓN"),
        (1, "REF",  "REFERENCIAS BIBLIOGRÁFICAS"),
    ]
    for level, num, title in entries:
        p = doc.add_paragraph()
        _set_spacing(p, multiple=1.0)
        p.paragraph_format.first_line_indent = Cm(0)
        p.paragraph_format.left_indent = Cm((level - 1) * 0.75)
        label = f"{num}  {title}" if num != "REF" else title
        run = p.add_run(label)
        _set_font(run, size=12, bold=(level == 1))
    page_break(doc)


# ── SECCIÓN 1 ─────────────────────────────────────────────────────────────────

def build_seccion_1(doc):
    add_heading(doc, "1  INTRODUCCIÓN Y CONTEXTUALIZACIÓN DEL PROBLEMA", level=1)
    add_body(doc,
        "La concesión de crédito al segmento microempresarial (específicamente el nicho "
        "Subprime o Thin-File) en Brasil y en toda América Latina enfrenta una severa asimetría "
        "de información. Las instituciones financieras tradicionales basan sus modelos de riesgo "
        "en datos estáticos e históricos desfasados (como reportes en burós de crédito, scores "
        "estáticos o balances anuales). Este enfoque frecuentemente penaliza al microempresario "
        "por eventos pasados, ignorando su real y actual capacidad de generación de caja.")
    add_body(doc,
        "Ante este escenario, esta investigación propone un cambio de paradigma: la utilización "
        "de datos dinámicos y de alta frecuencia — específicamente el registro interno de pagos "
        "diarios (abonos) y sus respectivas modalidades de liquidación — para evaluar la salud "
        "financiera del negocio en tiempo real. El estudio se viabiliza mediante una base de datos "
        "estratégica provista por una empresa asociada especializada en microcrédito para el sector "
        "informal. El gran diferencial reside en observar la liquidez diaria y la intensidad de "
        "los pagos parciales, modelando el riesgo de incumplimiento no como un evento binario y "
        "estático, sino como un proceso dinámico y continuo en el tiempo.")


# ── SECCIÓN 2 ─────────────────────────────────────────────────────────────────

def build_seccion_2(doc):
    add_heading(doc, "2  OBJETIVOS", level=1)
    add_heading(doc, "2.1  Objetivo General", level=2)
    add_body(doc,
        "Desarrollar un modelo predictivo de riesgo de crédito basado en Análisis de Supervivencia "
        "para estimar el tiempo exacto hasta la ruptura del flujo de caja y de la capacidad de pago "
        "(morosidad técnica) de microempresarios, integrando variables estáticas demográficas y datos "
        "longitudinales de flujo transaccional de alta frecuencia.")
    add_heading(doc, "2.2  Objetivos Específicos", level=2)
    items = [
        ("Ingeniería de Datos (ETL/RPA):",
         "Diseñar e implementar un sistema robusto de ingesta masiva capaz de superar limitaciones "
         "de sistemas legados, extrayendo y organizando el historial transaccional de múltiples "
         "unidades de negocio en un Data Lake."),
        ("Data Stitching y MLOps:",
         "Unificar los snapshots temporales en una Matriz Maestra (Silver Layer) con trazabilidad "
         "total (Data Lineage) y optimización computacional de memoria."),
        ("Tratamiento y EDA:",
         "Aplicar el estimador no paramétrico de Kaplan-Meier para el análisis exploratorio del "
         "tiempo de supervivencia de la capacidad de pago de la cartera, y extraer covariables "
         "espacio-temporales (clústeres de rutas)."),
        ("Modelamiento de Baseline Clásico:",
         "Entrenar y ajustar el Modelo de Riesgos Proporcionales de Cox para cuantificar el "
         "impacto de las covariables estáticas y dependientes del tiempo en la función de riesgo basal."),
        ("Innovación y Aporte Académico (Deep Learning):",
         "Comparar el rendimiento predictivo del modelo paramétrico de Cox con arquitecturas "
         "contemporáneas de Deep Learning adaptadas para datos de supervivencia (DeepSurv/RNNs), "
         "incorporando tratamiento para censura (Negative Partial Log-Likelihood)."),
        ("Comparativo Clasificatorio:",
         "Evaluar las ganancias marginales del enfoque de supervivencia frente a los modelos "
         "tradicionales de Credit Scoring de clasificación binaria."),
    ]
    for label, text in items:
        add_labeled(doc, label, text)


# ── SECCIÓN 3 — EXPANDIDA ─────────────────────────────────────────────────────

def build_seccion_3(doc):
    add_heading(doc, "3  ARQUITECTURA DE DATOS Y PIPELINE DE EXTRACCIÓN INDUSTRIAL (ETL)", level=1)
    add_body(doc,
        "La construcción de modelos de análisis de supervivencia con covariables tiempo-variantes "
        "exige series longitudinales de alta granularidad que registren el comportamiento de pago "
        "de cada crédito a lo largo del tiempo. La única fuente de datos disponible para esta "
        "investigación es el Sistema ATLAS, plataforma de gestión crediticia que no expone APIs "
        "REST y restringe el acceso a una interfaz web de tercera generación. Superar esta barrera "
        "tecnológica exigió el desarrollo de un pipeline de automatización web (RPA) de nivel "
        "industrial, implementado en Python 3.12 con Selenium WebDriver, cuya arquitectura completa "
        "se detalla en las subsecciones siguientes.")

    # ── 3.1 ──────────────────────────────────────────────────────────────────
    add_heading(doc, "3.1  El Sistema ATLAS: Contexto y Barreras Técnicas de la Extracción", level=2)
    add_body(doc,
        "El Sistema ATLAS es la "
        "plataforma de gestión crediticia de la institución asociada. Se trata de "
        "una aplicación web desarrollada en PHP, hospedada en infraestructura privada, sin "
        "exposición de endpoints REST, GraphQL ni ningún mecanismo programático de acceso a datos. "
        "El único canal disponible es la interfaz de usuario en el navegador, lo que convierte la "
        "automatización web (web scraping mediante Selenium) en la única alternativa viable para "
        "la extracción sistemática del historial transaccional.")
    add_body(doc,
        "La interfaz del ATLAS impone seis barreras técnicas específicas que demandan soluciones "
        "individuales, detalladas en la Tabla 1. Cada barrera representa un punto de falla potencial "
        "en el pipeline: la ausencia de cualquiera de las soluciones resulta en crash silencioso del "
        "robot, extracción parcial o datos corrompidos.")

    add_table_data(doc,
        ["Barrera Técnica", "Causa Raíz", "Solución Implementada"],
        [
            ["Sin API REST",
             "Backend PHP sin endpoints programáticos",
             "Selenium WebDriver + ChromeDriver (webdriver-manager)"],
            ["Frameset anidado (3 niveles)",
             "index2.php → leftFrame → mainFrame",
             "Secuencia precisa de switch_to.frame() + switch_to.default_content()"],
            ["Autenticación SELECT2 (fase 2)",
             "Widget jQuery ignora eventos DOM nativos",
             "DOM nativo: sel.value + dispatchEvent('change', {bubbles: true})"],
            ["Menú con etiquetas <op> no estándar",
             "Etiquetas HTML propietarias sin soporte is_displayed()",
             "XPath //op[normalize-space()='...'] + JS click via execute_script()"],
            ["Campo de fecha readonly (datepicker)",
             "jQuery UI bloquea edición manual del campo",
             "Inyección vía JS: arguments[0].value + dispatchEvent('change')"],
            ["Modal bootbox dinámico",
             "bootbox.js intercepta clics y bloquea el formulario",
             "find_elements() (sin excepción si ausente) + JS click en el botón de confirmación"],
            ["Descarga silenciosa de múltiples archivos",
             "Chrome requiere confirmación del usuario por defecto",
             "Chrome prefs: automatic_downloads: 1, prompt_for_download: False"],
        ],
        "Barreras técnicas del Sistema ATLAS y soluciones implementadas en el pipeline RPA",
        table_num=1,
    )

    # ── 3.2 ──────────────────────────────────────────────────────────────────
    add_heading(doc, "3.2  Autenticación Bifásica y Navegación en el Frameset Anidado", level=2)
    add_body(doc,
        "El pipeline de autenticación fue implementado en la clase orientada a objetos "
        "AtlasDataExtractor (src/atlas_extractor.py), que encapsula toda la lógica de interacción "
        "con el Sistema ATLAS. La autenticación ocurre en dos fases distintas, separadas por una "
        "transición de estado del servidor que invalida los elementos DOM previamente cargados.")

    add_labeled(doc, "Fase 1 — Credenciales:",
        "El formulario de inicio de sesión reside dentro de un iframe (frame índice 0 de "
        "frmAutenticacion.php). El robot utiliza WebDriverWait con expected_conditions para "
        "aguardar la disponibilidad de cada elemento antes de interactuar, garantizando tolerancia "
        "a variaciones de latencia del servidor. Los campos txtLogin y txtClave reciben las "
        "credenciales leídas de variables de entorno (.env), y el botón btnAutenticar se activa "
        "mediante clic nativo de Selenium.")

    add_labeled(doc, "Fase 2 — Selección de ruta (SELECT2):",
        "Tras validar las credenciales, el servidor renderiza un segundo formulario con un dropdown "
        "SELECT2 (biblioteca jQuery) para selección de la ruta. El SELECT2 ignora completamente "
        "eventos DOM nativos como 'input' o 'change' disparados por Selenium — el widget escucha "
        "solo eventos jQuery internos. La solución implementada es la inyección directa de "
        "JavaScript que escribe el valor en el elemento <select> subyacente y dispara un evento "
        "'change' nativo con propagación (bubbles: true), sorteando el interceptor jQuery:")

    add_code(doc,
        "# SELECT2 ignora eventos Selenium → DOM nativo con dispatchEvent\n"
        "driver.execute_script(\"\"\"\n"
        "    var sel = document.getElementById('cmbRutas');\n"
        "    sel.value = arguments[0];\n"
        "    sel.dispatchEvent(new Event('change', {bubbles: true}));\n"
        "\"\"\", valor_ruta)"
    )

    add_body(doc,
        "Tras la selección de la ruta, el servidor muestra un modal de bienvenida (bootbox.js) "
        "que bloquea cualquier interacción con el formulario subyacente. El tratamiento utiliza "
        "find_elements() (que retorna lista vacía en vez de lanzar excepción) en lugar de "
        "find_element(), evitando crash cuando el modal está ausente. El clic en el botón de "
        "confirmación se realiza vía JS para garantizar que interceptores DOM no interfieran. "
        "Tras el cierre del modal, el robot regresa al contexto por defecto "
        "(switch_to.default_content()) y espera la carga del frameset principal antes de continuar.")

    add_body(doc,
        "La navegación al formulario de extracción sigue una secuencia rígida de cambio de "
        "contexto de frame, pues la arquitectura del Sistema ATLAS utiliza frameset anidado en "
        "tres niveles. La Tabla 2 documenta la secuencia exacta implementada en el método "
        "_navegar_a_planilla_abonos().")

    add_table_data(doc,
        ["Paso", "Operación Selenium", "Frame / Elemento Objetivo", "Finalidad"],
        [
            ["1", "switch_to.default_content()", "Contexto raíz del navegador", "Resetear contexto tras cualquier operación anterior"],
            ["2", "switch_to.frame(0)", "index2.php (frame principal)", "Entrar en el frameset raíz del sistema"],
            ["3", "frame_to_be_available_and_switch_to_it('leftFrame')", "leftFrame (menú lateral)", "Acceder al menú de navegación"],
            ["4", "JS click: //op[normalize-space()='Reportes']", "Etiqueta <op> del menú", "Expandir el submenú de reportes"],
            ["5", "JS click: //op[normalize-space()='Recaudador']", "Etiqueta <op> del submenú", "Expandir el submenú de cobranza"],
            ["6", "JS click: //a[contains(@href,'ReportePlanillaReacudadorConAbono')]", "Enlace del reporte", "Cargar el formulario de extracción en mainFrame"],
            ["7", "switch_to.default_content() → switch_to.frame(0)", "De vuelta al frame raíz", "Preparar para entrar al mainFrame"],
            ["8", "frame_to_be_available_and_switch_to_it('mainFrame')", "mainFrame (formulario)", "Acceder al formulario de extracción"],
            ["9", "Select(sltOficina).select_by_value()", "Dropdown de oficina", "Configurar filtro estático de oficina"],
            ["10", "Select(cmbRutas).select_by_value()", "Dropdown de ruta", "Configurar filtro estático de ruta (tras AJAX)"],
        ],
        "Secuencia de navegación en el frameset anidado del Sistema ATLAS",
        table_num=2,
    )

    add_body(doc,
        "Los filtros de oficina y ruta (sltOficina y cmbRutas) se configuran una única vez antes "
        "del inicio del bucle de extracción batch, pues permanecen constantes para toda la secuencia "
        "temporal de una ruta. La selección de la oficina dispara una llamada AJAX que repopula el "
        "dropdown cmbRutas — el pipeline espera la presencia de la opción correcta con lambda "
        "WebDriverWait antes de continuar, garantizando sincronización con el servidor.")

    # ── 3.3 ──────────────────────────────────────────────────────────────────
    add_heading(doc, "3.3  Extracción Batch: Paginación Temporal y Filtro Anti-Cero", level=2)
    add_body(doc,
        "El Sistema ATLAS restringe cada extracción a una ventana de exactamente 10 días calendario. "
        "Para cubrir el horizonte histórico completo de 2020 a 2026 (~2.327 días), el pipeline "
        "implementa un cursor temporal que avanza en bloques estrictos de 10 días, generando "
        "aproximadamente 233 iteraciones por ruta y 3.961 iteraciones en el total corporativo.")

    add_labeled(doc, "Early-exit [YA EXISTE]:",
        "Antes de cualquier interacción con el DOM, el pipeline verifica si el archivo "
        "planilla_abonos_YYYYMMDD_YYYYMMDD.xlsx ya existe en el directorio de destino. Si existe, "
        "el bloque se omite completamente sin abrir el formulario, permitiendo retomar eficientemente "
        "sesiones interrumpidas sin reprocesamiento.")

    add_labeled(doc, "Inyección de fecha (datepicker bypass):",
        "El campo dtFechaIni está marcado como readonly por el jQuery UI datepicker, impidiendo "
        "cualquier edición mediante Selenium send_keys(). La solución inyecta el valor directamente "
        "en el elemento DOM vía JavaScript y dispara el evento 'change' para activar los listeners "
        "del formulario:")

    add_code(doc,
        "# Campo readonly → inyectar valor vía JS + disparar evento change\n"
        "driver.execute_script(\"\"\"\n"
        "    arguments[0].value = arguments[1];\n"
        "    arguments[0].dispatchEvent(new Event('change', {bubbles: true}));\n"
        "\"\"\", campo_fecha, cursor.strftime('%Y-%m-%d'))"
    )

    add_labeled(doc, "Filtro anti-cero (ebReportePantalla):",
        "Tras presionar btnAceptar, el servidor procesa la consulta y renderiza un PDF embebido "
        "en el elemento <object id='ebReportePantalla'>. Cuando el período consultado no contiene "
        "actividad para la ruta (ruta inactiva en ese intervalo), el objeto permanece oculto "
        "(display: none) o con atributo data vacío. El pipeline valida la presencia de datos antes "
        "de intentar la descarga:")

    add_code(doc,
        "# Validar presencia de datos antes de descargar\n"
        "obj = driver.find_element(By.ID, 'ebReportePantalla')\n"
        "tem_dados = (\n"
        "    '.pdf' in (obj.get_attribute('data') or '') and\n"
        "    'inline-block' in (obj.get_attribute('style') or '')\n"
        ")\n"
        "if not tem_dados:\n"
        "    cursor += timedelta(days=10)  # [SKIP] ruta inactiva"
    )

    add_body(doc,
        "Este filtro anti-cero es crítico para la integridad estadística del dataset: sin él, "
        "bloques sin actividad generarían archivos Excel vacíos que, al consolidarse en la Matriz "
        "Maestra, introducirían ceros espurios en las columnas de pago y distorsionarían el "
        "cronómetro dias_sem_pagar, generando falsos positivos en el evento de morosidad.")

    add_labeled(doc, "Monitoreo de descarga y renombramiento semántico:",
        "Tras presionar btnExcel, Chrome inicia la descarga hacia la carpeta staging (data/raw/). "
        "El pipeline monitorea la carpeta en bucle de 1 segundo, detectando el archivo .crdownload "
        "(parcial) y esperando su desaparición antes de renombrar el xlsx completo al patrón "
        "planilla_abonos_YYYYMMDD_YYYYMMDD.xlsx. Este patrón de nomenclatura incorpora las fechas "
        "de inicio y fin del bloque, viabilizando la extracción automática de metadatos temporales "
        "durante el Data Stitching.")

    # ── 3.4 ──────────────────────────────────────────────────────────────────
    add_heading(doc, "3.4  Escalabilidad Corporativa: Auto-Discovery, Data Lake Jerárquico y Resiliencia", level=2)
    add_body(doc,
        "Para escalar el pipeline piloto (una ruta) al universo corporativo completo (17 rutas en "
        "3 oficinas), se desarrolló la clase AtlasMasivoExtractor (src/atlas_masivo.py), que hereda "
        "toda la infraestructura de AtlasDataExtractor y agrega cuatro capacidades fundamentales: "
        "auto-discovery del mapa corporativo, organización jerárquica del Data Lake, tratamiento de "
        "errores de elemento obsoleto (StaleElementReferenceException) y sistema de checkpoint para "
        "resiliencia ante fallas.")

    add_labeled(doc, "Auto-Discovery del mapa corporativo:",
        "El método _descubrir_mapa_rutas() lee dinámicamente todas las opciones de los dropdowns "
        "sltOficina y cmbRutas directamente del DOM del formulario. Para cada oficina detectada, "
        "dispara un cambio de valor en el select (vía JavaScript) que activa la llamada AJAX de "
        "repopulación del dropdown de rutas, recolectando los IDs de todas las rutas disponibles. "
        "Este mecanismo elimina la necesidad de mantenimiento manual de un catálogo de rutas y "
        "garantiza que nuevas rutas añadidas por la institución sean incluidas automáticamente en "
        "extracciones futuras.")

    add_body(doc,
        "El mapa corporativo identificado automáticamente por el Auto-Discovery comprende tres "
        "oficinas y 17 rutas geográficas, conforme se documenta en la Tabla 3.")

    add_table_data(doc,
        ["Oficina", "ID", "Región", "Rutas (IDs)", "Total"],
        [
            ["OFI_23 — São Paulo",         "23", "São Paulo / Gran SP",
             "82, 96, 423, 136, 367, 448, 494", "7"],
            ["OFI_31 — Sociedades Brasil",  "31", "Interior y Sur de Brasil",
             "415, 68, 338, 347, 389", "5"],
            ["OFI_44 — Cabo Frio",          "44", "Región de los Lagos / RJ",
             "114, 439, 396, 420, 511", "5"],
        ],
        "Mapa corporativo detectado por Auto-Discovery: oficinas y rutas del Sistema ATLAS",
        table_num=3,
    )

    add_labeled(doc, "Organización jerárquica del Data Lake:",
        "Los archivos extraídos se organizan en una jerarquía de directorios que refleja la "
        "topología corporativa del sistema: data/raw/OFI_{id_oficina}/RTA_{id_ruta}/. Chrome "
        "descarga cada archivo inicialmente a data/raw/ (staging area) y el pipeline mueve el "
        "xlsx renombrado al subdirectorio correspondiente mediante shutil.move(). Esta estructura "
        "garantiza trazabilidad completa (Data Lineage): dado cualquier archivo, es posible "
        "identificar inmediatamente a qué oficina, ruta y período temporal pertenece, solo por "
        "la ruta y el nombre del archivo.")

    add_table_data(doc,
        ["Métrica", "Valor"],
        [
            ["Archivos Excel descargados",      "3.962 archivos"],
            ["Oficinas cubiertas",              "3 (OFI_23, OFI_31, OFI_44)"],
            ["Rutas cubiertas",                 "17"],
            ["Período de cobertura",            "2020-01-01 → 2026-05-15 (~6,4 años)"],
            ["Bloques temporales por ruta",     "~233 bloques de 10 días"],
            ["Tamaño total del Data Lake",      "~14 GB"],
            ["Pausa entre rutas",               "10 segundos (limpieza de caché del navegador)"],
        ],
        "Volumetría final del Data Lake extraído",
        table_num=4,
    )

    add_labeled(doc, "Tratamiento de StaleElementReferenceException:",
        "El Sistema ATLAS realiza re-renderizaciones parciales del DOM durante transiciones entre "
        "rutas (el AJAX de cmbRutas puede no haber terminado cuando el SELECT ya fue localizado). "
        "El pipeline implementa hasta 3 intentos con pausa de 3 segundos entre cada uno para el "
        "método _seleccionar_oficina_y_ruta(), que renavega al formulario desde el menú lateral "
        "en cada intento, garantizando un estado DOM fresco.")

    add_labeled(doc, "Sistema de Checkpoint JSON:",
        "El archivo oculto .checkpoint.json en data/raw/ persiste el estado de la extracción "
        "tras cada bloque temporal exitoso. En la inicialización, el pipeline lee el checkpoint "
        "y retoma exactamente desde el último punto procesado, omitiendo las rutas ya completadas. "
        "Al concluir la maratón completa, el archivo se elimina automáticamente.")

    add_table_data(doc,
        ["Campo JSON", "Tipo", "Ejemplo", "Descripción"],
        [
            ["id_oficina", "String", '"44"',         "ID de la oficina en extracción"],
            ["id_ruta",    "String", '"114"',        "ID de la ruta en extracción"],
            ["fecha",      "String", '"2023-07-15"', "Última fecha de inicio de bloque procesada exitosamente"],
        ],
        "Estructura del archivo de checkpoint JSON (.checkpoint.json)",
        table_num=5,
    )

    # ── 3.5 ──────────────────────────────────────────────────────────────────
    add_heading(doc, "3.5  Consolidación de la Matriz Maestra y Optimización de Memoria (Data Stitching)", level=2)
    add_body(doc,
        "El script consolidar_datos.py implementa el proceso de Data Stitching, que transforma "
        "los 3.962 archivos Excel fragmentados del Data Lake en un único panel longitudinal "
        "continuo: la Matriz Maestra (Silver Layer). El proceso recorre recursivamente la "
        "jerarquía data/raw/OFI_*/RTA_*/*.xlsx, extrayendo dos tipos de metadatos directamente "
        "del sistema de archivos, sin necesidad de parsear el contenido de los archivos:")

    add_labeled(doc, "Metadatos topológicos (de la ruta del archivo):",
        "El identificador de oficina (ofi_id) y el identificador de ruta (rta_id) se extraen "
        "de la ruta relativa mediante expresión regular sobre los componentes del Path. Estos "
        "metadatos se inyectan como columnas adicionales en cada fila del archivo correspondiente, "
        "viabilizando análisis estratificados por oficina y ruta en el modelo de Cox sin necesidad "
        "de joins posteriores.")

    add_labeled(doc, "Metadatos temporales (del nombre del archivo):",
        "Las fechas de inicio y fin del bloque de 10 días se extraen del nombre del archivo "
        r"mediante el patrón planilla_abonos_YYYYMMDD_YYYYMMDD.xlsx vía expresión regular "
        r"(\d{8})_(\d{8})\.xlsx. Estas fechas se utilizan durante la Ingeniería de Características "
        "para calcular la máscara de pagos del bloque y el cronómetro dias_sem_pagar.")

    add_body(doc,
        "El resultado del Data Stitching es la Matriz Maestra, cuyas dimensiones y características "
        "se documentan en la Tabla 6. La estructura matricial tiene los créditos como filas y las "
        "fechas calendario de 2020-01-01 a 2026-05-15 (~2.330 fechas) como columnas, con los "
        "valores de pago diario (abonos) llenando la intersección.")

    add_table_data(doc,
        ["Dimensión / Métrica", "Valor"],
        [
            ["Filas (observaciones de crédito)",    "344.869"],
            ["Columnas totales",                     "2.358"],
            ["Columnas de pagos diarios",            "~2.330 (fechas 2020-01-01 → 2026-05-15)"],
            ["Columnas estáticas del crédito",       "28 (CÓDIGO CRÉDITO, SALDO, CUOTAS PACTADAS, etc.)"],
            ["Tamaño en disco (CSV comprimido)",     "882 MB"],
            ["Tamaño en RAM (expandido, float64)",   "~6 GB"],
            ["Reducción RAM por downcasting",         "~49% (float32 + categorización de strings)"],
            ["archivo_origen (columna de trazabilidad)", "OFI_{id}/RTA_{id}/planilla_abonos_*.xlsx"],
        ],
        "Dimensiones de la Matriz Maestra tras consolidación (Data Stitching)",
        table_num=6,
    )

    add_body(doc,
        "El tamaño en RAM de ~6 GB imposibilita la carga completa de la Matriz Maestra con "
        "pd.read_csv() estándar en máquinas con menos de 16 GB de memoria disponible. El "
        "pipeline de Ingeniería de Características (src/feature_engineering.py) resuelve este "
        "problema mediante lectura en chunks con máscara NumPy vectorizada, descrita a continuación.")

    add_labeled(doc, "Chunked loading con máscara NumPy vectorizada:",
        "El pipeline lee la Matriz Maestra en bloques de 5.000 filas a la vez (chunksize=5000), "
        "procesando los agregados de pago de cada bloque en memoria y descartando las ~2.330 "
        "columnas de fecha antes de concatenar. El cálculo de los agregados "
        "(pago_promedio_diario, dias_con_abono) utiliza broadcasting NumPy para crear una máscara "
        "binaria (n_filas × n_columnas_pago) que selecciona solo las columnas de fecha dentro del "
        "intervalo del bloque, sin bucle Python:")

    add_code(doc,
        "# Máscara vectorizada (n_filas × n_cols_pago) — sin bucle Python\n"
        "ini_arr   = ini.values[:, np.newaxis]    # shape: (5000, 1)\n"
        "fin_arr   = fin.values[:, np.newaxis]    # shape: (5000, 1)\n"
        "dates_arr = pago_dates.values[np.newaxis, :]  # shape: (1, 2330)\n"
        "\n"
        "# Broadcasting: compara cada fila con todas las fechas simultáneamente\n"
        "mascara = (dates_arr >= ini_arr) & (dates_arr <= fin_arr)  # (5000, 2330)\n"
        "\n"
        "pagos_bloque       = pagos_vals * mascara\n"
        "pago_promedio      = pagos_bloque.sum(axis=1) / n_dias_bloque\n"
        "dias_com_abono     = (pagos_bloque > 0).sum(axis=1)"
    )

    add_table_data(doc,
        ["Parámetro", "Valor", "Justificación"],
        [
            ["Chunk size",              "5.000 filas",   "Equilibrio entre velocidad y consumo de RAM (~100 MB/chunk)"],
            ["Columnas de pago",        "~2.330",         "Fechas 2020-01-01 a 2026-05-15 detectadas por header scan"],
            ["Shape de la máscara",     "(5000 × 2330)", "Broadcasting NumPy — operación vectorizada sin bucle Python"],
            ["Throughput",              "~5.000 filas/s", "Medido en hardware con 8 GB RAM / CPU 4 núcleos"],
            ["RAM pico por chunk",      "~100 MB",        "Máscara booleana float32 + datos de pago"],
            ["Tiempo total de lectura", "~70 segundos",   "Para 344.869 filas × 2.358 columnas"],
        ],
        "Estrategia de chunked loading con máscara NumPy vectorizada",
        table_num=7,
    )

    # ── 3.6 ──────────────────────────────────────────────────────────────────
    add_heading(doc, "3.6  Gobernanza de Datos, Conformidad LGPD y Metodología CRISP-DS", level=2)
    add_body(doc,
        "El pipeline ETL fue diseñado con gobernanza de datos desde la concepción, atendiendo "
        "los requisitos de la Lei Geral de Proteção de Dados Pessoais (LGPD, Ley N.º 13.709/2018) "
        "y las mejores prácticas de seguridad de la información en proyectos de Ciencia de Datos.")

    add_table_data(doc,
        ["Control de Gobernanza", "Implementación", "Artículo LGPD"],
        [
            ["Exclusión del versionamiento (git)",
             "data/raw/, data/processed/ y .env en .gitignore",
             "Art. 46 — Medidas de seguridad"],
            ["Gestión de credenciales",
             "ATLAS_USER y ATLAS_PASS solo en .env (nunca en el código fuente)",
             "Art. 46 — Protección de acceso"],
            ["Seudonimización",
             "CÓDIGO CRÉDITO como clave — sin nombre, CPF, dirección ni datos de identificación directa",
             "Art. 13 — Seudonimización"],
            ["Minimización de datos",
             "Silver Layer contiene solo las variables necesarias para el modelo de supervivencia",
             "Art. 6 — Necesidad"],
            ["Finalidad definida",
             "Datos utilizados exclusivamente para investigación académica de riesgo de crédito",
             "Art. 6 — Finalidad"],
            ["Trazabilidad",
             "archivo_origen en cada fila de la Matriz Maestra identifica la fuente exacta del dato",
             "Art. 37 — Registro de las operaciones"],
        ],
        "Conformidad LGPD y gobernanza de datos en el pipeline ETL",
        table_num=8,
    )

    add_body(doc,
        "La metodología CRISP-DS (Cross Industry Standard Process for Data Science), adoptada "
        "como framework de gestión del proyecto (Louzada Neto, 2026), estructura el pipeline en "
        "seis fases iterativas que se retroalimentan:")

    fases = [
        ("(1) Entendimiento del Negocio:",
         "Definición del evento de castigo de cartera (dias_sem_pagar ≥ 120) a partir del proceso "
         "operativo de la institución asociada. Identificación del Sistema ATLAS como fuente "
         "primaria y diseño del pipeline RPA como solución de ingesta."),
        ("(2) Entendimiento de los Datos:",
         "Análisis exploratorio de la estructura de la Matriz Maestra (344.869 × 2.358), "
         "identificación de las ~2.330 columnas de pago, caracterización de la cohorte diaria "
         "y EDA del dataset de supervivencia (Sección 4.6)."),
        ("(3) Preparación de los Datos:",
         "Ingeniería de Características en formato Counting Process de Anderson-Gill: cronómetro "
         "dias_sem_pagar, corrección de truncación izquierda, continuidad vía shift(), filtro de "
         "cohorte diaria y construcción de las 7 covariables tiempo-variantes."),
        ("(4) Modelamiento:",
         "Ajuste del Modelo de Riesgos Proporcionales de Cox con covariables tiempo-variantes "
         "(lifelines.CoxTimeVaryingFitter) e implementación de DeepSurv/RNN-Survival con "
         "Negative Partial Log-Likelihood (pycox/PyTorch). [Sprint 3 — pendiente]"),
        ("(5) Evaluación:",
         "Comparación de modelos mediante C-index de Harrell, Brier Score temporal y Prueba de "
         "Log-Rank. Diagnóstico de residuos de Schoenfeld para validar el supuesto de "
         "proporcionalidad del Cox. [Sprint 4 — pendiente]"),
        ("(6) Implementación:",
         "Modelo en producción para scoring dinámico de nuevos créditos, integrado al pipeline "
         "ETL para actualización periódica de las covariables tiempo-variantes. [Sprint 4 — pendiente]"),
    ]
    for label, text in fases:
        add_labeled(doc, label, text)

    add_body(doc,
        "La gestión de riesgos del proyecto siguió las siete categorías identificadas en la "
        "literatura de gestión ágil de proyectos de Ciencia de Datos (Louzada Neto, 2026): "
        "(1) calidad de los datos — mitigada por el filtro anti-cero y validación del ebReportePantalla; "
        "(2) presupuesto — controlado por la solución in-house de web scraping, eliminando licencias "
        "externas; (3) compromiso — gestionado con entregas iterativas por Sprint; "
        "(4) recursos humanos — riesgo bajo por ser investigación individual; "
        "(5) proveedores — mitigado por la independencia del Sistema ATLAS (solución in-house); "
        "(6) seguridad de la información — LGPD + .gitignore + seudonimización; "
        "(7) expectativas de tiempo — cronograma CRISP-DS con 4 Sprints Scrum.")


# ── SECCIÓN 4 ─────────────────────────────────────────────────────────────────

def build_seccion_4(doc):
    add_heading(doc, "4  INGENIERÍA DE VARIABLES Y DEFINICIÓN DEL EVENTO TARGET", level=1)

    add_heading(doc, "4.1  Fundamentos Teóricos del Análisis de Supervivencia", level=2)
    add_body(doc,
        "El análisis de supervivencia comprende un conjunto de técnicas estadísticas diseñadas "
        "para modelar el tiempo hasta la ocurrencia de un evento de interés (Kalbfleisch y "
        "Prentice, 2002). A diferencia de la regresión logística — que estima la probabilidad "
        "de incumplimiento en un punto fijo del tiempo —, el análisis de supervivencia incorpora "
        "explícitamente la dimensión temporal, distinguiendo entre individuos que experimentaron "
        "el evento y aquellos observados sin experimentarlo (censurados).")

    add_heading(doc, "4.1.1  Función de Supervivencia y Función de Riesgo", level=3)
    add_body(doc, "La función de supervivencia se define como:")
    add_formula(doc, "S(t) = P(T > t) = 1 − F(t)")
    add_body(doc,
        "donde F(t) es la función de distribución acumulada de T. La función de riesgo (hazard), "
        "tasa condicional de ocurrencia del evento en el instante t dado que el individuo sobrevivió "
        "hasta ese momento, es:")
    add_formula(doc, "h(t) = lim[Δt→0] P(t ≤ T < t+Δt | T ≥ t) / Δt = f(t) / S(t)")
    add_body(doc, "La relación fundamental entre S(t) y h(t) es:")
    add_formula(doc, "S(t) = exp(−∫₀ᵗ h(u) du) = exp(−H(t))")
    add_body(doc,
        "donde H(t) es la función de riesgo acumulado (cumulative hazard function). Esta relación "
        "muestra que la función de supervivencia queda completamente determinada por la función de "
        "riesgo, que es el componente central del modelo de regresión de Cox.")

    add_heading(doc, "4.1.2  Tipos de Censura y Truncación por la Izquierda", level=3)
    add_body(doc,
        "La censura por la derecha (right censoring) ocurre cuando el evento no ocurrió antes del "
        "fin de la observación — aplicable a los créditos activos en el corte del estudio (15 de "
        "mayo de 2026). La truncación por la izquierda (left truncation) ocurre cuando el primer "
        "snapshot de un crédito corresponde a una fecha posterior a su desembolso. El formato "
        "Counting Process trata correctamente ambos fenómenos (Therneau y Grambsch, 2000).")

    add_heading(doc, "4.1.3  Estimador de Kaplan-Meier", level=3)
    add_body(doc,
        "El estimador de Kaplan-Meier (Kaplan y Meier, 1958) es el estimador no paramétrico "
        "estándar de la función de supervivencia. Sean dⱼ el número de eventos y nⱼ el número "
        "de individuos en riesgo en cada tiempo de evento tⱼ. El estimador es:")
    add_formula(doc, "Ŝ(t) = ∏[j: tⱼ ≤ t] (1 − dⱼ/nⱼ)")
    add_body(doc,
        "Sus propiedades: consistencia (converge a S(t) verdadero), no paramétrico (no asume "
        "distribución para T) y corrección automática por censura (individuos censurados "
        "contribuyen al denominador nⱼ hasta el momento de la censura). La varianza se obtiene "
        "por la fórmula de Greenwood: Var[Ŝ(t)] = Ŝ(t)² × Σ[dⱼ/(nⱼ(nⱼ−dⱼ))].")

    add_heading(doc, "4.1.4  Prueba de Log-Rank", level=3)
    add_body(doc,
        "La prueba de log-rank (Mantel, 1966) compara las curvas de supervivencia de dos o más "
        "grupos sin asumir forma paramétrica. La hipótesis nula es H₀: S₁(t) = S₂(t) para todo t. "
        "El estadístico Q sigue χ² con (k−1) grados de libertad bajo H₀, siendo más sensible a "
        "diferencias en la cola de la distribución de supervivencia.")

    add_heading(doc, "4.1.5  Proceso de Conteo de Anderson-Gill", level=3)
    add_body(doc,
        "Cuando las covariables cambian a lo largo del seguimiento — como saldo deudor, cuotas "
        "atrasadas y dias_sem_pagar —, es necesario el marco del Proceso de Conteo de Anderson "
        "y Gill (1982). El individuo i se representa por una secuencia de intervalos:")
    add_formula(doc, "(t_start₁, t_stop₁, δ₁, X_{i1}), (t_start₂, t_stop₂, δ₂, X_{i2}), ...")
    add_body(doc,
        "Restricciones: (1) intervalos contiguos: t_start[k] = t_stop[k−1]; (2) evento δ=1 solo "
        "en el último intervalo; (3) intervalos abiertos a la izquierda y cerrados a la derecha: "
        "(t_start, t_stop]. Implementado en lifelines.CoxTimeVaryingFitter y pycox.")

    add_heading(doc, "4.2  Definición Operacional de la Morosidad en Alta Frecuencia", level=2)
    add_body(doc,
        "La definición del evento requiere atención especial en el contexto del microcrédito "
        "diario. El campo CUOTAS_ATRASADAS registra el número de cuotas diarias pendientes en el "
        "snapshot: para créditos de 20 a 40 días, su máximo teórico es exactamente CUOTAS_PACTADAS. "
        "El umbral original de 120 cuotas atrasadas es operacionalmente imposible, produciendo "
        "cero eventos. La definición adoptada es el castigo de cartera operativo de la institución:")
    add_formula(doc, "E_i = 𝟙[dias_sem_pagar_{it} ≥ 120 días calendario]")
    add_body(doc,
        "Este umbral — equivalente a 4 meses de inactividad financiera total — distingue mora "
        "transitoria (cronómetro reiniciado por cualquier abono) de abandono real (inactividad "
        "superior a 4 veces el plazo máximo del crédito). "
        "Criterio de inclusión: cohorte diaria con CUOTAS_PACTADAS ≤ 40.")

    add_heading(doc, "4.3  Estructura Bimodal de Atributos y Estrategia de Proxy", level=2)
    add_body(doc,
        "Las covariables disponibles se dividen en dos grupos: (1) Variables Estáticas — "
        "parámetros del crédito (valor total, valor de la cuota, cuotas pactadas); (2) Variables "
        "Dinámicas (Heartbeat) — vector longitudinal de pagos, cuotas atrasadas, intensidad "
        "transaccional de los abonos y días con abono, capturando la 'frecuencia cardíaca' "
        "financiera del emprendedor. Los identificadores ofi_id y rta_id actúan como proxies "
        "geodemográficos para capturar el comportamiento de riesgo local.")

    add_heading(doc, "4.4  Formato Anderson-Gill (Counting Process)", level=2)
    add_body(doc,
        "La Matriz Maestra se transforma en intervalos longitudinales continuos (t_start, t_stop]. "
        "Dos desafíos matemáticos críticos fueron resueltos:")
    add_labeled(doc, "Truncación Izquierda:",
        "t_start(primera fila) = max(0, fecha_ini_bloque − FECHA_CRÉDITO) en días. "
        "Previene tiempos de vida negativos que colapsarían la función de verosimilitud.")
    add_labeled(doc, "Continuidad de Markov:",
        "t_start[n] = t_stop[n−1] vía shift(), eliminando brechas temporales que harían que "
        "el modelo asuma la desaparición artificial del cliente entre snapshots.")
    add_formula(doc, "t_stop[t] = (fecha_fin_bloque[t] − FECHA_CRÉDITO).días + 1")
    add_formula(doc, "t_start[t] = t_stop[t−1]  para  t > 1")

    add_heading(doc, "4.5  Construcción del Dataset de Supervivencia", level=2)
    add_body(doc,
        "El dataset final en formato Counting Process contiene las siguientes variables:")

    add_table_data(doc,
        ["Cohorte", "Criterio", "Créditos"],
        [["Diaria (incluida)",       "CUOTAS_PACTADAS ≤ 40", "28.386"],
         ["Semanal/quincenal/mensual (excluida)", "CUOTAS_PACTADAS > 40", "—"]],
        "Filtro de cohorte diaria: criterio y créditos retenidos", table_num=9)

    add_table_data(doc,
        ["Variable", "Tipo", "Descripción"],
        [["t_start", "Continua", "Inicio del intervalo (días desde el desembolso)"],
         ["t_stop",  "Continua", "Fin del intervalo (días desde el desembolso)"],
         ["evento",  "Binaria",  "1 = morosidad (dias_sem_pagar ≥ 120), 0 = censura"],
         ["dias_sem_pagar", "Discreta", "Cronómetro de inactividad financiera"]],
        "Variables de tiempo y evento del dataset de supervivencia", table_num=10)

    add_table_data(doc,
        ["Variable", "Fórmula", "Interpretación"],
        [["cuotas_atrasadas",       "CUOTAS_ATRASADAS",                  "Días en mora en el snapshot"],
         ["pago_promedio_diario",   "Σ(pagos_bloque) / días_bloque",     "Flujo promedio de pagos (BRL)"],
         ["dias_con_abono",         "#{días con abono > 0} en el bloque","Frecuencia de pago en el período"],
         ["intensidad_recuperacion","VALOR_ÚLTIMO_ABONO / VALOR_CUOTA",  "Fracción de la cuota pagada (clip [0,10])"],
         ["ratio_atraso",           "CUOTAS_ATRASADAS / CUOTAS_PACTADAS","Fracción del plazo en mora (clip [0,1])"],
         ["saldo_relativo",         "SALDO / TOTAL_CRÉDITO",              "Fracción del crédito pendiente (clip [0,1])"]],
        "Covariables tiempo-variantes y sus fórmulas", table_num=11)

    add_table_data(doc,
        ["Variable", "Descripción"],
        [["total_credito",  "Monto original del crédito (BRL)"],
         ["valor_cota",     "Valor de la cuota diaria pactada (BRL)"],
         ["cotas_pactadas", "Plazo del crédito en días"],
         ["ofi_id",         "Identificador de oficina (proxy geográfico)"],
         ["rta_id",         "Identificador de ruta (proxy de zona/cobrador)"]],
        "Covariables estáticas del modelo", table_num=12)

    # ── 4.6 EDA ──────────────────────────────────────────────────────────────
    add_heading(doc, "4.6  Análisis Exploratorio de Datos (EDA)", level=2)
    add_body(doc,
        "El análisis exploratorio fue desarrollado en el notebook notebooks/01_eda_survival.ipynb, "
        "generando nueve figuras de diagnóstico (Figuras 1–9).")

    add_heading(doc, "4.6.1  Caracterización General del Dataset", level=3)
    add_table_data(doc,
        ["Métrica", "Valor"],
        [["Créditos únicos",              "28.386"],
         ["Intervalos totales (filas)",   "301.434"],
         ["Eventos (E=1)",                "425"],
         ["Tasa de morosidad (nivel crédito)", "1,50%"],
         ["Créditos censurados (E=0)",    "27.961 (98,50%)"],
         ["Oficinas",                     "3"],
         ["Rutas",                        "17"],
         ["Período de observación",       "2020-01-01 → 2026-05-15 (~6,4 años)"]],
        "Caracterización general del dataset de supervivencia", table_num=13)
    add_body(doc,
        "El bajo índice de morosidad (1,50%) refleja la gestión de cobranza intensiva mediante "
        "cobrador de ruta: la mayoría de los morosos es transitoria y se resuelve antes de "
        "alcanzar 120 días de inactividad. La tasa es coherente con referencias de microcrédito "
        "de pago diario en economías emergentes (Schreiner, 2002).")

    add_heading(doc, "4.6.2  Distribución del Evento de Morosidad", level=3)
    add_figure(doc, REPORTS / "fig01_distribucion_evento.png",
               "Distribución del evento de morosidad: proporción (pie), tasa por oficina y tasa por ruta", 1)
    add_table_data(doc,
        ["Oficina", "Créditos", "Eventos", "Tasa de Morosidad"],
        [["OFI_23 (São Paulo)",      "14.031", "126", "0,90%"],
         ["OFI_31 (Soc. Brasil)",     "7.333",  "53",  "0,72%"],
         ["OFI_44 (Cabo Frio)",       "7.022",  "246", "3,50%"]],
        "Tasa de morosidad por oficina", table_num=14)
    add_body(doc,
        "OFI_44 (Cabo Frio) presenta una tasa casi cuatro veces superior a las demás (3,50% vs. "
        "0,72–0,90%), evidenciando heterogeneidad geográfica relevante para el modelo de Cox.")

    add_heading(doc, "4.6.3  Curva de Kaplan-Meier Global", level=3)
    add_figure(doc, REPORTS / "fig02_kaplan_meier_global.png",
               "Curva de Kaplan-Meier global del portafolio con tabla de n en riesgo", 2)
    add_table_data(doc,
        ["Tiempo (días)", "S(t)", "Riesgo Acumulado"],
        [["120", "1,0000", "0,00%"],
         ["180", "0,6815", "31,85%"],
         ["270", "0,6788", "32,12%"],
         ["365", "0,1673", "83,27%"],
         ["540", "0,0908", "90,92%"]],
        "Valores de la curva de Kaplan-Meier global", table_num=15)
    add_body(doc,
        "S(t) = 1,0 hasta el día 120 es consecuencia directa de la definición del evento "
        "(dias_sem_pagar ≥ 120 es imposible antes de 120 días de seguimiento). El salto de "
        "S=1,0 a S=0,68 entre los días 120 y 180 revela que créditos de larga permanencia — "
        "más allá del plazo original de 20–40 días — concentran el riesgo de morosidad.")

    add_heading(doc, "4.6.4  Análisis Estratificado por Oficina (Prueba de Log-Rank)", level=3)
    add_figure(doc, REPORTS / "fig03_kaplan_meier_oficinas.png",
               "Curvas de Kaplan-Meier por oficina con prueba de log-rank (OFI_23 vs. OFI_44)", 3)
    add_table_data(doc,
        ["Estadístico", "Valor"],
        [["χ² (log-rank)", "0,0817"], ["p-valor", "0,7750"]],
        "Resultado de la prueba de log-rank (OFI_23 vs. OFI_44)", table_num=16)
    add_body(doc,
        "p = 0,775 indica que no se rechaza H₀ de igualdad de curvas al nivel del 5%. "
        "A pesar de la diferencia bruta en tasas (0,90% vs. 3,50%), el timing de los eventos es "
        "similar entre oficinas, y la reducción de créditos en riesgo a horizontes largos disminuye "
        "el poder estadístico de la prueba. Esto motiva el uso del modelo de Cox, que controla "
        "simultáneamente por múltiples covariables.")

    add_heading(doc, "4.6.5  Tiempo de Seguimiento y Granularidad Longitudinal", level=3)
    add_figure(doc, REPORTS / "fig04_tiempo_seguimiento.png",
               "Distribución del tiempo de seguimiento (t_stop) y número de intervalos por crédito", 4)
    add_table_data(doc,
        ["Estadístico", "t_stop (días)", "n_intervalos"],
        [["Mediana", "29 días", "3"],
         ["Media",   "36 días", "10,6"],
         ["Máximo",  "815 días", "233"]],
        "Estadísticas del tiempo de seguimiento e intervalos por crédito", table_num=17)
    add_body(doc,
        "La mediana de 29 días refleja créditos cortos (20–30 días). La cola derecha pronunciada "
        "(máx 815 días, 233 snapshots) corresponde a clientes con múltiples renovaciones — "
        "estructura bimodal típica del microcrédito diario que justifica el análisis de supervivencia.")

    add_heading(doc, "4.6.6  Cronómetro dias_sem_pagar", level=3)
    add_figure(doc, REPORTS / "fig05_dias_sin_pagar.png",
               "Distribución de dias_sem_pagar: global, zoom 0–150 días y máximo por crédito", 5)
    add_table_data(doc,
        ["Estadístico", "Valor"],
        [["Mediana", "0 días"], ["Percentil 95", "0 días"],
         ["Percentil 99", "26 días"], ["Máximo", "400 días"]],
        "Estadísticas del cronómetro dias_sem_pagar", table_num=18)
    add_body(doc,
        "En más del 95% de los intervalos, dias_sem_pagar = 0: el cliente realizó al menos un "
        "abono en el bloque de 10 días. Valores altos (>26 días) corresponden casi exclusivamente "
        "a créditos que eventualmente entran en morosidad. Correlación de Pearson con el evento: "
        "r = 0,680 — la más alta del conjunto de covariables.")

    add_heading(doc, "4.6.7  Análisis de Covariables: Moroso vs. Censurado", level=3)
    add_figure(doc, REPORTS / "fig06_covariables_evento.png",
               "Distribución de las covariables por grupo: Moroso (E=1) versus Censurado (E=0)", 6)
    add_table_data(doc,
        ["Covariable", "r con evento", "Dirección"],
        [["dias_sem_pagar",          "+0,6796", "Cronómetro directo del evento"],
         ["saldo_relativo",          "−0,0350", "Mayor saldo → menor morosidad"],
         ["dias_con_abono",          "−0,0217", "Más días con abono → menor riesgo"],
         ["ratio_atraso",            "−0,0176", "Contraintuitivo por composición"],
         ["pago_promedio_diario",    "−0,0152", "Más pagos → menor riesgo"],
         ["intensidad_recuperacion", "+0,0071", "Efecto mixto"]],
        "Correlaciones de las covariables con el evento", table_num=19)
    add_body(doc,
        "Las correlaciones lineales bajas de las covariables de mora y pago con el evento no "
        "implican ausencia de efecto predictivo — reflejan la naturaleza no lineal y dinámica "
        "de las relaciones en el contexto del Counting Process, que el modelo de Cox cuantificará "
        "correctamente vía hazard ratios.")

    add_heading(doc, "4.6.8  Perfil Económico del Portafolio", level=3)
    add_figure(doc, REPORTS / "fig07_perfil_credito.png",
               "Perfil económico: distribución del plazo, monto y boxplot por evento", 7)
    add_table_data(doc,
        ["Estadístico", "Valor"],
        [["Mediana", "R$ 1.200"], ["Media", "R$ 1.491"],
         ["Percentil 10", "R$ 540"], ["Percentil 90", "R$ 3.000"]],
        "Monto del crédito por grupo de evento", table_num=20)
    add_body(doc,
        "Créditos de bajo monto (mediana R$ 1.200), con plazo concentrado en 20 días (62,7%), "
        "24 días (29,3%) y 30 días (5,2%). La gran mayoría (92,0%) tiene plazo de 20 o 24 días — "
        "productos predefinidos por la institución, no negociados individualmente.")

    add_heading(doc, "4.6.9  Estructura de Correlaciones", level=3)
    add_figure(doc, REPORTS / "fig08_correlaciones.png",
               "Mapa de calor de correlaciones de las covariables (triángulo inferior)", 8)
    add_body(doc,
        "Correlación ratio_atraso ↔ cuotas_atrasadas: r ≈ +0,90 (redundancia — incluir solo una "
        "en el modelo Cox). Demás pares sin correlaciones problemáticas (> 0,7), indicando ausencia "
        "de multicolinealidad grave en el conjunto de covariables seleccionado.")

    add_heading(doc, "4.6.10  Análisis de Trayectorias Individuales", level=3)
    add_figure(doc, REPORTS / "fig09_trayectorias.png",
               "Trayectorias individuales: 5 créditos en morosidad versus 5 censurados", 9)
    add_body(doc,
        "Créditos en morosidad: dias_sem_pagar crece monótonamente en los últimos bloques, "
        "cruzando 120 días exactamente en el intervalo marcado como evento. Créditos censurados: "
        "el cronómetro permanece en cero con reinicializaciones frecuentes — el forward-fill "
        "captura correctamente la mora transitoria vs. abandono real.")

    add_heading(doc, "4.7  Síntesis y Validación del Dataset", level=2)
    add_table_data(doc,
        ["Validación", "Resultado"],
        [["t_stop > t_start en todos los intervalos",   "✓ Verificado"],
         ["Cadena perfecta t_start[k] = t_stop[k−1]",  "✓ Verificado (vía shift)"],
         ["Evento E=1 solo en el último intervalo",      "✓ Regla de censura aplicada"],
         ["Sin valores nulos en columnas clave",          "✓ Verificado"],
         ["Número de eventos > 100",                      "✓ 425 eventos"],
         ["Covariables en rango esperado",                "✓ Clip aplicado a todas las razones"]],
        "Validación del formato Counting Process", table_num=21)
    add_body(doc,
        "El dataset queda preparado para la etapa siguiente: ajuste del Modelo de Cox de Riesgos "
        "Proporcionales con covariables tiempo-variantes (lifelines.CoxTimeVaryingFitter).")


# ── SECCIÓN 5 ─────────────────────────────────────────────────────────────────

def build_seccion_5(doc):
    add_heading(doc, "5  MODELAMIENTO MATEMÁTICO Y COMPUTACIONAL (EL DESAFÍO DE LA CENSURA)", level=1)
    add_heading(doc, "5.1  Baseline Clásico (Modelo de Cox)", level=2)
    add_body(doc,
        "La fase inicial aplicará el Modelo de Riesgos Proporcionales de Cox para establecer el "
        "marco de interpretabilidad y cuantificar el impacto de las covariables (Hazard Ratios). "
        "Los Residuos de Schoenfeld servirán como diagnóstico para validar el supuesto de "
        "proporcionalidad. [RESULTADO PENDIENTE — Sprint 3]")
    add_heading(doc, "5.2  El Desafío de la Censura por la Derecha en Arquitecturas Neurales", level=2)
    add_body(doc,
        "Las arquitecturas de Deep Learning tradicionales fallan al ignorar la información "
        "contenida en los registros censurados por la derecha. Descartar estas observaciones "
        "introduce sesgo severo y subestima el tiempo real de supervivencia.")
    add_heading(doc, "5.3  Enfoque Estado del Arte (Deep Learning bajo Censura)", level=2)
    add_body(doc,
        "Redes neuronales recurrentes (LSTM/GRU) integradas al Análisis de Supervivencia "
        "(DeepSurv/RNN-Survival) con optimización de la Verosimilitud Parcial Negativa "
        "(Negative Partial Log-Likelihood), respetando matemáticamente el tiempo de "
        "supervivencia acumulado de los clientes bajo censura. [IMPLEMENTACIÓN PENDIENTE — Sprint 3]")


# ── SECCIÓN 6 ─────────────────────────────────────────────────────────────────

def build_seccion_6(doc):
    add_heading(doc, "6  VALIDACIÓN", level=1)
    add_body(doc,
        "Las pruebas de rendimiento compararán el modelo de supervivencia clásico con las técnicas "
        "de Deep Learning, utilizando: C-index de Harrell (índice de concordancia), Brier Score "
        "temporal y Prueba de Log-Rank entre modelos. [RESULTADOS PENDIENTES — Sprint 4]")


# ── SECCIÓN 7 ─────────────────────────────────────────────────────────────────

def build_seccion_7(doc):
    add_heading(doc, "7  CRONOGRAMA INTEGRADO DE INVESTIGACIÓN", level=1)
    add_body(doc,
        "Proyecto estructurado en cuatro Sprints Scrum (Louzada Neto, 2026), con entregas "
        "iterativas que permiten ajustes de alcance sin comprometer el plazo final:")
    sprints = [
        ("Sprint 1 (Ene–Mar 2026) — ETL/Pipeline [COMPLETADO]:",
         "Desarrollo del extractor Selenium (AtlasDataExtractor y AtlasMasivoExtractor), "
         "extracción de 3.962 archivos Excel (3 oficinas, 17 rutas, 2020–2026), Data Lake "
         "jerárquico (~14 GB), sistema de checkpoint JSON, consolidación de la Matriz Maestra "
         "(344.869 × 2.358) y optimización de memoria vía chunked loading con máscara NumPy (−49% RAM)."),
        ("Sprint 2 (Mar–May 2026) — Ingeniería de Características + EDA [COMPLETADO]:",
         "Definición e implementación del cronómetro dias_sem_pagar, construcción del dataset "
         "de supervivencia en formato Counting Process (28.386 créditos, 301.434 intervalos, "
         "425 eventos, 1,50%), análisis exploratorio completo con 9 figuras de diagnóstico y "
         "elaboración del informe metodológico (Secciones 3 y 4 del TCC)."),
        ("Sprint 3 (Jun–Ago 2026) — Modelamiento Cox + DeepSurv [PENDIENTE]:",
         "Ajuste del Modelo de Riesgos Proporcionales de Cox con covariables tiempo-variantes, "
         "diagnóstico de residuos de Schoenfeld, implementación de DeepSurv/RNN-Survival con "
         "Negative Partial Log-Likelihood y comparación de Hazard Ratios."),
        ("Sprint 4 (Sep–Nov 2026) — Evaluación + Redacción final [PENDIENTE]:",
         "C-index de Harrell, Brier Score temporal, comparativo con Credit Scoring binario, "
         "redacción de Resultados, Discusión y Conclusión del TCC."),
    ]
    for label, text in sprints:
        add_labeled(doc, label, text)


# ── REFERENCIAS ───────────────────────────────────────────────────────────────

def build_referencias(doc):
    add_heading(doc, "REFERENCIAS BIBLIOGRÁFICAS", level=1)
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
        "proportional hazards deep neural network. BMC Medical Research Methodology, v. 18, n. 24, 2018.",
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
        p.paragraph_format.space_after = Pt(6)
        run = p.add_run(ref)
        _set_font(run, bold=True)


# ── MAIN ──────────────────────────────────────────────────────────────────────

def build_doc():
    doc = Document()
    configure_doc(doc)

    build_portada(doc)
    build_resumen(doc)
    build_abstract(doc)
    build_listas(doc)
    build_sumario(doc)

    build_seccion_1(doc)
    build_seccion_2(doc)
    build_seccion_3(doc)
    build_seccion_4(doc)
    build_seccion_5(doc)
    build_seccion_6(doc)
    build_seccion_7(doc)
    build_referencias(doc)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUTPUT)
    print(f"\n[ES] V22 generado: {OUTPUT}")
    print(f"     Tamaño: {OUTPUT.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    build_doc()
