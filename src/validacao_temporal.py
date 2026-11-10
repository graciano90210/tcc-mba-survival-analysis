"""
Validación temporal (Sprint 5): entrenar con el pasado y probar con el futuro.

La validación cruzada por cliente de cox_v2.py mezcla años: un crédito de 2021
puede quedar en prueba y uno de 2025 en entrenamiento. Aquí se simula el uso
real: el modelo se ajusta con los créditos desembolsados hasta 2024 y se evalúa
con los de enero a septiembre de 2025. Los de octubre de 2025 en adelante se
dejan fuera porque al corte (15/05/2026) todavía no pasaron 120 días para
confirmar un default.

Mismos modelos, variables y landmarks que cox_v2.py. Como hay un único conjunto
de prueba, los intervalos de confianza salen de un bootstrap de los créditos de
prueba.

Salida: reports/modelagem_v2/metricas_temporal.csv
"""

import logging

import numpy as np
import pandas as pd
from lifelines import CoxPHFitter
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

from cox_v2 import (BASE, CONTRATO, HISTORIAL_COLS, LANDMARKS, OUT_DIR, REGRAS_SIMPLES,
                    SEMILLA, _captura_top, _cargar, _preparar)
from reconstruir_dataset import SALIDA_DESENL

BLOQUE         = 7
FIM_TREINO     = pd.Timestamp("2025-01-01")    # treino: desembolsos antes desta data
INICIO_TESTE   = pd.Timestamp("2025-01-01")
FIM_TESTE      = pd.Timestamp("2025-10-01")    # depois disso o default ainda não se confirma
N_BOOTSTRAP    = 1000


def _ic(y, riesgo, rng):
    """Intervalo de 95% por bootstrap dos créditos de teste."""
    aucs, caps = [], []
    n = len(y)
    for _ in range(N_BOOTSTRAP):
        i = rng.integers(0, n, n)
        if 0 < y[i].sum() < n:
            aucs.append(roc_auc_score(y[i], riesgo[i]))
            caps.append(_captura_top(y[i], riesgo[i]))
    return np.percentile(aucs, [2.5, 97.5]), np.percentile(caps, [2.5, 97.5])


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    df = _cargar(BLOQUE)
    fechas = pd.read_csv(SALIDA_DESENL, parse_dates=["fecha_credito"]).set_index("CÓDIGO CRÉDITO")
    df = df.join(fechas["fecha_credito"], on="CÓDIGO CRÉDITO")
    fin = df.groupby("CÓDIGO CRÉDITO").agg(T=("t_stop", "max"), y=("evento", "max"),
                                            cura=("evento_cura", "max"))
    t_max = fin["T"].max()
    rng = np.random.default_rng(SEMILLA)
    filas = []
    for L in LANDMARKS[:2]:
        inicio = (L // BLOQUE) * BLOQUE
        foto = df[df["t_start"] == inicio].join(fin, on="CÓDIGO CRÉDITO")
        foto["dur_fg"] = np.where(foto["cura"] == 1, t_max, foto["T"]) - inicio
        treino = foto[foto["fecha_credito"] < FIM_TREINO]
        teste = foto[(foto["fecha_credito"] >= INICIO_TESTE) & (foto["fecha_credito"] < FIM_TESTE)]
        logging.info("dia %d: treino %d créditos (%d defaults) | teste %d (%d defaults)",
                     L, len(treino), treino["y"].sum(), len(teste), teste["y"].sum())

        modelos = {
            "fine_gray": ("fg", BASE),
            "logistica": ("lr", BASE),
            "logistica_solo_historial": ("lr", HISTORIAL_COLS + CONTRATO),
        }
        for nome, (tipo, covs) in modelos.items():
            tr, te, _ = _preparar(treino.copy(), teste.copy(), covs)
            if tipo == "fg":
                m = CoxPHFitter(penalizer=0.01).fit(tr[covs + ["dur_fg", "y"]], "dur_fg", "y")
                riesgo = m.predict_partial_hazard(te[covs]).values
            else:
                m = LogisticRegression(max_iter=2000).fit(tr[covs], tr["y"])
                riesgo = m.predict_proba(te[covs])[:, 1]
            filas.append((L, nome, te["y"].values, riesgo))
        for nome, (col, sinal) in REGRAS_SIMPLES.items():
            riesgo = sinal * teste[col].fillna(0).values + 1e-9 * rng.random(len(teste))
            filas.append((L, nome, teste["y"].values, riesgo))

    saida = []
    for L, nome, y, riesgo in filas:
        ic_auc, ic_cap = _ic(y, riesgo, rng)
        saida.append({"landmark": L, "modelo": nome, "defaults_teste": int(y.sum()),
                      "auc": roc_auc_score(y, riesgo), "auc_ic_inf": ic_auc[0], "auc_ic_sup": ic_auc[1],
                      "captura_top10": _captura_top(y, riesgo),
                      "captura_ic_inf": ic_cap[0], "captura_ic_sup": ic_cap[1]})
    saida = pd.DataFrame(saida)
    saida.round(4).to_csv(OUT_DIR / "metricas_temporal.csv", index=False)
    with pd.option_context("display.width", 200):
        print(saida.round(3))


if __name__ == "__main__":
    main()
