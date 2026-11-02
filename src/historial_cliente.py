"""
Historial de pago del cliente en sus créditos anteriores.

Un cliente que viene "apretado" lo muestra antes de volarse (confirmado con la
operación): paga la parcela incompleta, se atrasa respecto al plazo pactado o,
al final, abona de una vez un valor alto solo para cerrar y poder renovar.
Ese comportamiento queda en los créditos anteriores del mismo cliente, así que
cada crédito recibe un resumen de los créditos previos que ya estaban cerrados
el día de su desembolso (nunca información posterior a FECHA CRÉDITO).

Perfil de cada crédito cerrado (solo planes con cuota fija, CUOTAS PACTADAS ≤ 50):
    pct_parcela_incompleta  % de los días con abono en que se pagó menos del 90%
                            de la cuota.
    pontualidade            días con abono / días esperados de pago (máx. 1).
    razao_prazo             días hasta cerrar / plazo pactado (1 = en el plazo).
    pago_final_rel          último abono / valor de la cuota. Solo en cura por
                            pagos: en cura_cierre_sistema el abono de cierre es
                            el saldo faltante reconstruido, no un abono observado.

hist_renegociados cuenta los créditos anteriores que terminaron renegociados con
cuota de 1 real (el comerciante cerró el negocio y pasó a pagar semanal o
quincenal). En el crédito actual esa marca sería leakage, pero en un crédito ya
cerrado es información conocida el día del nuevo desembolso.

Salida: data/processed/historial_cliente.csv, una fila por crédito.
"""

import logging
from pathlib import Path

import numpy as np
import pandas as pd

from reconstruir_dataset import (
    MATRIZ, SALIDA_DESENL, EVENTO_DEFAULT, _extraer, _filtrar_cohorte,
)

_RAIZ  = Path(__file__).parent.parent
SALIDA = _RAIZ / "data" / "processed" / "historial_cliente.csv"

CUOTAS_FLEXIBLE   = 50
FRAC_INCOMPLETA   = 0.90       # abono menor que el 90% de la cuota
PAGO_FINAL_ALTO   = 3.0        # último abono de 3 cuotas o más

PERFIL = ["pct_parcela_incompleta", "pontualidade", "razao_prazo", "pago_final_rel"]


def _perfil_credito(creditos, pagos, desenlaces) -> pd.DataFrame:
    d = desenlaces.copy()
    d["cred"] = d["CÓDIGO CRÉDITO"].astype(str)
    d = d.join(creditos[["fc", "fv", "VALOR CUOTA", "CUOTAS PACTADAS"]], on="cred")
    d["fin"] = d["fc"] + pd.to_timedelta(d["T"], unit="D")

    p = pagos[pagos["cred"].isin(d["cred"])].merge(
        d[["cred", "fc", "fin", "VALOR CUOTA"]], on="cred")
    p = p[(p["fecha"] >= p["fc"]) & (p["fecha"] <= p["fin"])]
    p["incompleta"] = p["valor"] < FRAC_INCOMPLETA * p["VALOR CUOTA"]
    g = p.groupby("cred")
    d = d.join(pd.DataFrame({
        "dias_con_abono": g.size(),
        "pct_parcela_incompleta": g["incompleta"].mean(),
        "ultimo_abono": g["valor"].last(),
    }), on="cred")
    d["dias_con_abono"] = d["dias_con_abono"].fillna(0)

    fijo = d["CUOTAS PACTADAS"] <= CUOTAS_FLEXIBLE
    cura_pagos = d["motivo"] == "cura_pagos"
    prazo = (d["fv"] - d["fc"]).dt.days.clip(lower=1)
    d["pontualidade"] = (d["dias_con_abono"]
                         / np.minimum(d["T"], d["CUOTAS PACTADAS"])).clip(upper=1)
    d["razao_prazo"] = np.where(d["evento_tipo"] != EVENTO_DEFAULT, d["T"] / prazo, np.nan)
    d["pago_final_rel"] = np.where(cura_pagos, d["ultimo_abono"] / d["VALOR CUOTA"], np.nan)
    d.loc[~fijo, PERFIL] = np.nan
    d["fue_default"] = (d["evento_tipo"] == EVENTO_DEFAULT).astype(int)
    d["fue_renegociado"] = (~fijo).astype(int)
    return d


def _historial(d: pd.DataFrame) -> pd.DataFrame:
    """Para cada crédito, resumen de los créditos del mismo cliente cerrados
    (fin ≤ FECHA CRÉDITO) antes de su desembolso."""
    filas = []
    for _, g in d.sort_values("fc").groupby("codigo_cliente", sort=False):
        fc, fin = g["fc"].values, g["fin"].values
        perf = g[PERFIL].values
        alto = (g["pago_final_rel"] >= PAGO_FINAL_ALTO).astype(float).where(
            g["pago_final_rel"].notna()).values
        dflt = g["fue_default"].values
        reneg = g["fue_renegociado"].values
        for i, cred in enumerate(g["cred"].values):
            prev = np.flatnonzero(fin <= fc[i])
            fila = {"cred": cred, "n_creditos_previos": len(prev)}
            if len(prev):
                u = prev[np.argmax(fin[prev])]                 # el último cerrado
                with np.errstate(all="ignore"), pd.option_context("mode.chained_assignment", None):
                    medias = np.nanmean(perf[prev], axis=0) if np.isfinite(perf[prev]).any() else [np.nan] * 4
                for k, nombre in enumerate(PERFIL):
                    fila[f"hist_{nombre}"] = medias[k]
                    fila[f"ult_{nombre}"] = perf[u, k]
                fila["hist_pct_pago_final_alto"] = np.nanmean(alto[prev]) if np.isfinite(alto[prev]).any() else np.nan
                fila["hist_defaults"] = int(dflt[prev].sum())
                fila["hist_renegociados"] = int(reneg[prev].sum())
                fila["dias_desde_cierre_anterior"] = (fc[i] - fin[u]) / np.timedelta64(1, "D")
            filas.append(fila)
    return pd.DataFrame(filas).set_index("cred")


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    creditos, pagos = _extraer(MATRIZ)
    creditos = _filtrar_cohorte(creditos, pagos)
    desenlaces = pd.read_csv(SALIDA_DESENL)
    d = _perfil_credito(creditos, pagos, desenlaces)
    h = _historial(d)
    solapados = (d.sort_values("fc").groupby("codigo_cliente")["fin"].shift(1)
                 > d.sort_values("fc")["fc"]).sum()
    logging.info("  %d créditos | %d con historial | %d desembolsados antes de cerrar el anterior",
                 len(h), (h["n_creditos_previos"] > 0).sum(), solapados)
    h.to_csv(SALIDA)
    logging.info("Guardado %s", SALIDA.name)


if __name__ == "__main__":
    main()
