"""
gerar_tcc_v27.py — Gerador do TCC V27 (Português). [EM CONSTRUÇÃO]

Novidades vs. V26:
  - Resultados do Sprint 4 (02/11/2026): blocos de 7 dias (10 como
    sensibilidade), calendário de dias de cobrança (sem domingos nem
    feriados), histórico do cliente nos créditos anteriores, exclusão dos
    vales de trabalhadores e correção do leakage da parcela de 1 real
    (renegociação no mesmo crédito).
  - Modelo principal: landmark nos dias 14 e 21 com Fine-Gray (incidência
    acumulada de default), regressão logística como comparação, validação
    cruzada por cliente (src/cox_v2.py, reports/modelagem_v2/).
  - Pendente nesta versão: reescrever §4/§5 com o método e os resultados,
    frase do resultado no Resumo e no Abstract, figuras novas.

Histórico V26 (vs. V25):
  - Capa, dedicatória, resumo/abstract, sumário e listas automáticas,
    siglas, numeração de páginas e introdução reescritos.
  - §8 Cronograma reestruturado: meta de conclusão em dezembro de 2026
    (entrega oficial em fevereiro de 2027).

Histórico V25 (vs. V24):
  - Nova §5.8 "Auditoria de Integridade do Target": documenta um bug real
    encontrado e corrigido no pipeline (dias_sin_pagar seguia contando após
    o crédito já ter sido pago integralmente, gerando falsos defaults).
    Corrigido em feature_engineering.py com detecção de fechamento por
    pagamento total. Eventos: 425 → 273 (limpos).
  - §5.6 EDA totalmente recalculada com os números corrigidos (censura,
    Kaplan-Meier, Log-Rank OFI_23 vs OFI_44 — agora p=0,0040, antes
    p=0,775 — e correlações).
  - Nova §5.9 "Riscos Competitivos": pivô metodológico de evento binário
    para evento_tipo (0=censura, 1=default, 2=cura/pagamento total),
    respondendo à crítica do orientador sobre a censura de 98%+. Nova
    Figura CIF (Função de Incidência Acumulada, Aalen-Johansen).
  - §6 Modelagem atualizada com resultados reais do baseline Cox
    cause-specific (Default C-index=0,80; Cura C-index=0,76),
    substituindo os placeholders "[RESULTADO PENDENTE — Sprint 3]".
  - Novas referências: Fine e Gray (1999), Cox (1972).

Output: documentotcc/Projeto_Pesquisa_TCC_V27_Completo.docx
"""

from pathlib import Path
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING, WD_TAB_ALIGNMENT, WD_TAB_LEADER
from docx.enum.section import WD_SECTION
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
import re, subprocess, sys, io, tempfile

BASE   = Path(__file__).parent.parent
OUTPUT = BASE / "documentotcc" / "Projeto_Pesquisa_TCC_V27_Completo.docx"
ASSETS = BASE / "documentotcc" / "assets"
REPORTS = BASE / "reports"

# Registro do que entra no sumário e nas listas. É preenchido enquanto o
# documento é montado (títulos a partir da Introdução, figuras e tabelas), e
# as páginas são lidas do PDF gerado. Assim sumário e listas nunca ficam
# desatualizados em relação ao texto.
REGISTRO = {"ativo": False, "titulos": [], "figuras": [], "tabelas": [], "texto_corpo": ""}

# Siglas conhecidas. A Lista de Abreviaturas e Siglas mostra só as que
# aparecem de fato no corpo do texto (Introdução em diante). Trechos entre
# asteriscos saem em itálico (nomes em língua estrangeira).
SIGLAS = {
    "ABNT": "Associação Brasileira de Normas Técnicas",
    "API": "Interface de Programação de Aplicações (*Application Programming Interface*)",
    "CIF": "Função de Incidência Acumulada (*Cumulative Incidence Function*)",
    "CMN": "Conselho Monetário Nacional",
    "CNPJ": "Cadastro Nacional da Pessoa Jurídica",
    "CRISP-DS": "*Cross Industry Standard Process for Data Science*",
    "CSV": "Valores separados por vírgula (*Comma-Separated Values*)",
    "DDD": "Discagem Direta a Distância",
    "DOM": "*Document Object Model*",
    "EDA": "Análise Exploratória de Dados (*Exploratory Data Analysis*)",
    "ETL": "Extração, Transformação e Carga (*Extract, Transform, Load*)",
    "GRU": "*Gated Recurrent Unit*",
    "IBGE": "Instituto Brasileiro de Geografia e Estatística",
    "ICMC": "Instituto de Ciências Matemáticas e de Computação",
    "IFRS": "*International Financial Reporting Standards*",
    "IPCW": "Ponderação pela probabilidade inversa de censura (*Inverse Probability of Censoring Weighting*)",
    "JSON": "*JavaScript Object Notation*",
    "LGPD": "Lei Geral de Proteção de Dados Pessoais",
    "LSTM": "*Long Short-Term Memory*",
    "MBA": "*Master of Business Administration*",
    "MEI": "Microempreendedor Individual",
    "MLOps": "*Machine Learning Operations*",
    "RAM": "Memória de acesso aleatório (*Random Access Memory*)",
    "REST": "*Representational State Transfer*",
    "RPA": "Automação Robótica de Processos (*Robotic Process Automation*)",
    "RSF": "*Random Survival Forest*",
    "Sebrae": "Serviço Brasileiro de Apoio às Micro e Pequenas Empresas",
    "SHAP": "*SHapley Additive exPlanations*",
    "TCC": "Trabalho de Conclusão de Curso",
    "USP": "Universidade de São Paulo",
}
PAGINAS = {}  # chave ("titulo", i) / ("figura", n) / ("tabela", n) -> página exibida

# Numeração automática: cada tabela e figura recebe o número pela ordem em que
# aparece; o argumento table_num/fig_num passa a ser só uma chave. No texto,
# "{tab:chave}" e "{fig:chave}" viram o número (o da passada anterior).
CONTADOR = {"tab": 0, "fig": 0}
NUMEROS = {}
FONTE_PADRAO = "Elaborada pelo autor (2026)."


def _refs(texto):
    return re.sub(r"\{(tab|fig):([\w-]+)\}",
                  lambda m: str(NUMEROS.get((m.group(1), m.group(2)), "?")), texto)


def _numero(tipo, chave):
    CONTADOR[tipo] += 1
    NUMEROS[(tipo, str(chave))] = CONTADOR[tipo]
    return CONTADOR[tipo]


def _add_fonte(doc, fonte, centro=False):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER if centro else WD_ALIGN_PARAGRAPH.LEFT
    _set_spacing(p, multiple=1.0)
    p.paragraph_format.first_line_indent = Cm(0)
    p.paragraph_format.space_before = Pt(2)
    _set_font(p.add_run(f"Fonte: {fonte}"), size=10)


# ── Helpers de formatação USP ────────────────────────────────────────────────

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
    run = p.add_run(_refs(text))
    _set_font(run)
    return p


def add_body_italico(doc, text, indent_first=True):
    """Como add_body, mas o trecho entre asteriscos sai em itálico (termos em
    língua estrangeira, NBR 14724). Ex.: "modelos de *credit scoring*"."""
    p = doc.add_paragraph()
    _set_spacing(p)
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.first_line_indent = Cm(1.25) if indent_first else Cm(0)
    for i, trecho in enumerate(_refs(text).split("*")):
        if trecho:
            _set_font(p.add_run(trecho), italic=i % 2 == 1)
    return p


def add_heading(doc, text, level=1, maiusculas=True):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    _set_spacing(p, multiple=1.0)
    p.paragraph_format.space_before      = Pt(12)
    p.paragraph_format.space_after       = Pt(6)
    p.paragraph_format.first_line_indent = Cm(0)
    p.paragraph_format.keep_with_next    = True
    sizes = {1: 16, 2: 14, 3: 12, 4: 12}
    label = text.upper() if level == 1 and maiusculas else text
    if REGISTRO["ativo"]:
        REGISTRO["titulos"].append((level, label))
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


def add_table_data(doc, headers, rows, caption_text, table_num, fonte=FONTE_PADRAO, larguras=None):
    """larguras: lista com a largura de cada coluna em cm (padrão: colunas iguais)."""
    table_num = _numero("tab", table_num)
    REGISTRO["tabelas"].append((table_num, caption_text))
    cap = doc.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.LEFT
    _set_spacing(cap, multiple=1.0)
    cap.paragraph_format.first_line_indent = Cm(0)
    cap.paragraph_format.keep_with_next    = True
    run = cap.add_run(f"Tabela {table_num} – {caption_text}")
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
            cells[c_idx].text = _refs(str(val))
            for r in cells[c_idx].paragraphs[0].runs:
                r.font.name = "Arial"; r.font.size = Pt(10)
    if larguras:
        table.autofit = False
        for col, w in zip(table.columns, larguras):
            col.width = Cm(w)
        for row in table.rows:
            for cell, w in zip(row.cells, larguras):
                cell.width = Cm(w)
    _add_fonte(doc, fonte)
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
    """Bloco de código em Courier New com indentação."""
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


def add_figure(doc, img_path, caption, fig_num, fonte=FONTE_PADRAO, largura=14):
    """NBR 14724: identificação acima da figura e fonte abaixo."""
    fig_num = _numero("fig", fig_num)
    REGISTRO["figuras"].append((fig_num, caption))
    path = Path(img_path)
    if not path.exists():
        p = doc.add_paragraph()
        _set_spacing(p, multiple=1.0)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(f"[FIGURA {fig_num}, arquivo não encontrado: {path.name}]")
        _set_font(run, size=10, italic=True)
        return
    cap = doc.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _set_spacing(cap, multiple=1.0)
    cap.paragraph_format.first_line_indent = Cm(0)
    cap.paragraph_format.space_before      = Pt(6)
    cap.paragraph_format.space_after       = Pt(2)
    cap.paragraph_format.keep_with_next    = True
    r = cap.add_run(f"Figura {fig_num} – {caption}")
    _set_font(r, size=10, italic=True)
    p_img = doc.add_paragraph()
    p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_img.paragraph_format.first_line_indent = Cm(0)
    p_img.paragraph_format.keep_with_next    = True
    run = p_img.add_run()
    try:
        run.add_picture(str(path), width=Cm(largura))
    except Exception:
        run.add_picture(str(path))
    _add_fonte(doc, fonte, centro=True)


def add_labeled(doc, label, text):
    """Parágrafo com label em negrito seguido de texto normal."""
    p = doc.add_paragraph()
    _set_spacing(p)
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.first_line_indent = Cm(1.25)
    r1 = p.add_run(label + " ")
    _set_font(r1, bold=True)
    r2 = p.add_run(_refs(text))
    _set_font(r2)


def page_break(doc):
    doc.add_page_break()


def _linha_com_pagina(doc, texto, pagina, recuo=0.0, negrito=False):
    """Linha de sumário/lista: texto, pontilhado e número da página à direita."""
    p = doc.add_paragraph()
    _set_spacing(p, multiple=1.0)
    pf = p.paragraph_format
    pf.first_line_indent = Cm(0)
    pf.left_indent = Cm(recuo)
    pf.tab_stops.add_tab_stop(Cm(16), WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.DOTS)
    _set_font(p.add_run(f"{texto}\t{pagina}"), size=12, bold=negrito)
    return p


def _pagina(chave):
    return PAGINAS.get(chave, "000")


def _numerar_paginas(section):
    """Cabeçalho com o número da página no canto superior direito (NBR 14724)."""
    # A seção nova herda o "começar em 1" da folha de rosto; aqui a contagem
    # deve continuar, então essa instrução é removida.
    for pg in section._sectPr.findall(qn("w:pgNumType")):
        section._sectPr.remove(pg)
    section.header.is_linked_to_previous = False
    p = section.header.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    run = p.add_run()
    _set_font(run, size=10)
    for tipo, texto in (("begin", None), (None, "PAGE"), ("end", None)):
        if tipo:
            el = OxmlElement("w:fldChar")
            el.set(qn("w:fldCharType"), tipo)
        else:
            el = OxmlElement("w:instrText")
            el.set(qn("xml:space"), "preserve")
            el.text = texto
        run._r.append(el)


def configure_doc(doc):
    for section in doc.sections:
        section.page_width    = Cm(21)
        section.page_height   = Cm(29.7)
        section.left_margin   = Cm(3)
        section.right_margin  = Cm(2)
        section.top_margin    = Cm(3)
        section.bottom_margin = Cm(2)
    style = doc.styles["Normal"]
    style.font.name = "Arial"
    style.font.size = Pt(12)


# ── PRÉ-TEXTUAIS ─────────────────────────────────────────────────────────────

TITULO_TRABALHO = (
    "Modelagem de Risco de Crédito Dinâmico para Microempreendedores: "
    "Uma Abordagem via Análise de Sobrevivência em Fluxos de Alta Frequência sob Censura"
)


def _fit_wrapped_text(draw, text, box, font_path, max_size, min_size=14,
                       line_spacing=1.15, color=(22, 62, 94)):
    """Escreve texto centralizado (h. e v.) dentro de uma caixa, quebrando linhas e
    reduzindo o tamanho da fonte até caber. Usado para montar a imagem da capa."""
    from PIL import ImageFont
    x0, y0, x1, y1 = box
    box_w, box_h = x1 - x0, y1 - y0
    size = max_size
    lines, line_h, font = [], 0, None
    while size >= min_size:
        font = ImageFont.truetype(font_path, size)
        words = text.split()
        lines, cur = [], ""
        for w in words:
            trial = (cur + " " + w).strip()
            bbox = draw.textbbox((0, 0), trial, font=font)
            if bbox[2] - bbox[0] <= box_w or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
        line_h = draw.textbbox((0, 0), "Ag", font=font)[3] * line_spacing
        if line_h * len(lines) <= box_h:
            break
        size -= 2
    total_h = line_h * len(lines)
    y = y0 + (box_h - total_h) / 2
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        x = x0 + (box_w - (bbox[2] - bbox[0])) / 2
        draw.text((x, y), line, font=font, fill=color)
        y += line_h


def _limpar_texto_icmc(im, scale):
    """Substitui a região do texto 'ICMC / USP / SÃO CARLOS' (baixa resolução
    nativa na arte oficial) por uma versão vetorizada a partir dos contornos
    do texto original, com bordas suavizadas e anti-aliasing — nítida mesmo em
    zoom. O logo dos anéis entrelaçados (dentro da mesma região) é excluído
    dessa limpeza: sua topologia entrelaçada quebra ao suavizar contornos, e
    fica melhor preservado apenas com o unsharp mask já aplicado ao fundo."""
    import numpy as np
    import cv2
    from PIL import Image

    CROP = (600, 1020, 840, 1190)  # região no PNG original (840x1190)
    RINGS_BBOX = (140, 70, 240, 145)  # relativo ao CROP, exclui os anéis
    VSCALE = 8  # escala interna para suavizar; depois reamostrado para `scale`

    orig = Image.open(ASSETS / "capa_fundo_usp_icmc.png").convert("RGB")
    crop_arr = np.array(orig)[CROP[1]:CROP[3], CROP[0]:CROP[2]]
    gray = cv2.cvtColor(crop_arr, cv2.COLOR_RGB2GRAY)
    _, mask = cv2.threshold(gray, 140, 255, cv2.THRESH_BINARY)
    contours, hierarchy = cv2.findContours(mask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)

    def smooth_contour(cnt, win=5):
        pts = cnt[:, 0, :].astype(np.float32)
        n = len(pts)
        if n < win * 2:
            return pts
        kernel = np.ones(win) / win
        padded = np.vstack([pts[-win:], pts, pts[:win]])
        sx = np.convolve(padded[:, 0], kernel, mode='same')[win:win + n]
        sy = np.convolve(padded[:, 1], kernel, mode='same')[win:win + n]
        return np.stack([sx, sy], axis=1)

    def overlaps(b1, b2):
        return not (b1[2] < b2[0] or b1[0] > b2[2] or b1[3] < b2[1] or b1[1] > b2[3])

    h, w = crop_arr.shape[:2]
    canvas = np.zeros((h * VSCALE, w * VSCALE), dtype=np.uint8)
    for i, cnt in enumerate(contours):
        x, y, cw, ch = cv2.boundingRect(cnt)
        if overlaps((x, y, x + cw, y + ch), RINGS_BBOX) or len(cnt) < 3:
            continue
        sm_scaled = (smooth_contour(cnt) * VSCALE).astype(np.int32).reshape(-1, 1, 2)
        color = 255 if hierarchy[0][i][3] == -1 else 0
        cv2.drawContours(canvas, [sm_scaled], -1, color, thickness=cv2.FILLED,
                          lineType=cv2.LINE_AA)

    mask_img = Image.fromarray(canvas).resize((w * scale, h * scale), Image.LANCZOS)
    white = Image.new("RGB", mask_img.size, (255, 255, 255))
    dest = (CROP[0] * scale, CROP[1] * scale)
    im.paste(white, dest, mask_img)


def _reescrever_texto_lateral(im, scale):
    """Substitui o texto vertical da faixa cinza lateral ('UNIVERSIDADE DE SÃO
    PAULO / Instituto de Ciências Matemáticas e de Computação'), que na arte
    oficial é um bitmap de baixa resolução, por texto renderizado de novo com
    fonte real (Liberation Sans, métrica de Arial) na resolução final. Apaga a
    região com a cor lisa da faixa e escreve cada linha girada 90° (leitura de
    baixo para cima), no mesmo lugar e comprimento do original."""
    from PIL import Image, ImageDraw, ImageFont

    COR_FAIXA = (140, 140, 140)
    COR_TEXTO = (22, 62, 94)
    APAGAR = (110, 45, 215, 745)  # região do texto, no PNG original (840x1190)
    # (texto, fonte, x_ini, x_fim, y_fim do texto, comprimento) medidos no original
    LINHAS = [
        ("UNIVERSIDADE DE SÃO PAULO",
         "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", 124, 160, 59, 578),
        ("Instituto de Ciências Matemáticas e de Computação",
         "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", 174, 201, 59, 663),
    ]

    draw = ImageDraw.Draw(im)
    draw.rectangle([c * scale for c in APAGAR], fill=COR_FAIXA)

    for texto, fonte, x0, x1, y_fim, comprimento in LINHAS:
        # Ajusta o tamanho da fonte para o texto ocupar o mesmo comprimento.
        alvo = comprimento * scale
        tamanho = 10
        while True:
            f = ImageFont.truetype(fonte, tamanho + 1)
            if draw.textlength(texto, font=f) > alvo:
                break
            tamanho += 1
        font = ImageFont.truetype(fonte, tamanho)
        l, t, r, b = draw.textbbox((0, 0), texto, font=font)
        faixa = Image.new("L", (r - l + 4, b - t + 4), 0)
        ImageDraw.Draw(faixa).text((2 - l, 2 - t), texto, font=font, fill=255)
        faixa = faixa.rotate(90, expand=True)  # leitura de baixo para cima
        cx = (x0 + x1) / 2 * scale
        destino = (int(cx - faixa.width / 2), int(y_fim * scale))
        im.paste(Image.new("RGB", faixa.size, COR_TEXTO), destino, faixa)


def _gerar_imagem_capa():
    """Monta a imagem completa da capa: fundo oficial USP/ICMC (extraído do
    Modelo de documento USP) + título e autor sobrepostos nas caixas cinzas
    já existentes na arte. Retorna um buffer PNG em memória."""
    from PIL import Image, ImageDraw, ImageFilter

    SCALE = 3
    BOLD = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
    REG = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"

    im = Image.open(ASSETS / "capa_fundo_usp_icmc.png").convert("RGB")
    im = im.resize((im.width * SCALE, im.height * SCALE), Image.LANCZOS)
    # A arte oficial (logo/texto do fundo) é de baixa resolução nativa; o
    # unsharp mask não recupera detalhe real, mas melhora a nitidez percebida.
    im = im.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=2))
    _limpar_texto_icmc(im, SCALE)
    _reescrever_texto_lateral(im, SCALE)
    draw = ImageDraw.Draw(im)

    title_box = (250 * SCALE, 222 * SCALE, 838 * SCALE, 463 * SCALE)
    _fit_wrapped_text(draw, TITULO_TRABALHO, title_box, BOLD, max_size=52)

    author_box = (305 * SCALE, 480 * SCALE, 839 * SCALE, 535 * SCALE)
    subtitle_box = (305 * SCALE, 535 * SCALE, 839 * SCALE, 585 * SCALE)
    _fit_wrapped_text(draw, "Juan Fernando Graciano Pinzón", author_box, BOLD, max_size=36)
    _fit_wrapped_text(draw, "Monografia, MBA em Ciências de Dados (CeMEAI)",
                       subtitle_box, REG, max_size=26)

    buf = io.BytesIO()
    im.save(buf, format="PNG")
    buf.seek(0)
    return buf


def _anchor_picture_full_page(paragraph, run, page_w_cm, page_h_cm):
    """Converte a última imagem inline inserida no run em uma imagem ancorada
    (flutuante) posicionada em (0,0) relativo à página, com extensão exata de
    página. Evita depender do alinhamento/indentação do parágrafo (que se
    mostrou inconsistente em alguns renderizadores para imagens inline em
    seções de margem zero)."""
    from docx.oxml.ns import qn

    drawing = run._element.find(qn('w:drawing'))
    inline = drawing.find(qn('wp:inline'))
    graphic = inline.find(qn('a:graphic'))
    docPr = inline.find(qn('wp:docPr'))
    cNvGraphicFramePr = inline.find(qn('wp:cNvGraphicFramePr'))

    cx = str(Cm(page_w_cm).emu)
    cy = str(Cm(page_h_cm).emu)

    anchor = drawing.makeelement(qn('wp:anchor'), {
        'behindDoc': '0', 'distT': '0', 'distB': '0', 'distL': '0', 'distR': '0',
        'simplePos': '0', 'locked': '0', 'layoutInCell': '1', 'allowOverlap': '1',
        'relativeHeight': '1',
    })
    simplePos = anchor.makeelement(qn('wp:simplePos'), {'x': '0', 'y': '0'})
    positionH = anchor.makeelement(qn('wp:positionH'), {'relativeFrom': 'page'})
    posOffsetH = anchor.makeelement(qn('wp:posOffset'), {})
    posOffsetH.text = '0'
    positionH.append(posOffsetH)
    positionV = anchor.makeelement(qn('wp:positionV'), {'relativeFrom': 'page'})
    posOffsetV = anchor.makeelement(qn('wp:posOffset'), {})
    posOffsetV.text = '0'
    positionV.append(posOffsetV)
    extent = anchor.makeelement(qn('wp:extent'), {'cx': cx, 'cy': cy})
    effectExtent = anchor.makeelement(qn('wp:effectExtent'),
                                       {'l': '0', 't': '0', 'r': '0', 'b': '0'})
    wrapNone = anchor.makeelement(qn('wp:wrapNone'), {})

    anchor.append(simplePos)
    anchor.append(positionH)
    anchor.append(positionV)
    anchor.append(extent)
    anchor.append(effectExtent)
    anchor.append(wrapNone)
    anchor.append(docPr)
    anchor.append(cNvGraphicFramePr)
    anchor.append(graphic)

    drawing.remove(inline)
    drawing.append(anchor)


def build_capa(doc):
    """CAPA (elemento obrigatório, NBR 14724): imagem de fundo oficial USP/ICMC
    com título e autor sobrepostos, em seção própria com margens zero (full
    bleed). Uma nova seção é aberta em seguida com as margens normais (3/2 cm)
    para o restante do documento."""
    section = doc.sections[0]
    section.left_margin = section.right_margin = Cm(0)
    section.top_margin = section.bottom_margin = Cm(0)

    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(0)
    run = p.add_run()
    run.add_picture(_gerar_imagem_capa(), width=Cm(21), height=Cm(29.7))
    _anchor_picture_full_page(p, run, 21, 29.7)

    new_section = doc.add_section(WD_SECTION.NEW_PAGE)
    # A contagem de páginas começa na folha de rosto (a capa não conta).
    pg = OxmlElement("w:pgNumType")
    pg.set(qn("w:start"), "1")
    new_section._sectPr.append(pg)
    new_section.page_width = Cm(21)
    new_section.page_height = Cm(29.7)
    new_section.left_margin = Cm(3)
    new_section.right_margin = Cm(2)
    new_section.top_margin = Cm(3)
    new_section.bottom_margin = Cm(2)


def build_folha_rosto(doc):
    """FOLHA DE ROSTO (elemento obrigatório, NBR 14724): repete autor e título e
    acrescenta a natureza do trabalho, área de concentração e orientador."""
    add_centered(doc, "Juan Fernando Graciano Pinzón", size=13, bold=True, spacing=1.0)
    for _ in range(3): add_centered(doc, "", size=12, spacing=1.0)
    add_centered(doc,
        "Modelagem de Risco de Crédito Dinâmico para Microempreendedores: "
        "Uma Abordagem via Análise de Sobrevivência em Fluxos de Alta Frequência sob Censura",
        size=16, bold=True, spacing=1.5)
    for _ in range(4): add_centered(doc, "", size=12, spacing=1.0)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.left_indent = Cm(8)
    _set_spacing(p, multiple=1.0)
    run = p.add_run(
        "Monografia apresentada ao Centro de Ciências Matemáticas "
        "Aplicadas à Indústria do Instituto de Ciências Matemáticas e de Computação, "
        "Universidade de São Paulo - ICMC/USP, como parte dos requisitos para obtenção "
        "do título de Especialista em Ciências de Dados.")
    _set_font(run, size=12)

    doc.add_paragraph()
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.left_indent = Cm(8)
    _set_spacing(p, multiple=1.0)
    run = p.add_run("Área de concentração: Ciências de Dados")
    _set_font(run, size=12)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.left_indent = Cm(8)
    _set_spacing(p, multiple=1.0)
    # espaços não separáveis: o nome do orientador não se divide entre linhas
    run = p.add_run("Orientador: " + "Prof. Dr. Vicente Garibay Cancho".replace(" ", "\u00a0"))
    _set_font(run, size=12)

    for _ in range(6): add_centered(doc, "", size=12, spacing=1.0)
    add_centered(doc, "USP – São Carlos", size=12, spacing=1.0)
    add_centered(doc, "2026", size=12, spacing=1.0)
    page_break(doc)


def build_ficha_catalografica(doc):
    """Página reservada à Ficha Catalográfica (elemento obrigatório, verso da
    Folha de Rosto). Gerada pelo sistema oficial da Biblioteca do ICMC/USP
    (https://www.icmc.usp.br/institucional/estrutura-administrativa/biblioteca/servicos/ficha)
    e inserida aqui como imagem — não pode ser redigida pelo autor."""
    img_path = ASSETS / "ficha_catalografica-1.png"
    if not img_path.exists():
        add_centered(doc, "", size=12, spacing=1.0)
        for _ in range(8): add_centered(doc, "", size=12, spacing=1.0)
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        _set_spacing(p, multiple=1.5)
        run = p.add_run(
            "[Esta página deve conter a ficha catalográfica, gerada pelo sistema oficial da "
            "Biblioteca do ICMC/USP e impressa no verso da folha de rosto: "
            "https://www.icmc.usp.br/institucional/estrutura-administrativa/biblioteca/servicos/ficha]")
        _set_font(run, size=10, italic=True)
        page_break(doc)
        return

    p_img = doc.add_paragraph()
    p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_img.paragraph_format.first_line_indent = Cm(0)
    run = p_img.add_run()
    run.add_picture(str(img_path), width=Cm(16))
    page_break(doc)


def build_dedicatoria(doc):
    """DEDICATÓRIA (elemento opcional, NBR 14724): sem título, na parte inferior
    da página, com recuo de 8 cm à esquerda."""
    textos = [
        "À minha mãe, pelo exemplo de força e amor que me acompanha em cada etapa da vida.",
        "Aos meus filhos, Juan José Graciano e Matías Graciano, razão maior de cada "
        "esforço e de cada conquista.",
    ]
    espaco = doc.add_paragraph()
    espaco.paragraph_format.space_after = Cm(17)
    for i, texto in enumerate(textos):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT   # justificado abria espaços na coluna estreita
        _set_spacing(p, multiple=1.5)
        p.paragraph_format.first_line_indent = Cm(0)
        p.paragraph_format.left_indent = Cm(8)
        p.paragraph_format.space_before = Cm(0) if i == 0 else Cm(0.6)
        _set_font(p.add_run(texto), size=12, italic=True)
    page_break(doc)


def build_resumo(doc):
    add_heading(doc, "RESUMO", level=1)
    add_body(doc,
        "GRACIANO PINZÓN, J. F. Modelagem de Risco de Crédito Dinâmico para "
        "Microempreendedores: Uma Abordagem via Análise de Sobrevivência em Fluxos de Alta "
        f"Frequência sob Censura. 2026. {_pagina(('total', 0))} f. Monografia (MBA em Ciências de "
        "Dados) – Centro de Ciências Matemáticas Aplicadas à Indústria, Instituto de Ciências "
        "Matemáticas e de Computação, Universidade de São Paulo, São Carlos, 2026.",
        indent_first=False)
    doc.add_paragraph()
    add_body_italico(doc,
        "A concessão de crédito para pequenos comerciantes no Brasil é dificultada pela falta "
        "de informação sobre a sua real capacidade de pagamento, já que os modelos tradicionais "
        "se baseiam em dados fixos e respondem apenas se o cliente vai ou não deixar de pagar. "
        "Este trabalho propõe um modelo de risco que acompanha cada crédito ao longo do tempo, "
        "usando o histórico diário de pagamentos de uma instituição de microcrédito voltada a "
        "comerciantes formais e informais. Como o sistema da instituição não oferece acesso "
        "direto aos dados, foi desenvolvido um processo automatizado de extração (*web scraping*) "
        "que reuniu seis anos de "
        "pagamentos, de 2020 a 2026, de três escritórios. Os arquivos foram unidos em uma única "
        "base e revisados com cuidado, e o abandono do crédito foi definido como 120 dias "
        "seguidos sem nenhum pagamento. A base final tem 28.149 créditos, dos quais 200, ou "
        "0,71%, terminaram em abandono. Como um crédito pode terminar de duas formas, pelo "
        "abandono ou pela quitação, o risco é estudado com análise de sobrevivência para riscos "
        "competitivos, pelo modelo de Fine e Gray, comparado com a regressão logística e, nas "
        "próximas etapas, com modelos de aprendizado de máquina. Com as informações disponíveis "
        "no 21º dia do crédito, o modelo coloca 81% dos futuros abandonos entre os 10% de "
        "clientes de maior risco, cerca de quatro meses antes de o abandono se confirmar. O "
        "histórico do cliente também informa: usando apenas a informação disponível no dia do "
        "desembolso, o modelo reúne "
        "36% dos futuros abandonos entre os 10% de maior risco, mais de três vezes o esperado "
        "ao acaso. Os resultados indicam que o histórico pode apoiar a decisão de conceder o "
        "crédito e que o acompanhamento semanal dos pagamentos permite identificar cedo os "
        "clientes em dificuldade, antes que o atraso se transforme em perda.",
        indent_first=False)
    p = doc.add_paragraph()
    _set_spacing(p)
    run = p.add_run(
        "Palavras-chave: análise de sobrevivência; riscos competitivos; risco de crédito; "
        "microcrédito; pequenos negócios; modelo de Fine e Gray.")
    _set_font(run)
    # sem quebra explícita: o ABSTRACT começa em página nova pelo próprio título
    # (evita uma página em branco quando o resumo ocupa a página inteira)


def build_abstract(doc):
    add_heading(doc, "ABSTRACT", level=1).paragraph_format.page_break_before = True
    add_body(doc,
        "GRACIANO PINZÓN, J. F. Dynamic Credit Risk Modeling for Microentrepreneurs: "
        f"A Survival Analysis Approach on High-Frequency Flows under Censoring. 2026. "
        f"{_pagina(('total', 0))} f. Monografia (MBA em Ciências de Dados) – Centro de Ciências "
        "Matemáticas Aplicadas à Indústria, Instituto de Ciências Matemáticas e de Computação, "
        "Universidade de São Paulo, São Carlos, 2026.", indent_first=False)
    doc.add_paragraph()
    add_body(doc,
        "Lending to small merchants in Brazil is hindered by the lack of information about their "
        "real ability to pay, since traditional models rely on fixed data and only predict "
        "whether a client will default or not. This work proposes a risk model that follows "
        "each loan over time, using the daily payment history of a microcredit institution that "
        "serves formal and informal merchants. Because the institution's system does not offer "
        "direct access to its data, an automated extraction process (web scraping) was developed "
        "to collect six years "
        "of payments, from 2020 to 2026, from three offices. The files were merged into a single "
        "database and carefully reviewed, and loan abandonment was defined as 120 consecutive "
        "days without any payment. The final database has 28,149 loans, of which 200, or 0.71%, ended "
        "in abandonment. Since a loan can end in two ways, abandonment or full repayment, the "
        "risk is studied with survival analysis for competing risks, using the Fine and Gray "
        "model, compared with logistic regression and, in the next stages, with machine "
        "learning models. With the information available on the 21st day of the loan, the "
        "model places 81% of future abandonments among the 10% of clients with the highest "
        "risk, about four months before the abandonment is confirmed. "
        "The client's history is also informative: using only the information available on the "
        "disbursement day, the model places "
        "36% of future abandonments among the 10% with the highest risk, more than three times "
        "what would be expected by chance. The results indicate that the history can support "
        "the decision to grant credit and that weekly monitoring of payments makes it possible "
        "to identify clients in difficulty early, before the delay turns into a loss.",
        indent_first=False)
    p = doc.add_paragraph()
    _set_spacing(p)
    run = p.add_run(
        "Keywords: survival analysis; competing risks; credit risk; microcredit; small "
        "businesses; Fine and Gray model.")
    _set_font(run)
    page_break(doc)


def build_listas(doc):
    # Listas de ilustrações e de tabelas: geradas a partir do REGISTRO.
    add_heading(doc, "LISTA DE ILUSTRAÇÕES", level=1)
    for num, desc in REGISTRO["figuras"]:
        _linha_com_pagina(doc, f"Figura {num} – {desc}", _pagina(("figura", num)))
    page_break(doc)

    add_heading(doc, "LISTA DE TABELAS", level=1)
    for num, desc in REGISTRO["tabelas"]:
        _linha_com_pagina(doc, f"Tabela {num} – {desc}", _pagina(("tabela", num)))
    page_break(doc)

    # Lista de Abreviaturas e Siglas: só as siglas usadas no corpo do texto.
    add_heading(doc, "LISTA DE ABREVIATURAS E SIGLAS", level=1)
    for sigla in sorted(SIGLAS, key=str.upper):
        if re.search(rf"(?<!\w){re.escape(sigla)}(?!\w)", REGISTRO["texto_corpo"]):
            p = doc.add_paragraph()
            _set_spacing(p, multiple=1.0)
            p.paragraph_format.left_indent = Cm(3)
            p.paragraph_format.first_line_indent = Cm(-3)
            p.paragraph_format.tab_stops.add_tab_stop(Cm(3))
            _set_font(p.add_run(f"{sigla}\t"), size=12)
            for i, trecho in enumerate(SIGLAS[sigla].split("*")):
                if trecho:
                    _set_font(p.add_run(trecho), size=12, italic=i % 2 == 1)
    page_break(doc)

    # Lista de Símbolos: só os símbolos que aparecem no texto, na ordem em que
    # aparecem (NBR 14724), com o mesmo formato da lista de siglas.
    add_heading(doc, "LISTA DE SÍMBOLOS", level=1)
    simbolos = [
        ("S(t)", "Função de sobrevivência: probabilidade de o evento ainda não ter ocorrido no dia t"),
        ("P",    "Probabilidade"),
        ("T",    "Dia em que o evento ocorre, contado a partir do desembolso do crédito"),
        ("t",    "Um dia qualquer, contado a partir do desembolso do crédito"),
        ("h(t)", "Função de risco: chance de o evento ocorrer no dia t entre os créditos que chegaram até esse dia sem ele"),
    ]
    for simbolo, desc in simbolos:
        p = doc.add_paragraph()
        _set_spacing(p, multiple=1.0)
        p.paragraph_format.left_indent = Cm(3)
        p.paragraph_format.first_line_indent = Cm(-3)
        p.paragraph_format.tab_stops.add_tab_stop(Cm(3))
        _set_font(p.add_run(f"{simbolo}\t{desc}"), size=12)
    page_break(doc)


def build_sumario(doc):
    add_heading(doc, "SUMÁRIO", level=1)
    # Como no modelo oficial do MBA: todos os títulos na margem esquerda e, do
    # apêndice, só o título (sem as subseções A.1, A.2...).
    for i, (nivel, titulo) in enumerate(REGISTRO["titulos"]):
        if re.match(r"^[A-Z]\.\d", titulo):
            continue
        _linha_com_pagina(doc, titulo, _pagina(("titulo", i)),
                          recuo=0, negrito=(nivel == 1))
    # A numeração visível começa na Introdução (seção própria com cabeçalho).
    secao = doc.add_section(WD_SECTION.NEW_PAGE)
    _numerar_paginas(secao)
    REGISTRO["titulos"].clear()
    REGISTRO["figuras"].clear()
    REGISTRO["tabelas"].clear()
    REGISTRO["ativo"] = True
    REGISTRO["inicio_corpo"] = len(doc.paragraphs)


# ── SEÇÃO 1 ──────────────────────────────────────────────────────────────────

def build_secao_1(doc):
    add_heading(doc, "1  INTRODUÇÃO", level=1)
    add_body(doc,
        "No Brasil, os pequenos negócios têm um peso enorme na economia. Segundo o Mapa de "
        "Empresas (BRASIL, 2026), o país tinha 25,4 milhões de empresas ativas em julho de "
        "2026, das quais 13,6 milhões eram microempreendedores individuais (MEI). Além delas, "
        "existem muitos comerciantes que trabalham sem nenhum registro. Para esse público, o "
        "crédito continua sendo um desafio. De acordo com a pesquisa Pulso dos Pequenos "
        "Negócios, do Sebrae (ABREU, 2026), mesmo sendo o maior percentual desde 2022, menos "
        "da metade (46%) dos pequenos negócios que buscaram crédito nos três meses anteriores "
        "conseguiu aprovação, e um em cada quatro tinha dívidas em atraso em julho de 2026. "
        "Para o comerciante informal, que muitas vezes não tem comprovante de renda nem "
        "histórico bancário, a situação tende a ser ainda mais difícil.")
    add_body(doc,
        "Este trabalho utiliza dados de uma instituição de microcrédito voltada a "
        "comerciantes, formais e informais. Os créditos têm valores baixos e prazos curtos, de "
        "poucas semanas, e cada pagamento fica registrado no dia em que acontece. Isso permite "
        "acompanhar, para cada crédito, em quais dias houve pagamento e de quanto foi, o que é "
        "uma informação muito mais rica do que a que costuma estar disponível para esse "
        "público.")
    add_body_italico(doc,
        "Os modelos tradicionais de análise de crédito, conhecidos como *credit scoring*, "
        "costumam olhar para uma fotografia do cliente em um único momento, como o histórico "
        "em birôs de crédito ou a renda declarada, e respondem apenas se ele vai ou não deixar "
        "de pagar. Para o microempreendedor informal, essa fotografia quase não existe, e ela "
        "também não muda quando o comportamento do cliente muda. O resultado é uma decisão "
        "pouco informada, tanto para quem empresta quanto para quem precisa do dinheiro.")
    add_body(doc,
        "A proposta deste trabalho é usar o próprio histórico de pagamentos para acompanhar o "
        "risco de cada crédito ao longo do tempo. Em vez de perguntar apenas se o cliente vai "
        "deixar de pagar, a ideia é estimar quando isso pode acontecer, usando a análise de "
        "sobrevivência, um conjunto de métodos estatísticos criado para estudar o tempo até um "
        "evento. A pergunta que orienta a pesquisa é: é possível antecipar, a partir do "
        "histórico de pagamentos, quando um microempreendedor vai deixar de pagar o seu "
        "crédito, e quais fatores do seu comportamento, da sua região e do seu nível "
        "socioeconômico mudam esse risco?")
    add_body(doc,
        "Para responder a essa pergunta, o trabalho traz cinco contribuições. A primeira é um "
        "processo automatizado para extrair os dados de um sistema que não oferece acesso "
        "direto às informações, o que permitiu reunir seis anos de pagamentos de três "
        "escritórios, em três estados. A segunda é a construção e a revisão de uma base de "
        "dados em que o desfecho de cada crédito é definido a partir dos pagamentos reais. A "
        "terceira é a modelagem do risco considerando os dois finais possíveis de um crédito, "
        "o abandono e a quitação, que competem entre si. A quarta é a comparação entre "
        "modelos estatísticos clássicos, como o de Fine e Gray, regras simples de decisão e "
        "modelos de aprendizado de máquina. A quinta é uma análise de como o risco varia entre "
        "regiões e níveis socioeconômicos. Do ponto de vista prático, o trabalho mostra como "
        "transformar esses modelos em uma lista semanal de clientes priorizados por risco.")
    add_body(doc,
        "O texto está organizado da seguinte forma. O Capítulo 2 apresenta a revisão da "
        "literatura e o Capítulo 3, os objetivos. O Capítulo 4 descreve como os dados foram "
        "obtidos e organizados, e o Capítulo 5 explica o tratamento dos dados e a definição do "
        "evento estudado. O Capítulo 6 apresenta a análise exploratória, o Capítulo 7 traz os "
        "modelos e os resultados, e o Capítulo 8 reúne as considerações finais e os próximos "
        "passos.")


# ── SEÇÃO 2 — REVISÃO BIBLIOGRÁFICA ──────────────────────────────────────────

def build_secao_2_revisao_bibliografica(doc):
    add_heading(doc, "2  REVISÃO BIBLIOGRÁFICA", level=1)
    add_body(doc,
        "Esta seção situa o presente trabalho no corpo de literatura que sustenta suas três "
        "frentes: (i) a modelagem de risco de crédito para tomadores de baixa formalidade, "
        "(ii) os fundamentos estatísticos da Análise de Sobrevivência e sua extensão a "
        "covariáveis tempo-variantes, e (iii) as arquiteturas de Deep Learning aplicadas a dados "
        "censurados. Adota-se o sistema de chamada autor-data (ABNT NBR 10520), consistente com "
        "as citações utilizadas nas demais seções deste documento.")

    add_heading(doc, "2.1  Risco de Crédito para Microempreendedores: da Escassez de Dados ao "
                     "Comportamento Dinâmico", level=2)
    add_body(doc,
        "A literatura clássica de credit scoring para pequenas e médias empresas, como o "
        "modelo de Altman e Sabato (2007) para o mercado americano, demonstra que indicadores "
        "contábeis estáticos têm poder preditivo limitado quando aplicados a tomadores sem "
        "histórico formal consolidado (o segmento thin-file). Banerjee e Duflo (2007), ao "
        "descreverem a vida econômica dos pobres, evidenciam que a renda e o fluxo de caixa "
        "desse público são inerentemente irregulares e de alta frequência, o que é incompatível "
        "com fotografias mensais ou anuais de risco. Já Schreiner (2002), ao propor um arcabouço "
        "de avaliação do alcance social do microcrédito (outreach), reforça que a profundidade e "
        "a frequência do relacionamento entre credor e tomador, e não apenas o desfecho binário "
        "de inadimplência, são dimensões centrais para avaliar risco e impacto nesse segmento. "
        "Em conjunto, esses três trabalhos delimitam a lacuna que esta pesquisa busca preencher: "
        "modelos de credit scoring tradicionais, estáticos e binários, não capturam a dinâmica "
        "diária de pagamentos parciais que caracteriza o microcrédito informal, motivando a "
        "adoção de uma abordagem longitudinal e orientada ao tempo até o evento.")

    add_heading(doc, "2.2  Fundamentos da Análise de Sobrevivência e Extensão a Covariáveis "
                     "Tempo-Variantes", level=2)
    add_body(doc,
        "A base estatística deste trabalho parte de Kaplan e Meier (1958): o estimador não "
        "paramétrico da função de sobrevivência que dispensa qualquer suposição sobre a forma da "
        "distribuição de T, condição necessária quando (como na carteira de microcrédito aqui "
        "analisada) não há motivo teórico para assumir um formato específico para o tempo até o "
        "default. Para comparar grupos dentro dessa carteira, como escritórios com taxas de "
        "inadimplência distintas, recorre-se ao teste de log-rank de Mantel (1966), que dispensa "
        "igualmente pressupostos paramétricos. Kalbfleisch e Prentice (2002) e Klein e "
        "Moeschberger (2003) reúnem esse ferramental (Kaplan-Meier, log-rank e suas extensões) nos dois tratamentos de referência utilizados ao longo deste trabalho para dados "
        "censurados e truncados. A peça que conecta essa base clássica ao problema de alta "
        "frequência tratado aqui é o formato de Processo de Contagem de Andersen e Gill (1982): "
        "ao reescrever o Modelo de Riscos Proporcionais de Cox em intervalos de tempo consecutivos, "
        "ele permite que covariáveis como o atraso e o saldo devedor variem a "
        "cada bloco de tempo, em vez de permanecerem fixas como em uma especificação clássica "
        "de Cox. Por fim, os diagnósticos de Therneau e Grambsch (2000), em particular os resíduos de Schoenfeld, serão o critério para checar, já na fase de modelagem (Capítulo 7), "
        "se a suposição de riscos proporcionais se sustenta nesse regime tempo-variante.")

    add_heading(doc, "2.3  Deep Learning em Análise de Sobrevivência", level=2)
    add_body(doc,
        "Katzman et al. (2018) tratam o problema de linearidade do Cox por outro caminho: em vez "
        "de assumir que o log-hazard é uma combinação linear das covariáveis, o DeepSurv usa uma "
        "rede neural para aprender essa função diretamente da verossimilhança parcial de Cox, "
        "dispensando a especificação manual de interações entre variáveis, ponto relevante aqui, "
        "dado o número elevado de covariáveis tempo-variantes derivadas do histórico de "
        "pagamentos. Kim (2026) mapeia esse campo em expansão, incluindo variantes recorrentes "
        "(LSTM/GRU) pensadas para sequências longas, como as séries diárias de pagamentos "
        "observadas neste portfólio, e aponta abordagens multimodais como direção "
        "futura. É esse mapeamento que orienta a comparação prevista para o Sprint 5 (Seção 8) "
        "entre o baseline de Cox e uma arquitetura de Deep Learning sob censura.")

    add_heading(doc, "2.4  Gestão Ágil de Projetos de Ciência de Dados como Framework "
                     "Metodológico", level=2)
    add_body(doc,
        "Do ponto de vista da condução do projeto, Louzada Neto (2026) caracteriza projetos de "
        "Ciência de Dados e Inteligência Artificial como empreendimentos de alto risco e médio "
        "a longo prazo, propondo a adoção conjunta do ciclo CRISP-DS (Cross Industry Standard "
        "Process for Data Science) e de práticas ágeis de gestão (Scrum) como mitigadores desse "
        "risco. Esse referencial é adotado neste trabalho tanto para estruturar o pipeline de "
        "dados em seis etapas (Seção 4.5) quanto para organizar o cronograma de pesquisa em "
        "Sprints com entregas incrementais (Seção 8).")


# ── SEÇÃO 3 — OBJETIVOS ───────────────────────────────────────────────────────

def build_secao_2(doc):
    add_heading(doc, "3  OBJETIVOS", level=1)
    add_heading(doc, "3.1  Objetivo Geral", level=2)
    add_body(doc,
        "Desenvolver e avaliar modelos de análise de sobrevivência com riscos competitivos "
        "que antecipem, a partir do comportamento diário de pagamento e do histórico do "
        "cliente, quais créditos de microempreendedores terminarão em abandono (default), "
        "comparando modelos estatísticos clássicos com modelos de aprendizado de máquina.")
    add_heading(doc, "3.2  Objetivos Específicos", level=2)
    items = [
        ("Extração e consolidação:",
         "Construir um processo automatizado para extrair e consolidar o histórico diário de "
         "pagamentos do sistema da instituição."),
        ("Qualidade dos dados:",
         "Auditar a base, tratar dados ausentes e inconsistentes e reconstruir o desfecho de "
         "cada crédito a partir das datas reais dos pagamentos."),
        ("Análise exploratória:",
         "Descrever quando e onde ocorrem os desfechos, os sinais que antecedem o default e o "
         "efeito do calendário e da conjuntura, incluindo diferenças regionais e socioeconômicas."),
        ("Modelos clássicos:",
         "Ajustar os modelos de Cox, de Fine e Gray e de fração de cura e a regressão "
         "logística para estimar o risco de default em diferentes momentos da vida do "
         "crédito, comparando-os com regras simples de decisão."),
        ("Aprendizado de máquina:",
         "Comparar esses modelos com o Random Survival Forest e o DeepHit, com a mesma "
         "validação e as mesmas métricas."),
        ("Aplicação:",
         "Traduzir os resultados em um alerta semanal de risco útil para a operação."),
    ]
    for label, text in items:
        add_labeled(doc, label, text)


# ── SEÇÃO 4: ARQUITETURA DE DADOS (ETL) ────────────────────────────────────

def build_secao_3(doc):
    add_heading(doc, "4  ARQUITETURA DE DADOS E PIPELINE DE EXTRAÇÃO (ETL)", level=1)
    add_body_italico(doc,
        "Para estudar o comportamento de pagamento dos clientes ao longo do tempo, foi "
        "preciso primeiro reunir o histórico diário de pagamentos de cada crédito. Esse "
        "trabalho seguiu as três etapas clássicas de um *pipeline* ETL: extração (baixar os "
        "dados do sistema da instituição), transformação (organizar, limpar e corrigir) e "
        "carga (gravar uma base única pronta para a análise). A Figura {fig:fluxo} resume o "
        "caminho completo, da extração até a avaliação dos modelos.")
    add_figure(doc, REPORTS / "fig00_fluxo_metodologico.png",
               "Fluxo metodológico do trabalho, da extração dos dados à avaliação dos modelos",
               "fluxo", largura=16)

    add_heading(doc, "4.1  Fonte dos Dados e Extração Automatizada", level=2)
    add_body_italico(doc,
        "Os dados vêm do sistema de gestão da instituição parceira, chamado aqui de ATLAS "
        "por confidencialidade. É nele que ficam registrados os créditos e cada pagamento "
        "diário. O sistema não oferece uma opção para exportar a base completa: só permite "
        "baixar, pela tela do navegador, relatórios de pagamentos de no máximo 10 dias e "
        "de uma rota por vez. Para cobrir 17 rotas entre janeiro de 2020 e maio de 2026 "
        "seriam necessários cerca de 4 mil downloads, o que é inviável de forma manual.")
    add_body_italico(doc,
        "A solução foi construir um processo automatizado de extração em Python, com a "
        "biblioteca Selenium, que repete "
        "no navegador os mesmos passos que uma pessoa faria: entrar com usuário e senha, "
        "escolher o escritório e a rota, preencher as datas e baixar o relatório. Essa "
        "técnica é conhecida como automação web (*web scraping*). A Tabela {tab:barreiras} "
        "resume as principais dificuldades encontradas e como cada uma foi resolvida; o "
        "detalhe técnico está no Apêndice A.")
    add_table_data(doc,
        ["Dificuldade", "O que acontecia", "Como foi resolvida"],
        [["Sistema sem opção de exportar a base",
          "Só era possível baixar relatórios de 10 dias pela tela",
          "Rotina que baixa os relatórios um a um, avançando 10 dias por vez"],
         ["Campos que não respondem a cliques automáticos",
          "A rotina selecionava a rota ou a data, mas o sistema não registrava",
          "A rotina escreve o valor diretamente na página, como se o usuário o tivesse escolhido"],
         ["Períodos sem movimento",
          "Relatórios vazios criariam zeros falsos na base",
          "Antes de baixar, a rotina verifica se o relatório tem dados"],
         ["Extração longa sujeita a quedas",
          "Uma falha obrigaria a recomeçar do zero",
          "A rotina guarda o último relatório baixado, retoma desse ponto e pula os já existentes"]],
        "Principais dificuldades da extração e soluções adotadas", "barreiras",
        larguras=[4.2, 5.4, 6.4])
    add_body(doc,
        "Ao final, foram baixados 3.962 relatórios de 3 escritórios e 17 rotas, cobrindo o "
        "período de 1º de janeiro de 2020 a 15 de maio de 2026.")

    add_heading(doc, "4.2  Consolidação dos Relatórios (Data Stitching)", level=2)
    add_body_italico(doc,
        "*Data Stitching* (em tradução livre, costura de dados) é o processo de juntar "
        "arquivos parciais em uma única base contínua. Cada relatório baixado cobre apenas "
        "10 dias e uma rota; a consolidação reúne todos eles em uma tabela chamada Matriz "
        "Mestra, na qual cada linha é um crédito em um relatório e cada coluna de data guarda "
        "o valor pago naquele dia. O escritório, a rota e as datas de cada relatório são "
        "lidos do nome da pasta e do arquivo, e a origem de cada linha fica registrada, o "
        "que permite voltar ao relatório original sempre que for preciso conferir um dado.")
    add_body_italico(doc,
        "A Matriz Mestra tem 344.869 linhas e 2.358 colunas e ocupa cerca de 6 GB na memória, "
        "mais do que o computador usado dispõe. Por isso ela é lida em partes de 5.000 "
        "linhas (*chunks*), e de cada parte se guardam apenas os pagamentos efetivos. O "
        "resultado é uma lista com cerca de 470 mil pagamentos diários, uma linha por crédito "
        "e dia com pagamento, que é a base de todo o restante do trabalho.")

    add_heading(doc, "4.3  Tratamento de Dados Ausentes e Inconsistentes", level=2)
    add_body_italico(doc,
        "O sistema da instituição foi feito para a operação do dia a dia, não para pesquisa. "
        "Por isso, antes de modelar, os dados passaram por uma auditoria que encontrou "
        "valores ausentes, campos enganosos e registros que não correspondem a créditos de "
        "clientes. Cada problema foi confirmado com a equipe da operação e recebeu um "
        "tratamento específico, seguindo as técnicas de tratamento de dados faltantes, "
        "*outliers* e redundância vistas na disciplina Técnicas Avançadas de Captura e "
        "Tratamento de Dados do MBA. A Tabela {tab:auditoria} resume a auditoria.")
    add_table_data(doc,
        ["Problema encontrado", "Como foi identificado", "Tratamento"],
        [["Campos com o estado do dia da descarga (saldo, parcelas em atraso, valor e número de parcelas)",
          "O mesmo valor aparece em todos os relatórios do crédito, inclusive nos de anos anteriores",
          "Não são usados como variáveis; saldo e atraso são recalculados a partir dos pagamentos diários"],
         ["Pagamento de fechamento ausente",
          "O crédito não aparece no relatório do período em que é quitado",
          "A data do último abono registrada pelo sistema marca o fechamento (só define o desfecho)"],
         ["Créditos sem nenhum movimento (250)",
          "Saldo zero e nenhum abono registrado",
          "Excluídos"],
         ["Empréstimos internos a funcionários (150)",
          "O nome do cliente começa com VALE",
          "Excluídos, pois não são créditos de clientes"],
         ["Créditos não diários (256) e anteriores a 2020 (43)",
          "Mais de 1,5 dia entre parcelas (créditos semanais ou quinzenais); histórico de pagamentos incompleto",
          "Excluídos da coorte"],
         ["Renegociação com parcela de 1 real (269)",
          "Prazo alongado no mesmo crédito quando o comerciante fecha o negócio",
          "Usa-se a parcela original estimada (total dividido por 20)"],
         ["Baixa contábil de créditos abandonados",
          "Abono pelo saldo total depois de meses sem pagamento",
          "Não conta como pagamento: o default já está marcado no dia 120 sem pagar"],
         ["Abonos depois do fechamento (89 créditos)",
          "Valores pagos acima do total depois de o crédito estar quitado",
          "Ignorados: usam-se só os pagamentos até o fechamento"],
         ["Cliente sem créditos anteriores",
          "Histórico do cliente ausente no primeiro crédito",
          "Indicador de primeiro crédito e imputação pela mediana do conjunto de treino"],
         ["Domingos e feriados",
          "Não há cobrança nesses dias",
          "O atraso é medido em dias de cobrança, por estado"]],
        "Auditoria dos dados: problemas encontrados e tratamento", "auditoria",
        larguras=[5.0, 5.5, 5.5])
    add_body(doc,
        "Dos 28.849 créditos lidos, 699 foram excluídos pelos critérios da Tabela "
        "{tab:auditoria} e 1 por não ter dados de contrato, restando 28.149 créditos de "
        "clientes para a análise.")

    add_heading(doc, "4.4  Governança de Dados e LGPD", level=2)
    add_body(doc,
        "O pipeline ETL foi projetado com governança de dados desde a concepção, atendendo "
        "aos requisitos da Lei Geral de Proteção de Dados Pessoais (LGPD, Lei nº 13.709/2018) "
        "e às melhores práticas de segurança da informação em projetos de Ciência de Dados.")
    add_body(doc,
        "O uso dos dados foi autorizado pelo proprietário da instituição parceira, que também "
        "forneceu o acesso ao sistema para a extração, exclusivamente para fins acadêmicos. Os "
        "dados não saem do ambiente local da pesquisa: o nome da instituição e o do sistema "
        "foram substituídos por pseudônimos, os clientes são identificados apenas por códigos "
        "e nenhum dado individual é publicado neste trabalho.")

    add_table_data(doc,
        ["Controle de Governança", "Implementação", "Artigo LGPD"],
        [
            ["Exclusão do versionamento (git)",
             "Dados brutos, dados processados e credenciais fora do repositório público",
             "Art. 46 (medidas de segurança)"],
            ["Gestão de credenciais",
             "Usuário e senha guardados em arquivo local, nunca no código",
             "Art. 46 (proteção de acesso)"],
            ["Pseudonimização",
             "Clientes e créditos identificados só por códigos, sem nome, CPF ou endereço nos dados dos modelos",
             "Art. 13 (pseudonimização)"],
            ["Minimização de dados",
             "A base de análise contém apenas as variáveis necessárias para os modelos",
             "Art. 6 (necessidade)"],
            ["Finalidade definida",
             "Dados utilizados exclusivamente para pesquisa acadêmica de risco de crédito",
             "Art. 6 (finalidade)"],
            ["Rastreabilidade",
             "Cada linha da Matriz Mestra guarda o relatório de origem do dado",
             "Art. 37 (registro das operações)"],
        ],
        "Conformidade LGPD e governança de dados no pipeline ETL",
        table_num=8,
    )


    add_heading(doc, "4.5  Gestão do Projeto", level=2)
    add_body(doc,
        "A metodologia CRISP-DS (Cross Industry Standard Process for Data Science), adotada "
        "como framework de gestão do projeto (Louzada Neto, 2026), estrutura o pipeline em seis "
        "fases iterativas que se retroalimentam:")

    fases = [
        ("(1) Entendimento do Negócio:",
         "Definição dos desfechos com a operação da instituição: default após 120 dias sem "
         "pagamento, quitação pelo pagamento de pelo menos 98% do total (Seção 5.2)."),
        ("(2) Entendimento dos Dados:",
         "Extração e consolidação dos relatórios, auditoria dos dados (Capítulo 4) e análise "
         "exploratória da base reconstruída (Capítulo 6)."),
        ("(3) Preparação dos Dados:",
         "Reconstrução dos desfechos a partir dos pagamentos diários, blocos de 7 dias, "
         "calendário de cobrança e histórico do cliente (Capítulo 5)."),
        ("(4) Modelagem:",
         "Modelo de Fine e Gray em landmark, regressão logística e Cox tempo-variante "
         "(Capítulo 7); modelo de fração de cura, Random Survival Forest e DeepHit nos "
         "próximos Sprints."),
        ("(5) Avaliação:",
         "Validação cruzada agrupada por cliente, AUC, captura dos defaults no top 10% de "
         "risco e índice de concordância (Seção 7.2)."),
        ("(6) Implantação:",
         "Lista semanal de clientes priorizados por risco para a operação (trabalho futuro)."),
    ]
    for label, text in fases:
        add_labeled(doc, label, text)

    add_body(doc,
        "A gestão de riscos do projeto seguiu as sete categorias identificadas na literatura "
        "de gerenciamento ágil de projetos de Ciência de Dados (Louzada Neto, 2026): "
        "(1) qualidade dos dados: mitigada pela verificação de relatórios vazios e pela auditoria dos dados (Seção 4.3); "
        "(2) orçamento: controlado pela solução in-house de web scraping, eliminando licenças "
        "externas; (3) comprometimento: gerenciado com entregas iterativas por Sprint; "
        "(4) recursos humanos: risco baixo por ser pesquisa individual; "
        "(5) fornecedores: mitigado porque a extração foi desenvolvida pelo próprio autor, sem depender de ferramentas de terceiros; "
        "(6) segurança da informação: LGPD, exclusão dos dados do repositório e pseudonimização; "
        "(7) expectativas de tempo: cronograma CRISP-DS com 7 Sprints Scrum.")
    add_body(doc,
        "A formatação deste documento e pequenos trechos de código contaram com apoio pontual "
        "de uma ferramenta de inteligência artificial (ANTHROPIC, 2026).")



# ── SEÇÃO 4 ──────────────────────────────────────────────────────────────────

def build_secao_4(doc):
    add_heading(doc, "5  DEFINIÇÃO DO EVENTO E ENGENHARIA DE ATRIBUTOS", level=1)
    add_body(doc,
        "Este capítulo apresenta as ideias de análise de sobrevivência usadas no trabalho, "
        "explica como foi definido o desfecho de cada crédito e mostra como os pagamentos "
        "diários foram transformados nas variáveis que alimentam os modelos.")

    add_heading(doc, "5.1  Conceitos de Análise de Sobrevivência", level=2)
    add_body(doc,
        "A análise de sobrevivência estuda o tempo até a ocorrência de um evento "
        "(Kalbfleisch e Prentice, 2002; Klein e Moeschberger, 2003). Aqui, o tempo é contado "
        "em dias desde o desembolso do crédito, e o evento de interesse é o default. A "
        "diferença em relação a uma regressão logística comum é que a análise de "
        "sobrevivência considera não só se o evento acontece, mas também quando, e aproveita "
        "a informação dos créditos que ainda estão em andamento.")
    add_body(doc,
        "Esses créditos em andamento são chamados de censurados. Em 15 de maio de 2026, data "
        "de corte do estudo, alguns créditos ainda estavam abertos: sabe-se que até ali não "
        "houve default, mas não se sabe o que acontecerá depois. Descartá-los ou tratá-los "
        "como bons pagadores distorceria o resultado; a análise de sobrevivência os usa até o "
        "último dia observado.")
    add_body(doc,
        "Duas funções resumem esse tipo de dado. A função de sobrevivência, S(t), é a "
        "probabilidade de o crédito ainda não ter sofrido o evento no dia t:")
    add_formula(doc, "S(t) = P(T > t)")
    add_body(doc, indent_first=False, text=
        "em que T é o dia em que o evento ocorre. A função de risco, h(t), é a chance de o "
        "evento acontecer exatamente no dia t entre os créditos que chegaram até ali sem ele. "
        "O estimador de Kaplan e Meier (1958) calcula S(t) diretamente dos dados, sem supor "
        "nenhuma forma para a distribuição do tempo.")
    add_body_italico(doc,
        "Neste problema, porém, cada crédito pode terminar de duas formas que competem "
        "entre si: em default (o cliente abandona o crédito) ou em quitação (o cliente paga tudo). "
        "Uma impede a outra, situação chamada de riscos competitivos. Tratar a quitação como "
        "simples censura, como faz o Kaplan-Meier comum, superestima o risco, porque supõe que "
        "quem já pagou tudo ainda poderia entrar em default. A medida correta é a função de "
        "incidência acumulada (CIF, *cumulative incidence function*), que dá a probabilidade "
        "de o crédito ter terminado em default até o dia t, considerando que a maioria termina "
        "antes em quitação.")
    add_body_italico(doc,
        "Para relacionar o risco com as características do crédito e do cliente, o modelo de "
        "Cox (1972) é a referência clássica. Ele estima quanto cada variável multiplica o "
        "risco de default, medida chamada razão de risco (*hazard ratio*): uma razão de 2 "
        "indica risco duas vezes maior. O modelo de Fine e Gray (1999) adapta essa ideia aos "
        "riscos competitivos e modela diretamente a incidência acumulada de default. Por isso "
        "ele é o modelo principal deste trabalho, como detalhado no Capítulo 7.")

    add_heading(doc, "5.2  Definição dos Desfechos", level=2)
    add_body(doc,
        "O desfecho de cada crédito foi reconstruído a partir das datas reais dos "
        "pagamentos, com as regras confirmadas pela operação da instituição e resumidas na "
        "Tabela {tab:desfechos}.")
    add_table_data(doc,
        ["Desfecho", "Regra", "Créditos", "%"],
        [["Default",
          "120 dias corridos sem nenhum pagamento, contados do último pagamento (ou do desembolso, se nunca pagou)",
          "200", "0,71"],
         ["Quitação",
          "Pagamento acumulado de pelo menos 98% do total antes de qualquer silêncio de 120 dias",
          "27.191", "96,60"],
         ["Censura",
          "Nenhum dos dois até 15 de maio de 2026",
          "758", "2,69"],
         ["Total", "", "28.149", "100,00"]],
        "Definição dos desfechos e quantidade de créditos em cada um", "desfechos",
        larguras=[2.3, 9.7, 2.2, 1.8])
    add_body(doc,
        "O limite de 120 dias é a regra que a própria instituição usa para considerar um "
        "crédito perdido. Ele separa o atraso passageiro do abandono: um comerciante pode "
        "ficar doente ou viajar por um ou dois meses e depois voltar a pagar. Os dados "
        "confirmam isso: 476 créditos ficaram 30 dias ou mais sem nenhum pagamento e ainda "
        "assim foram quitados, 235 ficaram 60 dias ou mais e 100 ficaram 90 dias ou mais. Com "
        "um limite de 60 dias, esses 235 créditos teriam sido marcados como default, mais do "
        "que os 200 defaults da base. Já o limite de 98%, e não de 100%, para a quitação "
        "absorve pequenas diferenças de arredondamento e ajustes no último pagamento.")
    add_body(doc,
        "Meses depois do abandono, a instituição faz a baixa contábil do crédito com um "
        "lançamento pelo saldo; esse lançamento não é pagamento do cliente e não altera o "
        "desfecho, que já foi marcado no dia 120.")
    add_body(doc,
        "O default é raro: 200 créditos em 28.149, ou 0,71%. Essa raridade orienta a escolha "
        "das métricas de avaliação, que precisam medir se o modelo encontra esses poucos "
        "casos entre milhares de créditos bons (Capítulo 7).")

    add_heading(doc, "5.3  Granularidade dos Dados: Dados Diários e Blocos de 7 Dias", level=2)
    add_body(doc,
        "Os créditos estudados duram de 20 a 50 dias e são pagos diariamente. Em uma visão "
        "mensal, como a dos modelos tradicionais de crédito, um crédito inteiro caberia em "
        "uma ou duas fotografias, e não seria possível ver o que realmente antecede o "
        "abandono: semanas sem pagamento, parcelas pagas pela metade ou a retomada depois de "
        "um atraso. Os registros diários permitem medir esses comportamentos e também "
        "distinguir os dias em que simplesmente não há cobrança, como domingos e feriados, "
        "dos dias em que o cliente deixou de pagar.")
    add_body(doc,
        "Isso não exige recalcular o modelo todos os dias. A vida de cada crédito é dividida "
        "em blocos, e no início de cada bloco as variáveis são recalculadas usando apenas a "
        "informação disponível naquele dia, sem nenhuma informação do futuro. Esse formato, "
        "em que o mesmo crédito aparece em vários intervalos consecutivos, é o processo de "
        "contagem de Andersen e Gill (1982). O bloco principal tem 7 dias, um ciclo completo "
        "de cobrança (segunda a sábado, com o domingo livre); blocos de 10 dias, o tamanho "
        "das janelas de extração, foram usados como comparação. Com blocos de 7 dias, os "
        "28.149 créditos geram 126.132 intervalos, contra 93.117 com blocos de 10 dias. O "
        "bloco de 7 dias deu o alerta mais cedo, como mostra o Capítulo 7.")
    add_body(doc,
        "Na prática, recalcular as variáveis a cada bloco significa que o risco de cada "
        "cliente é atualizado toda semana, e não fica congelado no dia da concessão. Um "
        "cliente que paga bem na primeira semana e passa a pagar metade da parcela na "
        "terceira tem o risco aumentado já na terceira semana. É a mesma lógica do "
        "acompanhamento que a operação faz: a cada semana, uma lista dos clientes que mais "
        "precisam de atenção, para priorizar contatos e visitas antes que o atraso vire perda.")

    add_heading(doc, "5.4  Variáveis dos Modelos", level=2)
    add_body(doc,
        "As variáveis foram organizadas em três grupos, descritos na Tabela {tab:variaveis}. "
        "As do crédito atual mudam a cada bloco; as do contrato são fixas; e as do histórico "
        "resumem como o mesmo cliente pagou os créditos anteriores, considerando apenas os "
        "que já estavam fechados no dia do novo desembolso. Esse último grupo nasceu de uma "
        "observação da operação: o cliente que está passando aperto costuma mostrar isso "
        "antes, pagando parcelas incompletas, atrasando ou fazendo um pagamento alto no fim "
        "apenas para conseguir renovar.")
    add_table_data(doc,
        ["Grupo", "Variável", "O que mede"],
        [["Crédito atual", "Atraso relativo", "Parcelas em atraso medidas em dias de cobrança, dividido pelo prazo"],
         ["Crédito atual", "Saldo relativo", "Parte do total que ainda falta pagar"],
         ["Crédito atual", "Dias com pagamento no bloco anterior", "Em quantos dias da semana anterior o cliente pagou"],
         ["Crédito atual", "Pagamento relativo no bloco anterior", "Valor pago por dia na semana anterior dividido pela parcela"],
         ["Crédito atual", "Percentual de pagamentos incompletos", "Pagamentos menores que 90% da parcela, desde o desembolso"],
         ["Crédito atual", "Dias sem cobrança no bloco", "Domingos e feriados da semana, conhecidos de antemão"],
         ["Contrato", "Valor do crédito", "Valor total, em escala logarítmica"],
         ["Contrato", "Prazo", "Prazo pactuado (20, 24, 30, 40 ou 50 dias)"],
         ["Contrato", "Escritório", "São Paulo, Sociedades Brasil ou Cabo Frio"],
         ["Histórico", "Primeiro crédito", "Indica se o cliente não tem créditos anteriores"],
         ["Histórico", "Pontualidade no crédito anterior", "Dias com pagamento divididos pelos dias esperados"],
         ["Histórico", "Prazo usado no crédito anterior", "Dias até fechar divididos pelo prazo pactuado"],
         ["Histórico", "Último pagamento do crédito anterior", "Valor do último pagamento dividido pela parcela"],
         ["Histórico", "Parcelas incompletas nos créditos anteriores", "Percentual médio de pagamentos menores que 90% da parcela"]],
        "Variáveis usadas nos modelos", "variaveis", larguras=[2.6, 5.4, 8.0])
    add_body(doc,
        "Os dias sem pagamento, contados em dias de cobrança, são usados apenas em um modelo "
        "de referência, porque estão ligados à própria definição do default, como explicado "
        "no Capítulo 7. Os campos do sistema que mostram o estado do crédito no dia da "
        "descarga não foram usados (Seção 4.3), e, quando o cliente não tem créditos "
        "anteriores, as variáveis de histórico são preenchidas com a mediana do conjunto de "
        "treino, junto com o indicador de primeiro crédito.")



# ── CAPÍTULO 6: ANÁLISE EXPLORATÓRIA (figuras de src/fig_eda_v27.py) ─────────

FIG_EDA = REPORTS / "figuras_v27"


def build_capitulo_6(doc):
    add_heading(doc, "6  ANÁLISE EXPLORATÓRIA DOS DADOS", level=1)
    add_body(doc,
        "A análise exploratória descreve a base reconstruída de 28.149 créditos de 4.024 "
        "clientes, desembolsados entre janeiro de 2020 e maio de 2026. O objetivo é entender "
        "quando os créditos terminam, onde o risco se concentra, que comportamento antecede o "
        "default e como o calendário e a conjuntura afetam os pagamentos, para então definir "
        "a estratégia de modelagem.")

    add_heading(doc, "6.1  Quando os Créditos Terminam", level=2)
    add_body(doc,
        "A Figura {fig:cif} mostra a incidência acumulada de cada desfecho, estimada pelo "
        "método de Aalen-Johansen, que leva em conta os riscos competitivos. A quitação é rápida: "
        "30% dos créditos estão quitados até o dia 20, 78% até o dia 30 e 95,5% até o dia 60, "
        "o que corresponde aos prazos de 20 a 50 dias. O default, por definição, só aparece "
        "a partir do dia 120 e cresce até cerca de 0,8% em um ano. O tempo mediano até a quitação "
        "é de 24 dias; até o default, de 148 dias. Como o default é marcado 120 dias depois do "
        "último pagamento, isso significa que o cliente que se perde costuma parar de pagar "
        "perto da quarta semana, isto é, ainda dentro do prazo do crédito. Há, portanto, uma "
        "janela de algumas semanas em que os sinais de risco já existem e ainda é possível agir.")
    add_figure(doc, FIG_EDA / "fig_cif_desfechos.png",
               "Incidência acumulada de quitação e de default ao longo do tempo", "cif", largura=16)

    add_heading(doc, "6.2  Diferenças entre Escritórios", level=2)
    add_body(doc,
        "O risco não é igual em toda a carteira (Tabela {tab:escritorios} e Figura "
        "{fig:escritorio}). O escritório Sociedades Brasil, que reúne as rotas de Santa "
        "Catarina, Campinas e parte do Rio de Janeiro, tem 1,37% de default, contra 0,50% em "
        "São Paulo e 0,44% em Cabo Frio. O teste de log-rank para o risco de default, com a "
        "quitação tratada como censura, rejeita a igualdade entre os três escritórios "
        "(estatística de 16,2 com 2 graus de liberdade; valor-p de 0,0003).")
    add_table_data(doc,
        ["Escritório", "Créditos", "Default", "Taxa de default", "Quitação", "Censura"],
        [["São Paulo", "13.793", "69", "0,50%", "13.480", "244"],
         ["Sociedades Brasil", "7.276", "100", "1,37%", "6.983", "193"],
         ["Cabo Frio", "7.080", "31", "0,44%", "6.728", "321"],
         ["Total", "28.149", "200", "0,71%", "27.191", "758"]],
        "Desfechos por escritório", "escritorios", larguras=[3.6, 2.4, 2.0, 3.0, 2.4, 2.6])
    add_figure(doc, FIG_EDA / "fig_default_escritorio.png",
               "Incidência acumulada de default por escritório", "escritorio", largura=15)
    add_body(doc,
        "A comparação socioeconômica entre os clientes será feita com uma medida mais "
        "precisa do que o escritório. A localização de cada cliente, disponível para 94% "
        "deles a partir das coordenadas registradas nos pagamentos, será cruzada com a renda "
        "média dos domicílios do setor censitário do IBGE em que ele está. Isso permitirá "
        "comparar a taxa de abandono entre faixas de renda e incluir a renda do entorno como "
        "variável nos modelos, na próxima etapa do trabalho. O cruzamento é feito localmente, "
        "sem enviar endereços ou coordenadas a serviços externos.")

    add_heading(doc, "6.3  Comportamento nas Primeiras Semanas", level=2)
    add_body(doc,
        "A Figura {fig:dia14} mostra, para os 25.223 créditos ainda abertos no dia 14, a taxa "
        "de default final segundo o comportamento observado até aquele dia. Entre os clientes "
        "que pagaram em no máximo um dia da semana anterior, 7,51% terminaram em default, "
        "contra 0,07% entre os que pagaram em seis ou sete dias. Quem pagou até metade da "
        "parcela chegou a 3,10%; quem acumulava mais de 50% de atraso, a 15,70%; e quem ainda "
        "devia mais de 85% do total, a 7,87%. Para comparação, a taxa média nesse grupo é de "
        "0,79%. Os sinais de risco, portanto, aparecem cedo e são fortes.")
    add_figure(doc, FIG_EDA / "fig_comportamento_dia14.png",
               "Taxa de default segundo o comportamento de pagamento até o dia 14", "dia14", largura=16)

    add_heading(doc, "6.4  Histórico do Cliente", level=2)
    add_body(doc,
        "O comportamento nos créditos anteriores também informa sobre o risco, como havia "
        "apontado a equipe da operação (Figura {fig:historico}). No primeiro crédito do "
        "cliente, a taxa de default é de 1,44%, contra 0,59% para quem já tem histórico. Entre "
        "quem já teve créditos, o risco é maior quando, no crédito anterior, o cliente pagou "
        "em até 70% dos dias esperados (1,22%), usou mais de 1,2 vez o prazo pactuado (1,00%) "
        "ou fechou o crédito com um pagamento final de mais de nove parcelas, típico de quem "
        "junta o saldo de uma vez apenas para conseguir renovar (0,86%, contra 0,23% quando o "
        "último pagamento foi de até uma parcela e meia).")
    add_figure(doc, FIG_EDA / "fig_historico_cliente.png",
               "Taxa de default segundo o histórico do cliente no crédito anterior", "historico", largura=16)

    add_heading(doc, "6.5  Calendário de Cobrança e Contexto Social", level=2)
    add_body(doc,
        "A cobrança depende do calendário (Figura {fig:cobranca}). Aos domingos praticamente "
        "não há pagamentos, nos feriados nacionais e estaduais o volume cai para 22% de um dia "
        "útil e no Carnaval para 54%. Um dia sem pagamento nessas datas não é atraso, e por "
        "isso o atraso é medido em dias de cobrança, com o calendário de cada estado. Nos "
        "dias de jogos da seleção brasileira na Copa do Mundo de 2022, a queda foi menor, "
        "entre 15% e 20%, e esses dias foram mantidos como dias de cobrança.")
    add_figure(doc, FIG_EDA / "fig_cobranca_tipo_dia.png",
               "Pagamentos por tipo de dia em relação a um dia útil", "cobranca", largura=15)
    add_body(doc,
        "A conjuntura também pesa. No início da pandemia de covid-19, os pagamentos da "
        "carteira caíram de 554 em março de 2020 para 83 em abril e 50 em maio, e só voltaram "
        "ao patamar anterior no fim daquele ano (Figura {fig:pandemia}). Depois disso, a "
        "carteira cresceu até cerca de 14 mil pagamentos por mês em 2026. Choques como esse "
        "motivam a inclusão de variáveis macroeconômicas e sociais na próxima etapa.")
    add_figure(doc, FIG_EDA / "fig_pagamentos_mensais.png",
               "Pagamentos por mês em 2020 e 2021, com o período da pandemia destacado", "pandemia",
               largura=15)

    add_heading(doc, "6.6  Síntese e Implicações para a Modelagem", level=2)
    add_body(doc,
        "Os resultados da análise exploratória orientam diretamente as escolhas de "
        "modelagem do Capítulo 7. Primeiro, o default é raro e tardio, enquanto a quitação domina "
        "e acontece cedo; por isso o problema é tratado com riscos competitivos, pelo modelo "
        "de Fine e Gray (1999), e avaliado com métricas de ordenação, que medem se os poucos "
        "defaults ficam entre os clientes de maior risco, em vez da acurácia, que seria alta "
        "mesmo para um modelo que nunca previsse default. Segundo, os sinais de risco "
        "aparecem nas primeiras semanas; daí a ideia de dar o alerta em datas fixas da vida "
        "do crédito, nos dias 14 e 21, com variáveis atualizadas a cada semana. Terceiro, o "
        "histórico do cliente já informa sobre o risco antes do desembolso, o que justifica "
        "as variáveis de histórico. Quarto, as diferenças entre escritórios indicam "
        "que a localização precisa entrar no modelo.")
    add_body_italico(doc,
        "Por fim, várias relações observadas não são lineares: a taxa de default pouco muda "
        "entre faixas intermediárias e salta nos extremos, como no atraso acima de 50%, e o "
        "efeito de uma variável pode depender de outra. Um modelo linear como o de Cox ou o "
        "de Fine e Gray capta essas relações só em parte. Esse é o ponto de partida da fase de "
        "aprendizado de máquina e *Deep Learning*: o *Random Survival Forest* e o DeepHit "
        "aprendem não linearidades e interações diretamente dos dados, sem que seja preciso "
        "especificá-las à mão, e serão comparados ao modelo de Fine e Gray com as mesmas "
        "métricas e a mesma validação.")

def build_capitulo_7(doc):
    """Resultados do Sprint 4 (src/cox_v2.py, reports/modelagem_v2/)."""
    add_heading(doc, "7  MODELAGEM E RESULTADOS", level=1)

    add_heading(doc, "7.1  Estratégia de Modelagem", level=2)
    add_body_italico(doc,
        "A pergunta prática é: com o que se sabe hoje sobre um crédito em andamento, ele vai "
        "terminar em default? Para respondê-la, adotou-se a abordagem de *landmark* "
        "(marco temporal): em datas fixas da vida do crédito, os dias 14 e 21, tira-se uma "
        "fotografia das variáveis de todos os créditos ainda abertos e estima-se, a partir "
        "dela, o risco de o crédito terminar em default. As datas foram escolhidas porque a "
        "maior parte dos créditos ainda está aberta nesses dias e porque o cliente que se "
        "perde costuma parar de pagar perto da quarta semana (Seção 6.1).")
    add_body(doc,
        "O modelo principal é o de Fine e Gray (1999), que estima diretamente a incidência "
        "acumulada de default levando em conta que a quitação impede o default. Como a censura é "
        "pequena (2,69% dos créditos), ele foi ajustado nesta etapa de forma simplificada, "
        "mantendo os créditos quitados no conjunto de risco até o fim do seguimento; a versão "
        "com pesos para a censura será ajustada no próximo Sprint. Como modelo de comparação "
        "usou-se a regressão logística, um modelo linear generalizado que estima a "
        "probabilidade de o crédito terminar em default a partir da mesma fotografia.")
    add_body(doc,
        "Também foi ajustado o modelo de Cox com covariáveis que mudam a cada bloco, na "
        "versão de riscos específicos por causa (Kalbfleisch e Prentice, 2002). Ele revelou "
        "uma armadilha importante: como o default é definido por 120 dias sem pagamento, no "
        "último bloco antes do evento o cliente já está entre 113 e 119 dias sem pagar, e a "
        "variável de dias sem pagamento praticamente anuncia o evento. Com ela, o índice de "
        "concordância chega a 0,98, mas o modelo apenas confirma o que a operação já vê. Sem "
        "ela, o índice cai para 0,90, e ainda assim o modelo ordena mal os créditos nas "
        "primeiras semanas, porque, no dia 120, compara quem abandonou o crédito com os poucos "
        "créditos lentos que ainda estão abertos, já que os bons pagadores saíram pela quitação. "
        "Por isso ele ficou como referência, e não como modelo principal.")

    add_heading(doc, "7.2  Validação e Métricas", level=2)
    add_body(doc,
        "Os modelos foram avaliados por validação cruzada agrupada por cliente: os clientes "
        "foram divididos em cinco partes, e cada parte serviu uma vez de conjunto de teste "
        "enquanto as outras quatro treinavam o modelo; o processo foi repetido três vezes com "
        "sorteios diferentes. Assim, nenhum cliente aparece ao mesmo tempo no treino e no "
        "teste, o que evitaria um resultado otimista para quem tem vários créditos. A "
        "padronização das variáveis e o preenchimento de valores ausentes usaram apenas os "
        "dados de treino de cada partição.")
    add_body(doc,
        "Como o default é raro, a acurácia não serve: um modelo que nunca previsse default "
        "acertaria 99,3% das vezes. Foram usadas duas métricas de ordenação. A AUC é a "
        "probabilidade de um crédito que terminou em default receber risco maior que um "
        "crédito que não terminou; vale 0,5 para um sorteio e 1 para uma ordenação perfeita. "
        "A captura no top 10% é a porcentagem dos defaults que ficam entre os 10% de créditos "
        "com maior risco previsto; ela traduz o uso prático do modelo, que é dizer à operação "
        "quais clientes acompanhar primeiro. Para o modelo de Cox foi usado o índice de "
        "concordância de Harrell.")

    add_heading(doc, "7.3  Resultados", level=2)
    add_body(doc,
        "A Tabela {tab:resultados} resume o desempenho com blocos de 7 dias. No dia 21, o "
        "modelo de Fine e Gray alcança AUC de 0,93 e coloca 81% dos futuros defaults entre os "
        "10% de créditos de maior risco. Em termos práticos, uma lista semanal com um em cada "
        "dez clientes concentraria oito em cada dez dos que vão abandonar o crédito, cerca de "
        "quatro meses antes de o default ser confirmado pela regra dos 120 dias. No dia 14 a "
        "alerta é um pouco menos precisa (AUC de 0,90 e captura de 73%), mas chega uma semana "
        "antes. Como cada partição de teste tem apenas cerca de 40 defaults, a captura varia "
        "bastante entre as partições: no dia 21, ficou entre 72% e 88%.")
    add_table_data(doc,
        ["Modelo", "AUC dia 14", "Top 10% dia 14", "AUC dia 21", "Top 10% dia 21"],
        [["Fine e Gray (crédito atual e histórico)", "0,896 (0,022)", "72,8% (7,1)", "0,930 (0,012)", "81,2% (4,9)"],
         ["Regressão logística (mesmas variáveis)", "0,899 (0,020)", "72,7% (6,4)", "0,928 (0,012)", "80,5% (4,3)"],
         ["Regressão logística, só histórico e contrato", "0,759 (0,038)", "35,7% (5,9)", "0,753 (0,040)", "34,5% (5,0)"],
         ["Cox tempo-variante, sem dias sem pagar", "0,704 (0,061)", "47,8% (11,4)", "0,806 (0,037)", "58,1% (7,1)"],
         ["Regra simples: dias com pagamento na semana anterior", "0,863 (0,027)", "64,2% (6,7)", "0,902 (0,017)", "72,1% (5,6)"],
         ["Regra simples: pagamento em relação à parcela", "0,833 (0,025)", "60,7% (4,9)", "0,897 (0,024)", "73,5% (6,8)"]],
        "Desempenho dos modelos na validação cruzada por cliente (blocos de 7 dias)", "resultados",
        fonte="Elaborada pelo autor (2026). Média de 15 partições; desvio-padrão entre parênteses.",
        larguras=[5.6, 2.6, 2.4, 2.6, 2.4])
    add_body(doc,
        "Para saber quanto o modelo acrescenta a uma regra óbvia, os créditos também foram "
        "ordenados por uma única variável, sem nenhum modelo, como faria um analista "
        "experiente: quem pagou em menos dias na semana anterior ou quem pagou menos em "
        "relação à parcela. Essas regras já funcionam bem, o que confirma a força dos sinais "
        "vistos no Capítulo 6, e capturam até 64% dos defaults no dia 14 e 74% no dia 21. O "
        "modelo de Fine e Gray acrescenta cerca de 8 pontos a esse resultado, e a vantagem é "
        "consistente: ele superou a melhor regra simples em todas as 15 partições no dia 14 e "
        "em 13 das 15 no dia 21, com AUC maior em todas elas. O ganho do modelo vem de "
        "combinar vários sinais ao mesmo tempo, e não de um único indicador.")
    add_body(doc,
        "A regressão logística teve desempenho praticamente igual ao do modelo de Fine e Gray. "
        "Isso é esperado: na fotografia do dia 21, quase todos os créditos já têm o desfecho "
        "conhecido, e estimar a incidência acumulada de default até o fim do seguimento "
        "equivale, na prática, a estimar a probabilidade de o crédito terminar em default. A "
        "abordagem de sobrevivência se justifica por outros dois motivos. Primeiro, ela trata "
        "corretamente os 758 créditos ainda abertos, que a regressão logística precisa "
        "considerar como bons pagadores ou descartar. Segundo, ela descreve quando o default "
        "acontece, o que permite acompanhar a incidência acumulada de cada grupo de risco ao "
        "longo do tempo, como na Figura {fig:cif}, e não apenas a probabilidade final.")
    add_body(doc,
        "O modelo que usa apenas o histórico do cliente e os dados do contrato, informação "
        "disponível praticamente no dia do desembolso, ainda captura 36% dos defaults no top "
        "10%, mais de três vezes o que se esperaria de uma escolha ao acaso. Isso indica que o "
        "histórico já pode apoiar a decisão de conceder ou não um novo crédito, enquanto o "
        "comportamento das primeiras semanas permite um alerta bem mais preciso.")
    add_body(doc,
        "A comparação entre os tamanhos de bloco (Tabela {tab:blocos}) confirma a escolha de "
        "7 dias. No dia 14, o bloco de 7 dias captura 73% dos defaults no top 10%, contra 61% "
        "com blocos de 10 dias, porque usa informação mais recente: com blocos de 10 dias, a "
        "fotografia do dia 14 ainda é a do dia 10. No dia 21 a diferença diminui.")
    add_table_data(doc,
        ["Bloco", "AUC dia 14", "Top 10% dia 14", "AUC dia 21", "Top 10% dia 21"],
        [["7 dias", "0,896", "72,8%", "0,930", "81,2%"],
         ["10 dias", "0,867", "61,3%", "0,926", "78,3%"]],
        "Modelo de Fine e Gray com blocos de 7 e de 10 dias", "blocos",
        larguras=[3.2, 3.2, 3.2, 3.2, 3.2])

    add_heading(doc, "7.4  Interpretação das Variáveis", level=2)
    add_body_italico(doc,
        "A Tabela {tab:shr} mostra as razões de risco do modelo de Fine e Gray no dia 21, "
        "para as variáveis com efeito estatisticamente significativo. Como as variáveis foram "
        "padronizadas, cada razão indica quanto o risco de default se multiplica quando a "
        "variável aumenta um desvio-padrão, mantidas as demais. Um atraso relativo maior "
        "eleva o risco em 38%, e um saldo maior a pagar, em 28%; mais dias com pagamento na "
        "semana anterior reduzem o risco em 36%, e um pagamento maior em relação à parcela, "
        "em 28%. Mesmo com essas variáveis, os créditos do escritório Sociedades Brasil "
        "continuam com risco 28% maior, e o primeiro crédito do cliente, 11% maior.")
    add_table_data(doc,
        ["Variável", "Razão de risco", "Intervalo de 95%", "Valor-p"],
        [["Atraso relativo", "1,38", "1,24 a 1,54", "menor que 0,001"],
         ["Saldo relativo", "1,28", "1,13 a 1,44", "menor que 0,001"],
         ["Dias com pagamento no bloco anterior", "0,64", "0,57 a 0,72", "menor que 0,001"],
         ["Pagamento relativo no bloco anterior", "0,72", "0,64 a 0,82", "menor que 0,001"],
         ["Escritório Sociedades Brasil", "1,28", "1,16 a 1,42", "menor que 0,001"],
         ["Primeiro crédito do cliente", "1,11", "1,01 a 1,22", "0,038"]],
        "Razões de risco do modelo de Fine e Gray no dia 21, por desvio-padrão da variável",
        "shr", larguras=[6.4, 2.8, 3.6, 3.2])
    add_body(doc,
        "As demais variáveis de histórico perdem significância quando o comportamento atual "
        "entra no modelo. A leitura é que, no dia 21, o modo como o cliente está pagando o "
        "crédito atual já resume boa parte do que o histórico dizia; o histórico pesa mais "
        "antes de haver pagamentos, como mostrou o modelo que usa só essa informação.")

    add_heading(doc, "7.5  Limitações e Próximos Passos", level=2)
    add_body_italico(doc,
        "Estes resultados são da primeira rodada de modelagem e têm limitações conhecidas. A "
        "mais importante é que a validação foi por cliente, mas ainda não temporal. Como a "
        "carteira cresceu muito e atravessou a pandemia, a prova mais exigente é treinar o "
        "modelo com os créditos de 2020 a 2024 e testá-lo com os de 2025 e 2026, simulando o "
        "uso real; essa validação é a prioridade do próximo Sprint. Além disso, o modelo de "
        "Fine e Gray foi ajustado sem os pesos de censura, faltam as variáveis "
        "macroeconômicas e sociais, e, com 200 defaults, os resultados têm variação "
        "considerável entre partições.")
    add_body_italico(doc,
        "Os próximos Sprints comparam o modelo de Fine e Gray com o modelo de fração de cura "
        "(*mixture cure model*), com o *Random Survival Forest* e com o DeepHit (Lee et al., "
        "2018), sempre com a mesma validação e as mesmas métricas, e acrescentam a "
        "interpretação das previsões com valores SHAP. Com apenas 200 eventos, modelos muito "
        "flexíveis como o DeepHit correm o risco de sobreajuste, e é possível que não superem o "
        "modelo de Fine e Gray. Esse resultado também será relatado, porque mostra até onde a "
        "complexidade compensa com o volume de dados disponível.")

def build_secao_7(doc):
    add_heading(doc, "8  CONSIDERAÇÕES FINAIS", level=1)

    add_heading(doc, "8.1  Conclusões Parciais", level=2)
    add_body(doc,
        "Os resultados obtidos até esta etapa permitem algumas conclusões. A primeira é que "
        "os pagamentos diários trazem sinais fortes e precoces de abandono: com a informação "
        "disponível no 21º dia do crédito, o modelo de Fine e Gray reúne 81% dos futuros "
        "defaults entre os 10% de clientes de maior risco, cerca de quatro meses antes de a "
        "regra dos 120 dias confirmar a perda. A segunda é que o modelo acrescenta cerca de "
        "8 pontos de captura a regras simples baseadas em uma única variável; o ganho é "
        "moderado, mas se repete em quase todas as partições, o que mostra que combinar vários "
        "sinais compensa.")
    add_body(doc,
        "A terceira conclusão é que o histórico do cliente nos créditos anteriores já informa "
        "sobre o risco no dia do desembolso, reunindo 36% dos futuros defaults entre os 10% de "
        "maior risco, o que abre a possibilidade de apoiar a decisão de conceder ou não um novo "
        "crédito. A quarta é metodológica: como a quitação impede o default, tratá-la como "
        "risco competitivo é necessário, e tratá-la como simples censura superestimaria o "
        "risco. Por fim, a qualidade dos dados exigiu tanto trabalho quanto a modelagem: campos "
        "que mostram o estado do dia da descarga, renegociações e lançamentos contábeis teriam "
        "levado a resultados enganosos sem a auditoria descrita no Capítulo 4.")
    add_body(doc,
        "Essas conclusões ainda são parciais. Elas dependem da validação temporal, da inclusão "
        "das variáveis de contexto e socioeconômicas e da comparação com os modelos de "
        "aprendizado de máquina, previstas para as próximas etapas e descritas a seguir.")

    add_heading(doc, "8.2  Próximos Passos e Cronograma", level=2)
    add_body(doc,
        "O projeto segue estruturado em Sprints Scrum (Louzada Neto, 2026), com entregas "
        "iterativas que permitem ajustes de escopo sem comprometer o prazo final. A entrega "
        "oficial do TCC está prevista para fevereiro de 2027; a meta interna é concluir a "
        "versão final em dezembro de 2026, reservando janeiro e fevereiro de 2027 como "
        "margem para os ajustes solicitados pelo orientador e para os trâmites de entrega. "
        "Os quatro primeiros Sprints estão concluídos, e os três seguintes, de duas semanas "
        "cada, organizam o trabalho restante:")
    sprints = [
        ("Sprint 1 (jan. a mar. 2026), ETL e pipeline [CONCLUÍDO]:",
         "Desenvolvimento do extrator Selenium (AtlasDataExtractor e AtlasMasivoExtractor), "
         "extração de 3.962 arquivos Excel (3 escritórios, 17 rotas, 2020 a 2026), Data Lake "
         "hierárquico (~14 GB), sistema de checkpoint JSON, consolidação da Matriz Mestra "
         "(344.869 linhas e 2.358 colunas) e otimização de memória via chunked loading com máscara NumPy (redução de 49% no uso de RAM)."),
        ("Sprint 2 (mar. a mai. 2026), Feature Engineering e EDA [CONCLUÍDO]:",
         "Primeira versão do dataset de sobrevivência no formato Counting Process, "
         "definição do cronômetro dias_sem_pagar, análise exploratória com figuras de "
         "diagnóstico e elaboração do relatório metodológico (Seções 4 e 5 do TCC)."),
        ("Sprint 3 (jun. a set. 2026), auditoria do target e Riscos Competitivos [CONCLUÍDO]:",
         "Auditoria de integridade do target (§5.8), pivô metodológico para Riscos "
         "Competitivos (§5.9) e baseline Cox cause-specific preliminar. Reconstrução do "
         "dataset a partir dos pagamentos diários (src/reconstruir_dataset.py), que mede o "
         "silêncio de pagamento entre as datas reais dos abonos, fixa o fechamento do "
         "crédito pela data do último abono registrado pelo sistema, recalcula as "
         "covariáveis apenas com informação disponível no início de cada intervalo e exclui "
         "os créditos sem nenhum movimento."),
        ("Sprint 4 (29 set. a 2 nov. 2026), reprocessamento e modelos de base [CONCLUÍDO]:",
         "Blocos de 7 dias (10 dias como análise de sensibilidade), calendário de dias de "
         "cobrança sem domingos nem feriados, histórico do cliente nos créditos anteriores, "
         "exclusão dos vales de funcionários e correção do leakage da parcela de 1 real. "
         "Cox cause-specific tempo-variante e modelo de Fine-Gray em landmark (dias 14 e 21), "
         "com regressão logística como comparação e validação cruzada agrupada por cliente. "
         "Adiantamento a ser enviado à tutora em 8 de novembro de 2026."),
        ("Sprint 5 (9 a 22 nov. 2026), covariáveis de contexto e modelos de comparação [PENDENTE]:",
         "Validação temporal (treino com créditos de 2020 a 2024 e teste com os de 2025 e "
         "2026), prioridade do Sprint; covariáveis macroeconômicas e sociais (Selic, IPCA, desemprego, programas de "
         "transferência de renda e o período da pandemia), com os dias de jogos do Brasil na "
         "Copa de 2022 em análise descritiva; modelo de Fine-Gray com ponderação pela "
         "probabilidade inversa de censura; modelo de fração de cura (mixture cure model), "
         "visto na disciplina de Aprendizado Dinâmico, como comparação; Random Survival "
         "Forest, a partir do conteúdo de florestas aleatórias da disciplina de Aprendizado "
         "de Máquina; submissão de uma versão à autochecagem Turnitin do ICMC até 18 de "
         "novembro de 2026."),
        ("Sprint 6 (23 nov. a 6 dez. 2026), Deep Learning e avaliação comparativa [PENDENTE]:",
         "DeepHit para riscos competitivos, com embeddings de rota e escritório e uma "
         "variante com rede recorrente (LSTM) sobre a sequência diária de pagamentos, "
         "conforme a disciplina de Aprendizado Profundo; comparação de todos os modelos com "
         "C-index dependente do tempo, Brier Score com ponderação pela probabilidade inversa "
         "de censura e porcentagem de defaults capturados entre os 10% de maior risco; "
         "validação temporal e interpretabilidade (SHAP)."),
        ("Sprint 7 (7 a 18 dez. 2026), redação final [PENDENTE]:",
         "Redação de Resultados, Discussão, Conclusão, Limitações e Trabalhos Futuros; "
         "metodologia organizada pelas fases do CRISP-DS e seção curta sobre ética e LGPD; "
         "revisão bibliográfica pelo método de revisão sistemática da literatura; "
         "incorporação completa do feedback da avaliação de Metodologia e Projeto II "
         "(padronização de itálico e pontuação); revisão integral pelo orientador. Marco: "
         "versão final concluída em 18 de dezembro de 2026."),
        ("Margem (jan. a fev. 2027), entrega [PENDENTE]:",
         "Ajustes finais solicitados pelo orientador, atualização da ficha catalográfica, "
         "geração do PDF final e entrega oficial."),
    ]
    for label, text in sprints:
        add_labeled(doc, label, text)

    add_table_data(doc,
        ["Data", "Marco"],
        [["2 nov. 2026",  "Dataset reconstruído e modelos de base (Cox e Fine-Gray)"],
         ["8 nov. 2026",  "Adiantamento enviado à tutora"],
         ["18 nov. 2026", "Versão submetida à autochecagem Turnitin"],
         ["22 nov. 2026", "Covariáveis de contexto, fração de cura e Random Survival Forest"],
         ["6 dez. 2026",  "DeepHit e avaliação comparativa concluídos"],
         ["18 dez. 2026", "Versão final do TCC concluída"],
         ["fev. 2027",    "Entrega oficial"]],
        "Marcos do cronograma de conclusão", table_num=25)


# ── REFERÊNCIAS ───────────────────────────────────────────────────────────────

def build_referencias(doc):
    """Referências conforme ABNT NBR 6023: sem negrito; título do periódico/livro
    (o 'veículo') em itálico; demais elementos em fonte regular."""
    add_heading(doc, "REFERÊNCIAS", level=1)
    refs = [
        [("ABREU, C. Inadimplência de pequenos negócios cai, e aprovação de crédito atinge maior "
          "nível desde 2022. ", False),
         ("Agência Sebrae de Notícias", True),
         (", 15 set. 2026. Disponível em: https://agenciasebrae.com.br/dados/inadimplencia-de-"
          "pequenos-negocios-cai-e-aprovacao-de-credito-atinge-maior-nivel-desde-2022/. "
          "Acesso em: 16 out. 2026.", False)],
        [("ALTMAN, E. I.; SABATO, G. Modeling Credit Risk for SMEs: Evidence from the US Market. ", False),
         ("Abacus", True),
         (", v. 43, n. 3, p. 332-357, 2007.", False)],
        [("ANDERSEN, P. K.; GILL, R. D. Cox's regression model for counting processes: a large "
          "sample study. ", False),
         ("The Annals of Statistics", True),
         (", v. 10, n. 4, p. 1100-1120, 1982.", False)],
        [("ANTHROPIC. ", False),
         ("Claude", True),
         (". Sonnet 5. Large Language Model. San Francisco: Anthropic, 2026. Disponível em: "
          "https://claude.ai/. Acesso em: 4 jul. 2026. Nota: Apoio pontual na formatação ABNT/USP "
          "do documento e em pequenos trechos de código.", False)],
        [("BANERJEE, A. V.; DUFLO, E. The economic lives of the poor. ", False),
         ("Journal of Economic Perspectives", True),
         (", v. 21, n. 1, p. 141-167, 2007.", False)],
        [("BRASIL. Ministério do Empreendedorismo, da Microempresa e da Empresa de Pequeno "
          "Porte. ", False),
         ("Painéis do Mapa de Empresas", True),
         (". Brasília, 2026. Disponível em: https://www.gov.br/empresas-e-negocios/pt-br/"
          "mapa-de-empresas/painel-mapa-de-empresas. Acesso em: 16 out. 2026.", False)],
        [("COX, D. R. Regression models and life-tables. ", False),
         ("Journal of the Royal Statistical Society: Series B (Methodological)", True),
         (", v. 34, n. 2, p. 187-220, 1972.", False)],
        [("FINE, J. P.; GRAY, R. J. A proportional hazards model for the subdistribution of a "
          "competing risk. ", False),
         ("Journal of the American Statistical Association", True),
         (", v. 94, n. 446, p. 496-509, 1999.", False)],
        [("KALBFLEISCH, J. D.; PRENTICE, R. L. ", False),
         ("The Statistical Analysis of Failure Time Data", True),
         (". 2. ed. New York: Wiley, 2002.", False)],
        [("KAPLAN, E. L.; MEIER, P. Nonparametric estimation from incomplete observations. ", False),
         ("Journal of the American Statistical Association", True),
         (", v. 53, n. 282, p. 457-481, 1958.", False)],
        [("KATZMAN, J. L. et al. DeepSurv: personalized treatment recommender system using a Cox "
          "proportional hazards deep neural network. ", False),
         ("BMC Medical Research Methodology", True),
         (", v. 18, n. 24, 2018.", False)],
        [("KIM, Jong-Min. ", False),
         ("Deep Learning in Survival Analysis: Recent Advances and Multimodal Approaches", True),
         (". 2026.", False)],
        [("KLEIN, J. P.; MOESCHBERGER, M. L. ", False),
         ("Survival Analysis: Techniques for Censored and Truncated Data", True),
         (". 2. ed. New York: Springer, 2003.", False)],
        [("LEE, C. et al. DeepHit: a deep learning approach to survival analysis with "
          "competing risks. In: AAAI CONFERENCE ON ARTIFICIAL INTELLIGENCE, 32., 2018, "
          "New Orleans. ", False),
         ("Proceedings [...]", True),
         (" [S.l.]: AAAI Press, 2018. p. 2314-2321.", False)],
        [("LOUZADA NETO, F. ", False),
         ("Gestão de Projetos de Ciência de Dados e Inteligência Artificial", True),
         (". Material didático, MBA em Ciências de Dados. ICMC/USP, São Carlos, 2026.", False)],
        [("MANTEL, N. Evaluation of survival data and two new rank order statistics arising in "
          "its consideration. ", False),
         ("Cancer Chemotherapy Reports", True),
         (", v. 50, n. 3, p. 163-170, 1966.", False)],
        [("SCHREINER, M. Aspects of outreach: a framework for discussion of the social benefits "
          "of microfinance. ", False),
         ("Journal of International Development", True),
         (", v. 14, n. 5, p. 591-603, 2002.", False)],
        [("THERNEAU, T. M.; GRAMBSCH, P. M. ", False),
         ("Modeling Survival Data: Extending the Cox Model", True),
         (". New York: Springer, 2000.", False)],
    ]
    for segments in refs:
        p = doc.add_paragraph()
        _set_spacing(p, multiple=1.0)
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.first_line_indent = Cm(0)
        p.paragraph_format.space_after = Pt(12)
        for text, italic in segments:
            run = p.add_run(text)
            _set_font(run, bold=False, italic=italic)


# ── APÊNDICE A: DETALHE TÉCNICO DO PIPELINE ──────────────────────────────────

def build_apendice_a(doc):
    """Detalhe técnico da extração (antigas seções 4.1 a 4.5 da V26). Saiu do
    corpo do texto a pedido da tutora e da aula de Metodologia: o capítulo 4
    explica o pipeline em linguagem simples e remete a este apêndice."""
    doc.add_page_break()
    add_heading(doc, "APÊNDICE A – Detalhamento técnico do pipeline de extração", level=1,
                maiusculas=False)
    add_body_italico(doc,
        "Este apêndice reúne os detalhes de implementação do pipeline de extração e da "
        "consolidação dos relatórios, resumidos no capítulo 4. O código completo está no "
        "repositório do projeto (pasta src).")

    # ── 3.1 ──────────────────────────────────────────────────────────────────
    add_heading(doc, "A.1  O Sistema ATLAS: Contexto e Barreiras Técnicas da Extração", level=2)
    add_body(doc,
        "O Sistema ATLAS (codinome atribuído neste trabalho por confidencialidade) é a "
        "plataforma de gestão creditícia da instituição parceira. Trata-se de "
        "uma aplicação web desenvolvida em PHP, hospedada em infraestrutura privada, sem "
        "exposição de endpoints REST, GraphQL ou qualquer mecanismo programático de acesso "
        "a dados. O único canal disponível é a interface de usuário no navegador, o que torna "
        "a automação web (web scraping via Selenium) a única alternativa viável para a extração "
        "sistemática do histórico transacional.")
    add_body(doc,
        "A interface do ATLAS impõe seis barreiras técnicas específicas que demandam soluções "
        "individuais, detalhadas na Tabela {tab:1}. Cada barreira representa um ponto de falha "
        "potencial no pipeline: a ausência de qualquer uma das soluções resulta em crash "
        "silencioso do pipeline, extração parcial ou dados corrompidos.")

    add_table_data(doc,
        ["Barreira Técnica", "Causa Raiz", "Solução Implementada"],
        [
            ["Sem API REST",
             "Backend PHP sem endpoints programáticos",
             "Selenium WebDriver + ChromeDriver (webdriver-manager)"],
            ["Frameset aninhado (3 níveis)",
             "página principal, depois frameMenu e por fim frameFormulario",
             "Sequência precisa de switch_to.frame() + switch_to.default_content()"],
            ["Autenticação SELECT2 (fase 2)",
             "Widget jQuery ignora eventos DOM nativos",
             "DOM nativo: sel.value + dispatchEvent('change', {bubbles: true})"],
            ["Menu com tags <op> não-padrão",
             "Tags HTML proprietárias sem suporte is_displayed()",
             "XPath //op[normalize-space()='...'] + JS click via execute_script()"],
            ["Campo de data readonly (datepicker)",
             "jQuery UI bloqueia edição manual do campo",
             "Injeção via JS: arguments[0].value + dispatchEvent('change')"],
            ["Modal bootbox dinâmico",
             "bootbox.js intercepta cliques e bloqueia o formulário",
             "find_elements() (sem exceção se ausente) + JS click no botão de confirmação"],
            ["Download silencioso de múltiplos arquivos",
             "Chrome exige confirmação do usuário por padrão",
             "Chrome prefs: automatic_downloads: 1, prompt_for_download: False"],
        ],
        "Detalhe técnico das soluções da extração",
        table_num=1,
    )

    # ── 3.2 ──────────────────────────────────────────────────────────────────
    add_heading(doc, "A.2  Autenticação Bifásica e Navegação no Frameset Aninhado", level=2)
    add_body(doc,
        "O pipeline de autenticação foi implementado na classe orientada a objetos "
        "AtlasDataExtractor (src/atlas_extractor.py), que encapsula toda a lógica de interação "
        "com o Sistema ATLAS. A autenticação ocorre em duas fases distintas, separadas por uma "
        "transição de estado do servidor que invalida os elementos DOM previamente carregados.")

    add_labeled(doc, "Fase 1, credenciais:",
        "O formulário de login reside dentro de um iframe (frame index 0 de página de autenticação do sistema). "
        "O pipeline utiliza WebDriverWait com expected_conditions para aguardar a disponibilidade de "
        "cada elemento antes de interagir, garantindo tolerância a variações de latência do "
        "servidor. Os campos campoUsuario e campoSenha recebem as credenciais lidas de variáveis de "
        "ambiente (.env), e o botão botaoEntrar é ativado via clique nativo do Selenium.")

    add_labeled(doc, "Fase 2, seleção de rota (SELECT2):",
        "Após validar as credenciais, o servidor renderiza um segundo formulário com um dropdown "
        "SELECT2 (biblioteca jQuery) para seleção da rota. O SELECT2 ignora completamente eventos "
        "DOM nativos como 'input' ou 'change' disparados por Selenium; o widget escuta apenas "
        "eventos jQuery internos. A solução implementada é a injeção direta de JavaScript que "
        "escreve o valor no elemento <select> subjacente e dispara um evento 'change' nativo com "
        "propagação (bubbles: true), contornando o interceptor jQuery:")

    add_code(doc,
        "# SELECT2 ignora eventos Selenium; usa-se DOM nativo com dispatchEvent\n"
        "driver.execute_script(\"\"\"\n"
        "    var sel = document.getElementById('campoRota');\n"
        "    sel.value = arguments[0];\n"
        "    sel.dispatchEvent(new Event('change', {bubbles: true}));\n"
        "\"\"\", valor_ruta)"
    )

    add_body(doc,
        "Após a seleção da rota, o servidor exibe um modal de boas-vindas (bootbox.js) que bloqueia "
        "qualquer interação com o formulário subjacente. O tratamento utiliza find_elements() (que "
        "retorna lista vazia em vez de lançar exceção) em vez de find_element(), evitando crash "
        "quando o modal está ausente. O clique no botão de confirmação é realizado via JS para "
        "garantir que interceptores DOM não interfiram. Após o fechamento do modal, o pipeline retorna "
        "ao contexto padrão (switch_to.default_content()) e aguarda o carregamento do frameset "
        "principal antes de prosseguir.")

    add_body(doc,
        "A navegação ao formulário de extração segue uma sequência rígida de troca de contexto "
        "de frame, pois a arquitetura do Sistema ATLAS utiliza frameset aninhado em três níveis. "
        "A Tabela {tab:2} documenta a sequência exata implementada no método _navegar_ao_relatorio_pagamentos().")

    add_table_data(doc,
        ["Passo", "Operação Selenium", "Frame / Elemento Alvo", "Finalidade"],
        [
            ["1", "switch_to.default_content()", "Contexto raiz do navegador", "Resetar contexto após qualquer operação anterior"],
            ["2", "switch_to.frame(0)", "página principal do sistema (frame raiz)", "Entrar no frameset raiz do sistema"],
            ["3", "frame_to_be_available_and_switch_to_it('frameMenu')", "frameMenu (menu lateral)", "Acessar o menu de navegação"],
            ["4", "JS click: //op[normalize-space()='Reportes']", "Tag <op> do menu", "Expandir o submenu de relatórios"],
            ["5", "JS click: //op[normalize-space()='Recaudador']", "Tag <op> do submenu", "Expandir o submenu de cobrança"],
            ["6", "JS click: //a[contains(@href,'RelatorioPagamentos')]", "Link do relatório", "Carregar o formulário de extração no frameFormulario"],
            ["7", "switch_to.default_content() e depois switch_to.frame(0)", "De volta ao frame raiz", "Preparar para entrar no frameFormulario"],
            ["8", "frame_to_be_available_and_switch_to_it('frameFormulario')", "frameFormulario (formulário)", "Acessar o formulário de extração"],
            ["9", "Select(campoOficina).select_by_value()", "Dropdown de oficina", "Configurar filtro estático de escritório"],
            ["10", "Select(campoRota).select_by_value()", "Dropdown de rota", "Configurar filtro estático de rota (após AJAX)"],
        ],
        "Sequência de navegação no frameset aninhado do Sistema ATLAS",
        table_num=2,
    )

    add_body(doc,
        "Os filtros de escritório e rota (campoOficina e campoRota) são configurados uma única vez "
        "antes do início do laço de extração batch, pois permanecem constantes para toda a "
        "sequência temporal de uma rota. A seleção da oficina dispara uma chamada AJAX que "
        "repopula o dropdown campoRota; o pipeline aguarda a presença da opção correta com "
        "lambda WebDriverWait antes de prosseguir, garantindo sincronização com o servidor.")

    # ── 3.3 ──────────────────────────────────────────────────────────────────
    add_heading(doc, "A.3  Extração Batch: Paginação Temporal e Filtro Anti-Zero", level=2)
    add_body(doc,
        "O Sistema ATLAS restringe cada extração a uma janela de exatamente 10 dias calendário. "
        "Para cobrir o horizonte histórico completo de 2020 a 2026 (~2.327 dias), o pipeline "
        "implementa um cursor temporal que avança em blocos estritos de 10 dias, gerando "
        "aproximadamente 233 iterações por rota e 3.961 iterações no total corporativo.")

    add_labeled(doc, "Early-exit [YA EXISTE]:",
        "Antes de qualquer interação com o DOM, o pipeline verifica se o arquivo "
        "relatorio_pagamentos_YYYYMMDD_YYYYMMDD.xlsx já existe no diretório de destino. Se existir, "
        "o bloco é saltado completamente sem abrir o formulário, permitindo retomada eficiente "
        "de sessões interrompidas sem reprocessamento.")

    add_labeled(doc, "Injeção de data (datepicker bypass):",
        "O campo campoDataInicial é marcado como readonly pelo jQuery UI datepicker, impedindo "
        "qualquer edição via Selenium send_keys(). A solução injeta o valor diretamente no "
        "elemento DOM via JavaScript e dispara o evento 'change' para ativar os listeners "
        "do formulário:")

    add_code(doc,
        "# Campo readonly: injetar valor via JS e disparar evento change\n"
        "driver.execute_script(\"\"\"\n"
        "    arguments[0].value = arguments[1];\n"
        "    arguments[0].dispatchEvent(new Event('change', {bubbles: true}));\n"
        "\"\"\", campo_fecha, cursor.strftime('%Y-%m-%d'))"
    )

    add_labeled(doc, "Filtro anti-zero (visualizadorRelatorio):",
        "Após pressionar botaoConfirmar, o servidor processa a consulta e renderiza um PDF "
        "embebido no elemento <object id='visualizadorRelatorio'>. Quando o período consultado "
        "não contém atividade para a rota (rota inativa naquele intervalo), o objeto "
        "permanece oculto (display: none) ou com atributo data vazio. O pipeline valida a "
        "presença de dados antes de tentar o download:")

    add_code(doc,
        "# Validar presença de dados antes de baixar\n"
        "obj = driver.find_element(By.ID, 'visualizadorRelatorio')\n"
        "tem_dados = (\n"
        "    '.pdf' in (obj.get_attribute('data') or '') and\n"
        "    'inline-block' in (obj.get_attribute('style') or '')\n"
        ")\n"
        "if not tem_dados:\n"
        "    cursor += timedelta(days=10)  # [SKIP] rota inativa"
    )

    add_body(doc,
        "Este filtro anti-zero é crítico para a integridade estatística do dataset: sem ele, "
        "blocos sem atividade gerariam arquivos Excel vazios que, ao serem consolidados na "
        "Matriz Mestra, introduziriam zeros espúrios nas colunas de pagamento e distorceriam "
        "o cronômetro dias_sem_pagar, gerando falsos positivos no evento de default.")

    add_labeled(doc, "Monitoramento de download e renomeação semântica:",
        "Após pressionar botaoExportar, o Chrome inicia o download para a pasta staging "
        "(data/raw/). O pipeline monitora a pasta em loop de 1 segundo, detectando o "
        "arquivo .crdownload (parcial) e aguardando seu desaparecimento antes de renomear "
        "o xlsx completo para o padrão relatorio_pagamentos_YYYYMMDD_YYYYMMDD.xlsx. Este padrão "
        "de nomenclatura incorpora as datas de início e fim do bloco, viabilizando a extração "
        "automática de metadados temporais durante o Data Stitching.")

    # ── 3.4 ──────────────────────────────────────────────────────────────────
    add_heading(doc, "A.4  Escalabilidade Corporativa: Auto-Discovery, Data Lake Hierárquico e Resiliência", level=2)
    add_body(doc,
        "Para escalar o pipeline piloto (uma rota) para o universo corporativo completo (17 "
        "rotas em 3 escritórios), foi desenvolvida a classe AtlasMasivoExtractor "
        "(src/atlas_masivo.py), que herda toda a infraestrutura de AtlasDataExtractor e "
        "adiciona quatro capacidades fundamentais: auto-discovery do mapa corporativo, "
        "organização hierárquica do Data Lake, tratamento de erros de elemento obsoleto "
        "(StaleElementReferenceException) e sistema de checkpoint para resiliência a falhas.")

    add_labeled(doc, "Auto-Discovery do mapa corporativo:",
        "O método _descobrir_mapa_rotas() lê dinamicamente todas as opções dos dropdowns "
        "campoOficina e campoRota diretamente do DOM do formulário. Para cada escritório detectado, "
        "dispara uma mudança de valor no select (via JavaScript) que aciona a chamada AJAX de "
        "repopulação do dropdown de rotas, coletando os IDs de todas as rotas disponíveis. "
        "Este mecanismo elimina a necessidade de manutenção manual de um catálogo de rotas e "
        "garante que novas rotas adicionadas pela instituição sejam automaticamente incluídas "
        "em extrações futuras.")

    add_body(doc,
        "O mapa corporativo identificado automaticamente pelo Auto-Discovery compreende três "
        "escritórios e 17 rotas geográficas, conforme documentado na Tabela {tab:3}.")

    add_table_data(doc,
        ["Escritório", "ID", "Região", "Rotas (IDs)", "Total"],
        [
            ["OFI_23 (São Paulo)",       "23", "São Paulo / Grande SP",
             "82, 96, 423, 136, 367, 448, 494", "7"],
            ["OFI_31 (Sociedades Brasil)","31", "Interior e Sul do Brasil",
             "415, 68, 338, 347, 389", "5"],
            ["OFI_44 (Cabo Frio)",        "44", "Região dos Lagos / RJ",
             "114, 439, 396, 420, 511", "5"],
        ],
        "Mapa corporativo detectado pelo Auto-Discovery: escritórios e rotas do Sistema ATLAS",
        table_num=3,
    )

    add_labeled(doc, "Organização hierárquica do Data Lake:",
        "Os arquivos extraídos são organizados em uma hierarquia de diretórios que reflete "
        "a topologia corporativa do sistema: data/raw/OFI_{id_oficina}/RTA_{id_ruta}/. "
        "O Chrome baixa cada arquivo inicialmente para data/raw/ (staging area) e o pipeline "
        "move o xlsx renomeado para o subdiretório correspondente via shutil.move(). "
        "Esta estrutura garante rastreabilidade completa (Data Lineage): dado qualquer arquivo, "
        "é possível identificar imediatamente a qual escritório, rota e período temporal "
        "ele pertence, apenas pelo caminho e nome do arquivo.")

    add_table_data(doc,
        ["Métrica", "Valor"],
        [
            ["Arquivos Excel baixados",        "3.962 arquivos"],
            ["Escritórios cobertos",           "3 (OFI_23, OFI_31, OFI_44)"],
            ["Rotas cobertas",                 "17"],
            ["Período de cobertura",           "2020-01-01 a 2026-05-15 (~6,4 anos)"],
            ["Blocos temporais por rota",      "~233 blocos de 10 dias"],
            ["Tamanho total do Data Lake",     "~14 GB"],
            ["Pausa entre rotas",              "10 segundos (limpeza de cache do navegador)"],
        ],
        "Volumetria final do Data Lake extraído",
        table_num=4,
    )

    add_labeled(doc, "Tratamento de StaleElementReferenceException:",
        "O Sistema ATLAS realiza re-renderizações parciais do DOM durante transições entre "
        "rotas (o AJAX de campoRota pode não ter terminado quando o SELECT já foi localizado). "
        "O pipeline implementa até 3 tentativas com pausa de 3 segundos entre cada uma para "
        "o método _seleccionar_oficina_y_ruta(), que renavega ao formulário desde o menu "
        "lateral a cada tentativa, garantindo um estado DOM fresco.")

    add_labeled(doc, "Sistema de Checkpoint JSON:",
        "O arquivo oculto .checkpoint.json em data/raw/ persiste o estado da extração após "
        "cada bloco temporal bem-sucedido. Na inicialização, o pipeline lê o checkpoint e "
        "retoma exatamente do último ponto processado, saltando as rotas já completadas. "
        "Ao concluir a maratón completa, o arquivo é deletado automaticamente.")

    add_table_data(doc,
        ["Campo JSON", "Tipo", "Exemplo", "Descrição"],
        [
            ["id_oficina", "String", '"44"',         "ID do escritório em extração"],
            ["id_ruta",    "String", '"114"',        "ID da rota em extração"],
            ["fecha",      "String", '"2023-07-15"', "Última data de início de bloco processada com sucesso"],
        ],
        "Estrutura do arquivo de controle da extração",
        table_num=5,
    )

    # ── 3.5 ──────────────────────────────────────────────────────────────────
    add_heading(doc, "A.5  Consolidação da Matriz Mestra e Otimização de Memória (Data Stitching)", level=2)
    add_body(doc,
        "O script consolidar_datos.py implementa o processo de Data Stitching, que transforma "
        "os 3.962 arquivos Excel fragmentados do Data Lake em um único painel longitudinal "
        "contínuo: a Matriz Mestra (Silver Layer). O processo percorre recursivamente a "
        "hierarquia data/raw/OFI_*/RTA_*/*.xlsx, extraindo dois tipos de metadados diretamente "
        "do sistema de arquivos, sem necessidade de parsing do conteúdo dos arquivos:")

    add_labeled(doc, "Metadados topológicos (do caminho do arquivo):",
        "O identificador de escritório (ofi_id) e o identificador de rota (rta_id) são "
        "extraídos do caminho relativo por expressão regular sobre os componentes do "
        "Path. Estes metadados são injetados como colunas adicionais em cada linha do "
        "arquivo correspondente, viabilizando análises estratificadas por escritório e "
        "rota no modelo de Cox sem necessidade de joins posteriores.")

    add_labeled(doc, "Metadados temporais (do nome do arquivo):",
        "As datas de início e fim do bloco de 10 dias são extraídas do nome do arquivo "
        "pelo padrão relatorio_pagamentos_YYYYMMDD_YYYYMMDD.xlsx via expressão regular "
        r"(\d{8})_(\d{8})\.xlsx. Estas datas são utilizadas durante a Feature Engineering "
        "para calcular a máscara de pagamentos do bloco e o cronômetro dias_sem_pagar.")

    add_body(doc,
        "O resultado do Data Stitching é a Matriz Mestra, cujas dimensões e características "
        "são documentadas na Tabela {tab:6}. A estrutura matricial tem os créditos como linhas e "
        "as datas calendário de 2020-01-01 a 2026-05-15 (~2.330 datas) como colunas, "
        "com os valores de pagamento diário (abonos) preenchendo a interseção.")

    add_table_data(doc,
        ["Dimensão / Métrica", "Valor"],
        [
            ["Linhas (observações de crédito)", "344.869"],
            ["Colunas totais",                   "2.358"],
            ["Colunas de pagamentos diários",    "~2.330 (datas 2020-01-01 a 2026-05-15)"],
            ["Colunas estáticas do crédito",     "28 (CÓDIGO CRÉDITO, SALDO, CUOTAS PACTADAS, etc.)"],
            ["Tamanho em disco (CSV comprimido)","882 MB"],
            ["Tamanho em RAM (expandido, float64)","~6 GB"],
            ["Redução RAM por downcasting",       "~49% (float32 + categorização de strings)"],
            ["arquivo_origen (coluna de rastreabilidade)", "OFI_{id}/RTA_{id}/planilla_abonos_*.xlsx"],
        ],
        "Dimensões da Matriz Mestra após consolidação (Data Stitching)",
        table_num=6,
    )

    add_body(doc,
        "O tamanho em RAM de ~6 GB impossibilita a carga completa da Matriz Mestra com "
        "pd.read_csv() padrão em máquinas com menos de 16 GB de memória disponível. O "
        "pipeline de Feature Engineering (src/feature_engineering.py) resolve este "
        "problema mediante leitura em chunks com máscara NumPy vetorizada, descrita a seguir.")

    add_labeled(doc, "Chunked loading com máscara NumPy vetorizada:",
        "O pipeline lê a Matriz Mestra em blocos de 5.000 linhas por vez (chunksize=5000), "
        "processando os agregados de pagamento de cada bloco em memória e descartando as "
        "~2.330 colunas de data antes de concatenar. O cálculo dos agregados "
        "(pago_promedio_diario, dias_con_abono) utiliza broadcasting NumPy para criar uma "
        "máscara binária (n_linhas por n_colunas_pagamento) que seleciona apenas as colunas "
        "de data dentro do intervalo do bloco, sem loop Python:")

    add_code(doc,
        "# Máscara vetorizada (n_linhas por n_colunas_pago), sem loop Python\n"
        "ini_arr   = ini.values[:, np.newaxis]    # shape: (5000, 1)\n"
        "fin_arr   = fin.values[:, np.newaxis]    # shape: (5000, 1)\n"
        "dates_arr = pago_dates.values[np.newaxis, :]  # shape: (1, 2330)\n"
        "\n"
        "# Broadcasting: compara cada linha com todas as datas simultaneamente\n"
        "mascara = (dates_arr >= ini_arr) & (dates_arr <= fin_arr)  # (5000, 2330)\n"
        "\n"
        "pagos_bloque       = pagos_vals * mascara\n"
        "pago_promedio      = pagos_bloque.sum(axis=1) / n_dias_bloque\n"
        "dias_com_abono     = (pagos_bloque > 0).sum(axis=1)"
    )

    add_table_data(doc,
        ["Parâmetro", "Valor", "Justificativa"],
        [
            ["Chunk size",              "5.000 linhas",  "Equilíbrio entre velocidade e consumo de RAM (~100 MB/chunk)"],
            ["Colunas de pagamento",    "~2.330",         "Datas 2020-01-01 a 2026-05-15 detectadas pelo header scan"],
            ["Shape da máscara",        "(5000 por 2330)", "Broadcasting NumPy, operação vetorizada sem loop Python"],
            ["Throughput",              "~5.000 linhas/s","Medido em hardware com 8 GB RAM / CPU 4 núcleos"],
            ["RAM pico por chunk",      "~100 MB",        "Máscara booleana float32 + dados de pagamento"],
            ["Tempo total de leitura",  "~70 segundos",   "Para 344.869 linhas e 2.358 colunas"],
        ],
        "Estratégia de chunked loading com máscara NumPy vetorizada",
        table_num=7,
    )



# ── MAIN ──────────────────────────────────────────────────────────────────────

def _montar(registro_anterior):
    """Monta o documento. As listas e o sumário usam o registro da passada
    anterior (o desta passada só fica completo ao final)."""
    for k in ("titulos", "figuras", "tabelas"):
        REGISTRO[k] = list(registro_anterior[k])
    REGISTRO["texto_corpo"] = registro_anterior.get("texto_corpo", "")
    REGISTRO["ativo"] = False
    NUMEROS.clear()
    NUMEROS.update(registro_anterior.get("numeros", {}))
    CONTADOR.update({"tab": 0, "fig": 0})
    doc = Document()
    configure_doc(doc)

    build_capa(doc)
    build_folha_rosto(doc)
    build_ficha_catalografica(doc)
    build_dedicatoria(doc)
    build_resumo(doc)
    build_abstract(doc)
    build_listas(doc)
    build_sumario(doc)

    build_secao_1(doc)
    build_secao_2_revisao_bibliografica(doc)
    build_secao_2(doc)
    build_secao_3(doc)
    build_secao_4(doc)
    build_capitulo_6(doc)
    build_capitulo_7(doc)
    build_secao_7(doc)
    build_referencias(doc)
    build_apendice_a(doc)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUTPUT)
    corpo = [p.text for p in doc.paragraphs[REGISTRO["inicio_corpo"]:]]
    corpo += [c.text for t in doc.tables for row in t.rows for c in row.cells]
    registro = {k: list(REGISTRO[k]) for k in ("titulos", "figuras", "tabelas")}
    registro["texto_corpo"] = "\n".join(corpo)
    registro["numeros"] = dict(NUMEROS)
    return registro


def _pdf(docx_path, pasta):
    subprocess.run(["libreoffice", "--headless", "--convert-to", "pdf", "--outdir",
                    str(pasta), str(docx_path)], capture_output=True, check=True)
    return Path(pasta) / (Path(docx_path).stem + ".pdf")


def _ler_paginas(pdf, registro):
    """Procura no PDF a página de cada título, figura e tabela. A página exibida
    é a física menos 1, porque a capa não é contada."""
    n = int(re.search(r"Pages:\s+(\d+)", subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True).stdout).group(1))
    textos = [re.sub(r"\s+", " ", subprocess.run(["pdftotext", "-f", str(i), "-l", str(i), str(pdf), "-"],
        capture_output=True, text=True).stdout) for i in range(1, n + 1)]

    def norm(t):
        return re.sub(r"\s+", " ", t).strip()

    # O corpo começa na página da Introdução que vem depois do sumário.
    sumario = next(i for i, t in enumerate(textos) if "SUMÁRIO" in t)
    paginas, atual = {("total", 0): str(n)}, sumario + 1
    for i, (_, titulo) in enumerate(registro["titulos"]):
        alvo = norm(titulo)[:40]
        for j in range(atual, n):
            if alvo in textos[j]:
                paginas[("titulo", i)] = str(j)  # índice 0-based = física - 1
                atual = j
                break
    for tipo, rotulo in (("figura", "Figura"), ("tabela", "Tabela")):
        atual = sumario + 1
        for num, _ in registro[tipo + "s"]:
            padrao = re.compile(rf"(^| ){rotulo} {num} – ")
            for j in range(atual, n):
                if padrao.search(textos[j]):
                    paginas[(tipo, num)] = str(j)
                    atual = j
                    break
    return paginas


def build_doc():
    # 1ª passada: só descobre títulos, figuras e tabelas.
    registro = _montar({"titulos": [], "figuras": [], "tabelas": []})
    # 2ª passada: sumário e listas completos, ainda sem páginas; gera o PDF.
    PAGINAS.clear()
    registro = _montar(registro)
    with tempfile.TemporaryDirectory() as tmp:
        PAGINAS.update(_ler_paginas(_pdf(OUTPUT, tmp), registro))
    # 3ª passada: versão final com os números de página.
    _montar(registro)
    faltando = (len(registro["titulos"]) + len(registro["figuras"])
                + len(registro["tabelas"]) - len(PAGINAS) + 1)
    print(f"\n[PT] V27 gerado: {OUTPUT}")
    print(f"     Sumário: {len(registro['titulos'])} títulos | figuras: "
          f"{len(registro['figuras'])} | tabelas: {len(registro['tabelas'])} | "
          f"sem página encontrada: {faltando}")


if __name__ == "__main__":
    build_doc()

    es_script = Path(__file__).parent / "gerar_tcc_v27_es.py"  # ainda não criado — sync ES pendente
    if es_script.exists():
        print("\n[ES] Gerando versão em Espanhol...")
        result = subprocess.run([sys.executable, str(es_script)], capture_output=True, text=True)
        print(result.stdout)
        if result.returncode != 0:
            print("ERRO:", result.stderr)
