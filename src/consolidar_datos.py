"""
Fase de Transformación del pipeline ETL del TCC.
Lee todos los .xlsx de data/raw/ y los consolida en data/processed/matriz_maestra.csv.
"""

import logging
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).parent.parent
DIR_RAW = RAIZ / "data" / "raw"
DIR_PROC = RAIZ / "data" / "processed"
SALIDA = DIR_PROC / "matriz_maestra.csv"


def consolidar_cartera() -> pd.DataFrame:
    """
    Apila verticalmente todos los archivos .xlsx de data/raw/ en un DataFrame maestro
    y lo exporta como CSV a data/processed/matriz_maestra.csv.

    Returns:
        DataFrame consolidado con todos los registros de cartera.
    """
    DIR_PROC.mkdir(parents=True, exist_ok=True)

    archivos = sorted(DIR_RAW.glob("*.xlsx"))
    total = len(archivos)

    if total == 0:
        logging.warning("No se encontraron archivos .xlsx en %s. Verifica la extracción.", DIR_RAW)
        return pd.DataFrame()

    logging.info("%d archivos .xlsx encontrados en %s.", total, DIR_RAW)

    fragmentos = []
    for i, archivo in enumerate(archivos, start=1):
        try:
            df = pd.read_excel(archivo, engine="openpyxl")
            logging.info("[%3d/%d] %s — %d filas", i, total, archivo.name, len(df))
            fragmentos.append(df)
        except Exception as exc:
            logging.error("Archivo corrupto, se omite [%s]: %s", archivo.name, exc)
            continue

    if not fragmentos:
        logging.error("Ningún archivo pudo ser leído. Verifica data/raw/.")
        return pd.DataFrame()

    maestro = pd.concat(fragmentos, ignore_index=True)
    logging.info(
        "DataFrame maestro consolidado: %s → %d filas × %d columnas.",
        maestro.shape,
        maestro.shape[0],
        maestro.shape[1],
    )

    # BOM UTF-8 garantiza apertura correcta en Excel y sin errores en Jupyter
    maestro.to_csv(SALIDA, index=False, encoding="utf-8-sig")
    logging.info("CSV exportado → %s", SALIDA)

    return maestro


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    consolidar_cartera()
