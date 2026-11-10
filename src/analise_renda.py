"""
Abandono por faixa de renda do entorno do cliente (Sprint 5).

Usa data/processed/clientes_setor.csv (renda_setor.py): renda média do
responsável no setor censitário do cliente (Censo 2022). Divide os clientes em
quintis dessa renda e compara a porcentagem que abandonou algum crédito, no
total e por estado, e estima o efeito da renda com uma regressão logística
(com e sem controle do escritório).

Saídas: reports/figuras_v27/renda_quintis.csv e renda_quintis_uf.csv
"""

from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from statsmodels.stats.proportion import proportion_confint

_RAIZ = Path(__file__).parent.parent
PROC  = _RAIZ / "data" / "processed"
OUT   = _RAIZ / "reports" / "figuras_v27"
QUINTIS = ["Q1 (mais pobre)", "Q2", "Q3", "Q4", "Q5 (mais rico)"]


def main():
    x = pd.read_csv(PROC / "clientes_setor.csv", dtype={"CD_SETOR": str})
    k = pd.read_csv(PROC / "kpis_clientes.csv", usecols=["codigo_cliente", "cliente_volou", "oficina"])
    x = x.merge(k, on="codigo_cliente").dropna(subset=["renda_media_setor"])
    x["quintil"] = pd.qcut(x["renda_media_setor"], 5, labels=QUINTIS)

    g = x.groupby("quintil", observed=True).agg(
        clientes=("codigo_cliente", "size"), abandonaram=("cliente_volou", "sum"),
        renda_min=("renda_media_setor", "min"), renda_max=("renda_media_setor", "max"))
    inf, sup = proportion_confint(g["abandonaram"], g["clientes"], method="wilson")
    g["pct"] = 100 * g["abandonaram"] / g["clientes"]
    g["ic95_inf"], g["ic95_sup"] = 100 * inf, 100 * sup
    g.round(2).to_csv(OUT / "renda_quintis.csv")

    uf = x.groupby(["UF", "quintil"], observed=True)["cliente_volou"].agg(["size", "mean"])
    uf["mean"] *= 100
    uf.round(2).to_csv(OUT / "renda_quintis_uf.csv")

    x["log_renda"] = np.log(x["renda_media_setor"])
    for nome, formula in [("sem controle", "cliente_volou ~ log_renda"),
                          ("com escritório", "cliente_volou ~ log_renda + C(oficina)")]:
        m = smf.logit(formula, data=x).fit(disp=0)
        b = m.params["log_renda"] * np.log(2)
        lo, hi = m.conf_int().loc["log_renda"] * np.log(2)
        print(f"{nome}: razão de chances ao dobrar a renda = {np.exp(b):.2f} "
              f"(IC95% {np.exp(lo):.2f} a {np.exp(hi):.2f}), p = {m.pvalues['log_renda']:.3f}")
    print(g.round(1))
    print(uf.round(1).unstack(0))


if __name__ == "__main__":
    main()
