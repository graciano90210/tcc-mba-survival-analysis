"""
Renda do entorno de cada cliente pelo setor censitário do IBGE (Sprint 5).

1. Localiza cada cliente no setor censitário do Censo 2022, cruzando a mediana
   das coordenadas GPS dos seus pagamentos (kpis_clientes.csv) com as malhas de
   setores de SP, RJ e SC. O cruzamento é feito localmente: nenhuma coordenada
   ou endereço sai do computador (LGPD).
2. Quando o arquivo de renda por setor estiver disponível
   (Agregados_por_setores_renda_responsavel_BR, variável V06004: rendimento
   médio do responsável, em reais), une a renda pelo código do setor.

Entradas (em ~/Descargas, baixadas do IBGE pelo autor):
    {SP,RJ,SC}_setores_CD2022.gpkg
    Agregados_por_setores_renda_responsavel_BR.(csv|zip)   (opcional)
Saída: data/processed/clientes_setor.csv (uma linha por cliente)
"""

import logging
from pathlib import Path

import geopandas as gpd
import pandas as pd

_RAIZ     = Path(__file__).parent.parent
PROC      = _RAIZ / "data" / "processed"
DESCARGAS = Path.home() / "Descargas"
UFS       = ("SP", "RJ", "SC")
SAIDA     = PROC / "clientes_setor.csv"
COLUNAS   = ["CD_SETOR", "SITUACAO", "NM_MUN", "NM_BAIRRO", "geometry"]


def _malhas() -> gpd.GeoDataFrame:
    partes = []
    for uf in UFS:
        caminho = DESCARGAS / f"{uf}_setores_CD2022.gpkg"
        g = gpd.read_file(caminho, columns=COLUNAS[:-1], engine="pyogrio")
        g["UF"] = uf
        partes.append(g)
        logging.info("  malha %s: %d setores", uf, len(g))
    return pd.concat(partes, ignore_index=True)


def _renda() -> pd.DataFrame | None:
    """Renda por setor: V06004 = rendimento médio do responsável (R$) e
    V06006 = mediana (R$). Conferir no dicionário de variáveis do IBGE."""
    arquivos = sorted(DESCARGAS.glob("Agregados_por_setores_renda_responsavel_BR*"))
    if not arquivos:
        logging.info("  arquivo de renda por setor ainda não encontrado em %s", DESCARGAS)
        return None
    r = pd.read_csv(arquivos[-1], sep=";", dtype={"CD_SETOR": str}, decimal=".",
                    na_values=["X", "."], encoding="latin-1")
    r = r[["CD_SETOR", "V06004", "V06006"]].rename(
        columns={"V06004": "renda_media_setor", "V06006": "renda_mediana_setor"})
    logging.info("  renda: %d setores (%s)", len(r), arquivos[-1].name)
    return r


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    k = pd.read_csv(PROC / "kpis_clientes.csv", usecols=["codigo_cliente", "lat", "lon"])
    k = k.dropna(subset=["lat", "lon"])
    pontos = gpd.GeoDataFrame(k, geometry=gpd.points_from_xy(k["lon"], k["lat"]), crs="EPSG:4326")
    malha = _malhas()
    pontos = pontos.to_crs(malha.crs)
    x = gpd.sjoin(pontos, malha, how="left", predicate="within").drop(columns=["index_right"])
    x = x.drop_duplicates("codigo_cliente")
    logging.info("Clientes com GPS: %d | localizados em um setor: %d",
                 len(x), x["CD_SETOR"].notna().sum())
    renda = _renda()
    if renda is not None:
        x = x.merge(renda, on="CD_SETOR", how="left")
        logging.info("  com renda do setor: %d", x["renda_media_setor"].notna().sum())
    x.drop(columns=["geometry", "lat", "lon"]).to_csv(SAIDA, index=False)
    logging.info("Guardado %s", SAIDA.name)


if __name__ == "__main__":
    main()
