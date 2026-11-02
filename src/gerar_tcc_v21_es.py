"""
gerar_tcc_v21_es.py — Versión en Español del TCC V21 (formato USP).

Misma estructura que la versión en Portugués pero con todo el texto en Español.
Output: documentotcc/TCC_V21_Español_Completo.docx
"""

from pathlib import Path
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING

BASE   = Path(__file__).parent.parent
OUTPUT = BASE / "documentotcc" / "TCC_V21_Español_Completo.docx"

# ── Helpers (idénticos al script PT) ────────────────────────────────────────

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
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after  = Pt(6)
    p.paragraph_format.first_line_indent = Cm(0)
    sizes = {1: 16, 2: 14, 3: 12, 4: 12, 5: 12}
    size  = sizes.get(level, 12)
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
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after  = Pt(6)
    p.paragraph_format.first_line_indent = Cm(0)
    run = p.add_run(formula_text)
    _set_font(run, size=11, italic=True)
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
    cap.paragraph_format.space_after = Pt(12)
    r = cap.add_run(f"Figura {fig_num} – {caption}")
    _set_font(r, size=10, italic=True)

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


# ── PRE-TEXTUALES ────────────────────────────────────────────────────────────

def build_capa(doc):
    add_centered(doc, "UNIVERSIDAD DE SÃO PAULO", size=14, bold=True, spacing=1.0)
    add_centered(doc, "Instituto de Ciências Matemáticas e de Computação – ICMC", size=12, bold=True, spacing=1.0)
    add_centered(doc, "MBA en Ciencia de Datos", size=12, bold=False, spacing=1.0)
    for _ in range(6):
        add_centered(doc, "", size=12, spacing=1.0)
    add_centered(doc, "Juan Fernando Graciano Pinzón", size=13, bold=True, spacing=1.0)
    for _ in range(4):
        add_centered(doc, "", size=12, spacing=1.0)
    add_centered(
        doc,
        "Modelado de Riesgo de Crédito Dinámico para Microempresarios: "
        "Un Enfoque vía Análisis de Supervivencia en Flujos de Alta Frecuencia bajo Censura",
        size=17, bold=True, spacing=1.5,
    )
    for _ in range(4):
        add_centered(doc, "", size=12, spacing=1.0)
    add_centered(doc, "Director: Prof. Dr. Vicente Garibay Cancho", size=12, bold=False, spacing=1.0)
    add_centered(doc, "Área de concentración: Ciencia de Datos", size=12, bold=False, spacing=1.0)
    for _ in range(4):
        add_centered(doc, "", size=12, spacing=1.0)
    add_centered(doc, "São Paulo / São Carlos, 2026", size=11, bold=False, spacing=1.0)
    page_break(doc)


def build_resumen(doc):
    add_heading(doc, "RESUMEN", level=1)
    add_body(doc,
        "GRACIANO PINZÓN, Juan Fernando. Modelado de Riesgo de Crédito Dinámico para "
        "Microempresarios: Un Enfoque vía Análisis de Supervivencia en Flujos de Alta "
        "Frecuencia bajo Censura. 2026. Trabajo de Conclusión de Curso – MBA en Ciencia "
        "de Datos, Instituto de Ciências Matemáticas e de Computação, Universidad de São Paulo, "
        "São Paulo/São Carlos, 2026.",
        indent_first=False)
    doc.add_paragraph()
    add_body(doc,
        "La concesión de crédito para el segmento de microempresarios en Brasil enfrenta una "
        "severa asimetría de información, con modelos tradicionales basados en datos estáticos "
        "que ignoran la dinámica de pagos en tiempo real. Esta investigación desarrolla un modelo "
        "predictivo de riesgo de crédito dinámico utilizando Análisis de Supervivencia con "
        "covariables dependientes del tiempo, fundamentado en datos de alta frecuencia de una "
        "institución de microcrédito de pago diario. Un pipeline de extracción automatizado "
        "(RPA con Selenium) recopiló 3.962 planillas Excel del Sistema ATLAS, cubriendo tres "
        "oficinas y 17 rutas en el período 2020–2026, resultando en una Matriz Maestra de "
        "344.869 filas y 2.358 columnas. Tras la ingeniería de características en formato "
        "Counting Process (Anderson y Gill, 1982), el dataset de supervivencia final contiene "
        "28.386 créditos únicos, 301.434 intervalos temporales y 425 eventos de castigo de "
        "cartera (tasa de default del 1,50%). El evento se define como dias_sin_pagar ≥ 120 "
        "días calendario — equivalente a cuatro meses consecutivos sin ningún abono. El "
        "análisis exploratorio reveló que la curva de Kaplan-Meier permanece en S(t) = 1,0 "
        "hasta el día 120, cayendo a S(180) = 0,68 y S(365) = 0,17, indicando que los créditos "
        "de larga permanencia concentran el riesgo. La siguiente etapa comprende el ajuste del "
        "Modelo de Cox de Riesgos Proporcionales con covariables tiempo-variantes y la "
        "implementación de arquitecturas de Deep Learning para supervivencia (DeepSurv), con "
        "comparación vía C-index de Harrell y Brier Score temporal.",
        indent_first=False)
    p = doc.add_paragraph()
    _set_spacing(p)
    run = p.add_run(
        "Palabras clave: análisis de supervivencia; microcrédito; modelo de Cox; DeepSurv; "
        "alta frecuencia; proceso de conteo; default."
    )
    _set_font(run)
    page_break(doc)


def build_abstract(doc):
    add_heading(doc, "ABSTRACT", level=1)
    add_body(doc,
        "GRACIANO PINZÓN, Juan Fernando. Dynamic Credit Risk Modeling for Microentrepreneurs: "
        "A Survival Analysis Approach on High-Frequency Flows under Censoring. 2026. Final "
        "Course Work – MBA in Data Science, Institute of Mathematics and Computer Science, "
        "University of São Paulo, São Paulo/São Carlos, 2026.",
        indent_first=False)
    doc.add_paragraph()
    add_body(doc,
        "Lending to the micro-entrepreneur segment in Brazil faces severe information asymmetry, "
        "with traditional models based on static data that ignore real-time payment dynamics. This "
        "research develops a dynamic credit risk prediction model using Survival Analysis with "
        "time-varying covariates, grounded in high-frequency data from a daily-payment microcredit "
        "institution. An automated extraction pipeline (RPA with Selenium) collected 3,962 Excel "
        "spreadsheets from the ATLAS System, covering three offices and 17 routes over the period "
        "2020–2026, resulting in a Master Matrix of 344,869 rows and 2,358 columns. After feature "
        "engineering in the Counting Process format (Anderson and Gill, 1982), the final survival "
        "dataset contains 28,386 unique credits, 301,434 time intervals, and 425 write-off events "
        "(default rate: 1.50%). The event is defined as days_without_payment ≥ 120 calendar days. "
        "Exploratory analysis revealed that the Kaplan-Meier curve remains at S(t) = 1.0 until "
        "day 120, dropping to S(180) = 0.68 and S(365) = 0.17.",
        indent_first=False)
    p = doc.add_paragraph()
    _set_spacing(p)
    run = p.add_run(
        "Keywords: survival analysis; microcredit; Cox model; DeepSurv; high-frequency data; "
        "counting process; default."
    )
    _set_font(run)
    page_break(doc)


def build_listas(doc):
    add_heading(doc, "LISTA DE ILUSTRACIONES", level=1)
    figs = [
        ("1",  "Distribución del evento de default: proporción, tasa por oficina y por ruta"),
        ("2",  "Curva de Kaplan-Meier global del portafolio con tabla de n en riesgo"),
        ("3",  "Curvas de Kaplan-Meier por oficina con prueba de log-rank"),
        ("4",  "Distribución del tiempo de seguimiento (t_stop) e intervalos por crédito"),
        ("5",  "Distribución de dias_sin_pagar: global, zoom 0–150 días y máximo por crédito"),
        ("6",  "Distribución de covariables: Default (E=1) versus Censurado (E=0)"),
        ("7",  "Perfil económico del portafolio: plazo, monto y boxplot por evento"),
        ("8",  "Mapa de calor de correlaciones de las covariables del modelo"),
        ("9",  "Trayectorias individuales: 5 créditos en default versus 5 censurados"),
    ]
    for num, desc in figs:
        p = doc.add_paragraph()
        _set_spacing(p, multiple=1.0)
        p.paragraph_format.first_line_indent = Cm(0)
        run = p.add_run(f"Figura {num} – {desc}")
        _set_font(run, size=12)
    page_break(doc)

    add_heading(doc, "LISTA DE ABREVIATURAS Y SIGLAS", level=1)
    abrevs = [
        ("ABNT",    "Asociación Brasileña de Normas Técnicas"),
        ("CRISP-DS","Cross Industry Standard Process for Data Science"),
        ("EDA",     "Análisis Exploratorio de Datos"),
        ("ETL",     "Extract, Transform, Load"),
        ("KM",      "Kaplan-Meier"),
        ("LGPD",    "Ley General de Protección de Datos Personales (Brasil)"),
        ("LSTM",    "Long Short-Term Memory"),
        ("MLOps",   "Machine Learning Operations"),
        ("RPA",     "Robotic Process Automation"),
        ("TCC",     "Trabajo de Conclusión de Curso"),
        ("USP",     "Universidad de São Paulo"),
    ]
    for sigla, desc in abrevs:
        p = doc.add_paragraph()
        _set_spacing(p, multiple=1.0)
        p.paragraph_format.first_line_indent = Cm(0)
        run = p.add_run(f"{sigla} – {desc}")
        _set_font(run, size=12)
    page_break(doc)


def build_sumario(doc):
    add_heading(doc, "ÍNDICE", level=1)
    entries = [
        (1, "1", "INTRODUCCIÓN Y CONTEXTUALIZACIÓN DEL PROBLEMA"),
        (1, "2", "OBJETIVOS"),
        (1, "3", "ARQUITECTURA DE DATOS Y PIPELINE DE EXTRACCIÓN INDUSTRIAL (ETL)"),
        (1, "4", "INGENIERÍA DE VARIABLES Y DEFINICIÓN DEL EVENTO OBJETIVO"),
        (2, "4.1", "Fundamentos Teóricos del Análisis de Supervivencia"),
        (3, "4.1.1", "Función de Supervivencia y Función de Riesgo"),
        (3, "4.1.2", "Tipos de Censura y Truncación por la Izquierda"),
        (3, "4.1.3", "Estimador de Kaplan-Meier"),
        (3, "4.1.4", "Prueba de Log-Rank"),
        (3, "4.1.5", "Proceso de Conteo de Anderson-Gill"),
        (2, "4.2", "Definición Operacional de la Morosidad en Alta Frecuencia"),
        (2, "4.3", "Estructura Bimodal de Atributos y Estrategia de Proxy"),
        (2, "4.4", "Formateo Anderson-Gill (Counting Process)"),
        (2, "4.5", "Construcción del Dataset de Supervivencia"),
        (2, "4.6", "Análisis Exploratorio de Datos (EDA)"),
        (3, "4.6.1", "Caracterización General del Dataset"),
        (3, "4.6.2", "Distribución del Evento de Default"),
        (3, "4.6.3", "Curva de Kaplan-Meier Global"),
        (3, "4.6.4", "Análisis Estratificado por Oficina (Log-Rank)"),
        (3, "4.6.5", "Tiempo de Seguimiento y Granularidad Longitudinal"),
        (3, "4.6.6", "Cronómetro dias_sin_pagar"),
        (3, "4.6.7", "Covariables: Default vs. Censurado"),
        (3, "4.6.8", "Perfil Económico del Portafolio"),
        (3, "4.6.9", "Estructura de Correlaciones"),
        (3, "4.6.10", "Análisis de Trayectorias Individuales"),
        (2, "4.7", "Síntesis y Validación del Dataset"),
        (1, "5", "MODELADO MATEMÁTICO Y COMPUTACIONAL"),
        (1, "6", "VALIDACIÓN"),
        (1, "7", "CRONOGRAMA INTEGRADO DE INVESTIGACIÓN"),
        (1, "REFERENCIAS", "REFERENCIAS BIBLIOGRÁFICAS"),
    ]
    for level, num, title in entries:
        p = doc.add_paragraph()
        _set_spacing(p, multiple=1.0)
        p.paragraph_format.first_line_indent = Cm(0)
        p.paragraph_format.left_indent = Cm((level - 1) * 0.75)
        label = f"{num}  {title}" if num != "REFERENCIAS" else title
        run = p.add_run(label)
        _set_font(run, size=12, bold=(level == 1))
    page_break(doc)


# ── SECCIONES ────────────────────────────────────────────────────────────────

def build_secao_1(doc):
    add_heading(doc, "1  INTRODUCCIÓN Y CONTEXTUALIZACIÓN DEL PROBLEMA", level=1)
    add_body(doc,
        "La concesión de crédito para el segmento microempresarial (específicamente el nicho "
        "Subprime o Thin-File) en Brasil y en toda América Latina enfrenta una severa asimetría "
        "de información. Las instituciones financieras tradicionales basan sus modelos de riesgo "
        "en datos estáticos e históricos desactualizados (como anotaciones en burós de crédito, "
        "scores estáticos o balances anuales). Este enfoque frecuentemente penaliza al "
        "microempresario por eventos pasados, ignorando su real y actual capacidad de generación "
        "de flujo de caja."
    )
    add_body(doc,
        "Ante este escenario, esta investigación propone un cambio de paradigma: la utilización "
        "de datos dinámicos y de alta frecuencia, específicamente el registro interno de pagos "
        "diarios (abonos) y sus respectivas modalidades de liquidación, para evaluar la salud "
        "financiera del negocio en tiempo real. El estudio es viabilizado a través del uso de "
        "una base de datos estratégica proporcionada por una empresa socia especializada en "
        "microcrédito para el sector informal. El gran diferencial de este enfoque reside en "
        "observar la liquidez diaria y la intensidad de estos pagos parciales, modelando el "
        "riesgo de default no como un evento binario y estático, sino como un proceso dinámico "
        "y continuo en el tiempo."
    )


def build_secao_2(doc):
    add_heading(doc, "2  OBJETIVOS", level=1)
    add_heading(doc, "2.1  Objetivo General", level=2)
    add_body(doc,
        "Desarrollar un modelo predictivo de riesgo de crédito basado en Análisis de "
        "Supervivencia (Survival Analysis) para estimar el tiempo exacto hasta la ruptura del "
        "flujo de caja y de la capacidad de pago (morosidad técnica) de los microempresarios, "
        "integrando variables estáticas demográficas y datos longitudinales de flujo transaccional "
        "de alta frecuencia."
    )
    add_heading(doc, "2.2  Objetivos Específicos", level=2)
    items = [
        ("Ingeniería de Datos (ETL/RPA):",
         "Diseñar e implementar un sistema robusto de ingestión masiva capaz de superar "
         "limitaciones de sistemas legados, extrayendo y organizando el historial transaccional "
         "de múltiples unidades de negocio en un Data Lake."),
        ("Data Stitching y MLOps:",
         "Unificar los snapshots temporales en una Matriz Maestra (Silver Layer) con "
         "trazabilidad total (Data Lineage) y optimización computacional de memoria."),
        ("Tratamiento y EDA:",
         "Aplicar el estimador no paramétrico de Kaplan-Meier para el análisis exploratorio "
         "del tiempo de supervivencia de la capacidad de pago de la cartera, y extraer "
         "covariables espacio-temporales (clústeres de rutas)."),
        ("Modelado de Baseline Clásico:",
         "Entrenar y ajustar el Modelo de Riesgos Proporcionales de Cox para cuantificar la "
         "inferencia y el impacto de las covariables estáticas y dependientes del tiempo "
         "(time-varying covariates) en la función de riesgo basal."),
        ("Innovación y Aporte Académico (Deep Learning):",
         "Comparar el rendimiento predictivo y la explicabilidad del modelo paramétrico de Cox "
         "con arquitecturas contemporáneas de Deep Learning adaptadas para datos de supervivencia "
         "(como DeepSurv o Redes Neuronales Recurrentes — RNNs), incorporando tratamiento para "
         "censura (Negative Partial Log-Likelihood)."),
        ("Comparativo Clasificatorio:",
         "Evaluar las ganancias marginales del enfoque de supervivencia frente a los modelos "
         "tradicionales de Credit Scoring de clasificación binaria."),
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


def build_secao_3(doc):
    add_heading(doc, "3  ARQUITECTURA DE DATOS Y PIPELINE DE EXTRACCIÓN INDUSTRIAL (ETL)", level=1)

    add_heading(doc, "3.1  Contexto y Resolución de Barreras vía Automatización (RPA)", level=2)
    add_body(doc,
        "La construcción de modelos de análisis de supervivencia exige series longitudinales "
        "precisas. La fuente primaria es el Sistema corporativo ATLAS que no expone APIs REST "
        "y restringe extracciones a ventanas de 10 días en una interfaz web basada en frames "
        "anidados y autenticación compleja. Para superar esto, se desarrolló la clase orientada "
        "a objetos AtlasDataExtractor en Python 3.12 (Selenium WebDriver), con mecanismo de "
        "retry de tres intentos para manejar errores de elemento obsoleto (StaleElementReferenceException)."
    )

    add_heading(doc, "3.2  Escalabilidad Corporativa y Descubrimiento Automático", level=2)
    add_body(doc,
        "El pipeline evolucionó hacia un sistema de Ingestión Masiva que opera de forma "
        "autónoma. Un algoritmo de Auto-Discovery navega la jerarquía de oficinas y rutas "
        "mapeando todas las dependencias sin intervención humana, detectando automáticamente "
        "3 Oficinas y 17 Rutas geográficas, generando una extracción de 3.962 archivos Excel "
        "con historial de 2020 a 2026."
    )

    add_heading(doc, "3.3  Procesamiento Batch, Filtro Anti-Cero y Persistencia", level=2)
    add_body(doc,
        "Debido al límite de 10 días por extracción del sistema, el algoritmo de paginación "
        "temporal divide el horizonte de ~seis años en bloques estrictos. El pipeline "
        "implementa: (1) Validación de UI — aborta el descarga si los datos retornan nulos; "
        "(2) Smart Wait — monitoreo asíncrono con renombrado semántico de cada lote en el "
        "patrón planilla_abonos_YYYYMMDD_YYYYMMDD.xlsx; (3) Checkpointing — persistencia de "
        "estado en JSON para reanudar en el último bloque procesado con éxito. La gestión de "
        "riesgos siguió las siete categorías del gerenciamiento de proyectos de Ciencia de "
        "Datos: calidad de datos, presupuesto, compromiso, recursos humanos, proveedores, "
        "seguridad y expectativas de tiempo (Louzada Neto, 2026)."
    )

    add_heading(doc, "3.4  Arquitectura del Data Lake, Pipeline de Consolidación y CRISP-DS", level=2)
    add_body(doc,
        "Los archivos ingeridos alimentan una jerarquía rígida de directorios "
        "(data/raw/OFI_{id}/RTA_{id}/planilla.xlsx) que garantiza trazabilidad total "
        "(Data Lineage). El pipeline es estructurado bajo la metodología CRISP-DS (Cross "
        "Industry Standard Process for Data Science): (1) Entendimiento del Negocio → "
        "definición del evento de castigo de cartera; (2) Entendimiento de los Datos → EDA; "
        "(3) Preparación de Datos → Feature Engineering en formato Counting Process; "
        "(4) Modelado → Cox y DeepSurv; (5) Evaluación → C-index y Brier Score; "
        "(6) Despliegue → scoring dinámico en producción. Un algoritmo de optimización de "
        "memoria vía downcasting numérico y categorización de strings redujo el footprint "
        "en RAM en un 49%, viabilizando el procesamiento de la Matriz Maestra de 882 MB."
    )


def build_secao_4(doc):
    add_heading(doc, "4  INGENIERÍA DE VARIABLES Y DEFINICIÓN DEL EVENTO OBJETIVO", level=1)

    # 4.1 Fundamentos Teóricos
    add_heading(doc, "4.1  Fundamentos Teóricos del Análisis de Supervivencia", level=2)
    add_body(doc,
        "El análisis de supervivencia comprende un conjunto de técnicas estadísticas diseñadas "
        "para modelar el tiempo hasta la ocurrencia de un evento de interés (Kalbfleisch y "
        "Prentice, 2002). A diferencia de la regresión logística — que estima la probabilidad "
        "de default en un punto fijo del tiempo —, el análisis de supervivencia incorpora "
        "explícitamente la dimensión temporal, distinguiendo entre individuos que experimentaron "
        "el evento y aquellos observados sin experimentarlo (censurados)."
    )

    add_heading(doc, "4.1.1  Función de Supervivencia y Función de Riesgo", level=3)
    add_body(doc,
        "Sea T una variable aleatoria continua no negativa que representa el tiempo hasta el "
        "evento. La función de supervivencia es:"
    )
    add_formula(doc, "S(t) = P(T > t) = 1 − F(t)")
    add_body(doc,
        "donde F(t) es la función de distribución acumulada de T. La función de riesgo "
        "(hazard function) mide la tasa condicional de ocurrencia del evento en el instante t:"
    )
    add_formula(doc, "h(t) = lim[Δt→0] P(t ≤ T < t+Δt | T ≥ t) / Δt = f(t) / S(t)")
    add_body(doc, "La relación fundamental entre ambas funciones es:")
    add_formula(doc, "S(t) = exp(−∫₀ᵗ h(u) du) = exp(−H(t))")

    add_heading(doc, "4.1.2  Tipos de Censura y Truncación por la Izquierda", level=3)
    add_body(doc,
        "La censura a la derecha (right censoring) ocurre cuando el evento no ocurrió antes "
        "del fin de la observación — aplica a los créditos activos al corte del estudio "
        "(15 de mayo de 2026). La truncación por la izquierda (left truncation) ocurre cuando "
        "el primer snapshot disponible de un crédito corresponde a una fecha posterior a su "
        "desembolso. El tratamiento correcto de ambos fenómenos — implementado mediante el "
        "formato Counting Process — es condición necesaria para la validez estadística del "
        "modelo de Cox (Therneau y Grambsch, 2000)."
    )

    add_heading(doc, "4.1.3  Estimador de Kaplan-Meier", level=3)
    add_body(doc,
        "El estimador de Kaplan-Meier (Kaplan y Meier, 1958) es el estimador no paramétrico "
        "estándar de la función de supervivencia. Sean t₁ < t₂ < ... < tₖ los tiempos distintos "
        "en que ocurrieron eventos, dⱼ el número de eventos y nⱼ el número de individuos en "
        "riesgo en tⱼ:"
    )
    add_formula(doc, "Ŝ(t) = ∏[j: tⱼ ≤ t] (1 − dⱼ/nⱼ)")
    add_body(doc,
        "Propiedades: (1) Consistencia; (2) No paramétrico; (3) Corrección automática por "
        "censura. El intervalo de confianza usa la transformación de Greenwood: "
        "Var[Ŝ(t)] = Ŝ(t)² × Σ[dⱼ / (nⱼ(nⱼ−dⱼ))]."
    )

    add_heading(doc, "4.1.4  Prueba de Log-Rank", level=3)
    add_body(doc,
        "La prueba de log-rank (Mantel, 1966) compara las curvas de supervivencia de dos o más "
        "grupos sin asumir una forma paramétrica. La hipótesis nula es H₀: S₁(t) = S₂(t) ∀t. "
        "El estadístico Q sigue una distribución χ² con (k−1) grados de libertad bajo H₀."
    )

    add_heading(doc, "4.1.5  Proceso de Conteo de Anderson-Gill", level=3)
    add_body(doc,
        "El modelo clásico de Cox asume covariables fijas en el tiempo. El marco del Proceso "
        "de Conteo de Anderson y Gill (1982) representa al individuo i mediante una secuencia "
        "de intervalos contiguos:"
    )
    add_formula(doc, "(t_start₁, t_stop₁, δ₁, X_{i1}), (t_start₂, t_stop₂, δ₂, X_{i2}), ...")
    add_body(doc,
        "Restricciones: (1) t_start[k] = t_stop[k−1] exactamente; (2) el evento δ=1 solo en "
        "el último intervalo; (3) intervalos (t_start, t_stop] abiertos por la izquierda."
    )

    # 4.2 Definición Operacional
    add_heading(doc, "4.2  Definición Operacional de la Morosidad en Alta Frecuencia", level=2)
    add_body(doc,
        "A diferencia del retail bancario tradicional (donde 1 cuota = 30 días), el modelo "
        "operativo de la institución socia se basa en ciclos diarios. La calibración del evento "
        "fue definida bajo los siguientes parámetros:"
    )
    for label, text in [
        ("Equivalencia Temporal:",
         "Se adopta la premisa fundamental de que 1 cuota atrasada equivale a 1 día de atraso real."),
        ("Evento de Falla/Ruptura (E=1):",
         "Definido inicialmente como el alcance del campo CUOTAS_ATRASADAS igual a 120. Sin "
         "embargo, la ejecución empírica del pipeline reveló que esta variable tiene techo "
         "operacional equivalente a CUOTAS_PACTADAS (máximo 40 días para la cohorte diaria), "
         "haciendo imposible alcanzar 120 cuotas atrasadas — lo que produjo exactamente cero "
         "eventos. La definición fue revisada a: E=1 cuando dias_sin_pagar ≥ 120 días "
         "calendario, el denominado 'castigo de cartera' operativo. La distinción conceptual "
         "central es entre mora transitoria (el cliente atrasa algunos días pero retoma los "
         "pagos, reiniciando el cronómetro) y abandono real (el cliente cesa completamente los "
         "pagos por más de 4 meses)."),
        ("Tiempo de Supervivencia (T):",
         "Mide el número de días desde el desembolso del microcrédito hasta que dias_sin_pagar "
         "= 120. Clientes activos, saldados o con inactividad inferior a 120 días al corte de "
         "la base son tratados mediante Censura a la Derecha (E=0)."),
        ("Criterio de Pureza Temporal:",
         "El universo de estudio se restringe a la cohorte de pagos diarios (planes de 20, 24, "
         "30 y 40 cuotas), excluyendo créditos semanales/quincenales/mensuales."),
    ]:
        p = doc.add_paragraph()
        _set_spacing(p)
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.first_line_indent = Cm(1.25)
        r1 = p.add_run(label + " ")
        _set_font(r1, bold=True)
        r2 = p.add_run(text)
        _set_font(r2)

    # 4.3
    add_heading(doc, "4.3  Estructura Bimodal de Atributos y Estrategia de Proxy", level=2)
    for txt in [
        "Variables Estáticas: Parámetros del crédito (Monto Total, Valor de Cuota, Cuotas Pactadas).",
        "Geodemographic Proxy: Ante la informalidad del sector y la ausencia de variables "
        "demográficas estructuradas, el modelo utiliza la ubicación geográfica (IDs de Ruta y "
        "Oficina) como covariables de control proxy del contexto socioeconómico local.",
        "Variables Dinámicas (Heartbeat): El vector longitudinal de pagos, cuotas atrasadas en "
        "el tiempo t, intensidad transaccional de abonos (Valor Último Abono / Valor Cuota) y "
        "días con abono, capturando la verdadera 'frecuencia cardíaca' financiera del empresario.",
    ]:
        add_body(doc, txt)

    # 4.4
    add_heading(doc, "4.4  Formateo Anderson-Gill (Counting Process)", level=2)
    add_body(doc,
        "La matriz transaccional es transformada en intervalos longitudinales contínuos (t_start, t_stop]. "
        "Se resuelven dos desafíos matemáticos críticos:"
    )
    for label, text in [
        ("Left Truncation:",
         "t_start(primera fila) = max(0, fecha_ini_bloque − FECHA_CRÉDITO) en días, "
         "previniendo tiempos de vida negativos."),
        ("Continuidad de Markov:",
         "t_start[n] = t_stop[n−1] garantizado vía shift(), eliminando gaps temporales "
         "que harían que el modelo asumiera la desaparición artificial del cliente."),
    ]:
        p = doc.add_paragraph()
        _set_spacing(p)
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.first_line_indent = Cm(1.25)
        r1 = p.add_run(label + " ")
        _set_font(r1, bold=True)
        r2 = p.add_run(text)
        _set_font(r2)

    # 4.5
    add_heading(doc, "4.5  Construcción del Dataset de Supervivencia", level=2)
    add_heading(doc, "4.5.1  Fuente de Datos: Sistema ATLAS y Data Lake", level=3)
    add_table_data(doc,
        ["Componente", "Volumen"],
        [["Archivos Excel descargados", "3.962"],
         ["Oficinas cubiertas", "3 (OFI_23 São Paulo, OFI_31 Soc. Brasil, OFI_44 Cabo Frio)"],
         ["Rutas cubiertas", "17"],
         ["Período de cobertura", "2020-01-01 → 2026-05-15"],
         ["Tamaño del Data Lake (bruto)", "~14 GB"]],
        "Componentes y volumen del Data Lake extraído", table_num=1)
    add_table_data(doc,
        ["Métrica", "Valor"],
        [["Filas (observaciones)", "344.869"],
         ["Columnas totales", "2.358"],
         ["Columnas de pagos diarios", "~2.330"],
         ["Tamaño en disco", "882 MB"],
         ["Tamaño en RAM (expandido)", "~6 GB"]],
        "Dimensiones de la Matriz Maestra tras la consolidación", table_num=2)
    add_body(doc,
        "La escala del dataset imposibilita su carga completa en memoria. El pipeline implementa "
        "lectura por chunks de 5.000 filas con máscara vectorizada NumPy para calcular los "
        "agregados de pago sin materializar las ~2.330 columnas de fecha en RAM."
    )

    add_heading(doc, "4.5.2  Filtro de Cohorte Diaria", level=3)
    add_table_data(doc,
        ["Cohorte", "Criterio", "Créditos"],
        [["Diaria (incluida)", "CUOTAS_PACTADAS ≤ 40", "28.386"],
         ["Semanal/quincenal/mensual (excluida)", "CUOTAS_PACTADAS > 40", "—"]],
        "Filtro de cohorte diaria: criterio y créditos retenidos", table_num=3)

    add_heading(doc, "4.5.3  Cronómetro de Inactividad Financiera (forward-fill)", level=3)
    add_body(doc,
        "El cálculo de dias_sin_pagar sigue lógica de forward-fill: (1) inicializar "
        "fecha_ultimo_pago_efectivo = FECHA_CRÉDITO; (2) por cada bloque t: si "
        "dias_con_abono > 0, actualizar fecha = fecha_fin_bloque; si no, mantener el valor "
        "anterior; (3) dias_sin_pagar = (fecha_fin_bloque − fecha_ultimo_pago_efectivo).días. "
        "Propiedades: semilla correcta, reinicio automático por cualquier abono, acumulación "
        "continua y clipeo inferior (max(0, días))."
    )

    add_heading(doc, "4.5.4  Correcciones del Formato Counting Process", level=3)
    add_formula(doc, "t_stop[t] = (fecha_fin_bloque[t] − FECHA_CRÉDITO).días + 1")
    add_formula(doc, "t_start[t] = t_stop[t−1]  para  t > 1")
    add_body(doc,
        "Tras el evento (dias_sin_pagar ≥ 120), la trayectoria del crédito se trunca: "
        "los snapshots posteriores son eliminados, garantizando que el evento sea el "
        "último intervalo observado de cada crédito."
    )

    add_heading(doc, "4.5.5  Variables Covariadas", level=3)
    add_table_data(doc,
        ["Variable", "Tipo", "Descripción"],
        [["t_start", "Continua", "Inicio del intervalo (días desde el desembolso)"],
         ["t_stop",  "Continua", "Fin del intervalo (días desde el desembolso)"],
         ["evento",  "Binaria",  "1 = default (dias_sin_pagar ≥ 120), 0 = censura"],
         ["dias_sin_pagar", "Discreta", "Cronómetro de inactividad financiera"]],
        "Variables de tiempo y evento", table_num=4)
    add_table_data(doc,
        ["Variable", "Fórmula", "Interpretación"],
        [["cuotas_atrasadas", "CUOTAS_ATRASADAS", "Días en mora en el snapshot"],
         ["pago_promedio_diario", "Σ(pagos_bloque)/días_bloque", "Flujo promedio de pagos (BRL)"],
         ["dias_con_abono", "#{días con abono > 0}", "Frecuencia de pago en el período"],
         ["intensidad_recuperacion", "ÚLTIMO_ABONO / VALOR_CUOTA", "Fracción de la cuota pagada (clip [0,10])"],
         ["ratio_atraso", "CUOTAS_ATR / CUOTAS_PACT", "Fracción del plazo en mora (clip [0,1])"],
         ["saldo_relativo", "SALDO / TOTAL_CRÉDITO", "Fracción del crédito pendiente (clip [0,1])"]],
        "Covariables tiempo-variantes y sus fórmulas", table_num=5)

    # 4.6 EDA
    add_heading(doc, "4.6  Análisis Exploratorio de Datos (EDA)", level=2)
    add_body(doc,
        "El análisis exploratorio fue desarrollado en el notebook notebooks/01_eda_survival.ipynb, "
        "generando nueve figuras de diagnóstico (Figuras 1–9) documentadas a continuación."
    )

    add_heading(doc, "4.6.1  Caracterización General del Dataset", level=3)
    add_table_data(doc,
        ["Métrica", "Valor"],
        [["Créditos únicos", "28.386"],
         ["Intervalos totales (filas)", "301.434"],
         ["Eventos (E=1)", "425"],
         ["Tasa de default (nivel crédito)", "1,50%"],
         ["Créditos censurados (E=0)", "27.961 (98,50%)"],
         ["Oficinas", "3"],
         ["Rutas", "17"],
         ["Período de observación", "2020-01-01 → 2026-05-15 (~6,4 años)"]],
        "Caracterización general del dataset de supervivencia", table_num=6)
    add_body(doc,
        "La baja tasa de default (1,50%) refleja la dinámica operativa del microcrédito de "
        "pago diario: la institución realiza gestión de cobro intensiva a través del cobrador "
        "de ruta (gestora), reduciendo significativamente la incidencia de abandono total."
    )

    add_heading(doc, "4.6.2  Distribución del Evento de Default", level=3)
    add_figure(doc, BASE / "reports" / "fig01_distribucion_evento.png",
               "Distribución del evento de default: proporción, tasa por oficina y tasa por ruta", 1)
    add_table_data(doc,
        ["Oficina", "Créditos", "Eventos", "Tasa de Default"],
        [["OFI_23 (São Paulo)", "14.031", "126", "0,90%"],
         ["OFI_31 (Soc. Brasil)", "7.333", "53", "0,72%"],
         ["OFI_44 (Cabo Frio)", "7.022", "246", "3,50%"]],
        "Tasa de default por oficina", table_num=7)
    add_body(doc,
        "OFI_44 (Cabo Frio) presenta una tasa de default casi cuatro veces superior a las "
        "demás oficinas (3,50% vs. 0,72–0,90%). Esta heterogeneidad geográfica es "
        "estadísticamente relevante para el modelo de Cox: ofi_id y rta_id actúan como "
        "variables proxy del contexto socioeconómico local, la intensidad de supervisión del "
        "cobrador y la composición del portafolio de clientes."
    )

    add_heading(doc, "4.6.3  Curva de Kaplan-Meier Global", level=3)
    add_figure(doc, BASE / "reports" / "fig02_kaplan_meier_global.png",
               "Curva de Kaplan-Meier global del portafolio con tabla de n en riesgo", 2)
    add_table_data(doc,
        ["Tiempo (días)", "S(t)", "Riesgo Acumulado"],
        [["30",  "1,0000", "0,00%"],
         ["60",  "1,0000", "0,00%"],
         ["90",  "1,0000", "0,00%"],
         ["120", "1,0000", "0,00%"],
         ["180", "0,6815", "31,85%"],
         ["270", "0,6788", "32,12%"],
         ["365", "0,1673", "83,27%"],
         ["540", "0,0908", "90,92%"]],
        "Valores de la curva de Kaplan-Meier global", table_num=8)
    add_body(doc,
        "S(t) = 1,0 hasta el día 120 es consistente con la definición del evento: "
        "dias_sin_pagar ≥ 120 es imposible antes de que el crédito tenga al menos ~120 días "
        "de antigüedad. El salto brusco a S(180) = 0,68 indica que los créditos de larga "
        "permanencia (más allá de su plazo de 20–40 días) concentran el riesgo de default."
    )

    add_heading(doc, "4.6.4  Análisis Estratificado por Oficina (Log-Rank)", level=3)
    add_figure(doc, BASE / "reports" / "fig03_kaplan_meier_oficinas.png",
               "Curvas de Kaplan-Meier por oficina con prueba de log-rank (OFI_23 vs. OFI_44)", 3)
    add_table_data(doc,
        ["Estadístico", "Valor"],
        [["χ² (log-rank)", "0,0817"], ["p-valor", "0,7750"]],
        "Resultado de la prueba de log-rank (OFI_23 vs. OFI_44)", table_num=9)
    add_body(doc,
        "El p-valor de 0,775 indica que no se puede rechazar H₀ de igualdad de curvas al 5%. "
        "Aparentemente contradictorio con la diferencia de tasas brutas (0,90% vs. 3,50%), "
        "se explica por: (1) diferencia en el timing del evento; (2) reducción drástica del "
        "n en riesgo a horizontes largos. Esta limitación del test no paramétrico motiva el "
        "uso del modelo de Cox con control por múltiples covariables."
    )

    add_heading(doc, "4.6.5  Tiempo de Seguimiento y Granularidad Longitudinal", level=3)
    add_figure(doc, BASE / "reports" / "fig04_tiempo_seguimiento.png",
               "Distribución del tiempo de seguimiento (t_stop) e intervalos por crédito", 4)
    add_table_data(doc,
        ["Estadístico", "t_stop (días)", "n_intervalos"],
        [["Mediana", "29 días", "3"],
         ["Media", "36 días", "10,6"],
         ["Máximo", "815 días", "233"]],
        "Estadísticas del tiempo de seguimiento e intervalos por crédito", table_num=10)

    add_heading(doc, "4.6.6  Cronómetro dias_sin_pagar", level=3)
    add_figure(doc, BASE / "reports" / "fig05_dias_sin_pagar.png",
               "Distribución de dias_sin_pagar: global, zoom 0–150 días y máximo por crédito", 5)
    add_table_data(doc,
        ["Estadístico", "Valor"],
        [["Mediana", "0 días"], ["Percentil 95", "0 días"],
         ["Percentil 99", "26 días"], ["Máximo", "400 días"]],
        "Estadísticas del cronómetro dias_sin_pagar", table_num=11)
    add_body(doc,
        "En más del 95% de los intervalos, dias_sin_pagar = 0. La correlación de Pearson "
        "entre dias_sin_pagar y evento es r = 0,680 — la más alta del conjunto de covariables "
        "con la variable objetivo."
    )

    add_heading(doc, "4.6.7  Análisis de Covariables: Default vs. Censurado", level=3)
    add_figure(doc, BASE / "reports" / "fig06_covariables_evento.png",
               "Distribución de covariables por grupo: Default (E=1) versus Censurado (E=0)", 6)
    add_table_data(doc,
        ["Covariable", "r con evento", "Dirección"],
        [["dias_sin_pagar", "+0,6796", "Cronómetro directo del evento"],
         ["saldo_relativo", "−0,0350", "Mayor saldo → menor default"],
         ["dias_con_abono", "−0,0217", "Más días con abono → menor riesgo"],
         ["ratio_atraso", "−0,0176", "Contra-intuitivo; explicado por composición"],
         ["cuotas_atrasadas", "−0,0166", "Ídem"],
         ["pago_promedio_diario", "−0,0152", "Más pagos → menor riesgo"],
         ["intensidad_recuperacion", "+0,0071", "Efecto mixto"]],
        "Correlaciones de las covariables con el evento", table_num=12)

    add_heading(doc, "4.6.8  Perfil Económico del Portafolio", level=3)
    add_figure(doc, BASE / "reports" / "fig07_perfil_credito.png",
               "Perfil económico del portafolio: distribución del plazo, monto y boxplot por evento", 7)
    add_table_data(doc,
        ["Estadístico", "Valor"],
        [["Mediana", "R$ 1.200"], ["Media", "R$ 1.491"],
         ["P10", "R$ 540"], ["P90", "R$ 3.000"]],
        "Monto del crédito por grupo de evento", table_num=13)
    add_body(doc,
        "Los créditos son de bajo monto (mediana R$ 1.200). La distribución del plazo está "
        "concentrada en: 20 días (62,7%), 24 días (29,3%) y 30 días (5,2%). El 92% del "
        "portafolio tiene plazo de 20 o 24 días."
    )

    add_heading(doc, "4.6.9  Estructura de Correlaciones", level=3)
    add_figure(doc, BASE / "reports" / "fig08_correlaciones.png",
               "Mapa de calor de correlaciones de las covariables del modelo (triángulo inferior)", 8)
    add_body(doc,
        "La correlación ratio_atraso ↔ cuotas_atrasadas (r ≈ +0,90) indica redundancia — "
        "en el modelo de Cox final deberá incluirse solo una de las dos. La ausencia de "
        "correlaciones altas (> 0,7) entre las demás covariables indica que el conjunto "
        "seleccionado no presenta problemas graves de multicolinealidad."
    )

    add_heading(doc, "4.6.10  Análisis de Trayectorias Individuales", level=3)
    add_figure(doc, BASE / "reports" / "fig09_trayectorias.png",
               "Trayectorias individuales: 5 créditos en default versus 5 censurados", 9)
    add_body(doc,
        "En los créditos en default, dias_sin_pagar crece monotónicamente hasta cruzar el "
        "umbral de 120 días exactamente en el intervalo marcado como evento. En los créditos "
        "censurados, el cronómetro permanece en cero o cerca de cero con reinicializaciones "
        "inmediatas al ocurrir un abono, confirmando que el forward-fill captura correctamente "
        "la mora transitoria."
    )

    # 4.7
    add_heading(doc, "4.7  Síntesis y Validación del Dataset", level=2)
    add_table_data(doc,
        ["Validación", "Resultado"],
        [["t_stop > t_start en todos los intervalos", "✓ Verificado"],
         ["Cadena perfecta t_start[k] = t_stop[k−1]", "✓ Verificado (via shift)"],
         ["Evento E=1 solo en el último intervalo", "✓ Aplicado por regla de censura"],
         ["Sin valores nulos en columnas clave", "✓ Verificado"],
         ["Número de eventos > 100", "✓ 425 eventos"],
         ["Covariables numéricas en rango esperado", "✓ Clip aplicado a todas las razones"]],
        "Validación del formato Counting Process", table_num=14)
    add_body(doc,
        "La definición dias_sin_pagar ≥ 120 demostró ser operacionalmente válida y "
        "estadísticamente estable: tasa de default 1,50%, coherente con referencias de "
        "microcrédito de pago diario en economías emergentes (Schreiner, 2002; "
        "Banerjee y Duflo, 2007). El dataset queda preparado para el Modelo de Cox."
    )


def build_secao_5(doc):
    add_heading(doc, "5  MODELADO MATEMÁTICO Y COMPUTACIONAL (EL DESAFÍO DE LA CENSURA)", level=1)
    add_heading(doc, "5.1  Baseline Clásico (Modelo de Cox)", level=2)
    add_body(doc,
        "La fase inicial aplicará el Modelo de Riesgos Proporcionales de Cox para establecer "
        "el marco de interpretabilidad y cuantificar el impacto de las covariables estáticas "
        "y dinámicas (Hazard Ratios). Los Residuos de Schoenfeld servirán como diagnóstico. "
        "[RESULTADO PENDIENTE — Etapa de modelado en curso]"
    )
    add_heading(doc, "5.2  El Desafío de la Censura a la Derecha en Arquitecturas Neurales", level=2)
    add_body(doc,
        "Las arquitecturas de Deep Learning tradicionales fallan al ignorar la información "
        "contenida en los registros censurados. Descartarlos o clasificarlos como ceros "
        "introduce un sesgo severo y subestima el tiempo real de supervivencia."
    )
    add_heading(doc, "5.3  Enfoque Estado del Arte (Deep Learning bajo Censura)", level=2)
    add_body(doc,
        "La investigación implementará redes neuronales recurrentes (LSTM o GRU) integradas al "
        "Análisis de Supervivencia (DeepSurv/RNN-Survival), sustituyendo las funciones de "
        "pérdida convencionales por la optimización directa de la Verosimilitud Parcial Negativa "
        "(Negative Partial Log-Likelihood). [IMPLEMENTACIÓN PENDIENTE — Sprint 3]"
    )


def build_secao_6(doc):
    add_heading(doc, "6  VALIDACIÓN", level=1)
    add_body(doc,
        "Las pruebas de rendimiento compararán el modelo de supervivencia clásico con las "
        "técnicas de Deep Learning utilizando: C-index de Harrell (concordance index), "
        "Brier Score temporal y Prueba de Log-Rank. [RESULTADOS PENDIENTES — Sprint 4]"
    )


def build_secao_7(doc):
    add_heading(doc, "7  CRONOGRAMA INTEGRADO DE INVESTIGACIÓN", level=1)
    sprints = [
        ("Sprint 1 (Ene–Mar 2026) — ETL/Pipeline [COMPLETADO]:",
         "Extractor Selenium, extracción de 3.962 archivos, Matriz Maestra (344.869 × 2.358), "
         "optimización de memoria (−49% RAM)."),
        ("Sprint 2 (Mar–May 2026) — Feature Engineering + EDA [COMPLETADO]:",
         "Cronómetro dias_sin_pagar, dataset de supervivencia (28.386 créditos, 301.434 "
         "intervalos, 425 eventos), EDA completo con 9 figuras."),
        ("Sprint 3 (Jun–Ago 2026) — Modelado Cox + DeepSurv [PENDIENTE]:",
         "Ajuste del Modelo de Cox con covariables tiempo-variantes, diagnóstico de Schoenfeld, "
         "DeepSurv/RNN-Survival con Negative Partial Log-Likelihood."),
        ("Sprint 4 (Sep–Nov 2026) — Evaluación + Redacción final [PENDIENTE]:",
         "C-index de Harrell, Brier Score, comparativo con Credit Scoring binario, "
         "redacción de Resultados, Discusión y Conclusión."),
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
        "LOUZADA NETO, F. Gestión de Proyectos de Ciencia de Datos e Inteligencia Artificial. "
        "Material didáctico — MBA en Ciencia de Datos. ICMC/USP, São Carlos, 2026.",
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


# ── MAIN ─────────────────────────────────────────────────────────────────────

def build_doc():
    doc = Document()
    configure_doc(doc)

    build_capa(doc)
    build_resumen(doc)
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
    print(f"[ES] TCC V21 en Español generado: {OUTPUT}")
    print(f"     Tamaño: {OUTPUT.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    build_doc()
