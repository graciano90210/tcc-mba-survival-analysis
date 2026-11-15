"""
Interpretação das previsões com valores SHAP (Sprint 6; Lundberg e Lee, 2017).

Modelo de Fine e Gray do dia 21, treinado com os créditos de 2020 a 2024 e
aplicado aos créditos de janeiro a setembro de 2025 (mesmo desenho da
validação temporal). Como o modelo é linear no logaritmo do risco, os valores
SHAP são exatos: a contribuição de cada variável é o quanto ela afasta o risco
daquele crédito do risco médio do treino.

Saídas
  reports/figuras_sprint6/shap_beeswarm.png   importância e direção de cada variável
  reports/figuras_sprint6/shap_exemplo.png    explicação de um crédito de alto risco
  reports/modelagem_v2/shap_importancia.csv   média do valor SHAP absoluto
  reports/modelagem_v2/shap_exemplos_lista.csv  créditos em seis posições do top 10% do
                                              teste, anonimizados, com os três principais motivos
Nenhum nome ou código de cliente sai nas figuras ou tabelas (LGPD).
"""

import logging
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap
from lifelines import CoxPHFitter

from cox_v2 import BASE, OUT_DIR, _cargar, _preparar
from reconstruir_dataset import SALIDA_DESENL
from validacao_temporal import BLOQUE, FIM_TESTE, FIM_TREINO, INICIO_TESTE

LANDMARK = 21
FIG_DIR = Path(__file__).parent.parent / "reports" / "figuras_sprint6"
NOMES = {
    "ratio_atraso": "Atraso relativo",
    "saldo_relativo": "Saldo relativo a pagar",
    "dias_con_abono_prev": "Dias com pagamento na semana anterior",
    "pago_relativo_prev": "Pagamento em relação à parcela",
    "pct_abono_incompleto": "Proporção de pagamentos incompletos",
    "dias_sin_cobro_bloque": "Dias sem cobrança na semana",
    "log_total_credito": "Valor do crédito (log)",
    "plazo_dias": "Prazo do crédito",
    "ofi_31": "Escritório Sociedades Brasil",
    "ofi_44": "Escritório Cabo Frio",
    "primeiro_credito": "Primeiro crédito do cliente",
    "ult_pontualidade": "Pontualidade no crédito anterior",
    "ult_razao_prazo": "Prazo usado no crédito anterior",
    "ult_log_pago_final": "Pagamento final do crédito anterior (log)",
    "hist_pct_parcela_incompleta": "Histórico de parcelas incompletas",
}


def _motivo(var, valor):
    """Frase curta, na linguagem da operação, para o valor original da variável."""
    if var == "dias_con_abono_prev":
        return f"pagou em {valor:.0f} de 7 dias na semana anterior"
    if var == "pago_relativo_prev":
        return f"pagou {100 * valor:.0f}% da parcela por dia na semana anterior"
    if var == "saldo_relativo":
        return f"ainda deve {100 * valor:.0f}% do total"
    if var == "ratio_atraso":
        return f"parcelas atrasadas equivalentes a {100 * valor:.0f}% do total de parcelas"
    if var == "pct_abono_incompleto":
        return f"{100 * valor:.0f}% dos pagamentos foram incompletos"
    if var == "ofi_31":
        return "escritório Sociedades Brasil" if valor == 1 else "fora de Sociedades Brasil"
    if var == "log_total_credito":
        return f"crédito de R$ {np.exp(valor):,.0f}".replace(",", ".")
    if var == "ult_log_pago_final":
        return f"pagamento final do crédito anterior de {np.expm1(valor):.1f} parcelas".replace(".", ",")
    if var == "plazo_dias":
        return f"prazo de {valor:.0f} dias"
    if var == "primeiro_credito":
        return "primeiro crédito do cliente" if valor == 1 else "cliente com histórico"
    return f"{NOMES[var].lower()}: {valor:.2f}"


def _figura_exemplo(valores, brutos, posicao, n, k=7):
    """Barras horizontais: quantas vezes cada variável multiplica o risco desse
    crédito em relação ao crédito médio (exp do valor SHAP)."""
    s = pd.Series(valores, index=BASE)
    principais = s.reindex(s.abs().sort_values(ascending=False).index[:k])
    resto = s.drop(principais.index).sum()
    rotulos = [_motivo(v, brutos[v]) for v in principais.index] + ["demais variáveis"]
    fatores = np.exp(np.append(principais.to_numpy(), resto))
    ordem = np.arange(len(fatores))[::-1]
    fig, ax = plt.subplots(figsize=(10, 5))
    cores = ["#c0392b" if f > 1 else "#2471a3" for f in fatores]
    ax.barh(ordem, np.log(fatores), color=cores)
    for y, f in zip(ordem, fatores):
        ax.text(np.log(f) + (0.03 if f > 1 else -0.03), y, f"×{f:.2f}".replace(".", ","),
                va="center", ha="left" if f > 1 else "right", fontsize=10)
    ax.set_yticks(ordem, [r[0].upper() + r[1:] for r in rotulos], fontsize=10)
    ax.axvline(0, color="gray", lw=0.8)
    lim = np.abs(np.log(fatores)).max() * 1.35
    ax.set_xlim(-lim, lim)
    ax.set_xticks([])
    ax.set_xlabel("Vermelho: eleva o risco; azul: reduz. O número indica quantas vezes "
                  "multiplica o risco em relação ao crédito médio.", fontsize=9)
    total = np.exp(s.sum())
    ax.set_title(f"Crédito na posição {posicao} de {n} no dia 21 (risco {total:.0f} vezes "
                 "o do crédito médio; terminou em default)".replace(".", ","), fontsize=11)
    for lado in ("top", "right", "left"):
        ax.spines[lado].set_visible(False)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "shap_exemplo.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


def _dados():
    df = _cargar(BLOQUE)
    datas = pd.read_csv(SALIDA_DESENL, parse_dates=["fecha_credito"]).set_index("CÓDIGO CRÉDITO")
    df = df.join(datas["fecha_credito"], on="CÓDIGO CRÉDITO")
    fin = df.groupby("CÓDIGO CRÉDITO").agg(T=("t_stop", "max"), y=("evento", "max"),
                                            cura=("evento_cura", "max"))
    t_max = fin["T"].max()
    inicio = (LANDMARK // BLOQUE) * BLOQUE
    foto = df[df["t_start"] == inicio].join(fin, on="CÓDIGO CRÉDITO")
    foto["dur_fg"] = np.where(foto["cura"] == 1, t_max, foto["T"]) - inicio
    treino = foto[foto["fecha_credito"] < FIM_TREINO]
    teste = foto[(foto["fecha_credito"] >= INICIO_TESTE) & (foto["fecha_credito"] < FIM_TESTE)]
    return treino, teste


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    treino, teste = _dados()
    tr, te, _ = _preparar(treino.copy(), teste.copy(), BASE)
    fg = CoxPHFitter(penalizer=0.01).fit(tr[BASE + ["dur_fg", "y"]], "dur_fg", "y")
    beta = fg.params_[BASE].to_numpy()

    fundo = shap.maskers.Independent(tr[BASE].to_numpy(), max_samples=len(tr))
    explainer = shap.LinearExplainer((beta, 0.0), fundo)
    sv = explainer(te[BASE].to_numpy())
    # conferência: a soma dos valores SHAP reproduz o log do risco relativo
    log_risco = te[BASE].to_numpy() @ beta
    erro = np.abs(sv.values.sum(1) + sv.base_values - log_risco).max()
    logging.info("conferência SHAP (erro máximo): %.2e", erro)

    # valores originais (não padronizados) para mostrar nas figuras e motivos
    brutos = teste[BASE].fillna(treino[BASE].median())
    sv.data = brutos.to_numpy()
    sv.feature_names = [NOMES[c] for c in BASE]

    imp = pd.DataFrame({"variavel": [NOMES[c] for c in BASE],
                        "media_shap_abs": np.abs(sv.values).mean(0)}).sort_values(
        "media_shap_abs", ascending=False)
    imp.round(4).to_csv(OUT_DIR / "shap_importancia.csv", index=False)

    plt.figure()
    shap.plots.beeswarm(sv, max_display=15, show=False, color_bar_label="Valor da variável")
    fig = plt.gcf()
    fig.axes[-1].set_yticklabels(["Baixo", "Alto"])          # barra de cores
    fig.axes[0].set_xlabel("Contribuição ao risco de default (escala logarítmica)")
    fig.axes[0].xaxis.set_major_formatter(
        matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:.1f}".replace(".", ",")))
    fig.set_size_inches(10, 7)
    plt.tight_layout()
    plt.savefig(FIG_DIR / "shap_beeswarm.png", dpi=200, bbox_inches="tight")
    plt.close("all")

    # créditos em posições diferentes do top 10%: no topo estão os que já pararam de
    # pagar (óbvio para a operação); no meio da lista os motivos variam
    ordem = np.argsort(-log_risco)
    y = teste["y"].to_numpy()
    n_top = int(np.ceil(0.10 * len(y)))
    posicoes = [1, 25, 75, 150, 250, n_top]
    linhas = []
    for pos in posicoes:
        i = ordem[pos - 1]
        contrib = pd.Series(sv.values[i], index=BASE).sort_values(ascending=False)
        motivos = [_motivo(v, brutos.iloc[i][v]) for v in contrib.index[:3] if contrib[v] > 0]
        linhas.append({"posicao": pos, "risco_relativo": float(np.exp(log_risco[i] - sv.base_values[i])),
                       "terminou_em_default": "sim" if y[i] == 1 else "não",
                       "motivo_1": motivos[0] if len(motivos) > 0 else "",
                       "motivo_2": motivos[1] if len(motivos) > 1 else "",
                       "motivo_3": motivos[2] if len(motivos) > 2 else ""})
    top = pd.DataFrame(linhas)
    top.round(1).to_csv(OUT_DIR / "shap_exemplos_lista.csv", index=False)

    # exemplo: o crédito de maior risco que terminou em default embora ainda pagasse
    # em alguns dias da semana anterior (caso menos óbvio que o de quem parou de pagar)
    pagava = brutos["dias_con_abono_prev"].to_numpy() >= 2
    exemplo = next(i for i in ordem if y[i] == 1 and pagava[i])
    pos_ex = int(np.where(ordem == exemplo)[0][0]) + 1
    logging.info("exemplo: posição %d na lista", pos_ex)
    _figura_exemplo(sv.values[exemplo], brutos.iloc[exemplo], pos_ex, len(y))

    logging.info("teste: %d créditos, %d defaults; top 10%% = %d créditos com %d defaults",
                 len(y), y.sum(), n_top, y[ordem[:n_top]].sum())
    with pd.option_context("display.width", 220, "display.max_colwidth", 60):
        print(imp.round(3).to_string(index=False))
        print(top.to_string(index=False))


if __name__ == "__main__":
    main()
