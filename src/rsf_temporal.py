"""
Random Survival Forest (Ishwaran et al., 2008) na validação temporal (Sprint 5).

Pergunta: um modelo não linear, que capta interações entre as variáveis sem
precisar especificá-las, coloca mais futuros defaults entre os 10% de maior
risco do que o modelo de Fine e Gray?

Mesmo desenho de validacao_temporal.py: landmarks nos dias 14 e 21, treino com
os créditos desembolsados até 2024, teste com os de janeiro a setembro de 2025.
A quitação entra como no Fine e Gray simplificado: o crédito quitado continua
no conjunto de risco até o fim do seguimento (o scikit-survival não tem riscos
competitivos; o fine_gray_ipcw.py mostrou que essa simplificação ordena os
clientes praticamente igual ao método exato).

Hiperparâmetros fixos (500 árvores, ao menos 15 créditos por folha, raiz do
número de variáveis em cada divisão), sem ajuste olhando o teste.

Saídas em reports/modelagem_v2/: rsf_temporal.csv (métricas com IC por
bootstrap e diferença pareada contra o Fine e Gray) e rsf_importancia.csv
(importância por permutação no dia 21, queda do C-index).
"""

import logging

import numpy as np
import pandas as pd
from lifelines import CoxPHFitter
from sklearn.inspection import permutation_importance
from sklearn.metrics import roc_auc_score
from sksurv.ensemble import RandomSurvivalForest
from sksurv.metrics import concordance_index_censored
from sksurv.util import Surv

from cox_v2 import BASE, OUT_DIR, SEMILLA, _captura_top, _cargar, _preparar
from reconstruir_dataset import SALIDA_DESENL
from validacao_temporal import BLOQUE, FIM_TESTE, FIM_TREINO, INICIO_TESTE

LANDMARKS   = (14, 21)
N_BOOTSTRAP = 1000
RSF_PARAMS  = dict(n_estimators=500, min_samples_leaf=15, max_features="sqrt",
                   n_jobs=6, random_state=SEMILLA)


def _fotos():
    df = _cargar(BLOQUE)
    datas = pd.read_csv(SALIDA_DESENL, parse_dates=["fecha_credito"]).set_index("CÓDIGO CRÉDITO")
    df = df.join(datas["fecha_credito"], on="CÓDIGO CRÉDITO")
    fin = df.groupby("CÓDIGO CRÉDITO").agg(T=("t_stop", "max"), y=("evento", "max"),
                                            cura=("evento_cura", "max"))
    t_max = fin["T"].max()
    for L in LANDMARKS:
        inicio = (L // BLOQUE) * BLOQUE
        foto = df[df["t_start"] == inicio].join(fin, on="CÓDIGO CRÉDITO")
        foto["dur_fg"] = np.where(foto["cura"] == 1, t_max, foto["T"]) - inicio
        treino = foto[foto["fecha_credito"] < FIM_TREINO]
        teste = foto[(foto["fecha_credito"] >= INICIO_TESTE) & (foto["fecha_credito"] < FIM_TESTE)]
        tr, te, _ = _preparar(treino.copy(), teste.copy(), BASE)
        yield L, tr, te


def _cindex(te, risco):
    return concordance_index_censored(te["y"].astype(bool).to_numpy(),
                                      te["dur_fg"].to_numpy(dtype=float), risco)[0]


def _bootstrap(y, riscos, rng):
    """IC de 95% de cada modelo e da diferença pareada RSF menos Fine e Gray."""
    n, acc = len(y), {k: {"auc": [], "cap": []} for k in list(riscos) + ["dif"]}
    for _ in range(N_BOOTSTRAP):
        i = rng.integers(0, n, n)
        if not 0 < y[i].sum() < n:
            continue
        for nome, r in riscos.items():
            acc[nome]["auc"].append(roc_auc_score(y[i], r[i]))
            acc[nome]["cap"].append(_captura_top(y[i], r[i]))
        acc["dif"]["auc"].append(acc["rsf"]["auc"][-1] - acc["fine_gray"]["auc"][-1])
        acc["dif"]["cap"].append(acc["rsf"]["cap"][-1] - acc["fine_gray"]["cap"][-1])
    return {k: {m: np.percentile(v, [2.5, 97.5]) for m, v in d.items()} for k, d in acc.items()}, acc["dif"]


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    rng = np.random.default_rng(SEMILLA)
    linhas, importancia = [], None
    for L, tr, te in _fotos():
        logging.info("dia %d: treino %d (%d defaults) | teste %d (%d defaults)",
                     L, len(tr), tr["y"].sum(), len(te), te["y"].sum())
        y_tr = Surv.from_arrays(tr["y"].astype(bool), tr["dur_fg"].astype(float))
        rsf = RandomSurvivalForest(**RSF_PARAMS).fit(tr[BASE], y_tr)
        fg = CoxPHFitter(penalizer=0.01).fit(tr[BASE + ["dur_fg", "y"]], "dur_fg", "y")
        riscos = {"rsf": rsf.predict(te[BASE]),
                  "fine_gray": fg.predict_partial_hazard(te[BASE]).to_numpy()}
        y = te["y"].to_numpy()
        ic, dif = _bootstrap(y, riscos, rng)
        for nome, r in riscos.items():
            linhas.append({"landmark": L, "modelo": nome, "defaults_teste": int(y.sum()),
                           "auc": roc_auc_score(y, r), "auc_ic_inf": ic[nome]["auc"][0],
                           "auc_ic_sup": ic[nome]["auc"][1], "cindex": _cindex(te, r),
                           "captura_top10": _captura_top(y, r),
                           "captura_ic_inf": ic[nome]["cap"][0], "captura_ic_sup": ic[nome]["cap"][1]})
        d_cap = np.asarray(dif["cap"])
        linhas.append({"landmark": L, "modelo": "dif_rsf_menos_fg",
                       "auc": roc_auc_score(y, riscos["rsf"]) - roc_auc_score(y, riscos["fine_gray"]),
                       "auc_ic_inf": ic["dif"]["auc"][0], "auc_ic_sup": ic["dif"]["auc"][1],
                       "captura_top10": _captura_top(y, riscos["rsf"]) - _captura_top(y, riscos["fine_gray"]),
                       "captura_ic_inf": ic["dif"]["cap"][0], "captura_ic_sup": ic["dif"]["cap"][1],
                       "p_boot_captura": 2 * min((d_cap <= 0).mean(), (d_cap >= 0).mean())})
        if L == 21:
            y_te = Surv.from_arrays(te["y"].astype(bool), te["dur_fg"].astype(float))
            p = permutation_importance(rsf, te[BASE], y_te, n_repeats=10,
                                       random_state=SEMILLA, n_jobs=1)
            importancia = pd.DataFrame({"queda_cindex": p.importances_mean,
                                        "dp": p.importances_std}, index=BASE
                                       ).sort_values("queda_cindex", ascending=False)

    saida = pd.DataFrame(linhas)
    saida.round(4).to_csv(OUT_DIR / "rsf_temporal.csv", index=False)
    importancia.round(4).to_csv(OUT_DIR / "rsf_importancia.csv")
    with pd.option_context("display.width", 200):
        print(saida.round(3))
        print(importancia.round(4))


if __name__ == "__main__":
    main()
