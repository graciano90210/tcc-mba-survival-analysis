"""
As variáveis macroeconômicas acrescentam algo ao modelo? (Sprint 5)

Cada crédito recebe a Selic, o IPCA em 12 meses e a desocupação do mês do seu
21º dia (data/external/macro_bcb.csv, de macro_bcb.py), mais um indicador da
pandemia (março a dezembro de 2020, quando os pagamentos caíram; Seção 6.5).

1. Todos os créditos, landmark do dia 21: modelo de Fine e Gray (simplificado)
   com e sem as variáveis macro, razões de risco e teste da razão de
   verossimilhança (sem penalização, para o teste ser válido).
2. Validação temporal (treino até 2024, teste jan a set de 2025), com e sem macro.

Saídas em reports/modelagem_v2/: macro_coeficientes.csv e macro_temporal.csv
"""

import logging
from pathlib import Path

import numpy as np
import pandas as pd
from lifelines import CoxPHFitter
from scipy import stats
from sklearn.metrics import roc_auc_score

from cox_v2 import BASE, OUT_DIR, SEMILLA, _captura_top, _cargar, _preparar
from reconstruir_dataset import SALIDA_DESENL
from validacao_temporal import BLOQUE, FIM_TESTE, FIM_TREINO, INICIO_TESTE

LANDMARK = 21
MACRO_CSV = Path(__file__).parent.parent / "data" / "external" / "macro_bcb.csv"
MACRO = ["selic", "ipca_12m", "desocupacao", "pandemia"]
N_BOOTSTRAP = 1000


def _foto():
    df = _cargar(BLOQUE)
    datas = pd.read_csv(SALIDA_DESENL, parse_dates=["fecha_credito"]).set_index("CÓDIGO CRÉDITO")
    df = df.join(datas["fecha_credito"], on="CÓDIGO CRÉDITO")
    fin = df.groupby("CÓDIGO CRÉDITO").agg(T=("t_stop", "max"), y=("evento", "max"),
                                            cura=("evento_cura", "max"))
    t_max = fin["T"].max()
    inicio = (LANDMARK // BLOQUE) * BLOQUE
    foto = df[df["t_start"] == inicio].join(fin, on="CÓDIGO CRÉDITO")
    foto["dur_fg"] = np.where(foto["cura"] == 1, t_max, foto["T"]) - inicio
    macro = pd.read_csv(MACRO_CSV, parse_dates=["mes"]).set_index("mes")
    mes = (foto["fecha_credito"] + pd.Timedelta(days=LANDMARK)).dt.to_period("M").dt.to_timestamp()
    foto = pd.concat([foto, macro.reindex(mes.to_numpy()).set_index(foto.index)], axis=1)
    foto["pandemia"] = ((mes >= "2020-03-01") & (mes <= "2020-12-01")).astype(int)
    return foto


def _fg(tr, covs, pen):
    return CoxPHFitter(penalizer=pen).fit(tr[covs + ["dur_fg", "y"]], "dur_fg", "y")


def coeficientes(foto):
    covs = BASE + MACRO
    tr, _, _ = _preparar(foto.copy(), foto.iloc[:1].copy(), covs)
    sem, com = _fg(tr, BASE, 0.0), _fg(tr, covs, 0.0)
    lr = 2 * (com.log_likelihood_ - sem.log_likelihood_)
    p = stats.chi2.sf(lr, df=len(MACRO))
    logging.info("razão de verossimilhança (4 gl): %.2f, p = %.4f", lr, p)
    c = com.summary.loc[MACRO, ["exp(coef)", "exp(coef) lower 95%", "exp(coef) upper 95%", "p"]]
    c.columns = ["shr", "ic95_inf", "ic95_sup", "p"]
    c.loc["teste_rv_4gl"] = [lr, np.nan, np.nan, p]
    logging.info("créditos na pandemia: %d (%d defaults)",
                 foto["pandemia"].sum(), foto.loc[foto["pandemia"] == 1, "y"].sum())
    return c


def temporal(foto, rng):
    treino = foto[foto["fecha_credito"] < FIM_TREINO]
    teste = foto[(foto["fecha_credito"] >= INICIO_TESTE) & (foto["fecha_credito"] < FIM_TESTE)]
    for v in MACRO[:3]:
        logging.info("  %s: treino %.2f a %.2f | teste %.2f a %.2f", v, treino[v].min(),
                     treino[v].max(), teste[v].min(), teste[v].max())
    riscos = {}
    for nome, covs in [("fine_gray", BASE), ("fine_gray_macro", BASE + MACRO)]:
        tr, te, _ = _preparar(treino.copy(), teste.copy(), covs)
        riscos[nome] = _fg(tr, covs, 0.01).predict_partial_hazard(te[covs]).to_numpy()
    y = teste["y"].to_numpy()
    dif = []
    for _ in range(N_BOOTSTRAP):
        i = rng.integers(0, len(y), len(y))
        if 0 < y[i].sum() < len(y):
            dif.append(_captura_top(y[i], riscos["fine_gray_macro"][i]) - _captura_top(y[i], riscos["fine_gray"][i]))
    linhas = [{"modelo": k, "auc": roc_auc_score(y, r), "captura_top10": _captura_top(y, r)}
              for k, r in riscos.items()]
    linhas.append({"modelo": "dif_macro_menos_base",
                   "captura_top10": linhas[1]["captura_top10"] - linhas[0]["captura_top10"],
                   "captura_ic_inf": np.percentile(dif, 2.5), "captura_ic_sup": np.percentile(dif, 97.5)})
    return pd.DataFrame(linhas)


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    foto = _foto()
    coefs = coeficientes(foto)
    coefs.round(4).to_csv(OUT_DIR / "macro_coeficientes.csv")
    met = temporal(foto, np.random.default_rng(SEMILLA))
    met.round(4).to_csv(OUT_DIR / "macro_temporal.csv", index=False)
    with pd.option_context("display.width", 200):
        print(coefs.round(3))
        print(met.round(3))


if __name__ == "__main__":
    main()
