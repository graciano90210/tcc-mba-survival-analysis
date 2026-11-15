"""
DeepHit para riscos competitivos (Lee et al., 2018) na validação temporal (Sprint 6).

Diferente do Random Survival Forest e do modelo de fração de cura, o DeepHit
modela os dois desfechos ao mesmo tempo (default e quitação), sem a
simplificação de manter os quitados no conjunto de risco. A rede estima, para
cada crédito, a probabilidade de cada desfecho em cada intervalo de tempo; o
risco usado para ordenar é a incidência acumulada de default no fim do
seguimento.

Mesmo desenho das demais comparações: fotografia do dia 21, treino com os
créditos de 2020 a 2024, teste com os de janeiro a setembro de 2025. Dentro do
treino, 20% dos clientes ficam separados para a parada antecipada (nenhum
cliente aparece nas duas partes). Rede pequena (duas camadas de 32 neurônios,
dropout de 0,2), hiperparâmetros fixos, cinco sementes; a previsão final é a
média das cinco redes.

Saída: reports/modelagem_v2/deephit_temporal.csv
"""

import logging

import numpy as np
import pandas as pd
import torch
import torchtuples as tt
from lifelines import CoxPHFitter
from pycox.models import DeepHit
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import GroupShuffleSplit

from cox_v2 import BASE, OUT_DIR, SEMILLA, _captura_top, _cargar, _preparar
from reconstruir_dataset import SALIDA_DESENL
from validacao_temporal import BLOQUE, FIM_TESTE, FIM_TREINO, INICIO_TESTE

LANDMARK    = 21
N_CORTES    = 30
SEMENTES    = (1, 2, 3, 4, 5)
N_BOOTSTRAP = 1000


class Rede(torch.nn.Module):
    """Camadas compartilhadas e uma cabeça por desfecho (como no artigo original)."""

    def __init__(self, n_entrada, n_riscos, n_tempos, oculto=32, dropout=0.2):
        super().__init__()
        self.n_riscos, self.n_tempos = n_riscos, n_tempos
        self.comum = torch.nn.Sequential(
            torch.nn.Linear(n_entrada, oculto), torch.nn.ReLU(), torch.nn.Dropout(dropout),
            torch.nn.Linear(oculto, oculto), torch.nn.ReLU(), torch.nn.Dropout(dropout))
        self.cabecas = torch.nn.ModuleList(
            torch.nn.Linear(oculto, n_tempos) for _ in range(n_riscos))

    def forward(self, x):
        h = self.comum(x)
        return torch.stack([c(h) for c in self.cabecas], dim=1)


def _foto():
    df = _cargar(BLOQUE)
    datas = pd.read_csv(SALIDA_DESENL, parse_dates=["fecha_credito"]).set_index("CÓDIGO CRÉDITO")
    df = df.join(datas["fecha_credito"], on="CÓDIGO CRÉDITO")
    fin = df.groupby("CÓDIGO CRÉDITO").agg(T=("t_stop", "max"), y=("evento", "max"),
                                            cura=("evento_cura", "max"))
    t_max = fin["T"].max()
    inicio = (LANDMARK // BLOQUE) * BLOQUE
    foto = df[df["t_start"] == inicio].join(fin, on="CÓDIGO CRÉDITO")
    foto["dur"] = (foto["T"] - inicio).astype(float)
    foto["status"] = np.where(foto["y"] == 1, 1, np.where(foto["cura"] == 1, 2, 0))
    foto["dur_fg"] = np.where(foto["cura"] == 1, t_max, foto["T"]) - inicio
    return foto


def _discretizar(dur, cortes):
    """Índice do intervalo de cada duração (o último corte cobre o resto)."""
    return np.clip(np.searchsorted(cortes, dur, side="left"), 0, len(cortes) - 1)


def _ajustar_deephit(tr, va, semente, cortes):
    torch.manual_seed(semente)
    np.random.seed(semente)
    x_tr = tr[BASE].to_numpy("float32")
    x_va = va[BASE].to_numpy("float32")
    y_tr = (_discretizar(tr["dur"].to_numpy(), cortes).astype("int64"),
            tr["status"].to_numpy("int64"))
    y_va = (_discretizar(va["dur"].to_numpy(), cortes).astype("int64"),
            va["status"].to_numpy("int64"))
    rede = Rede(len(BASE), n_riscos=2, n_tempos=len(cortes))
    modelo = DeepHit(rede, tt.optim.Adam(lr=0.005), alpha=0.2, sigma=0.1,
                     duration_index=cortes)
    modelo.fit(x_tr, y_tr, batch_size=256, epochs=200, verbose=False,
               callbacks=[tt.callbacks.EarlyStopping(patience=15)],
               val_data=(x_va, y_va))
    return modelo


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    foto = _foto()
    treino = foto[foto["fecha_credito"] < FIM_TREINO]
    teste = foto[(foto["fecha_credito"] >= INICIO_TESTE) & (foto["fecha_credito"] < FIM_TESTE)]
    tr_all, te, _ = _preparar(treino.copy(), teste.copy(), BASE)

    # grade de tempo: quantis das durações com evento no treino
    cortes = np.unique(np.quantile(tr_all.loc[tr_all["status"] > 0, "dur"],
                                   np.linspace(0, 1, N_CORTES))).astype("float32")
    split = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=SEMILLA)
    i_tr, i_va = next(split.split(tr_all, groups=tr_all["codigo_cliente"]))
    tr, va = tr_all.iloc[i_tr], tr_all.iloc[i_va]
    logging.info("treino %d (%d defaults) | validação %d (%d) | teste %d (%d) | %d cortes",
                 len(tr), (tr["status"] == 1).sum(), len(va), (va["status"] == 1).sum(),
                 len(te), (te["status"] == 1).sum(), len(cortes))

    x_te = te[BASE].to_numpy("float32")
    y = te["y"].to_numpy()
    riscos_sem = []
    for s in SEMENTES:
        m = _ajustar_deephit(tr, va, s, cortes)
        cif = m.predict_cif(x_te)            # (riscos, tempos, créditos)
        r = cif[0, -1, :]
        riscos_sem.append(r)
        logging.info("  semente %d: AUC %.3f, captura %.3f", s, roc_auc_score(y, r), _captura_top(y, r))
    r_dh = np.mean(riscos_sem, axis=0)

    fg = CoxPHFitter(penalizer=0.01).fit(tr_all[BASE + ["dur_fg", "y"]], "dur_fg", "y")
    r_fg = fg.predict_partial_hazard(te[BASE]).to_numpy()

    rng = np.random.default_rng(SEMILLA)
    boot = {"deephit": [], "fine_gray": [], "auc_dh": [], "auc_fg": []}
    for _ in range(N_BOOTSTRAP):
        i = rng.integers(0, len(y), len(y))
        if not 0 < y[i].sum() < len(y):
            continue
        boot["deephit"].append(_captura_top(y[i], r_dh[i]))
        boot["fine_gray"].append(_captura_top(y[i], r_fg[i]))
        boot["auc_dh"].append(roc_auc_score(y[i], r_dh[i]))
        boot["auc_fg"].append(roc_auc_score(y[i], r_fg[i]))
    b = {k: np.asarray(v) for k, v in boot.items()}
    dif = b["deephit"] - b["fine_gray"]
    capt_sem = [_captura_top(y, r) for r in riscos_sem]
    auc_sem = [roc_auc_score(y, r) for r in riscos_sem]
    saida = pd.DataFrame([
        {"modelo": "deephit_media_5_sementes", "auc": roc_auc_score(y, r_dh),
         "auc_ic_inf": np.percentile(b["auc_dh"], 2.5), "auc_ic_sup": np.percentile(b["auc_dh"], 97.5),
         "captura_top10": _captura_top(y, r_dh),
         "captura_ic_inf": np.percentile(b["deephit"], 2.5),
         "captura_ic_sup": np.percentile(b["deephit"], 97.5),
         "auc_min_sementes": min(auc_sem), "auc_max_sementes": max(auc_sem),
         "captura_min_sementes": min(capt_sem), "captura_max_sementes": max(capt_sem)},
        {"modelo": "fine_gray", "auc": roc_auc_score(y, r_fg),
         "auc_ic_inf": np.percentile(b["auc_fg"], 2.5), "auc_ic_sup": np.percentile(b["auc_fg"], 97.5),
         "captura_top10": _captura_top(y, r_fg),
         "captura_ic_inf": np.percentile(b["fine_gray"], 2.5),
         "captura_ic_sup": np.percentile(b["fine_gray"], 97.5)},
        {"modelo": "dif_deephit_menos_fg",
         "captura_top10": _captura_top(y, r_dh) - _captura_top(y, r_fg),
         "captura_ic_inf": np.percentile(dif, 2.5), "captura_ic_sup": np.percentile(dif, 97.5),
         "p_boot_captura": 2 * min((dif <= 0).mean(), (dif >= 0).mean())},
    ])
    saida.round(4).to_csv(OUT_DIR / "deephit_temporal.csv", index=False)
    with pd.option_context("display.width", 220):
        print(saida.round(3).T)


if __name__ == "__main__":
    main()
