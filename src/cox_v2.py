"""
Cox cause-specific tempo-variante sobre el dataset reconstruido (Sprint 4).

Sustituye a modelagem_riscos_competitivos.py (que se conserva para la V25).
Cambios respecto a esa versión:

1. Lee survival_dataset_v2_b{7,10}.csv (eventos medidos por fechas de pago) y
   el historial del cliente en sus créditos anteriores (historial_cliente.py).
2. Validación cruzada por cliente (5 particiones, 3 repeticiones): ningún
   cliente aparece en entrenamiento y prueba a la vez, y los bloques de 7 y 10
   días usan las mismas particiones. Escalado e imputación solo con entrenamiento.
3. Entrada tardía en el segundo bloque: en el primero no hay pagos previos y
   las covariables "_prev" no existen. Ningún default ocurre antes del día 120.
4. Créditos renegociados con cuota de 1 real: el dataset ya trae la cuota
   original estimada (reconstruir_dataset._cuota_original). La marca de
   renegociación NO entra al modelo: es el estado del día de la descarga y
   solo existe después de que el cliente cayó (leakage).
5. Dos especificaciones para el default:
     A "completo"        incluye los días sin pagar. Como el default es llegar a
                         120 días sin pagar, en el último bloque esa variable
                         vale 113–119 y el modelo solo confirma lo que la
                         operación ya ve. Sirve de referencia.
     B "alerta_temprana" sin los días sin pagar.
6. Métricas en prueba:
     C-index tempo-variante: cada evento se compara con los créditos en riesgo
         ese mismo día, con las covariables del bloque vigente.
     Alerta temprana en los días 14, 21 y 28 del crédito: con la información
         disponible ese día se ordena a los créditos abiertos; AUC para
         "termina en default" y % de defaults en el 10% de mayor riesgo.

7. Modelo principal: landmark en los días 14 y 21. Con la foto de las
   covariables ese día se modela la incidencia acumulada de default (Fine-Gray).
   Con 2,7% de censura se aproxima dejando a los curados en riesgo hasta el fin
   del seguimiento (así se construye el conjunto de riesgo de Fine-Gray sin
   censura). El Cox cause-specific compara en el día 120 a los volados con los
   créditos lentos aún abiertos (los buenos ya se curaron) y no sirve para
   ordenar en un landmark. La regresión logística ("¿termina en default?") es
   el modelo de comparación; "solo_historial" usa contrato e historial, la
   información disponible casi en el desembolso.

Salidas en reports/modelagem_v2/: metricas_cv.csv (por partición),
metricas_resumen.csv (media y desvío), hazard_ratios_b{b}.csv (modelo
ajustado con todos los datos, para interpretar), metricas_landmark.csv y
landmark_coeficientes.csv.
"""

import logging
from pathlib import Path

import numpy as np
import pandas as pd
from lifelines import CoxPHFitter, CoxTimeVaryingFitter
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.preprocessing import StandardScaler

_RAIZ     = Path(__file__).parent.parent
DATASET   = _RAIZ / "data" / "processed" / "survival_dataset_v2_b{}.csv"
HISTORIAL = _RAIZ / "data" / "processed" / "historial_cliente.csv"
OUT_DIR   = _RAIZ / "reports" / "modelagem_v2"

BLOQUES          = (7, 10)
N_PARTICIONES    = 5
REPETICIONES     = 3
SEMILLA          = 42
PENALIZER        = 0.005
LANDMARKS        = (14, 21, 28)
TOP_RIESGO       = 0.10

CREDITO_ACTUAL = [
    "ratio_atraso",            # atraso en días de cobro (sin domingos ni feriados)
    "saldo_relativo",
    "dias_con_abono_prev",
    "pago_relativo_prev",      # lo pagado por día en el bloque anterior / cuota
    "pct_abono_incompleto",
    "dias_sin_cobro_bloque",
]
CONTRATO = ["log_total_credito", "plazo_dias", "ofi_31", "ofi_44"]
HISTORIAL_COLS = [
    "primeiro_credito",
    "ult_pontualidade",
    "ult_razao_prazo",
    "ult_log_pago_final",
    "hist_pct_parcela_incompleta",
]
BASE = CREDITO_ACTUAL + CONTRATO + HISTORIAL_COLS
ESPECIFICACIONES = {
    "A_completo":        ["dias_cobro_sin_pagar"] + BASE,
    "B_alerta_temprana": BASE,
}
REGRAS_SIMPLES = {                          # coluna, sinal (+1: maior = mais risco)
    "regra_atraso":             ("ratio_atraso", 1),
    "regra_dias_sem_pagamento": ("dias_con_abono_prev", -1),
    "regra_pagamento_relativo": ("pago_relativo_prev", -1),
    "regra_saldo":              ("saldo_relativo", 1),
}
CON_IMPUTACION = ["ult_pontualidade", "ult_razao_prazo", "ult_log_pago_final",
                  "hist_pct_parcela_incompleta"]


# ------------------------------------------------------------------ #
# Datos                                                               #
# ------------------------------------------------------------------ #

def _cargar(bloque: int) -> pd.DataFrame:
    df = pd.read_csv(str(DATASET).format(bloque))
    df = df[df["t_start"] >= bloque].copy()                # entrada tardía

    df["plazo_dias"] = df["cuotas_pactadas"]
    # pago por día del bloque anterior como fracción de la cuota
    df["pago_relativo_prev"] = np.clip(df["pago_promedio_diario_prev"] / df["valor_cuota"], 0, 3)
    df["log_total_credito"] = np.log(df["total_credito"])
    df["ofi_31"] = (df["ofi_id"] == 31).astype(int)
    df["ofi_44"] = (df["ofi_id"] == 44).astype(int)

    h = pd.read_csv(HISTORIAL, index_col=0)
    h["primeiro_credito"] = (h["n_creditos_previos"] == 0).astype(int)
    h["tuvo_renegociacion"] = (h["hist_renegociados"].fillna(0) > 0).astype(int)
    h["ult_log_pago_final"] = np.log1p(h["ult_pago_final_rel"])
    h["ult_razao_prazo"] = h["ult_razao_prazo"].clip(upper=3)
    df = df.merge(h[["primeiro_credito", "tuvo_renegociacion"] + CON_IMPUTACION], left_on="CÓDIGO CRÉDITO",
                  right_index=True, how="left")
    return df


def _particiones(clientes: np.ndarray):
    """(repetición, partición, clientes de prueba) sorteados sobre la lista de
    clientes, iguales para cualquier tamaño de bloque."""
    clientes = np.sort(clientes)
    for r in range(REPETICIONES):
        orden = np.random.default_rng(SEMILLA + r).permutation(clientes)
        for k, prueba in enumerate(np.array_split(orden, N_PARTICIONES)):
            yield r, k, prueba


# ------------------------------------------------------------------ #
# Métricas                                                            #
# ------------------------------------------------------------------ #

def _c_index_tv(te: pd.DataFrame, riesgo: np.ndarray, event_col: str) -> float:
    """Concordancia de Harrell con covariables tempo-variantes: en el día de
    cada evento, el crédito que lo sufre contra los demás en riesgo ese día."""
    t0, t1, r = te["t_start"].values, te["t_stop"].values, riesgo
    conc = total = 0.0
    for i in np.flatnonzero(te[event_col].values == 1):
        en_riesgo = (t0 < t1[i]) & (t1 >= t1[i])
        en_riesgo[i] = False
        otros = r[en_riesgo]
        conc  += (r[i] > otros).sum() + 0.5 * (r[i] == otros).sum()
        total += len(otros)
    return conc / total if total else np.nan


def _alerta_temprana(te: pd.DataFrame, riesgo: np.ndarray, bloque: int) -> dict:
    te = te.assign(riesgo=riesgo)
    default_final = te.groupby("CÓDIGO CRÉDITO")["evento"].max()
    out = {}
    for L in LANDMARKS:
        inicio = (L // bloque) * bloque                    # último bloque iniciado ≤ L
        foto = te[te["t_start"] == inicio].set_index("CÓDIGO CRÉDITO")
        y = default_final.loc[foto.index].values
        n_top = max(1, int(np.ceil(TOP_RIESGO * len(foto))))
        top = foto["riesgo"].rank(ascending=False, method="first") <= n_top
        out[f"auc_d{L}"] = roc_auc_score(y, foto["riesgo"]) if 0 < y.sum() < len(y) else np.nan
        out[f"captura_top10_d{L}"] = y[top.values].sum() / y.sum() if y.sum() else np.nan
    return out


# ------------------------------------------------------------------ #
# Ajuste                                                              #
# ------------------------------------------------------------------ #

def _preparar(tr, te, covs):
    medianas = tr[CON_IMPUTACION].median()
    tr, te = tr.fillna(medianas), te.fillna(medianas)
    scaler = StandardScaler().fit(tr[covs])
    tr[covs] = scaler.transform(tr[covs])
    te[covs] = scaler.transform(te[covs])
    return tr, te, scaler


def _ajustar(tr, covs, event_col):
    ctv = CoxTimeVaryingFitter(penalizer=PENALIZER)
    ctv.fit(tr[["CÓDIGO CRÉDITO", "t_start", "t_stop", event_col] + covs],
            id_col="CÓDIGO CRÉDITO", start_col="t_start", stop_col="t_stop",
            event_col=event_col)
    return ctv


def _modelos():
    for nombre, covs in ESPECIFICACIONES.items():
        yield nombre, covs, "evento"
    yield "C_cura", ESPECIFICACIONES["A_completo"], "evento_cura"


def _hazard_ratios(df) -> pd.DataFrame:
    """Modelos ajustados con todos los datos. HR por 1 desvío estándar (lo que
    estima el modelo) y por 1 unidad de la variable original."""
    tablas = []
    for nombre, covs, event_col in _modelos():
        tr, _, scaler = _preparar(df.copy(), df.iloc[:1].copy(), covs)
        s = _ajustar(tr, covs, event_col).summary
        sd = pd.Series(scaler.scale_, index=covs)
        tablas.append(pd.DataFrame({
            "modelo": nombre,
            "HR_1dp": s["exp(coef)"],
            "HR_1dp_ic95_inf": s["exp(coef) lower 95%"],
            "HR_1dp_ic95_sup": s["exp(coef) upper 95%"],
            "HR_1unidad": np.exp(s["coef"] / sd),
            "p": s["p"],
        }))
    return pd.concat(tablas)


def correr(bloque: int) -> list[dict]:
    df = _cargar(bloque)
    filas = []
    for r, k, prueba in _particiones(df["codigo_cliente"].unique()):
        es_prueba = df["codigo_cliente"].isin(prueba)
        for nombre, covs, event_col in _modelos():
            tr, te, _ = _preparar(df[~es_prueba].copy(), df[es_prueba].copy(), covs)
            riesgo = _ajustar(tr, covs, event_col).predict_partial_hazard(te[covs]).values
            fila = {"bloque": bloque, "repeticion": r, "particion": k, "modelo": nombre,
                    "eventos_prueba": int(te[event_col].sum()),
                    "c_index": _c_index_tv(te, riesgo, event_col)}
            if event_col == "evento":
                fila.update(_alerta_temprana(te, riesgo, bloque))
            filas.append(fila)
        logging.info("  bloque %d | repetición %d partición %d", bloque, r, k)
    _hazard_ratios(df).round(4).to_csv(OUT_DIR / f"hazard_ratios_b{bloque}.csv")
    return filas


def _captura_top(y, riesgo) -> float:
    n_top = int(np.ceil(TOP_RIESGO * len(y)))
    top = pd.Series(riesgo).rank(ascending=False, method="first").values <= n_top
    return y[top].sum() / y.sum()


def _landmark(bloque: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    df = _cargar(bloque)
    fin = df.groupby("CÓDIGO CRÉDITO").agg(T=("t_stop", "max"), y=("evento", "max"),
                                            cura=("evento_cura", "max"))
    t_max = fin["T"].max()
    variantes = {
        "fine_gray":                ("fg", BASE),
        "logistica":                ("lr", BASE),
        "logistica_solo_historial": ("lr", HISTORIAL_COLS + CONTRATO),
    }
    filas, coefs = [], []
    for L in LANDMARKS[:2]:
        inicio = (L // bloque) * bloque
        foto = df[df["t_start"] == inicio].join(fin, on="CÓDIGO CRÉDITO")
        # conjunto de riesgo de Fine-Gray: el curado sigue "en riesgo" de default
        foto["dur_fg"] = np.where(foto["cura"] == 1, t_max, foto["T"]) - inicio

        def ajustar(tr, tipo, covs):
            if tipo == "fg":
                m = CoxPHFitter(penalizer=0.01).fit(tr[covs + ["dur_fg", "y"]], "dur_fg", "y")
                return m, lambda te: m.predict_partial_hazard(te[covs]).values
            m = LogisticRegression(max_iter=2000).fit(tr[covs], tr["y"])
            return m, lambda te: m.predict_proba(te[covs])[:, 1]

        for nombre, (tipo, covs) in variantes.items():
            for r, k, prueba in _particiones(df["codigo_cliente"].unique()):
                es_prueba = foto["codigo_cliente"].isin(prueba)
                tr, te, _ = _preparar(foto[~es_prueba].copy(), foto[es_prueba].copy(), covs)
                _, predecir = ajustar(tr, tipo, covs)
                riesgo, y = predecir(te), te["y"].values
                filas.append({"bloque": bloque, "landmark": L, "modelo": nombre,
                              "repeticion": r, "particion": k, "defaults_prueba": int(y.sum()),
                              "auc": roc_auc_score(y, riesgo), "captura_top10": _captura_top(y, riesgo)})
            tr, _, _ = _preparar(foto.copy(), foto.iloc[:1].copy(), covs)
            m, _ = ajustar(tr, tipo, covs)
            if tipo == "fg":
                c = m.summary[["exp(coef)", "exp(coef) lower 95%", "exp(coef) upper 95%", "p"]]
                c.columns = ["razon", "ic95_inf", "ic95_sup", "p"]
            else:
                c = pd.DataFrame({"razon": np.exp(m.coef_[0])}, index=covs)
            coefs.append(c.assign(bloque=bloque, landmark=L, modelo=nombre,
                                  medida="SHR" if tipo == "fg" else "OR"))
        # Regras simples, sem modelo: ordenar os créditos por uma única variável.
        # Respondem à pergunta "quanto o modelo acrescenta a uma regra óbvia?".
        # Empates desfeitos ao acaso (semente fixa), senão a ordem do arquivo decidiria.
        rng = np.random.default_rng(SEMILLA)
        for nombre, (col, sinal) in REGRAS_SIMPLES.items():
            for r, k, prueba in _particiones(df["codigo_cliente"].unique()):
                te = foto[foto["codigo_cliente"].isin(prueba)]
                y = te["y"].values
                riesgo = sinal * te[col].fillna(0).values + 1e-9 * rng.random(len(te))
                filas.append({"bloque": bloque, "landmark": L, "modelo": nombre,
                              "repeticion": r, "particion": k, "defaults_prueba": int(y.sum()),
                              "auc": roc_auc_score(y, riesgo), "captura_top10": _captura_top(y, riesgo)})
        logging.info("  landmark día %d (bloque %d) listo", L, bloque)
    return pd.DataFrame(filas), pd.concat(coefs)


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    cv = pd.DataFrame([f for b in BLOQUES for f in correr(b)])
    cv.round(4).to_csv(OUT_DIR / "metricas_cv.csv", index=False)
    metricas = [c for c in cv.columns if c.startswith(("c_index", "auc", "captura"))]
    resumen = cv.groupby(["modelo", "bloque"])[metricas].agg(["mean", "std"])
    resumen.round(4).to_csv(OUT_DIR / "metricas_resumen.csv")
    with pd.option_context("display.width", 220, "display.max_columns", 40):
        print(resumen.round(3).T)

    lm = [_landmark(b) for b in BLOQUES]
    lm_cv = pd.concat([x[0] for x in lm])
    lm_cv.round(4).to_csv(OUT_DIR / "metricas_landmark.csv", index=False)
    pd.concat([x[1] for x in lm]).round(4).to_csv(OUT_DIR / "landmark_coeficientes.csv")
    with pd.option_context("display.width", 220):
        print(lm_cv.groupby(["bloque", "landmark", "modelo"])[["auc", "captura_top10"]]
              .agg(["mean", "std"]).round(3))


if __name__ == "__main__":
    main()
