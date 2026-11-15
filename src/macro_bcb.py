"""
Variáveis macroeconômicas (Sprint 5): séries públicas do Banco Central (SGS).

    432    Meta da taxa Selic (% ao ano, diária; média do mês)
    13522  IPCA acumulado em 12 meses (%)
    24369  Taxa de desocupação, PNAD Contínua (%; trimestre móvel)

Só se baixam dados públicos agregados; nenhum dado de cliente sai do computador.
Saída: data/external/macro_bcb.csv (uma linha por mês, de 2019 a 2026).
"""

import json
import logging
import urllib.request
from pathlib import Path

import pandas as pd

_RAIZ  = Path(__file__).parent.parent
SAIDA  = _RAIZ / "data" / "external" / "macro_bcb.csv"
SERIES = {"selic": 432, "ipca_12m": 13522, "desocupacao": 24369}
URL    = ("https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados"
          "?formato=json&dataInicial=01/01/2019&dataFinal=31/12/2026")


def _serie(codigo: int) -> pd.Series:
    with urllib.request.urlopen(URL.format(codigo=codigo), timeout=60) as r:
        dados = json.load(r)
    s = pd.DataFrame(dados)
    s["data"] = pd.to_datetime(s["data"], format="%d/%m/%Y")
    s["valor"] = s["valor"].astype(float)
    return s.set_index("data")["valor"].resample("MS").mean()


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    macro = pd.DataFrame({nome: _serie(cod) for nome, cod in SERIES.items()})
    macro.index.name = "mes"
    macro = macro.ffill()        # meses mais recentes ainda sem divulgação
    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    macro.round(3).to_csv(SAIDA)
    logging.info("Guardado %s (%d meses)", SAIDA.name, len(macro))
    print(macro.resample("YS").mean().round(2))


if __name__ == "__main__":
    main()
