"""
gerar_tcc_v23.py — Gerador do TCC V23 (Português).

Novidades vs. V22:
  - Nova §2 REVISÃO BIBLIOGRÁFICA (4 subseções), exigida pela Avaliação de
    "Metodologia e Projeto para Ciências de Dados II"
  - Renumeração em cadeia dos capítulos 2→8 (Objetivos, ETL, Engenharia de
    Variáveis, Modelagem, Validação, Cronograma)
  - Referências corrigidas conforme NBR 6023 (sem negrito, itálico no veículo)
  - Capa e Folha de Rosto separadas (NBR 14724), com o texto formal de
    apresentação da monografia; página reservada para Ficha Catalográfica
  - Citação NBR 6028 no Resumo/Abstract corrigida (sobrenome + iniciais)
  - Nova LISTA DE SÍMBOLOS
  - Capa com o fundo oficial USP/ICMC (imagem), corrigido tamanho de página
    para A4 (estava em Carta/Letter)

Output: documentotcc/Projeto_Pesquisa_TCC_V23_Completo.docx
"""

from pathlib import Path
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.enum.section import WD_SECTION
import subprocess, sys, io

BASE   = Path(__file__).parent.parent
OUTPUT = BASE / "documentotcc" / "Projeto_Pesquisa_TCC_V23_Completo.docx"
ASSETS = BASE / "documentotcc" / "assets"
REPORTS = BASE / "reports"


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


def add_figure(doc, img_path, caption, fig_num):
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
    cap.paragraph_format.space_after       = Pt(12)
    r = cap.add_run(f"Figura {fig_num} – {caption}")
    _set_font(r, size=10, italic=True)


def add_labeled(doc, label, text):
    """Parágrafo com label em negrito seguido de texto normal."""
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


def _limpar_texto_lateral(im, scale):
    """Mesma limpeza por contornos de `_limpar_texto_icmc`, aplicada à faixa
    lateral cinza ('UNIVERSIDADE DE SÃO PAULO / Instituto de Ciências
    Matemáticas e de Computação') — texto azul-marinho escuro sobre fundo
    cinza-claro, o inverso do caso ICMC (texto claro sobre fundo escuro)."""
    import numpy as np
    import cv2
    from PIL import Image

    CROP = (66, 0, 219, 1190)  # faixa cinza lateral, no PNG original
    VSCALE = 8
    COR_TEXTO = (22, 62, 94)  # azul-marinho já usado no resto da arte

    orig = Image.open(ASSETS / "capa_fundo_usp_icmc.png").convert("RGB")
    crop_arr = np.array(orig)[CROP[1]:CROP[3], CROP[0]:CROP[2]]
    gray = cv2.cvtColor(crop_arr, cv2.COLOR_RGB2GRAY)
    # texto é mais escuro que o fundo cinza-claro: threshold invertido
    _, mask = cv2.threshold(gray, 120, 255, cv2.THRESH_BINARY_INV)
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

    h, w = crop_arr.shape[:2]
    canvas = np.zeros((h * VSCALE, w * VSCALE), dtype=np.uint8)
    for i, cnt in enumerate(contours):
        if len(cnt) < 3:
            continue
        sm_scaled = (smooth_contour(cnt) * VSCALE).astype(np.int32).reshape(-1, 1, 2)
        color = 255 if hierarchy[0][i][3] == -1 else 0
        cv2.drawContours(canvas, [sm_scaled], -1, color, thickness=cv2.FILLED,
                          lineType=cv2.LINE_AA)

    mask_img = Image.fromarray(canvas).resize((w * scale, h * scale), Image.LANCZOS)
    cor = Image.new("RGB", mask_img.size, COR_TEXTO)
    dest = (CROP[0] * scale, CROP[1] * scale)
    im.paste(cor, dest, mask_img)


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
    _limpar_texto_lateral(im, SCALE)
    draw = ImageDraw.Draw(im)

    title_box = (250 * SCALE, 222 * SCALE, 838 * SCALE, 463 * SCALE)
    _fit_wrapped_text(draw, TITULO_TRABALHO, title_box, BOLD, max_size=52)

    author_box = (305 * SCALE, 480 * SCALE, 839 * SCALE, 535 * SCALE)
    subtitle_box = (305 * SCALE, 535 * SCALE, 839 * SCALE, 585 * SCALE)
    _fit_wrapped_text(draw, "Juan Fernando Graciano Pinzón", author_box, BOLD, max_size=36)
    _fit_wrapped_text(draw, "Monografia — MBA em Ciência de Dados (CeMEAI)",
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
        "Monografia apresentada ao Centro de Ciências Matemáticas Aplicadas à Indústria "
        "do Instituto de Ciências Matemáticas e de Computação, Universidade de São Paulo "
        "- ICMC/USP, como parte dos requisitos para obtenção do título de Especialista "
        "em Ciência de Dados.")
    _set_font(run, size=12)

    doc.add_paragraph()
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.left_indent = Cm(8)
    _set_spacing(p, multiple=1.0)
    run = p.add_run("Área de concentração: Ciência de Dados")
    _set_font(run, size=12)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.left_indent = Cm(8)
    _set_spacing(p, multiple=1.0)
    run = p.add_run("Orientador: Prof. Dr. Vicente Garibay Cancho")
    _set_font(run, size=12)

    for _ in range(6): add_centered(doc, "", size=12, spacing=1.0)
    add_centered(doc, "São Paulo / São Carlos, 2026", size=11, spacing=1.0)
    page_break(doc)


def build_ficha_catalografica(doc):
    """Página reservada à Ficha Catalográfica (elemento obrigatório, verso da
    Folha de Rosto). Deve ser gerada pelo sistema oficial da Biblioteca do ICMC
    e colada aqui antes da submissão final — não pode ser redigida pelo autor."""
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


def build_dedicatoria(doc):
    """DEDICATÓRIA (elemento opcional, NBR 14724)."""
    add_centered(doc, "DEDICATÓRIA", size=14, bold=True, spacing=1.0)
    for _ in range(14): add_centered(doc, "", size=12, spacing=1.0)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _set_spacing(p, multiple=1.5)
    run = p.add_run(
        "À minha mãe, pelo exemplo de força e amor que me acompanha em cada etapa da vida.")
    _set_font(run, size=12, italic=True)
    doc.add_paragraph()
    p2 = doc.add_paragraph()
    p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _set_spacing(p2, multiple=1.5)
    run2 = p2.add_run(
        "Aos meus filhos, Juan José Graciano e Matías Graciano, razão maior de cada "
        "esforço e de cada conquista.")
    _set_font(run2, size=12, italic=True)
    page_break(doc)


def build_resumo(doc):
    add_heading(doc, "RESUMO", level=1)
    add_body(doc,
        "GRACIANO PINZÓN, J. F. Modelagem de Risco de Crédito Dinâmico para "
        "Microempreendedores: Uma Abordagem via Análise de Sobrevivência em Fluxos de Alta "
        "Frequência sob Censura. 2026. Trabalho de Conclusão de Curso – MBA em Ciência de Dados, "
        "Instituto de Ciências Matemáticas e de Computação, Universidade de São Paulo, "
        "São Paulo/São Carlos, 2026.", indent_first=False)
    doc.add_paragraph()
    add_body(doc,
        "A concessão de crédito para o segmento de microempreendedores no Brasil enfrenta severa "
        "assimetria de informação, com modelos tradicionais baseados em dados estáticos que ignoram "
        "a dinâmica de pagamento em tempo real. Esta pesquisa desenvolve um modelo preditivo de risco "
        "de crédito dinâmico utilizando Análise de Sobrevivência com covariáveis dependentes do tempo, "
        "fundamentado em dados de alta frequência de uma instituição de microcrédito de pagamento "
        "diário. Um pipeline de extração automatizado (RPA com Selenium WebDriver) superou as barreiras "
        "técnicas do Sistema ATLAS — sem API REST, frameset aninhado, SELECT2, datepicker readonly e "
        "modais dinâmicos — coletando 3.962 planilhas Excel de três escritórios e 17 rotas no período "
        "2020–2026, totalizando ~14 GB de dados brutos. O Data Stitching consolidou os snapshots em "
        "uma Matriz Mestra de 344.869 linhas × 2.358 colunas (882 MB em disco, ~6 GB em RAM), "
        "processada em chunks de 5.000 linhas com máscara NumPy vetorizada (n_linhas × n_colunas_pagamento) "
        "para evitar erros de Out-of-Memory. Após engenharia de características no formato Counting Process "
        "(Anderson e Gill, 1982), o dataset de sobrevivência final contém 28.386 créditos únicos, 301.434 "
        "intervalos temporais e 425 eventos de castigo de carteira (taxa de inadimplência de 1,50%), "
        "com o evento definido como dias_sem_pagar ≥ 120 dias calendário. A análise exploratória revelou "
        "que a curva de Kaplan-Meier cai de S(t) = 1,0 para S(180) = 0,68 e S(365) = 0,17. A etapa "
        "seguinte compreende o ajuste do Modelo de Cox e a implementação de arquiteturas DeepSurv, "
        "com comparação via C-index de Harrell.", indent_first=False)
    p = doc.add_paragraph()
    _set_spacing(p)
    run = p.add_run(
        "Palavras-chave: análise de sobrevivência; microcrédito; Modelo de Cox; DeepSurv; "
        "alta frequência; processo de contagem; inadimplência; RPA; ETL.")
    _set_font(run)
    page_break(doc)


def build_abstract(doc):
    add_heading(doc, "ABSTRACT", level=1)
    add_body(doc,
        "GRACIANO PINZÓN, J. F. Dynamic Credit Risk Modeling for Microentrepreneurs: "
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
    # Lista de Ilustrações
    add_heading(doc, "LISTA DE ILUSTRAÇÕES", level=1)
    figs = [
        ("1",  "Distribuição do evento de default: proporção, taxa por escritório e por rota"),
        ("2",  "Curva de Kaplan-Meier global do portfólio com tabela de n em risco"),
        ("3",  "Curvas de Kaplan-Meier por escritório com teste de log-rank"),
        ("4",  "Distribuição do tempo de seguimento (t_stop) e número de intervalos por crédito"),
        ("5",  "Distribuição de dias_sem_pagar: global, zoom 0–150 dias e máximo por crédito"),
        ("6",  "Distribuição das covariáveis: Default (E=1) versus Censurado (E=0)"),
        ("7",  "Perfil econômico do portfólio: prazo, montante e boxplot por evento"),
        ("8",  "Mapa de calor de correlações das covariáveis do modelo de sobrevivência"),
        ("9",  "Trajetórias individuais: 5 créditos em default versus 5 censurados"),
    ]
    for num, desc in figs:
        p = doc.add_paragraph()
        _set_spacing(p, multiple=1.0)
        p.paragraph_format.first_line_indent = Cm(0)
        run = p.add_run(f"Figura {num} – {desc}")
        _set_font(run, size=12)
    page_break(doc)

    # Lista de Tabelas — V22 tem 21 tabelas
    add_heading(doc, "LISTA DE TABELAS", level=1)
    tabs = [
        ("1",  "Barreiras técnicas do Sistema ATLAS e soluções implementadas"),
        ("2",  "Sequência de navegação no frameset aninhado do Sistema ATLAS"),
        ("3",  "Mapa corporativo detectado: escritórios e rotas do Sistema ATLAS"),
        ("4",  "Volumetria final do Data Lake extraído"),
        ("5",  "Estrutura do arquivo de checkpoint JSON de resiliência"),
        ("6",  "Dimensões da Matriz Mestra após consolidação (Data Stitching)"),
        ("7",  "Estratégia de chunked loading com máscara NumPy vetorizada"),
        ("8",  "Conformidade LGPD e governança de dados no pipeline ETL"),
        ("9",  "Filtro de coorte diária: critério e créditos retidos"),
        ("10", "Variáveis de tempo e evento do dataset de sobrevivência"),
        ("11", "Covariáveis tempo-variantes e suas fórmulas"),
        ("12", "Covariáveis estáticas do modelo"),
        ("13", "Caracterização geral do dataset de sobrevivência"),
        ("14", "Taxa de default por escritório"),
        ("15", "Valores da curva de Kaplan-Meier global"),
        ("16", "Resultado do teste de log-rank (OFI_23 vs. OFI_44)"),
        ("17", "Estatísticas do tempo de seguimento e intervalos por crédito"),
        ("18", "Estatísticas do cronômetro dias_sem_pagar"),
        ("19", "Correlações das covariáveis com o evento"),
        ("20", "Montante do crédito por grupo de evento"),
        ("21", "Validação do formato Counting Process"),
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
        ("DOM",     "Document Object Model"),
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

    # Lista de Símbolos
    add_heading(doc, "LISTA DE SÍMBOLOS", level=1)
    simbolos = [
        ("S(t)",  "Função de sobrevivência: probabilidade de o evento não ter ocorrido até t"),
        ("h(t)",  "Função de risco (hazard): taxa instantânea de ocorrência do evento no tempo t"),
        ("H(t)",  "Função de risco acumulado (cumulative hazard function)"),
        ("F(t)",  "Função de distribuição acumulada do tempo até o evento T"),
        ("T",     "Variável aleatória tempo até o evento"),
        ("t_start, t_stop", "Limites inferior e superior de um intervalo no formato Counting Process"),
        ("δ (delta)", "Indicador de evento no intervalo (1 = evento; 0 = censura)"),
        ("E_i",   "Indicador de default do crédito i (variável evento)"),
        ("Ŝ(t)",  "Estimador de Kaplan-Meier da função de sobrevivência"),
        ("p",     "Valor-p do teste de hipótese (ex.: teste de log-rank)"),
        ("r",     "Coeficiente de correlação linear de Pearson"),
    ]
    for simbolo, desc in simbolos:
        p = doc.add_paragraph()
        _set_spacing(p, multiple=1.0)
        p.paragraph_format.first_line_indent = Cm(0)
        run = p.add_run(f"{simbolo}\t– {desc}")
        _set_font(run, size=12)
    page_break(doc)


def build_sumario(doc):
    add_heading(doc, "SUMÁRIO", level=1)
    entries = [
        (1, "1",    "INTRODUÇÃO E CONTEXTUALIZAÇÃO DO PROBLEMA"),
        (1, "2",    "REVISÃO BIBLIOGRÁFICA"),
        (2, "2.1",  "Risco de Crédito para Microempreendedores: da Escassez de Dados ao Comportamento Dinâmico"),
        (2, "2.2",  "Fundamentos da Análise de Sobrevivência e Extensão a Covariáveis Tempo-Variantes"),
        (2, "2.3",  "Deep Learning em Análise de Sobrevivência"),
        (2, "2.4",  "Gestão Ágil de Projetos de Ciência de Dados como Framework Metodológico"),
        (1, "3",    "OBJETIVOS"),
        (2, "3.1",  "Objetivo Geral"),
        (2, "3.2",  "Objetivos Específicos"),
        (1, "4",    "ARQUITETURA DE DADOS E PIPELINE DE EXTRAÇÃO INDUSTRIAL (ETL)"),
        (2, "4.1",  "O Sistema ATLAS: Contexto e Barreiras Técnicas da Extração"),
        (2, "4.2",  "Autenticação Bifásica e Navegação no Frameset Aninhado"),
        (2, "4.3",  "Extração Batch: Paginação Temporal e Filtro Anti-Zero"),
        (2, "4.4",  "Escalabilidade Corporativa: Auto-Discovery, Data Lake Hierárquico e Resiliência"),
        (2, "4.5",  "Consolidação da Matriz Mestra e Otimização de Memória (Data Stitching)"),
        (2, "4.6",  "Governança de Dados, Conformidade LGPD e Metodologia CRISP-DS"),
        (1, "5",    "ENGENHARIA DE VARIÁVEIS E DEFINIÇÃO DO EVENTO TARGET"),
        (2, "5.1",  "Fundamentos Teóricos da Análise de Sobrevivência"),
        (3, "5.1.1","Função de Sobrevivência e Função de Risco"),
        (3, "5.1.2","Tipos de Censura e Truncação à Esquerda"),
        (3, "5.1.3","Estimador de Kaplan-Meier"),
        (3, "5.1.4","Teste de Log-Rank"),
        (3, "5.1.5","Processo de Contagem de Anderson-Gill"),
        (2, "5.2",  "Definição Operacional da Inadimplência na Alta Frequência"),
        (2, "5.3",  "Estrutura Bimodal de Atributos e Estratégia de Proxy"),
        (2, "5.4",  "Formatação Anderson-Gill (Counting Process)"),
        (2, "5.5",  "Construção do Dataset de Sobrevivência"),
        (2, "5.6",  "Análise Exploratória de Dados (EDA)"),
        (2, "5.7",  "Síntese e Validação do Dataset"),
        (1, "6",    "MODELAGEM MATEMÁTICA E COMPUTACIONAL"),
        (2, "6.1",  "Baseline Clássico (Modelo de Cox)"),
        (2, "6.2",  "O Desafio da Censura à Direita em Arquiteturas Neurais"),
        (2, "6.3",  "Abordagem Estado da Arte (Deep Learning sob Censura)"),
        (1, "7",    "VALIDAÇÃO"),
        (1, "8",    "CRONOGRAMA INTEGRADO DE PESQUISA"),
        (1, "REF",  "REFERÊNCIAS BIBLIOGRÁFICAS"),
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
        "geração de caixa.")
    add_body(doc,
        "Diante desse cenário, esta pesquisa propõe uma mudança de paradigma: a utilização de "
        "dados dinâmicos e de alta frequência — especificamente o registro interno de pagamentos "
        "diários (abonos) e suas respectivas modalidades de liquidação — para avaliar a saúde "
        "financeira do negócio em tempo real. O estudo é viabilizado por meio de uma base de "
        "dados estratégica fornecida por uma empresa parceira especializada em microcrédito para "
        "o setor informal. O grande diferencial reside em observar a liquidez diária e a "
        "intensidade dos pagamentos parciais, modelando o risco de default não como um evento "
        "binário e estático, mas como um processo dinâmico e contínuo no tempo. A formatação "
        "deste documento contou com apoio pontual de ferramenta de inteligência artificial "
        "(ANTHROPIC, 2026).")


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
        "A literatura clássica de credit scoring para pequenas e médias empresas — como o "
        "modelo de Altman e Sabato (2007) para o mercado americano — demonstra que indicadores "
        "contábeis estáticos têm poder preditivo limitado quando aplicados a tomadores sem "
        "histórico formal consolidado (o segmento thin-file). Banerjee e Duflo (2007), ao "
        "descreverem a vida econômica dos pobres, evidenciam que a renda e o fluxo de caixa "
        "desse público são inerentemente irregulares e de alta frequência, o que é incompatível "
        "com fotografias mensais ou anuais de risco. Já Schreiner (2002), ao propor um arcabouço "
        "de avaliação do alcance social do microcrédito (outreach), reforça que a profundidade e "
        "a frequência do relacionamento entre credor e tomador — e não apenas o desfecho binário "
        "de inadimplência — são dimensões centrais para avaliar risco e impacto nesse segmento. "
        "Em conjunto, esses três trabalhos delimitam a lacuna que esta pesquisa busca preencher: "
        "modelos de credit scoring tradicionais, estáticos e binários, não capturam a dinâmica "
        "diária de pagamentos parciais que caracteriza o microcrédito informal, motivando a "
        "adoção de uma abordagem longitudinal e orientada ao tempo até o evento.")

    add_heading(doc, "2.2  Fundamentos da Análise de Sobrevivência e Extensão a Covariáveis "
                     "Tempo-Variantes", level=2)
    add_body(doc,
        "A base estatística deste trabalho parte de Kaplan e Meier (1958): o estimador não "
        "paramétrico da função de sobrevivência que dispensa qualquer suposição sobre a forma da "
        "distribuição de T, condição necessária quando — como na carteira de microcrédito aqui "
        "analisada — não há motivo teórico para assumir um formato específico para o tempo até o "
        "default. Para comparar grupos dentro dessa carteira, como escritórios com taxas de "
        "inadimplência distintas, recorre-se ao teste de log-rank de Mantel (1966), que dispensa "
        "igualmente pressupostos paramétricos. Kalbfleisch e Prentice (2002) e Klein e "
        "Moeschberger (2003) reúnem esse ferramental — Kaplan-Meier, log-rank e suas extensões — "
        "nos dois tratamentos de referência utilizados ao longo deste trabalho para dados "
        "censurados e truncados. A peça que conecta essa base clássica ao problema de alta "
        "frequência tratado aqui é o formato de Processo de Contagem de Anderson e Gill (1982): "
        "ao reescrever o Modelo de Riscos Proporcionais de Cox em intervalos (t_start, t_stop], "
        "ele permite que covariáveis como o cronômetro dias_sem_pagar e o saldo devedor variem a "
        "cada snapshot de 10 dias, em vez de permanecerem fixas como em uma especificação clássica "
        "de Cox. Por fim, os diagnósticos de Therneau e Grambsch (2000) — em particular os "
        "resíduos de Schoenfeld — serão o critério para checar, já na fase de modelagem (Seção 6), "
        "se a suposição de riscos proporcionais se sustenta nesse regime tempo-variante.")

    add_heading(doc, "2.3  Deep Learning em Análise de Sobrevivência", level=2)
    add_body(doc,
        "Katzman et al. (2018) tratam o problema de linearidade do Cox por outro caminho: em vez "
        "de assumir que o log-hazard é uma combinação linear das covariáveis, o DeepSurv usa uma "
        "rede neural para aprender essa função diretamente da verossimilhança parcial de Cox, "
        "dispensando a especificação manual de interações entre variáveis — ponto relevante aqui, "
        "dado o número elevado de covariáveis tempo-variantes derivadas do histórico de "
        "pagamentos. Kim (2026) mapeia esse campo em expansão, incluindo variantes recorrentes "
        "(LSTM/GRU) pensadas para sequências longas, como as séries de até centenas de snapshots "
        "por crédito observadas neste portfólio, e aponta abordagens multimodais como direção "
        "futura. É esse mapeamento que orienta a comparação prevista para o Sprint 3 (Seção 8) "
        "entre o baseline de Cox e uma arquitetura de Deep Learning sob censura.")

    add_heading(doc, "2.4  Gestão Ágil de Projetos de Ciência de Dados como Framework "
                     "Metodológico", level=2)
    add_body(doc,
        "Do ponto de vista da condução do projeto, Louzada Neto (2026) caracteriza projetos de "
        "Ciência de Dados e Inteligência Artificial como empreendimentos de alto risco e médio "
        "a longo prazo, propondo a adoção conjunta do ciclo CRISP-DS (Cross Industry Standard "
        "Process for Data Science) e de práticas ágeis de gestão (Scrum) como mitigadores desse "
        "risco. Esse referencial é adotado neste trabalho tanto para estruturar o pipeline de "
        "dados em seis etapas (Seção 3.6) quanto para organizar o cronograma de pesquisa em "
        "Sprints com entregas incrementais (Seção 8).")


# ── SEÇÃO 3 — OBJETIVOS ───────────────────────────────────────────────────────

def build_secao_2(doc):
    add_heading(doc, "3  OBJETIVOS", level=1)
    add_heading(doc, "3.1  Objetivo Geral", level=2)
    add_body(doc,
        "Desenvolver um modelo preditivo de risco de crédito baseado em Análise de Sobrevivência "
        "para estimar o tempo exato até a ruptura do fluxo de caixa e da capacidade de pagamento "
        "(inadimplência técnica) de microempreendedores, integrando variáveis estáticas demográficas "
        "e dados longitudinais de fluxo transacional de alta frequência.")
    add_heading(doc, "3.2  Objetivos Específicos", level=2)
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
         "Treinar e ajustar o Modelo de Riscos Proporcionais de Cox para quantificar o impacto "
         "das covariáveis estáticas e dependentes do tempo na função de risco basal."),
        ("Inovação e Aporte Acadêmico (Deep Learning):",
         "Comparar a performance preditiva do modelo paramétrico de Cox com arquiteturas "
         "contemporâneas de Deep Learning adaptadas para dados de sobrevivência (DeepSurv/RNNs), "
         "incorporando tratamento para censura (Negative Partial Log-Likelihood)."),
        ("Comparativo Classificatório:",
         "Avaliar os ganhos marginais da abordagem de sobrevivência contra os modelos tradicionais "
         "de Credit Scoring de classificação binária."),
    ]
    for label, text in items:
        add_labeled(doc, label, text)


# ── SEÇÃO 3 — EXPANDIDA ───────────────────────────────────────────────────────

def build_secao_3(doc):
    add_heading(doc, "4  ARQUITETURA DE DADOS E PIPELINE DE EXTRAÇÃO INDUSTRIAL (ETL)", level=1)
    add_body(doc,
        "A construção de modelos de análise de sobrevivência com covariáveis tempo-variantes "
        "exige séries longitudinais de alta granularidade que registrem o comportamento de "
        "pagamento de cada crédito ao longo do tempo. A única fonte de dados disponível para "
        "esta pesquisa é o Sistema ATLAS, plataforma de gestão creditícia que não expõe APIs "
        "REST e restringe o acesso a uma interface web de terceira geração. Superar essa barreira "
        "tecnológica exigiu o desenvolvimento de um pipeline de automação web (RPA) de nível "
        "industrial, implementado em Python 3.12 com Selenium WebDriver, cuja arquitetura "
        "completa é detalhada nas subseções seguintes.")

    # ── 3.1 ──────────────────────────────────────────────────────────────────
    add_heading(doc, "4.1  O Sistema ATLAS: Contexto e Barreiras Técnicas da Extração", level=2)
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
        "individuais, detalhadas na Tabela 1. Cada barreira representa um ponto de falha "
        "potencial no pipeline: a ausência de qualquer uma das soluções resulta em crash "
        "silencioso do robô, extração parcial ou dados corrompidos.")

    add_table_data(doc,
        ["Barreira Técnica", "Causa Raiz", "Solução Implementada"],
        [
            ["Sem API REST",
             "Backend PHP sem endpoints programáticos",
             "Selenium WebDriver + ChromeDriver (webdriver-manager)"],
            ["Frameset aninhado (3 níveis)",
             "página principal → frameMenu → frameFormulario",
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
        "Barreiras técnicas do Sistema ATLAS e soluções implementadas no pipeline RPA",
        table_num=1,
    )

    # ── 3.2 ──────────────────────────────────────────────────────────────────
    add_heading(doc, "4.2  Autenticação Bifásica e Navegação no Frameset Aninhado", level=2)
    add_body(doc,
        "O pipeline de autenticação foi implementado na classe orientada a objetos "
        "AtlasDataExtractor (src/atlas_extractor.py), que encapsula toda a lógica de interação "
        "com o Sistema ATLAS. A autenticação ocorre em duas fases distintas, separadas por uma "
        "transição de estado do servidor que invalida os elementos DOM previamente carregados.")

    add_labeled(doc, "Fase 1 — Credenciais:",
        "O formulário de login reside dentro de um iframe (frame index 0 de página de autenticação do sistema). "
        "O robô utiliza WebDriverWait com expected_conditions para aguardar a disponibilidade de "
        "cada elemento antes de interagir, garantindo tolerância a variações de latência do "
        "servidor. Os campos campoUsuario e campoSenha recebem as credenciais lidas de variáveis de "
        "ambiente (.env), e o botão botaoEntrar é ativado via clique nativo do Selenium.")

    add_labeled(doc, "Fase 2 — Seleção de rota (SELECT2):",
        "Após validar as credenciais, o servidor renderiza um segundo formulário com um dropdown "
        "SELECT2 (biblioteca jQuery) para seleção da rota. O SELECT2 ignora completamente eventos "
        "DOM nativos como 'input' ou 'change' disparados por Selenium — o widget escuta apenas "
        "eventos jQuery internos. A solução implementada é a injeção direta de JavaScript que "
        "escreve o valor no elemento <select> subjacente e dispara um evento 'change' nativo com "
        "propagação (bubbles: true), contornando o interceptor jQuery:")

    add_code(doc,
        "# SELECT2 ignora eventos Selenium → DOM nativo com dispatchEvent\n"
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
        "garantir que interceptores DOM não interfiram. Após o fechamento do modal, o robô retorna "
        "ao contexto padrão (switch_to.default_content()) e aguarda o carregamento do frameset "
        "principal antes de prosseguir.")

    add_body(doc,
        "A navegação ao formulário de extração segue uma sequência rígida de troca de contexto "
        "de frame, pois a arquitetura do Sistema ATLAS utiliza frameset aninhado em três níveis. "
        "A Tabela 2 documenta a sequência exata implementada no método _navegar_ao_relatorio_pagamentos().")

    add_table_data(doc,
        ["Passo", "Operação Selenium", "Frame / Elemento Alvo", "Finalidade"],
        [
            ["1", "switch_to.default_content()", "Contexto raiz do navegador", "Resetar contexto após qualquer operação anterior"],
            ["2", "switch_to.frame(0)", "página principal do sistema (frame raiz)", "Entrar no frameset raiz do sistema"],
            ["3", "frame_to_be_available_and_switch_to_it('frameMenu')", "frameMenu (menu lateral)", "Acessar o menu de navegação"],
            ["4", "JS click: //op[normalize-space()='Reportes']", "Tag <op> do menu", "Expandir o submenu de relatórios"],
            ["5", "JS click: //op[normalize-space()='Recaudador']", "Tag <op> do submenu", "Expandir o submenu de cobrança"],
            ["6", "JS click: //a[contains(@href,'RelatorioPagamentos')]", "Link do relatório", "Carregar o formulário de extração no frameFormulario"],
            ["7", "switch_to.default_content() → switch_to.frame(0)", "De volta ao frame raiz", "Preparar para entrar no frameFormulario"],
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
        "repopula o dropdown campoRota — o pipeline aguarda a presença da opção correta com "
        "lambda WebDriverWait antes de prosseguir, garantindo sincronização com o servidor.")

    # ── 3.3 ──────────────────────────────────────────────────────────────────
    add_heading(doc, "4.3  Extração Batch: Paginação Temporal e Filtro Anti-Zero", level=2)
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
        "# Campo readonly → injetar valor via JS + disparar evento change\n"
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
    add_heading(doc, "4.4  Escalabilidade Corporativa: Auto-Discovery, Data Lake Hierárquico e Resiliência", level=2)
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
        "escritórios e 17 rotas geográficas, conforme documentado na Tabela 3.")

    add_table_data(doc,
        ["Escritório", "ID", "Região", "Rotas (IDs)", "Total"],
        [
            ["OFI_23 — São Paulo",       "23", "São Paulo / Grande SP",
             "82, 96, 423, 136, 367, 448, 494", "7"],
            ["OFI_31 — Sociedades Brasil","31", "Interior e Sul do Brasil",
             "415, 68, 338, 347, 389", "5"],
            ["OFI_44 — Cabo Frio",        "44", "Região dos Lagos / RJ",
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
            ["Período de cobertura",           "2020-01-01 → 2026-05-15 (~6,4 anos)"],
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
        "Estrutura do arquivo de checkpoint JSON (.checkpoint.json)",
        table_num=5,
    )

    # ── 3.5 ──────────────────────────────────────────────────────────────────
    add_heading(doc, "4.5  Consolidação da Matriz Mestra e Otimização de Memória (Data Stitching)", level=2)
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
        "são documentadas na Tabela 6. A estrutura matricial tem os créditos como linhas e "
        "as datas calendário de 2020-01-01 a 2026-05-15 (~2.330 datas) como colunas, "
        "com os valores de pagamento diário (abonos) preenchendo a interseção.")

    add_table_data(doc,
        ["Dimensão / Métrica", "Valor"],
        [
            ["Linhas (observações de crédito)", "344.869"],
            ["Colunas totais",                   "2.358"],
            ["Colunas de pagamentos diários",    "~2.330 (datas 2020-01-01 → 2026-05-15)"],
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
        "máscara binária (n_linhas × n_colunas_pagamento) que seleciona apenas as colunas "
        "de data dentro do intervalo do bloco, sem loop Python:")

    add_code(doc,
        "# Máscara vetorizada (n_linhas × n_colunas_pago) — sem loop Python\n"
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
            ["Shape da máscara",        "(5000 × 2330)", "Broadcasting NumPy — operação vetorizada sem loop Python"],
            ["Throughput",              "~5.000 linhas/s","Medido em hardware com 8 GB RAM / CPU 4 núcleos"],
            ["RAM pico por chunk",      "~100 MB",        "Máscara booleana float32 + dados de pagamento"],
            ["Tempo total de leitura",  "~70 segundos",   "Para 344.869 linhas × 2.358 colunas"],
        ],
        "Estratégia de chunked loading com máscara NumPy vetorizada",
        table_num=7,
    )

    # ── 3.6 ──────────────────────────────────────────────────────────────────
    add_heading(doc, "4.6  Governança de Dados, Conformidade LGPD e Metodologia CRISP-DS", level=2)
    add_body(doc,
        "O pipeline ETL foi projetado com governança de dados desde a concepção, atendendo "
        "aos requisitos da Lei Geral de Proteção de Dados Pessoais (LGPD, Lei nº 13.709/2018) "
        "e às melhores práticas de segurança da informação em projetos de Ciência de Dados.")

    add_table_data(doc,
        ["Controle de Governança", "Implementação", "Artigo LGPD"],
        [
            ["Exclusão do versionamento (git)",
             "data/raw/, data/processed/ e .env no .gitignore",
             "Art. 46 — Medidas de segurança"],
            ["Gestão de credenciais",
             "ATLAS_USER e ATLAS_PASS apenas em .env (nunca no código-fonte)",
             "Art. 46 — Proteção de acesso"],
            ["Pseudonimização",
             "CÓDIGO CRÉDITO como chave — sem nome, CPF, endereço ou dados de identificação direta",
             "Art. 13 — Pseudonimização"],
            ["Minimização de dados",
             "Silver Layer contém apenas variáveis necessárias para o modelo de sobrevivência",
             "Art. 6 — Necessidade"],
            ["Finalidade definida",
             "Dados utilizados exclusivamente para pesquisa acadêmica de risco de crédito",
             "Art. 6 — Finalidade"],
            ["Rastreabilidade",
             "arquivo_origen em cada linha da Matriz Mestra identifica a fonte exata do dado",
             "Art. 37 — Registro das operações"],
        ],
        "Conformidade LGPD e governança de dados no pipeline ETL",
        table_num=8,
    )

    add_body(doc,
        "A metodologia CRISP-DS (Cross Industry Standard Process for Data Science), adotada "
        "como framework de gestão do projeto (Louzada Neto, 2026), estrutura o pipeline em seis "
        "fases iterativas que se retroalimentam:")

    fases = [
        ("(1) Entendimento do Negócio:",
         "Definição do evento de castigo de carteira (dias_sem_pagar ≥ 120) a partir do "
         "processo operativo da instituição parceira. Identificação do Sistema ATLAS como "
         "fonte primária e design do pipeline RPA como solução de ingestão."),
        ("(2) Entendimento dos Dados:",
         "Análise exploratória da estrutura da Matriz Mestra (344.869 × 2.358), identificação "
         "das ~2.330 colunas de pagamento, caracterização da cohorte diária e EDA do dataset "
         "de sobrevivência (Seção 5.6)."),
        ("(3) Preparação dos Dados:",
         "Feature Engineering no formato Counting Process de Anderson-Gill: cronômetro "
         "dias_sem_pagar, correção de left truncation, continuidade via shift(), filtro de "
         "coorte diária e construção das 7 covariáveis tempo-variantes."),
        ("(4) Modelagem:",
         "Ajuste do Modelo de Riscos Proporcionais de Cox com covariáveis tempo-variantes "
         "(lifelines.CoxTimeVaryingFitter) e implementação de DeepSurv/RNN-Survival com "
         "Negative Partial Log-Likelihood (pycox/PyTorch). [Sprint 3 — pendente]"),
        ("(5) Avaliação:",
         "Comparação de modelos via C-index de Harrell, Brier Score temporal e Teste de "
         "Log-Rank. Diagnóstico de resíduos de Schoenfeld para validar a suposição de "
         "proporcionalidade do Cox. [Sprint 4 — pendente]"),
        ("(6) Implantação:",
         "Modelo em produção para scoring dinâmico de novos créditos, integrado ao pipeline "
         "ETL para atualização periódica das covariáveis tempo-variantes. [Sprint 4 — pendente]"),
    ]
    for label, text in fases:
        add_labeled(doc, label, text)

    add_body(doc,
        "A gestão de riscos do projeto seguiu as sete categorias identificadas na literatura "
        "de gerenciamento ágil de projetos de Ciência de Dados (Louzada Neto, 2026): "
        "(1) qualidade dos dados — mitigada pelo filtro anti-zero e validação do visualizadorRelatorio; "
        "(2) orçamento — controlado pela solução in-house de web scraping, eliminando licenças "
        "externas; (3) comprometimento — gerenciado com entregas iterativas por Sprint; "
        "(4) recursos humanos — risco baixo por ser pesquisa individual; "
        "(5) fornecedores — mitigado pela independência do Sistema ATLAS (solução in-house); "
        "(6) segurança da informação — LGPD + .gitignore + pseudonimização; "
        "(7) expectativas de tempo — cronograma CRISP-DS com 4 Sprints Scrum.")


# ── SEÇÃO 4 ──────────────────────────────────────────────────────────────────

def build_secao_4(doc):
    add_heading(doc, "5  ENGENHARIA DE VARIÁVEIS E DEFINIÇÃO DO EVENTO TARGET", level=1)

    add_heading(doc, "5.1  Fundamentos Teóricos da Análise de Sobrevivência", level=2)
    add_body(doc,
        "A análise de sobrevivência compreende um conjunto de técnicas estatísticas projetadas "
        "para modelar o tempo até a ocorrência de um evento de interesse (Kalbfleisch e Prentice, "
        "2002). Diferentemente da regressão logística — que estima a probabilidade de default em "
        "um ponto fixo do tempo —, a análise de sobrevivência incorpora explicitamente a dimensão "
        "temporal, distinguindo entre indivíduos que experimentaram o evento e aqueles observados "
        "sem experimentá-lo (censurados).")

    add_heading(doc, "5.1.1  Função de Sobrevivência e Função de Risco", level=3)
    add_body(doc, "A função de sobrevivência é definida como:")
    add_formula(doc, "S(t) = P(T > t) = 1 − F(t)")
    add_body(doc,
        "em que F(t) é a função de distribuição acumulada de T. A função de risco (hazard), "
        "taxa condicional de ocorrência do evento no instante t dado que o indivíduo sobreviveu "
        "até aquele momento, é:")
    add_formula(doc, "h(t) = lim[Δt→0] P(t ≤ T < t+Δt | T ≥ t) / Δt = f(t) / S(t)")
    add_body(doc, "A relação fundamental entre S(t) e h(t) é:")
    add_formula(doc, "S(t) = exp(−∫₀ᵗ h(u) du) = exp(−H(t))")
    add_body(doc,
        "em que H(t) é a função de risco acumulado (cumulative hazard function). Esta relação "
        "mostra que a função de sobrevivência fica completamente determinada pela função de risco, "
        "que é o componente central do modelo de regressão de Cox.")

    add_heading(doc, "5.1.2  Tipos de Censura e Truncação à Esquerda", level=3)
    add_body(doc,
        "A censura à direita (right censoring) ocorre quando o evento não ocorreu antes do fim "
        "da observação — aplicável aos créditos ativos no corte do estudo (15 de maio de 2026). "
        "A truncação à esquerda (left truncation) ocorre quando o primeiro snapshot de um crédito "
        "corresponde a uma data posterior ao seu desembolso. O formato Counting Process trata "
        "corretamente ambos os fenômenos (Therneau e Grambsch, 2000).")

    add_heading(doc, "5.1.3  Estimador de Kaplan-Meier", level=3)
    add_body(doc,
        "O estimador de Kaplan-Meier (Kaplan e Meier, 1958) é o estimador não paramétrico "
        "padrão da função de sobrevivência. Sejam dⱼ o número de eventos e nⱼ o número de "
        "indivíduos em risco em cada tempo de evento tⱼ. O estimador é:")
    add_formula(doc, "Ŝ(t) = ∏[j: tⱼ ≤ t] (1 − dⱼ/nⱼ)")
    add_body(doc,
        "Suas propriedades: consistência (converge a S(t) verdadeiro), não paramétrico "
        "(não assume distribuição para T) e correção automática por censura (indivíduos "
        "censurados contribuem ao denominador nⱼ até o momento da censura). A variância "
        "é obtida pela fórmula de Greenwood: Var[Ŝ(t)] = Ŝ(t)² × Σ[dⱼ/(nⱼ(nⱼ−dⱼ))].")

    add_heading(doc, "5.1.4  Teste de Log-Rank", level=3)
    add_body(doc,
        "O teste de log-rank (Mantel, 1966) compara as curvas de sobrevivência de dois ou mais "
        "grupos sem assumir forma paramétrica. A hipótese nula é H₀: S₁(t) = S₂(t) para todo t. "
        "O estatístico Q segue χ² com (k−1) graus de liberdade sob H₀, sendo mais sensível a "
        "diferenças na cauda da distribuição de sobrevivência.")

    add_heading(doc, "5.1.5  Processo de Contagem de Anderson-Gill", level=3)
    add_body(doc,
        "Quando as covariáveis mudam ao longo do seguimento — como saldo devedor, cuotas "
        "atrasadas e dias_sem_pagar —, é necessário o marco do Processo de Contagem de "
        "Anderson e Gill (1982). O indivíduo i é representado por uma sequência de intervalos:")
    add_formula(doc, "(t_start₁, t_stop₁, δ₁, X_{i1}), (t_start₂, t_stop₂, δ₂, X_{i2}), ...")
    add_body(doc,
        "Restrições: (1) intervalos contíguos: t_start[k] = t_stop[k−1]; (2) evento δ=1 apenas "
        "no último intervalo; (3) intervalos abertos à esquerda e fechados à direita: (t_start, t_stop]. "
        "Implementado em lifelines.CoxTimeVaryingFitter e pycox.")

    add_heading(doc, "5.2  Definição Operacional da Inadimplência na Alta Frequência", level=2)
    add_body(doc,
        "A definição do evento requer atenção especial no contexto de microcrédito diário. "
        "O campo CUOTAS_ATRASADAS registra o número de cotas diárias pendentes no snapshot: "
        "para créditos de 20 a 40 dias, seu máximo teórico é exatamente CUOTAS_PACTADAS. "
        "O umbral original de 120 cotas atrasadas é operacionalmente impossível, produzindo "
        "zero eventos. A definição adotada é o castigo de carteira operativo da instituição:")
    add_formula(doc, "E_i = 𝟙[dias_sem_pagar_{it} ≥ 120 dias calendário]")
    add_body(doc,
        "Este umbral — equivalente a 4 meses de inatividade financeira total — distingue "
        "mora transitória (cronômetro reiniciado por qualquer abono) de abandono real "
        "(inatividade superior a 4 vezes o prazo máximo do crédito). "
        "Critério de inclusão: coorte diária com CUOTAS_PACTADAS ≤ 40.")

    add_heading(doc, "5.3  Estrutura Bimodal de Atributos e Estratégia de Proxy", level=2)
    add_body(doc,
        "As covariáveis disponíveis dividem-se em dois grupos: (1) Variáveis Estáticas — "
        "parâmetros do crédito (valor total, valor da cota, cotas pactadas); (2) Variáveis "
        "Dinâmicas (Heartbeat) — vetor longitudinal de pagamentos, cuotas atrasadas, "
        "intensidade transacional dos abonos e dias com abono, capturando a 'frequência "
        "cardíaca' financeira do empreendedor. Os identificadores ofi_id e rta_id atuam "
        "como proxies geodemográficos para capturar o comportamento de risco local.")

    add_heading(doc, "5.4  Formatação Anderson-Gill (Counting Process)", level=2)
    add_body(doc,
        "A Matriz Mestra é transformada em intervalos longitudinais contínuos (t_start, t_stop]. "
        "Dois desafios matemáticos críticos foram resolvidos:")
    add_labeled(doc, "Left Truncation:",
        "t_start(primeira linha) = max(0, data_ini_bloco − DATA_CRÉDITO) em dias. "
        "Previne tempos de vida negativos que colapsariam a função de verossimilhança.")
    add_labeled(doc, "Continuidade de Markov:",
        "t_start[n] = t_stop[n−1] via shift(), eliminando gaps temporais que fariam o modelo "
        "assumir o desaparecimento artificial do cliente entre snapshots.")
    add_formula(doc, "t_stop[t] = (data_fim_bloco[t] − DATA_CRÉDITO).dias + 1")
    add_formula(doc, "t_start[t] = t_stop[t−1]  para  t > 1")

    add_heading(doc, "5.5  Construção do Dataset de Sobrevivência", level=2)
    add_body(doc,
        "O dataset final no formato Counting Process contém as seguintes variáveis:")

    add_table_data(doc,
        ["Coorte", "Critério", "Créditos"],
        [["Diária (incluída)", "CUOTAS_PACTADAS ≤ 40", "28.386"],
         ["Semanal/quinzenal/mensal (excluída)", "CUOTAS_PACTADAS > 40", "—"]],
        "Filtro de coorte diária: critério e créditos retidos", table_num=9)

    add_table_data(doc,
        ["Variável", "Tipo", "Descrição"],
        [["t_start", "Contínua", "Início do intervalo (dias desde o desembolso)"],
         ["t_stop",  "Contínua", "Fim do intervalo (dias desde o desembolso)"],
         ["evento",  "Binária",  "1 = default (dias_sem_pagar ≥ 120), 0 = censura"],
         ["dias_sem_pagar", "Discreta", "Cronômetro de inatividade financeira"]],
        "Variáveis de tempo e evento do dataset de sobrevivência", table_num=10)

    add_table_data(doc,
        ["Variável", "Fórmula", "Interpretação"],
        [["cuotas_atrasadas",       "CUOTAS_ATRASADAS",                 "Dias em mora no snapshot"],
         ["pago_promedio_diario",   "Σ(pagamentos_bloco) / dias_bloco", "Fluxo médio de pagamentos (BRL)"],
         ["dias_con_abono",         "#{dias com abono > 0} no bloco",   "Frequência de pagamento no período"],
         ["intensidade_recuperacao","VALOR_ÚLTIMO_ABONO / VALOR_COTA",  "Fração da cota paga (clip [0,10])"],
         ["ratio_atraso",           "CUOTAS_ATRASADAS / CUOTAS_PACTADAS","Fração do prazo em mora (clip [0,1])"],
         ["saldo_relativo",         "SALDO / TOTAL_CRÉDITO",             "Fração do crédito pendente (clip [0,1])"]],
        "Covariáveis tempo-variantes e suas fórmulas", table_num=11)

    add_table_data(doc,
        ["Variável", "Descrição"],
        [["total_credito",  "Montante original do crédito (BRL)"],
         ["valor_cota",     "Valor da cota diária pactuada (BRL)"],
         ["cotas_pactadas", "Prazo do crédito em dias"],
         ["ofi_id",         "Identificador de escritório (proxy geográfico)"],
         ["rta_id",         "Identificador de rota (proxy de zona/cobrador)"]],
        "Covariáveis estáticas do modelo", table_num=12)

    # ── 4.6 EDA ──────────────────────────────────────────────────────────────
    add_heading(doc, "5.6  Análise Exploratória de Dados (EDA)", level=2)
    add_body(doc,
        "A análise exploratória foi desenvolvida no notebook notebooks/01_eda_survival.ipynb, "
        "gerando nove figuras de diagnóstico (Figuras 1–9).")

    add_heading(doc, "5.6.1  Caracterização Geral do Dataset", level=3)
    add_table_data(doc,
        ["Métrica", "Valor"],
        [["Créditos únicos",              "28.386"],
         ["Intervalos totais (linhas)",   "301.434"],
         ["Eventos (E=1)",                "425"],
         ["Taxa de default (nível crédito)", "1,50%"],
         ["Créditos censurados (E=0)",    "27.961 (98,50%)"],
         ["Escritórios",                  "3"],
         ["Rotas",                        "17"],
         ["Período de observação",        "2020-01-01 → 2026-05-15 (~6,4 anos)"]],
        "Caracterização geral do dataset de sobrevivência", table_num=13)
    add_body(doc,
        "O baixo índice de default (1,50%) reflete a gestão de cobrança intensiva via cobrador "
        "de rota: a maioria dos inadimplentes é transitória e se resolve antes de atingir 120 "
        "dias de inatividade. A taxa é coerente com referências de microcrédito de pagamento "
        "diário em economias emergentes (Schreiner, 2002).")

    add_heading(doc, "5.6.2  Distribuição do Evento de Default", level=3)
    add_figure(doc, REPORTS / "fig01_distribucion_evento.png",
               "Distribuição do evento de default: proporção (pie), taxa por escritório e taxa por rota", 1)
    add_table_data(doc,
        ["Escritório", "Créditos", "Eventos", "Taxa de Default"],
        [["OFI_23 (São Paulo)",      "14.031", "126", "0,90%"],
         ["OFI_31 (Soc. Brasil)",     "7.333",  "53",  "0,72%"],
         ["OFI_44 (Cabo Frio)",       "7.022",  "246", "3,50%"]],
        "Taxa de default por escritório", table_num=14)
    add_body(doc,
        "OFI_44 (Cabo Frio) apresenta taxa quase quatro vezes superior às demais (3,50% vs. "
        "0,72–0,90%), evidenciando heterogeneidade geográfica relevante para o modelo de Cox.")

    add_heading(doc, "5.6.3  Curva de Kaplan-Meier Global", level=3)
    add_figure(doc, REPORTS / "fig02_kaplan_meier_global.png",
               "Curva de Kaplan-Meier global do portfólio com tabela de n em risco", 2)
    add_table_data(doc,
        ["Tempo (dias)", "S(t)", "Risco Acumulado"],
        [["120", "1,0000", "0,00%"],
         ["180", "0,6815", "31,85%"],
         ["270", "0,6788", "32,12%"],
         ["365", "0,1673", "83,27%"],
         ["540", "0,0908", "90,92%"]],
        "Valores da curva de Kaplan-Meier global", table_num=15)
    add_body(doc,
        "S(t) = 1,0 até o dia 120 é consequência direta da definição do evento (dias_sem_pagar "
        "≥ 120 é impossível antes de 120 dias de seguimento). O salto de S=1,0 para S=0,68 "
        "entre os dias 120 e 180 revela que créditos de longa permanência — além do prazo "
        "original de 20–40 dias — concentram o risco de default.")

    add_heading(doc, "5.6.4  Análise Estratificada por Escritório (Teste de Log-Rank)", level=3)
    add_figure(doc, REPORTS / "fig03_kaplan_meier_oficinas.png",
               "Curvas de Kaplan-Meier por escritório com teste de log-rank (OFI_23 vs. OFI_44)", 3)
    add_table_data(doc,
        ["Estatístico", "Valor"],
        [["χ² (log-rank)", "0,0817"], ["p-valor", "0,7750"]],
        "Resultado do teste de log-rank (OFI_23 vs. OFI_44)", table_num=16)
    add_body(doc,
        "p = 0,775 indica que não se rejeita H₀ de igualdade de curvas ao nível de 5%. "
        "Apesar da diferença bruta em taxas (0,90% vs. 3,50%), o timing dos eventos é similar "
        "entre escritórios, e a redução de créditos em risco a horizontes longos diminui o "
        "poder estatístico do teste. Isso motiva o uso do modelo de Cox, que controla "
        "simultaneamente por múltiplas covariáveis.")

    add_heading(doc, "5.6.5  Tempo de Seguimento e Granularidade Longitudinal", level=3)
    add_figure(doc, REPORTS / "fig04_tiempo_seguimiento.png",
               "Distribuição do tempo de seguimento (t_stop) e número de intervalos por crédito", 4)
    add_table_data(doc,
        ["Estatístico", "t_stop (dias)", "n_intervalos"],
        [["Mediana", "29 dias", "3"],
         ["Média",   "36 dias", "10,6"],
         ["Máximo",  "815 dias", "233"]],
        "Estatísticas do tempo de seguimento e intervalos por crédito", table_num=17)
    add_body(doc,
        "A mediana de 29 dias reflete créditos curtos (20–30 dias). A cauda direita pronunciada "
        "(máx 815 dias, 233 snapshots) corresponde a clientes com múltiplas renovações — "
        "estrutura bimodal típica do microcrédito diário que justifica a análise de sobrevivência.")

    add_heading(doc, "5.6.6  Cronômetro dias_sem_pagar", level=3)
    add_figure(doc, REPORTS / "fig05_dias_sin_pagar.png",
               "Distribuição de dias_sem_pagar: global, zoom 0–150 dias e máximo por crédito", 5)
    add_table_data(doc,
        ["Estatístico", "Valor"],
        [["Mediana", "0 dias"], ["Percentil 95", "0 dias"],
         ["Percentil 99", "26 dias"], ["Máximo", "400 dias"]],
        "Estatísticas do cronômetro dias_sem_pagar", table_num=18)
    add_body(doc,
        "Em mais de 95% dos intervalos, dias_sem_pagar = 0: o cliente realizou pelo menos um "
        "abono no bloco de 10 dias. Valores altos (>26 dias) correspondem quase exclusivamente "
        "a créditos que eventualmente defaultam. Correlação de Pearson com evento: r = 0,680 "
        "— a mais alta do conjunto de covariáveis.")

    add_heading(doc, "5.6.7  Análise de Covariáveis: Default vs. Censurado", level=3)
    add_figure(doc, REPORTS / "fig06_covariables_evento.png",
               "Distribuição das covariáveis por grupo: Default (E=1) versus Censurado (E=0)", 6)
    add_table_data(doc,
        ["Covariável", "r com evento", "Direção"],
        [["dias_sem_pagar",          "+0,6796", "Cronômetro direto do evento"],
         ["saldo_relativo",          "−0,0350", "Maior saldo → menor default"],
         ["dias_con_abono",          "−0,0217", "Mais dias com abono → menor risco"],
         ["ratio_atraso",            "−0,0176", "Contra-intuitivo por composição"],
         ["pago_promedio_diario",    "−0,0152", "Mais pagamentos → menor risco"],
         ["intensidade_recuperacao", "+0,0071", "Efeito misto"]],
        "Correlações das covariáveis com o evento", table_num=19)
    add_body(doc,
        "As correlações lineares baixas das covariáveis de mora e pagamento com o evento não "
        "implicam ausência de efeito preditivo — refletem a natureza não linear e dinâmica "
        "das relações no contexto do Counting Process, que o modelo de Cox quantificará "
        "corretamente via hazard ratios.")

    add_heading(doc, "5.6.8  Perfil Econômico do Portfólio", level=3)
    add_figure(doc, REPORTS / "fig07_perfil_credito.png",
               "Perfil econômico: distribuição do prazo, montante e boxplot por evento", 7)
    add_table_data(doc,
        ["Estatístico", "Valor"],
        [["Mediana", "R$ 1.200"], ["Média", "R$ 1.491"],
         ["Percentil 10", "R$ 540"], ["Percentil 90", "R$ 3.000"]],
        "Montante do crédito por grupo de evento", table_num=20)
    add_body(doc,
        "Créditos de baixo montante (mediana R$ 1.200), com prazo concentrado em 20 dias "
        "(62,7%), 24 dias (29,3%) e 30 dias (5,2%). A grande maioria (92,0%) tem prazo de "
        "20 ou 24 dias — produtos pré-definidos pela instituição, não negociados individualmente.")

    add_heading(doc, "5.6.9  Estrutura de Correlações", level=3)
    add_figure(doc, REPORTS / "fig08_correlaciones.png",
               "Mapa de calor de correlações das covariáveis (triângulo inferior)", 8)
    add_body(doc,
        "Correlação ratio_atraso ↔ cuotas_atrasadas: r ≈ +0,90 (redundância — incluir apenas "
        "uma no modelo Cox). Demais pares sem correlações problemáticas (> 0,7), indicando "
        "ausência de multicolinearidade grave no conjunto de covariáveis selecionado.")

    add_heading(doc, "5.6.10  Análise de Trajetórias Individuais", level=3)
    add_figure(doc, REPORTS / "fig09_trayectorias.png",
               "Trajetórias individuais: 5 créditos em default versus 5 censurados", 9)
    add_body(doc,
        "Créditos em default: dias_sem_pagar cresce monotonicamente nos últimos blocos, "
        "cruzando 120 dias exatamente no intervalo marcado como evento. Créditos censurados: "
        "cronômetro permanece em zero com reinicializações frequentes — o forward-fill captura "
        "corretamente a mora transitória vs. abandono real.")

    add_heading(doc, "5.7  Síntese e Validação do Dataset", level=2)
    add_table_data(doc,
        ["Validação", "Resultado"],
        [["t_stop > t_start em todos os intervalos",   "✓ Verificado"],
         ["Cadeia perfeita t_start[k] = t_stop[k−1]", "✓ Verificado (via shift)"],
         ["Evento E=1 apenas no último intervalo",      "✓ Regra de censura aplicada"],
         ["Sem valores nulos em colunas-chave",         "✓ Verificado"],
         ["Número de eventos > 100",                    "✓ 425 eventos"],
         ["Covariáveis em faixa esperada",              "✓ Clip aplicado a todas as razões"]],
        "Validação do formato Counting Process", table_num=21)
    add_body(doc,
        "O dataset fica preparado para a etapa seguinte: ajuste do Modelo de Cox de Riscos "
        "Proporcionais com covariáveis tempo-variantes (lifelines.CoxTimeVaryingFitter).")


# ── SEÇÃO 5 ──────────────────────────────────────────────────────────────────

def build_secao_5(doc):
    add_heading(doc, "6  MODELAGEM MATEMÁTICA E COMPUTACIONAL (O DESAFIO DA CENSURA)", level=1)
    add_heading(doc, "6.1  Baseline Clássico (Modelo de Cox)", level=2)
    add_body(doc,
        "A fase inicial aplicará o Modelo de Riscos Proporcionais de Cox para estabelecer o "
        "marco de interpretabilidade e quantificar o impacto das covariáveis (Hazard Ratios). "
        "Os Resíduos de Schoenfeld servirão como diagnóstico para validar a suposição de "
        "proporcionalidade. [RESULTADO PENDENTE — Sprint 3]")
    add_heading(doc, "6.2  O Desafio da Censura à Direita em Arquiteturas Neurais", level=2)
    add_body(doc,
        "Arquiteturas de Deep Learning tradicionais falham ao ignorar a informação contida "
        "nos registros censurados à direita. Descartar essas observações introduz viés severo "
        "e subestima o tempo real de sobrevivência.")
    add_heading(doc, "6.3  Abordagem Estado da Arte (Deep Learning sob Censura)", level=2)
    add_body(doc,
        "Redes neurais recorrentes (LSTM/GRU) integradas à Análise de Sobrevivência "
        "(DeepSurv/RNN-Survival) com otimização da Verossimilhança Parcial Negativa "
        "(Negative Partial Log-Likelihood), respeitando matematicamente o tempo de "
        "sobrevivência acumulado dos clientes sob censura. [IMPLEMENTAÇÃO PENDENTE — Sprint 3]")


# ── SEÇÃO 6 ──────────────────────────────────────────────────────────────────

def build_secao_6(doc):
    add_heading(doc, "7  VALIDAÇÃO", level=1)
    add_body(doc,
        "Testes de performance compararão o modelo de sobrevivência clássico com as técnicas "
        "de Deep Learning, utilizando: C-index de Harrell (concordance index), Brier Score "
        "temporal e Teste de Log-Rank entre modelos. [RESULTADOS PENDENTES — Sprint 4]")


# ── SEÇÃO 7 ──────────────────────────────────────────────────────────────────

def build_secao_7(doc):
    add_heading(doc, "8  CRONOGRAMA INTEGRADO DE PESQUISA", level=1)
    add_body(doc,
        "Projeto estruturado em quatro Sprints Scrum (Louzada Neto, 2026), com entregas "
        "iterativas que permitem ajustes de escopo sem comprometer o prazo final:")
    sprints = [
        ("Sprint 1 (Jan–Mar 2026) — ETL/Pipeline [CONCLUÍDO]:",
         "Desenvolvimento do extrator Selenium (AtlasDataExtractor e AtlasMasivoExtractor), "
         "extração de 3.962 arquivos Excel (3 escritórios, 17 rotas, 2020–2026), Data Lake "
         "hierárquico (~14 GB), sistema de checkpoint JSON, consolidação da Matriz Mestra "
         "(344.869 × 2.358) e otimização de memória via chunked loading com máscara NumPy (−49% RAM)."),
        ("Sprint 2 (Mar–Mai 2026) — Feature Engineering + EDA [CONCLUÍDO]:",
         "Definição e implementação do cronômetro dias_sem_pagar, construção do dataset "
         "de sobrevivência no formato Counting Process (28.386 créditos, 301.434 intervalos, "
         "425 eventos, 1,50%), análise exploratória completa com 9 figuras de diagnóstico e "
         "elaboração do relatório metodológico (Seções 3 e 4 do TCC)."),
        ("Sprint 3 (Jun–Ago 2026) — Modelagem Cox + DeepSurv [PENDENTE]:",
         "Ajuste do Modelo de Riscos Proporcionais de Cox com covariáveis tempo-variantes, "
         "diagnóstico de resíduos de Schoenfeld, implementação de DeepSurv/RNN-Survival "
         "com Negative Partial Log-Likelihood e comparação de Hazard Ratios."),
        ("Sprint 4 (Set–Nov 2026) — Avaliação + Redação final [PENDENTE]:",
         "C-index de Harrell, Brier Score temporal, comparativo com Credit Scoring binário, "
         "redação de Resultados, Discussão e Conclusão do TCC."),
    ]
    for label, text in sprints:
        add_labeled(doc, label, text)


# ── REFERÊNCIAS ───────────────────────────────────────────────────────────────

def build_referencias(doc):
    """Referências conforme ABNT NBR 6023: sem negrito; título do periódico/livro
    (o 'veículo') em itálico; demais elementos em fonte regular."""
    add_heading(doc, "REFERÊNCIAS BIBLIOGRÁFICAS", level=1)
    refs = [
        [("ALTMAN, E. I.; SABATO, G. Modeling Credit Risk for SMEs: Evidence from the US Market. ", False),
         ("Abacus", True),
         (", v. 43, n. 3, p. 332–357, 2007.", False)],
        [("ANDERSON, P. K.; GILL, R. D. Cox's regression model for counting processes: a large "
          "sample study. ", False),
         ("The Annals of Statistics", True),
         (", v. 10, n. 4, p. 1100–1120, 1982.", False)],
        [("ANTHROPIC. ", False),
         ("Claude", True),
         (". Sonnet 5. Large Language Model. San Francisco: Anthropic, 2026. Disponível em: "
          "https://claude.ai/. Acesso em: 4 jul. 2026. Nota: Apoio pontual na formatação ABNT/USP "
          "do documento e em pequenos trechos de código.", False)],
        [("BANERJEE, A. V.; DUFLO, E. The economic lives of the poor. ", False),
         ("Journal of Economic Perspectives", True),
         (", v. 21, n. 1, p. 141–167, 2007.", False)],
        [("KALBFLEISCH, J. D.; PRENTICE, R. L. ", False),
         ("The Statistical Analysis of Failure Time Data", True),
         (". 2. ed. New York: Wiley, 2002.", False)],
        [("KAPLAN, E. L.; MEIER, P. Nonparametric estimation from incomplete observations. ", False),
         ("Journal of the American Statistical Association", True),
         (", v. 53, n. 282, p. 457–481, 1958.", False)],
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
        [("LOUZADA NETO, F. ", False),
         ("Gestão de Projetos de Ciência de Dados e Inteligência Artificial", True),
         (". Material didático — MBA em Ciência de Dados. ICMC/USP, São Carlos, 2026.", False)],
        [("MANTEL, N. Evaluation of survival data and two new rank order statistics arising in "
          "its consideration. ", False),
         ("Cancer Chemotherapy Reports", True),
         (", v. 50, n. 3, p. 163–170, 1966.", False)],
        [("SCHREINER, M. Aspects of outreach: a framework for discussion of the social benefits "
          "of microfinance. ", False),
         ("Journal of International Development", True),
         (", v. 14, n. 5, p. 591–603, 2002.", False)],
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


# ── MAIN ──────────────────────────────────────────────────────────────────────

def build_doc():
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
    build_secao_5(doc)
    build_secao_6(doc)
    build_secao_7(doc)
    build_referencias(doc)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUTPUT)
    print(f"\n[PT] V23 gerado: {OUTPUT}")
    print(f"     Tamanho: {OUTPUT.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    build_doc()

    es_script = Path(__file__).parent / "gerar_tcc_v23_es.py"  # ainda não criado — sync ES pendente
    if es_script.exists():
        print("\n[ES] Gerando versão em Espanhol...")
        result = subprocess.run([sys.executable, str(es_script)], capture_output=True, text=True)
        print(result.stdout)
        if result.returncode != 0:
            print("ERRO:", result.stderr)
