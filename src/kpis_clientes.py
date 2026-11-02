"""
KPIs de negocio por cliente y por ruta, sobre la cohorte de reconstruir_dataset.py.

Base para el análisis socioeconómico pedido en la evaluación de Metodologia e
Projeto II (comparación entre clases sociales): cada cliente conserva la mediana
de sus coordenadas GPS para cruzarla después con la renta por sector censal
del IBGE. Las coordenadas quedan solo en data/processed (fuera de git, LGPD).

Supuestos de negocio:
    - TOTAL CRÉDITO incluye el 20% de interés: capital = total / 1,2.
    - Pagos reales = abonos de las columnas diarias hasta el desenlace. En un
      default, el abono de limpieza posterior no es pago real y no se cuenta.

Salidas (data/processed):
    kpis_clientes.csv  una fila por cliente
    kpis_rutas.csv     una fila por ruta
"""

import logging
from pathlib import Path

import numpy as np
import pandas as pd

from reconstruir_dataset import (
    MATRIZ, SALIDA_DESENL, EVENTO_CURA, EVENTO_DEFAULT, EVENTO_CENSURA, _extraer,
)

_RAIZ          = Path(__file__).parent.parent
SALIDA_CLIENTE = _RAIZ / "data" / "processed" / "kpis_clientes.csv"
SALIDA_RUTA    = _RAIZ / "data" / "processed" / "kpis_rutas.csv"

TASA_INTERES = 0.20

# Nombre de la ruta en el encabezado de los reportes ATLAS ("Ruta: 01.07. SANTOS - S")
# y ciudad de operación. Las rutas con nombre de cobrador se ubicaron con la operación
# y se contrastaron con el DDD y las coordenadas de sus clientes; cuando los datos
# contradicen la respuesta ("creo que..."), prevalece la evidencia de los datos.
RUTAS = {
    "82":  ("01.01. JUAN SP",          "São Paulo"),
    "96":  ("01.02. FRANCISCO MORATO", "Francisco Morato"),
    "423": ("01.03. DIADEMA",          "Diadema"),
    "136": ("01.04. PINDA",            "Pindamonhangaba"),
    "367": ("01.07. SANTOS",           "Santos"),
    "448": ("01.08. GUARULHOS",        "Guarulhos"),
    "494": ("01.09. VAMPI SJ",         "São José dos Campos"),   # DDD 12 (93%)
    "415": ("01.06. CAMPINAS",         "Campinas"),
    "68":  ("04.01. BILLY",            "Petrópolis / Rio de Janeiro"),  # DDD 24 (59%), 21 (40%)
    "338": ("04.02. BLUMENAU",         "Blumenau"),
    "347": ("04.03. CAMBORIU",         "Balneário Camboriú"),
    "389": ("04.04. CANTI",            "Rio de Janeiro"),        # DDD 21 (100%)
    "114": ("02.01. RIO",              "Rio de Janeiro"),
    "439": ("02.02. COSTEÑO",          "Cabo Frio"),             # DDD 22 (88%), coords Cabo Frio
    "396": ("02.03. CRISTIAN",         "Cabo Frio"),
    "420": ("02.04. CRUZ",             "Rio das Ostras"),        # DDD 22 (100%), coords Rio das Ostras
    "511": ("02.05. LUIS ALFONSO CF",  "Cabo Frio"),
}


OFICINAS = {"23": "São Paulo", "31": "Soc. Brasil", "44": "Cabo Frio"}

UF_CIDADE = {
    "São Paulo": "SP", "Francisco Morato": "SP", "Diadema": "SP", "Pindamonhangaba": "SP",
    "Santos": "SP", "Guarulhos": "SP", "São José dos Campos": "SP", "Campinas": "SP",
    "Petrópolis / Rio de Janeiro": "RJ", "Rio de Janeiro": "RJ", "Cabo Frio": "RJ",
    "Rio das Ostras": "RJ", "Blumenau": "SC", "Balneário Camboriú": "SC",
}

# Región del cliente según el DDD (fuente más confiable de ubicación). Los DDD de
# fuera de la operación se agrupan por UF.
DDD_REGIAO = {
    11: "Grande São Paulo", 12: "Vale do Paraíba (SP)", 13: "Baixada Santista (SP)",
    19: "Campinas (SP)", 21: "Rio de Janeiro (metrópole)",
    22: "Região dos Lagos / Norte Fluminense (RJ)", 24: "Serrana / Sul Fluminense (RJ)",
    47: "Vale do Itajaí / Litoral Norte (SC)",
}

DDD_UF = {
    **{d: "SP" for d in range(11, 20)}, 21: "RJ", 22: "RJ", 24: "RJ", 27: "ES", 28: "ES",
    **{d: "MG" for d in (31, 32, 33, 34, 35, 37, 38)}, **{d: "PR" for d in range(41, 47)},
    47: "SC", 48: "SC", 49: "SC", **{d: "RS" for d in (51, 53, 54, 55)}, 61: "DF",
    62: "GO", 64: "GO", 63: "TO", 65: "MT", 66: "MT", 67: "MS", 68: "AC", 69: "RO",
    **{d: "BA" for d in (71, 73, 74, 75, 77)}, 79: "SE", 81: "PE", 87: "PE", 82: "AL",
    83: "PB", 84: "RN", 85: "CE", 88: "CE", 86: "PI", 89: "PI", 91: "PA", 93: "PA",
    94: "PA", 92: "AM", 97: "AM", 95: "RR", 96: "AP", 98: "MA", 99: "MA",
}


def _ddd(numero: pd.Series) -> pd.Series:
    """DDD de un número brasileño: quita el 55 del país y toma los 2 primeros
    dígitos de números con 10 u 11 dígitos. Sin DDD reconocible → NaN."""
    n = numero.astype(str).str.replace(r"\D", "", regex=True)
    n = n.where(~(n.str.len().isin([12, 13]) & n.str.startswith("55")), n.str[2:])
    ddd = pd.to_numeric(n.str[:2].where(n.str.len().isin([10, 11])), errors="coerce")
    return ddd.where(ddd.isin(list(DDD_UF)))


def _ubicacion(path: Path) -> pd.DataFrame:
    """Por crédito: mediana de LATITUD/LONGITUD válidas (dentro de Brasil) y DDD
    más frecuente del celular (o del teléfono fijo si el celular no lo trae)."""
    cols = ["CÓDIGO CRÉDITO", "LATITUD", "LONGITUD", "CELULAR", "TELÉFONO"]
    partes = []
    for chunk in pd.read_csv(path, usecols=cols, chunksize=50_000, low_memory=False,
                             dtype={"CELULAR": str, "TELÉFONO": str}):
        chunk = chunk.dropna(subset=["CÓDIGO CRÉDITO"])
        chunk["cred"] = chunk["CÓDIGO CRÉDITO"].astype(str).str.replace(r"\.0$", "", regex=True)
        chunk["lat"] = pd.to_numeric(chunk["LATITUD"], errors="coerce")
        chunk["lon"] = pd.to_numeric(chunk["LONGITUD"], errors="coerce")
        fuera = ~(chunk["lat"].between(-34, 5) & chunk["lon"].between(-74, -34))
        chunk.loc[fuera, ["lat", "lon"]] = np.nan
        chunk["ddd"] = _ddd(chunk["CELULAR"]).fillna(_ddd(chunk["TELÉFONO"]))
        partes.append(chunk[["cred", "lat", "lon", "ddd"]])
    u = pd.concat(partes).groupby("cred")
    out = u[["lat", "lon"]].median()
    out["ddd"] = u["ddd"].agg(lambda s: s.mode().iat[0] if s.notna().any() else np.nan)
    return out


def _kpis_credito(creditos, pagos, desenlaces) -> pd.DataFrame:
    d = desenlaces.copy()
    d["cred"] = d["CÓDIGO CRÉDITO"].astype(str)
    d = d.join(creditos.drop(columns=["CÓDIGO CRÉDITO"]), on="cred")
    d["T"] = d["T"].astype(int)
    fin = d.set_index("cred")["fc"] + pd.to_timedelta(d.set_index("cred")["T"], unit="D")

    p = pagos[pagos["cred"].isin(d["cred"])].copy()
    p["fin"] = p["cred"].map(fin)
    p = p[p["fecha"] <= p["fin"]]
    real = p.groupby("cred")["valor"].agg(pagado_real="sum", dias_con_abono="size")
    d = d.join(real, on="cred").fillna({"pagado_real": 0.0, "dias_con_abono": 0})

    total   = d["TOTAL CRÉDITO"]
    capital = total / (1 + TASA_INTERES)
    prazo   = (d["fv"] - d["fc"]).dt.days.clip(lower=1)
    es_def  = d["evento_tipo"] == EVENTO_DEFAULT
    es_cura = d["evento_tipo"] == EVENTO_CURA

    d["capital"]       = capital
    d["perda"]         = np.where(es_def, (capital - d["pagado_real"]).clip(lower=0), 0.0)
    d["juros_recebido"] = np.where(es_cura, total - capital, 0.0)
    d["razao_prazo"]   = np.where(es_cura, d["T"] / prazo, np.nan)
    d["pontualidade"]  = (d["dias_con_abono"] / np.minimum(d["T"], d["CUOTAS PACTADAS"])).clip(upper=1)
    return d


def _por_cliente(d: pd.DataFrame, ubicacion: pd.DataFrame) -> pd.DataFrame:
    d = d.join(ubicacion, on="cred").sort_values(["codigo_cliente", "fc"])
    d["dias_desde_anterior"] = d.groupby("codigo_cliente")["fc"].diff().dt.days
    g = d.groupby("codigo_cliente")
    k = pd.DataFrame({
        "ofi_id":                 g["ofi_id"].agg(lambda s: s.mode().iat[0]),
        "rta_id":                 g["rta_id"].agg(lambda s: s.mode().iat[0]),
        "n_creditos":             g.size(),
        "primeiro_credito":       g["fc"].min(),
        "ultimo_credito":         g["fc"].max(),
        "ticket_medio":           g["TOTAL CRÉDITO"].mean(),
        "valor_total_emprestado": g["capital"].sum(),
        "valor_cuota_medio":      g["VALOR CUOTA"].mean(),
        "prazo_medio_cuotas":     g["CUOTAS PACTADAS"].mean(),
        "intervalo_medio_renovacao": g["dias_desde_anterior"].mean(),
        "n_default":              g["evento_tipo"].agg(lambda s: (s == EVENTO_DEFAULT).sum()),
        "n_cura":                 g["evento_tipo"].agg(lambda s: (s == EVENTO_CURA).sum()),
        "n_ativo":                g["evento_tipo"].agg(lambda s: (s == EVENTO_CENSURA).sum()),
        "pontualidade_media":     g["pontualidade"].mean(),
        "razao_prazo_media":      g["razao_prazo"].mean(),
        "perda_total":            g["perda"].sum(),
        "juros_recebidos":        g["juros_recebido"].sum(),
        "lat":                    g["lat"].median(),
        "lon":                    g["lon"].median(),
        "ddd":                    g["ddd"].agg(lambda s: s.mode().iat[0] if s.notna().any() else np.nan),
    })
    k["uf_ddd"]  = k["ddd"].map(DDD_UF)
    k["oficina"] = k["ofi_id"].astype(str).map(OFICINAS)
    k["antiguidade_dias"] = (k["ultimo_credito"] - k["primeiro_credito"]).dt.days
    k["cliente_volou"]    = (k["n_default"] > 0).astype(int)
    k["resultado"]        = k["juros_recebidos"] - k["perda_total"]
    k["rota_nome"]   = k["rta_id"].astype(str).map(lambda r: RUTAS.get(r, (None, None))[0])
    k["cidade_rota"] = k["rta_id"].astype(str).map(lambda r: RUTAS.get(r, (None, None))[1])
    k["uf_rota"]     = k["cidade_rota"].map(UF_CIDADE)

    # Ubicación del cliente: DDD primero; sin DDD, la ciudad de la ruta.
    regiao_ddd = k["ddd"].map(DDD_REGIAO).fillna("Outro DDD (" + k["uf_ddd"] + ")")
    k["regiao_cliente"] = regiao_ddd.where(k["ddd"].notna(), "Sem DDD, rota: " + k["cidade_rota"])
    k["fonte_regiao"]   = np.where(k["ddd"].notna(), "ddd", "rota")
    # DDD de otro estado: probable cliente migrante que conservó su número de origen.
    k["migrante_ddd"]   = (k["ddd"].notna() & (k["uf_ddd"] != k["uf_rota"])).astype(int)
    return k


def _por_ruta(d: pd.DataFrame, k: pd.DataFrame) -> pd.DataFrame:
    g = d.groupby("rta_id")
    r = pd.DataFrame({
        "ofi_id":              g["ofi_id"].first(),
        "oficina":             g["ofi_id"].first().astype(str).map(OFICINAS),
        "n_creditos":          g.size(),
        "taxa_default_credito": g["evento_tipo"].agg(lambda s: (s == EVENTO_DEFAULT).mean()),
        "ticket_medio":        g["TOTAL CRÉDITO"].mean(),
        "capital_emprestado":  g["capital"].sum(),
        "perda_total":         g["perda"].sum(),
        "juros_recebidos":     g["juros_recebido"].sum(),
        "pontualidade_media":  g["pontualidade"].mean(),
    })
    kc = k.groupby("rta_id")
    r["n_clientes"]           = kc.size()
    r["taxa_clientes_volaram"] = kc["cliente_volou"].mean()
    r["taxa_perda"]           = r["perda_total"] / r["capital_emprestado"]
    r["resultado"]            = r["juros_recebidos"] - r["perda_total"]
    r["rota_nome"]   = r.index.astype(str).map(lambda x: RUTAS.get(x, (None, None))[0])
    r["cidade_rota"] = r.index.astype(str).map(lambda x: RUTAS.get(x, (None, None))[1])
    return r


def construir() -> tuple[pd.DataFrame, pd.DataFrame]:
    desenlaces = pd.read_csv(SALIDA_DESENL, dtype={"CÓDIGO CRÉDITO": str})
    creditos, pagos = _extraer(MATRIZ)
    creditos = creditos.drop(columns=["CÓDIGO CLIENTE"])
    d = _kpis_credito(creditos, pagos, desenlaces)
    k = _por_cliente(d, _ubicacion(MATRIZ))
    r = _por_ruta(d, k)

    logging.info("Clientes: %d | volaron al menos una vez: %d (%.1f%%)",
                 len(k), k["cliente_volou"].sum(), 100 * k["cliente_volou"].mean())
    logging.info("Con coordenadas: %d (%.1f%%) | con DDD: %d (%.1f%%) | UF: %s",
                 k["lat"].notna().sum(), 100 * k["lat"].notna().mean(),
                 k["ddd"].notna().sum(), 100 * k["ddd"].notna().mean(),
                 k["uf_ddd"].value_counts().to_dict())
    logging.info("Capital prestado: R$ %.0f | juros recibidos: R$ %.0f | pérdidas: R$ %.0f (%.2f%%)",
                 d["capital"].sum(), d["juros_recebido"].sum(), d["perda"].sum(),
                 100 * d["perda"].sum() / d["capital"].sum())
    return k, r


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    k, r = construir()
    k.to_csv(SALIDA_CLIENTE)
    r.to_csv(SALIDA_RUTA)
    pd.set_option("display.width", 200)
    print(r[["rota_nome", "cidade_rota", "n_clientes", "n_creditos", "taxa_default_credito",
             "taxa_clientes_volaram", "ticket_medio", "taxa_perda", "resultado"]]
          .sort_values("taxa_default_credito", ascending=False).round(3).to_string())
