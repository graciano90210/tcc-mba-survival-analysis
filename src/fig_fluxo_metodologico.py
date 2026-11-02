"""
Figura do fluxo metodológico do TCC: da extração à avaliação.

Gera reports/fig00_fluxo_metodologico.png, pensada para a abertura da
metodologia na V26 (substitui parte do detalhe técnico da §4). Os ícones são
desenhados como vetores com matplotlib, sem dependências externas.
"""

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Arc, Circle, Ellipse, FancyArrowPatch, FancyBboxPatch, Polygon, Rectangle

SAIDA = Path(__file__).parent.parent / "reports" / "fig00_fluxo_metodologico.png"

AZUL, VERDE, LARANJA = "#2E6DB4", "#2E8B6F", "#D9822B"
TINTA = {AZUL: "#EEF3FA", VERDE: "#EDF6F2", LARANJA: "#FBF1E7"}
TEXTO, CINZA = "#1F2933", "#7B8794"
BRANCO = "white"


# ── Ícones (coordenadas locais centradas em (cx, cy), escala s) ─────────────

def _navegador(ax, cx, cy, s):
    w, h = 1.0 * s, 0.78 * s
    ax.add_patch(FancyBboxPatch((cx - w / 2, cy - h / 2), w, h, boxstyle=f"round,pad=0,rounding_size={0.08 * s}",
                                fill=False, ec=BRANCO, lw=2))
    ax.plot([cx - w / 2, cx + w / 2], [cy + h / 2 - 0.2 * s] * 2, color=BRANCO, lw=2)
    for k in range(3):
        ax.add_patch(Circle((cx - w / 2 + (0.12 + 0.11 * k) * s, cy + h / 2 - 0.1 * s), 0.03 * s, color=BRANCO))
    ax.add_patch(FancyArrowPatch((cx, cy + 0.12 * s), (cx, cy - 0.3 * s), arrowstyle="-|>",
                                 mutation_scale=14 * s, color=BRANCO, lw=2.2))


def _banco(ax, cx, cy, s):
    w, h, e = 0.82 * s, 0.8 * s, 0.24 * s
    topo, base = cy + h / 2 - e / 2, cy - h / 2 + e / 2
    ax.add_patch(Ellipse((cx, topo), w, e, fill=False, ec=BRANCO, lw=2))
    for x in (cx - w / 2, cx + w / 2):
        ax.plot([x, x], [topo, base], color=BRANCO, lw=2)
    for y in (base, (topo + base) / 2):
        ax.add_patch(Arc((cx, y), w, e, theta1=180, theta2=360, ec=BRANCO, lw=2))


def _funil(ax, cx, cy, s):
    pts = [(-0.48, 0.36), (0.48, 0.36), (0.1, -0.04), (0.1, -0.4), (-0.1, -0.3), (-0.1, -0.04)]
    ax.add_patch(Polygon([(cx + x * s, cy + y * s) for x, y in pts], closed=True, fill=False, ec=BRANCO, lw=2,
                         joinstyle="round"))
    for dx in (-0.25, 0.0, 0.25):
        ax.add_patch(Circle((cx + dx * s, cy + 0.5 * s), 0.05 * s, color=BRANCO))


def _linha_do_tempo(ax, cx, cy, s):
    w, h = 1.0 * s, 0.26 * s
    x0 = cx - w / 2
    for k in range(4):
        ax.add_patch(Rectangle((x0 + k * w / 4, cy - h / 2 + 0.08 * s), w / 4, h, fill=k % 2 == 0,
                               fc=BRANCO, ec=BRANCO, lw=1.8, alpha=0.95 if k % 2 == 0 else 1))
    for k in range(5):
        x = x0 + k * w / 4
        ax.plot([x, x], [cy - h / 2 - 0.02 * s, cy - h / 2 - 0.14 * s], color=BRANCO, lw=1.8)
    ax.add_patch(FancyArrowPatch((x0, cy - 0.38 * s), (x0 + w + 0.05 * s, cy - 0.38 * s), arrowstyle="-|>",
                                 mutation_scale=10 * s, color=BRANCO, lw=1.8))


def _rede(ax, cx, cy, s):
    camadas = [(-0.42, [-0.3, 0.0, 0.3]), (0.0, [-0.38, -0.13, 0.13, 0.38]), (0.42, [-0.15, 0.15])]
    for (xa, ya), (xb, yb) in zip(camadas, camadas[1:]):
        for y1 in ya:
            for y2 in yb:
                ax.plot([cx + xa * s, cx + xb * s], [cy + y1 * s, cy + y2 * s], color=BRANCO, lw=0.9, alpha=0.75)
    for x, ys in camadas:
        for y in ys:
            ax.add_patch(Circle((cx + x * s, cy + y * s), 0.075 * s, color=BRANCO, zorder=5))


def _curva(ax, cx, cy, s):
    x0, y0 = cx - 0.45 * s, cy - 0.38 * s
    ax.plot([x0, x0, x0 + 0.95 * s], [y0 + 0.8 * s, y0, y0], color=BRANCO, lw=2)
    xs = [0, 0.18, 0.18, 0.38, 0.38, 0.6, 0.6, 0.88]
    ys = [0.68, 0.68, 0.5, 0.5, 0.34, 0.34, 0.22, 0.22]
    ax.plot([x0 + x * s for x in xs], [y0 + y * s for y in ys], color=BRANCO, lw=2.4, solid_joinstyle="round")


ETAPAS = [
    ("Extração", AZUL, _navegador,
     ["Robô de automação web", "(sistema sem API)", "3.962 planilhas", "17 rotas, 2020 a 2026"]),
    ("Consolidação", AZUL, _banco,
     ["Data Stitching: união", "dos arquivos em um", "painel único", "(Matriz Mestra)"]),
    ("Pré-processamento", VERDE, _funil,
     ["Reconstrução do desfecho", "pelos pagamentos diários", "(limiar de 120 dias)", "Exclusões e coorte diária"]),
    ("Engenharia\nde atributos", VERDE, _linha_do_tempo,
     ["Blocos de 10 dias", "Covariáveis sem", "informação futura", "Região, feriados, macro"]),
    ("Modelagem", LARANJA, _rede,
     ["Riscos competitivos", "(default × cura)", "Cox cause-specific", "e DeepHit"]),
    ("Avaliação", LARANJA, _curva,
     ["C-index e Brier", "dependentes do tempo", "Comparação de", "conjuntos de atributos"]),
]

GRUPOS = [(0, 1, "Engenharia de dados (ETL)", AZUL),
          (2, 3, "Preparação dos dados", VERDE),
          (4, 5, "Modelagem e avaliação", LARANJA)]


def desenhar(saida: Path = SAIDA) -> None:
    fig, ax = plt.subplots(figsize=(16, 5.0))
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 5.0)
    ax.set_aspect("equal")
    ax.axis("off")

    largura, altura, passo, y0, raio = 2.3, 2.75, 2.62, 0.25, 0.55
    topo = y0 + altura

    for ini, fim, rotulo, cor in GRUPOS:
        x_ini = 0.25 + ini * passo - 0.08
        x_fim = 0.25 + fim * passo + largura + 0.08
        ax.add_patch(FancyBboxPatch((x_ini, y0 - 0.1), x_fim - x_ini, altura + raio + 0.95,
                                    boxstyle="round,pad=0,rounding_size=0.2", fc=TINTA[cor], ec="none", zorder=0))
        ax.text((x_ini + x_fim) / 2, topo + raio + 0.55, rotulo, ha="center", va="center", fontsize=11.5,
                fontweight="bold", color=BRANCO, zorder=3,
                bbox=dict(boxstyle="round,pad=0.35,rounding_size=0.6", fc=cor, ec="none"))

    for i, (titulo, cor, icone, linhas) in enumerate(ETAPAS):
        x = 0.25 + i * passo
        cx = x + largura / 2
        ax.add_patch(FancyBboxPatch((x, y0), largura, altura, boxstyle="round,pad=0,rounding_size=0.14",
                                    fc=BRANCO, ec=cor, lw=1.6, zorder=1))
        ax.add_patch(Circle((cx, topo), raio, fc=cor, ec=BRANCO, lw=3, zorder=2))
        n_patches, n_linhas = len(ax.patches), len(ax.lines)
        icone(ax, cx, topo, 0.62)
        for artista in ax.patches[n_patches:] + ax.lines[n_linhas:]:
            artista.set_zorder(4)
        ax.text(x + 0.14, topo - 0.12, str(i + 1), ha="left", va="top", fontsize=10, fontweight="bold",
                color=cor, zorder=3)
        ax.text(cx, topo - raio - 0.12, titulo, ha="center", va="top", fontsize=11, fontweight="bold",
                color=TEXTO, linespacing=1.05, zorder=3)
        for j, linha in enumerate(linhas):
            ax.text(cx, y0 + 1.3 - j * 0.3, linha, ha="center", va="center", fontsize=9.3, color=TEXTO, zorder=3)
        if i < len(ETAPAS) - 1:
            ax.add_patch(FancyArrowPatch((x + largura + 0.02, y0 + altura / 2), (x + passo - 0.02, y0 + altura / 2),
                                         arrowstyle="-|>", mutation_scale=15, color=CINZA, lw=1.6, zorder=3))

    fig.savefig(saida, dpi=220, bbox_inches="tight", pad_inches=0.08, facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    desenhar()
    print(f"Figura salva em {SAIDA}")
