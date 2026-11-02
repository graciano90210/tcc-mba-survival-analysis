"""
Figuras e tabelas da análise exploratória da V27 (capítulo 6).

Usa o dataset reconstruído (desenlaces_v2.csv, survival_dataset_v2_b7.csv),
o histórico do cliente (historial_cliente.csv), os KPIs por cliente e os
pagamentos diários (lidos da matriz com reconstruir_dataset._extraer).

Saídas em reports/figuras_v27/ (PNG, 200 dpi, largura de 16 cm) e
reports/figuras_v27/eda_resumo.json com os números citados no texto.
Paleta: a categórica validada do projeto (azul, laranja, verde-água), sempre
na mesma ordem; texto em cinza escuro, grade discreta.
"""

import json
import logging
from pathlib import Path

import holidays
import matplotlib
matplotlib.use("Agg")
import matplotlib.dates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from lifelines.statistics import multivariate_logrank_test

from calendario_cobro import UF_RUTA
from reconstruir_dataset import MATRIZ, _extraer

_RAIZ  = Path(__file__).parent.parent
PROC   = _RAIZ / "data" / "processed"
OUT    = _RAIZ / "reports" / "figuras_v27"

AZUL, LARANJA, VERDE = "#2a78d6", "#eb6834", "#1baf7a"
TINTA, TINTA_SUAVE, GRADE = "#1f2328", "#59636e", "#d8dee4"
OFICINAS = {23: ("São Paulo", AZUL), 31: ("Sociedades Brasil", LARANJA), 44: ("Cabo Frio", VERDE)}
LANDMARK = 14
CM = 1 / 2.54

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 9, "axes.edgecolor": GRADE,
    "axes.labelcolor": TINTA, "xtick.color": TINTA_SUAVE, "ytick.color": TINTA_SUAVE,
    "text.color": TINTA, "axes.grid": True, "grid.color": GRADE, "grid.linewidth": 0.6,
    "axes.spines.top": False, "axes.spines.right": False, "axes.axisbelow": True,
    "legend.frameon": False, "savefig.dpi": 200, "savefig.bbox": "tight",
})


def _pct(ax):
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(
        lambda v, _: f"{v:.1f}%".replace(".", ",")))


def _barras_taxa(ax, rotulos, taxas, ns, titulo, cor=AZUL):
    x = np.arange(len(rotulos))
    ax.bar(x, taxas, width=0.6, color=cor)
    for xi, t in zip(x, taxas):
        ax.text(xi, t, f"{t:.2f}%".replace(".", ","), ha="center", va="bottom",
                fontsize=7.5, color=TINTA)
    ax.set_xticks(x, rotulos, fontsize=7.5)
    ax.set_title(titulo, fontsize=9, loc="left", color=TINTA)
    ax.grid(axis="x", visible=False)
    ax.set_ylim(0, max(taxas) * 1.25)
    _pct(ax)


def incidencia_acumulada(T, evento, de_interesse):
    """Estimador de Aalen-Johansen da incidência acumulada (riscos competitivos).
    Escrito aqui porque o AalenJohansenFitter do lifelines desempata tempos
    somando ruído aleatório, o que espalha eventos para dias em que não houve
    nenhum (p. ex. default antes do dia 120). Retorna uma série indexada pelo dia."""
    t = pd.DataFrame({"T": np.asarray(T), "e": np.asarray(evento)})
    g = t.groupby("T")["e"]
    dias = g.size().index.values
    saidas = g.size().values
    eventos = g.apply(lambda e: (e == de_interesse).sum()).values
    qualquer = g.apply(lambda e: (e != 0).sum()).values
    em_risco = len(t) - np.concatenate([[0], np.cumsum(saidas)[:-1]])
    sobrev_antes = np.concatenate([[1.0], np.cumprod(1 - qualquer / em_risco)[:-1]])
    cif = np.cumsum(sobrev_antes * eventos / em_risco)
    return pd.Series(np.concatenate([[0.0], cif]), index=np.concatenate([[0], dias]))


# ------------------------------------------------------------------ #
# 1. Incidência acumulada de cura e de default                        #
# ------------------------------------------------------------------ #

def fig_cif(d, resumo):
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(16 * CM, 6.5 * CM))
    for ax, evento, cor, titulo, limite in [
            (a1, 2, AZUL, "Cura (pagamento total)", 120),
            (a2, 1, LARANJA, "Default (120 dias sem pagar)", 540)]:
        cif_total = incidencia_acumulada(d["T"], d["evento_tipo"], evento)
        cif = cif_total[cif_total.index <= limite] * 100
        ax.step(cif.index, cif.values, where="post", color=cor, lw=2)
        ax.set_title(titulo, fontsize=9, loc="left")
        ax.set_xlabel("Dias desde o desembolso")
        ax.set_xlim(0, limite)
        _pct(ax)
        resumo[f"cif_{evento}"] = {int(t): round(float(cif_total.asof(t)) * 100, 3)
                                   for t in (20, 30, 60, 120, 150, 180, 365)}
    a1.set_ylabel("Incidência acumulada")
    fig.savefig(OUT / "fig_cif_desfechos.png")
    plt.close(fig)


# ------------------------------------------------------------------ #
# 2. Default por escritório                                           #
# ------------------------------------------------------------------ #

def fig_escritorio(d, resumo):
    fig, ax = plt.subplots(figsize=(16 * CM, 6.5 * CM))
    for ofi, (nome, cor) in OFICINAS.items():
        g = d[d["ofi_id"] == ofi]
        cif = incidencia_acumulada(g["T"], g["evento_tipo"], 1)
        cif = cif[cif.index <= 540] * 100
        resumo.setdefault("cif_default_365", {})[nome] = round(float(cif.asof(365)), 3)
        ax.step(cif.index, cif.values, where="post", color=cor, lw=2)
        ajuste = {"São Paulo": -0.05, "Cabo Frio": 0.05}.get(nome, 0)
        ax.text(545, cif.values[-1] + ajuste, nome, va="center", fontsize=8, color=TINTA)
    ax.set_xlim(0, 640)
    ax.set_xlabel("Dias desde o desembolso")
    ax.set_ylabel("Incidência acumulada de default")
    _pct(ax)
    fig.savefig(OUT / "fig_default_escritorio.png")
    plt.close(fig)

    # teste de log-rank do risco específico de default (cura tratada como censura)
    teste = multivariate_logrank_test(d["T"], d["ofi_id"], (d["evento_tipo"] == 1).astype(int))
    tab = d.groupby("ofi_id").agg(creditos=("T", "size"),
                                  default=("evento_tipo", lambda s: (s == 1).sum()),
                                  cura=("evento_tipo", lambda s: (s == 2).sum()),
                                  censura=("evento_tipo", lambda s: (s == 0).sum()))
    resumo["escritorio"] = {OFICINAS[o][0]: {k: int(v) for k, v in r.items()} for o, r in tab.iterrows()}
    resumo["logrank_escritorio"] = {"estatistica": round(float(teste.test_statistic), 2),
                                    "p": float(teste.p_value)}


# ------------------------------------------------------------------ #
# 3. Comportamento no dia 14 e default                                #
# ------------------------------------------------------------------ #

def _faixas(serie, y, cortes, rotulos):
    f = pd.cut(serie, cortes, labels=rotulos, include_lowest=True, right=True)
    g = pd.DataFrame({"f": f, "y": y}).groupby("f", observed=False)["y"]
    return list(rotulos), (g.mean() * 100).tolist(), g.size().tolist()


def fig_dia14(df, d, resumo):
    foto = df[df["t_start"] == LANDMARK].merge(d["evento_tipo"].rename("desfecho"),
                                               left_on="CÓDIGO CRÉDITO", right_index=True)
    y = (foto["desfecho"] == 1).astype(int)
    pago_rel = (foto["pago_promedio_diario_prev"] / foto["valor_cuota"]).clip(0, 3)
    paineis = [
        ("Dias com pagamento na semana anterior", foto["dias_con_abono_prev"],
         [-0.5, 1.5, 3.5, 5.5, 7], ["0 a 1", "2 a 3", "4 a 5", "6 a 7"]),
        ("Pagamento diário dividido pela parcela", pago_rel,
         [-0.01, 0.5, 0.9, 1.1, 3], ["até 0,5", "0,5 a 0,9", "0,9 a 1,1", "acima\nde 1,1"]),
        ("Atraso relativo", foto["ratio_atraso"],
         [-0.01, 0.1, 0.25, 0.5, 1], ["até 10%", "10 a 25%", "25 a 50%", "acima\nde 50%"]),
        ("Saldo que falta pagar", foto["saldo_relativo"],
         [-0.01, 0.5, 0.7, 0.85, 1], ["até 50%", "50 a 70%", "70 a 85%", "acima\nde 85%"]),
    ]
    fig, axs = plt.subplots(2, 2, figsize=(16 * CM, 10 * CM))
    resumo["dia14"] = {"creditos": int(len(foto)), "default_pct": round(float(y.mean() * 100), 3)}
    for ax, (titulo, serie, cortes, rot) in zip(axs.flat, paineis):
        r, t, n = _faixas(serie, y, cortes, rot)
        _barras_taxa(ax, r, t, n, titulo)
        resumo["dia14"][titulo] = dict(zip(r, [round(v, 2) for v in t]))
    for ax in axs[:, 0]:
        ax.set_ylabel("Taxa de default")
    fig.tight_layout()
    fig.savefig(OUT / "fig_comportamento_dia14.png")
    plt.close(fig)


# ------------------------------------------------------------------ #
# 4. Histórico do cliente e default                                   #
# ------------------------------------------------------------------ #

def fig_historico(h, d, resumo):
    x = h.join(d[["evento_tipo"]], how="inner")
    y = (x["evento_tipo"] == 1).astype(int)
    com = x["n_creditos_previos"] > 0
    fig, axs = plt.subplots(2, 2, figsize=(16 * CM, 10 * CM))
    resumo["historico"] = {}
    r, t = ["Primeiro\ncrédito", "Com créditos\nanteriores"], [y[~com].mean() * 100, y[com].mean() * 100]
    _barras_taxa(axs[0, 0], r, t, [(~com).sum(), com.sum()], "Primeiro crédito do cliente")
    resumo["historico"]["primeiro_credito"] = dict(zip(r, [round(v, 2) for v in t]))
    paineis = [
        (axs[0, 1], "Pontualidade no crédito anterior", x["ult_pontualidade"],
         [-0.01, 0.7, 0.85, 0.95, 1], ["até 70%", "70 a 85%", "85 a 95%", "acima\nde 95%"]),
        (axs[1, 0], "Prazo usado no crédito anterior", x["ult_razao_prazo"],
         [-0.01, 0.9, 1.0, 1.2, 20], ["até 0,9", "0,9 a 1,0", "1,0 a 1,2", "acima\nde 1,2"]),
        (axs[1, 1], "Último pagamento do crédito anterior (em parcelas)", x["ult_pago_final_rel"],
         [-0.01, 1.5, 3, 9, 1000], ["até 1,5", "1,5 a 3", "3 a 9", "acima\nde 9"]),
    ]
    for ax, titulo, serie, cortes, rot in paineis:
        m = serie.notna() & com
        r, t, n = _faixas(serie[m], y[m], cortes, rot)
        _barras_taxa(ax, r, t, n, titulo)
        resumo["historico"][titulo] = dict(zip(r, [round(v, 2) for v in t]))
    for ax in axs[:, 0]:
        ax.set_ylabel("Taxa de default")
    fig.tight_layout()
    fig.savefig(OUT / "fig_historico_cliente.png")
    plt.close(fig)


# ------------------------------------------------------------------ #
# 5 e 6. Calendário de cobrança e evolução mensal                     #
# ------------------------------------------------------------------ #

def figs_calendario(pagos, creditos, resumo):
    pagos = pagos.join(creditos["rta_id"], on="cred")
    pagos["uf"] = pagos["rta_id"].map(lambda r: UF_RUTA.get(int(r), "SP") if pd.notna(r) else "SP")
    dias = pd.date_range("2020-07-01", "2026-05-10")
    linhas = []
    for uf, g in pagos.groupby("uf"):
        por_dia = g.groupby("fecha").size().reindex(dias, fill_value=0)
        anos = range(2020, 2027)
        fer = holidays.Brazil(years=anos, subdiv=uf)
        opc = holidays.Brazil(years=anos, subdiv=uf, categories=("optional",))
        for dia, n in por_dia.items():
            if dia.dayofweek == 6:
                tipo = "Domingo"
            elif dia.date() in fer:
                tipo = "Feriado"
            elif "Carnaval" in (opc.get(dia.date()) or ""):
                tipo = "Carnaval"
            else:
                tipo = "Sábado" if dia.dayofweek == 5 else "Dia útil"
            linhas.append((uf, tipo, n))
    t = pd.DataFrame(linhas, columns=["uf", "tipo", "n"]).groupby(["uf", "tipo"])["n"].mean().unstack()
    rel = (t.div(t["Dia útil"], axis=0) * 100).mean()
    ordem = ["Dia útil", "Sábado", "Carnaval", "Feriado", "Domingo"]
    rel = rel[ordem]
    resumo["cobranca_relativa"] = {k: round(float(v), 1) for k, v in rel.items()}

    fig, ax = plt.subplots(figsize=(16 * CM, 5.5 * CM))
    yy = np.arange(len(ordem))[::-1]
    ax.barh(yy, rel.values, height=0.55, color=AZUL)
    for yi, v in zip(yy, rel.values):
        ax.text(v + 1.5, yi, f"{v:.0f}%", va="center", fontsize=8)
    ax.set_yticks(yy, ordem)
    ax.set_xlim(0, 115)
    ax.set_xlabel("Pagamentos por dia em relação a um dia útil (média de SP, RJ e SC)")
    ax.grid(axis="y", visible=False)
    fig.savefig(OUT / "fig_cobranca_tipo_dia.png")
    plt.close(fig)

    mensal = pagos.set_index("fecha").resample("MS").size()
    resumo["pagamentos_mensais_2026_04"] = int(mensal["2026-04"].iloc[0])
    mensal = mensal["2020-01":"2021-12"]
    resumo["pagamentos_mensais"] = {"2020-03": int(mensal["2020-03"].iloc[0]),
                                    "2020-04": int(mensal["2020-04"].iloc[0]),
                                    "2020-05": int(mensal["2020-05"].iloc[0]),
                                    "2020-12": int(mensal["2020-12"].iloc[0])}
    fig, ax = plt.subplots(figsize=(16 * CM, 5.5 * CM))
    ax.axvspan(pd.Timestamp("2020-03-15"), pd.Timestamp("2020-12-31"), color=GRADE, alpha=0.5, lw=0)
    ax.text(pd.Timestamp("2020-06-01"), mensal.max() * 0.92, "Pandemia (março a dezembro de 2020)",
            fontsize=7.5, color=TINTA_SUAVE)
    ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%m/%Y"))
    ax.plot(mensal.index, mensal.values, color=AZUL, lw=2)
    ax.set_ylabel("Pagamentos por mês")
    ax.set_ylim(0)
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(
        lambda v, _: f"{v:,.0f}".replace(",", ".")))
    fig.savefig(OUT / "fig_pagamentos_mensais.png")
    plt.close(fig)


# ------------------------------------------------------------------ #
# Tabela regional                                                     #
# ------------------------------------------------------------------ #

def tabela_regioes(resumo):
    k = pd.read_csv(PROC / "kpis_clientes.csv")
    k = k[k["fonte_regiao"] == "ddd"]
    g = k.groupby("regiao_cliente").agg(clientes=("codigo_cliente", "size"),
                                        volaram=("cliente_volou", "mean"))
    g = g[g["clientes"] >= 100].sort_values("volaram", ascending=False)
    resumo["regioes_ddd"] = {r: {"clientes": int(v.clientes), "pct_volaram": round(float(v.volaram) * 100, 1)}
                             for r, v in g.iterrows()}
    resumo["clientes_sem_ddd"] = int((pd.read_csv(PROC / "kpis_clientes.csv")["fonte_regiao"] != "ddd").sum())


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    OUT.mkdir(parents=True, exist_ok=True)
    d = pd.read_csv(PROC / "desenlaces_v2.csv", index_col="CÓDIGO CRÉDITO")
    df = pd.read_csv(PROC / "survival_dataset_v2_b7.csv")
    d = d.join(df.groupby("CÓDIGO CRÉDITO")["ofi_id"].first())
    h = pd.read_csv(PROC / "historial_cliente.csv", index_col=0)
    resumo = {"tempo_mediano": {k: float(v) for k, v in
                                d.groupby("evento_tipo")["T"].median().rename({0: "censura", 1: "default", 2: "cura"}).items()}}

    fig_cif(d, resumo)
    fig_escritorio(d, resumo)
    fig_dia14(df, d, resumo)
    fig_historico(h, d, resumo)
    tabela_regioes(resumo)
    creditos, pagos = _extraer(MATRIZ)
    pagos = pagos[pagos["cred"].isin(d.index.astype(str))]
    figs_calendario(pagos, creditos, resumo)

    (OUT / "eda_resumo.json").write_text(json.dumps(resumo, ensure_ascii=False, indent=1))
    logging.info("Figuras em %s", OUT)


if __name__ == "__main__":
    main()
