"""
Modelagem de Riscos Competitivos — baseline clássico (Cox cause-specific).

Substitui o Cox de evento único (que misturava "Cura" com censura) por dois
modelos de Cox de risco proporcional tempo-variante, um por desfecho:

  - Modelo Default:  evento_col='evento'      (Cura tratada como censura)
  - Modelo Cura:     evento_col='evento_cura' (Default tratado como censura)

Essa é a abordagem "cause-specific hazards" (Kalbfleisch & Prentice, 2002),
a alternativa clássica ao modelo de subdistribution hazard de Fine-Gray
(1999) — mais simples de ajustar com as ferramentas já disponíveis
(lifelines.CoxTimeVaryingFitter) e igualmente válida para descrever como
cada covariável afeta o risco de cada desfecho especificamente.

Covariáveis ajustadas em relação à versão anterior (mlops-zoomcamp):
removidas cuotas_atrasadas (r=0,977 com ratio_atraso) e
variabilidade_pago_diario (r=0,854 com pago_promedio_diario) por
multicolinearidade — recomendação do orientador.
"""

import logging
import pickle
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
from lifelines import CoxTimeVaryingFitter
from lifelines.utils import concordance_index
from sklearn.preprocessing import StandardScaler

_RAIZ = Path(__file__).parent.parent
DATA_PATH = _RAIZ / "data" / "processed" / "survival_dataset.csv"
OUT_DIR = _RAIZ / "reports" / "modelagem"

COVARIATES = [
    "dias_sin_pagar",
    "ratio_atraso",
    "pago_promedio_diario",
    "dias_con_abono",
    "dias_desde_ultimo_abono_no_bloco",
    "intensidad_recuperacion",
    "saldo_relativo",
    "total_credito",
    "valor_cuota",
    "cuotas_pactadas",
]


def _cargar_datos() -> tuple[pd.DataFrame, StandardScaler]:
    df = pd.read_csv(DATA_PATH)
    df = df.dropna(subset=COVARIATES + ["t_start", "t_stop", "evento", "evento_cura"])
    df = df[df["t_stop"] > df["t_start"]].copy()

    scaler = StandardScaler()
    df[COVARIATES] = scaler.fit_transform(df[COVARIATES])
    return df, scaler


def _c_index(ctv: CoxTimeVaryingFitter, df: pd.DataFrame, event_col: str) -> float:
    ultima = df.sort_values("t_stop").groupby("CÓDIGO CRÉDITO").last().reset_index()
    hazard = ctv.predict_partial_hazard(ultima)
    return concordance_index(ultima["t_stop"], -hazard, ultima[event_col])


def _ajustar_cause_specific(df: pd.DataFrame, event_col: str, nombre: str) -> CoxTimeVaryingFitter:
    logging.info("── Ajustando Cox cause-specific: %s (event_col=%s) ──", nombre, event_col)
    ctv = CoxTimeVaryingFitter(penalizer=0.01)
    ctv.fit(
        df,
        id_col="CÓDIGO CRÉDITO",
        start_col="t_start",
        stop_col="t_stop",
        event_col=event_col,
        formula=" + ".join(COVARIATES),
    )
    c_index = _c_index(ctv, df, event_col)
    n_eventos = int(df.groupby("CÓDIGO CRÉDITO")[event_col].max().sum())
    epv = n_eventos / len(COVARIATES)
    logging.info("  Eventos (%s): %d | EPV: %.1f | C-index: %.4f", nombre, n_eventos, epv, c_index)
    return ctv, c_index


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    df, scaler = _cargar_datos()
    logging.info(
        "Dataset: %d intervalos, %d créditos", len(df), df["CÓDIGO CRÉDITO"].nunique()
    )

    ctv_default, c_default = _ajustar_cause_specific(df, "evento", "Default")
    print("\n" + "=" * 70)
    print("MODELO CAUSE-SPECIFIC — DEFAULT")
    print("=" * 70)
    ctv_default.print_summary()

    ctv_cura, c_cura = _ajustar_cause_specific(df, "evento_cura", "Cura")
    print("\n" + "=" * 70)
    print("MODELO CAUSE-SPECIFIC — CURA")
    print("=" * 70)
    ctv_cura.print_summary()

    with open(OUT_DIR / "cox_default.pkl", "wb") as f:
        pickle.dump(ctv_default, f)
    with open(OUT_DIR / "cox_cura.pkl", "wb") as f:
        pickle.dump(ctv_cura, f)
    with open(OUT_DIR / "scaler.pkl", "wb") as f:
        pickle.dump(scaler, f)

    print("\n" + "=" * 70)
    print("RESUMO")
    print("=" * 70)
    print(f"C-index Default: {c_default:.4f}")
    print(f"C-index Cura:    {c_cura:.4f}")
    print(f"Modelos salvos em: {OUT_DIR}")


if __name__ == "__main__":
    main()
