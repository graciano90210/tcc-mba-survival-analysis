"""
Calendario de días de cobro por estado (SP, RJ, SC).

Validado con los abonos diarios 2020–2026 (abonos por día respecto a un día
hábil): domingo ≈ 0%, feriado nacional ≈ 23%, feriado estadual ≈ 30%,
Corpus Christi y vísperas de Navidad/Año Nuevo ≈ 20–30%, Carnaval ≈ 50%,
sábado ≈ 80–90%. Se consideran días SIN cobro el domingo, los feriados
nacionales y estaduales, el Carnaval, Corpus Christi y las vísperas de
Navidad y Año Nuevo. Los feriados municipales no están en la librería y quedan
fuera (pendiente).

Los días de partido de Brasil en la Copa 2022 bajaron el cobro solo un 15–20%:
siguen siendo días de cobro y se tratan en el análisis descriptivo.
"""

from functools import lru_cache

import holidays
import numpy as np
import pandas as pd

INICIO = pd.Timestamp("2019-12-01")
FIN    = pd.Timestamp("2027-12-31")

# UF de cada ruta (ciudad confirmada con la operación, ver kpis_clientes.RUTAS)
UF_RUTA = {
    68: "RJ", 82: "SP", 96: "SP", 114: "RJ", 136: "SP", 338: "SC", 347: "SC",
    367: "SP", 389: "RJ", 396: "RJ", 415: "SP", 420: "RJ", 423: "SP", 439: "RJ",
    448: "SP", 494: "SP", 511: "RJ",
}
FACULTATIVOS_SIN_COBRO = ("Carnaval", "Corpus Christi", "Véspera de Natal", "Véspera de Ano-Novo")


@lru_cache(maxsize=None)
def dias_cobro(uf: str) -> pd.Series:
    """Serie booleana diaria INICIO..FIN: True si es día de cobro en la UF."""
    anos = range(INICIO.year, FIN.year + 1)
    feriados = holidays.Brazil(years=anos, subdiv=uf)
    opcionales = holidays.Brazil(years=anos, subdiv=uf, categories=("optional",))
    dias = pd.date_range(INICIO, FIN)
    sin_cobro = [
        d.dayofweek == 6 or d.date() in feriados
        or any(n in (opcionales.get(d.date()) or "") for n in FACULTATIVOS_SIN_COBRO)
        for d in dias
    ]
    return pd.Series(~np.array(sin_cobro), index=dias)


@lru_cache(maxsize=None)
def acumulado(uf: str) -> pd.Series:
    """Días de cobro acumulados hasta cada fecha (inclusive)."""
    return dias_cobro(uf).cumsum()


def uf_de_ruta(rta_id) -> str:
    """UF de la ruta; SP por defecto (oficina con más créditos)."""
    try:
        return UF_RUTA.get(int(rta_id), "SP")
    except (TypeError, ValueError):
        return "SP"
