"""
Data Stitching — pipeline de consolidação do Data Lake para modelagem de sobrevivência.

Lê todos os arquivos .xlsx extraídos pelo robô (estrutura OFI_*/RTA_*/) e os
concatena num único DataFrame longitudinal, adicionando colunas de rastreabilidade
(ofi_id, rta_id, arquivo_origen) e otimizando os tipos de dados para reduzir
o consumo de memória antes da exportação CSV.
"""

import logging
from pathlib import Path

import numpy as np
import pandas as pd

# ------------------------------------------------------------------ #
# Constantes                                                          #
# ------------------------------------------------------------------ #

_RAIZ    = Path(__file__).parent.parent
DIR_RAW  = _RAIZ / "data" / "raw"
DIR_PROC = _RAIZ / "data" / "processed"
SALIDA   = DIR_PROC / "matriz_maestra.csv"

_INT32_MIN = np.iinfo(np.int32).min
_INT32_MAX = np.iinfo(np.int32).max

_COLS_METADATA = {"ofi_id", "rta_id", "archivo_origen"}

# Sufijos de archivos parciales/ocultos que el robot puede dejar
_SUFIJOS_INVALIDOS = {".crdownload", ".tmp"}


# ------------------------------------------------------------------ #
# Paso 1 — Escaneo del Data Lake                                      #
# ------------------------------------------------------------------ #

def _listar_archivos(dir_raw: Path) -> list[dict]:
    """Escanea dir_raw recursivamente y retorna metadatos de cada .xlsx válido.

    Extrae ofi_id y rta_id directamente del path (sin regex), filtrando
    archivos ocultos y descargas parciales del robot Selenium.

    Args:
        dir_raw: Raíz del Data Lake (data/raw/).

    Returns:
        Lista de dicts con claves ``path``, ``ofi_id`` y ``rta_id``,
        ordenada por path para reproducibilidad.
    """
    resultado = []

    for archivo in sorted(dir_raw.rglob("*.xlsx")):
        # Descartar archivos ocultos o temporales
        if archivo.name.startswith(".") or archivo.suffix in _SUFIJOS_INVALIDOS:
            continue

        # Extraer IDs del path: .../OFI_23/RTA_96/planilla_*.xlsx
        # parent      → RTA_96   parent.parent → OFI_23
        rta_dir = archivo.parent.name        # "RTA_96"
        ofi_dir = archivo.parent.parent.name  # "OFI_23"

        # Solo procesar archivos dentro de la jerarquía OFI_*/RTA_*/
        if not (ofi_dir.startswith("OFI_") and rta_dir.startswith("RTA_")):
            logging.warning("Archivo fuera de jerarquía esperada, omitido: %s", archivo)
            continue

        resultado.append({
            "path":    archivo,
            "ofi_id": ofi_dir.split("_", 1)[1],  # "23"
            "rta_id": rta_dir.split("_", 1)[1],  # "96"
        })

    logging.info("%d archivos .xlsx válidos encontrados en %s.", len(resultado), dir_raw)
    return resultado


# ------------------------------------------------------------------ #
# Paso 2 — Lectura individual con metadatos                           #
# ------------------------------------------------------------------ #

def _leer_archivo(info: dict, idx: int, total: int) -> "pd.DataFrame | None":
    """Lee un archivo .xlsx y añade columnas de trazabilidad.

    Args:
        info:  Dict con claves ``path``, ``ofi_id``, ``rta_id``.
        idx:   Posición en el lote (para log de progreso).
        total: Total de archivos en el lote.

    Returns:
        DataFrame con columnas originales más ``ofi_id``, ``rta_id`` y
        ``archivo_origen``. Retorna ``None`` si el archivo está corrupto.
    """
    archivo: Path = info["path"]
    try:
        # header=8: primeras 8 filas son metadatos del reporte (título, ruta, etc.)
        # La fila 8 contiene los nombres reales de columnas (CÓDIGO CLIENTE, etc.)
        df = pd.read_excel(archivo, engine="openpyxl", header=8)
    except Exception as exc:
        logging.error("[SKIP] [%d/%d] %s — %s", idx, total, archivo.name, exc)
        return None

    df["ofi_id"]         = info["ofi_id"]
    df["rta_id"]         = info["rta_id"]
    df["archivo_origen"] = archivo.name

    logging.info("[%4d/%d] %s — %d filas", idx, total, archivo.name, len(df))
    return df


# ------------------------------------------------------------------ #
# Paso 3 — Optimización de memoria                                    #
# ------------------------------------------------------------------ #

def _optimizar_dtypes(df: pd.DataFrame) -> pd.DataFrame:
    """Reduce el consumo de memoria del DataFrame aplicando tipos eficientes.

    Reglas aplicadas en orden de precedencia por columna:
    1. Columnas de metadatos y object con ≤ 50 valores únicos → ``category``
    2. Columnas object parseables como fecha → ``datetime64[ns]``
    3. float64 → ``float32``
    4. int64 dentro del rango int32 → ``int32``

    Args:
        df: DataFrame consolidado tras pd.concat.

    Returns:
        DataFrame con tipos optimizados (in-place sobre copia).
    """
    mb_antes = df.memory_usage(deep=True).sum() / 1_048_576

    for col in df.columns:
        dtype = df[col].dtype

        # ── object ────────────────────────────────────────────────────
        if dtype == object:
            if col in _COLS_METADATA or df[col].nunique() <= 50:
                df[col] = df[col].astype("category")
            else:
                # Intentar conversión a datetime
                try:
                    convertida = pd.to_datetime(df[col], errors="raise")
                    df[col] = convertida
                except (ValueError, TypeError):
                    pass  # dejar como object si no es fecha

        # ── float64 → float32 ─────────────────────────────────────────
        elif dtype == np.float64:
            df[col] = df[col].astype(np.float32)

        # ── int64 → int32 si el rango lo permite ──────────────────────
        elif dtype == np.int64:
            if df[col].between(_INT32_MIN, _INT32_MAX).all():
                df[col] = df[col].astype(np.int32)

    mb_despues = df.memory_usage(deep=True).sum() / 1_048_576
    reduccion  = (1 - mb_despues / mb_antes) * 100 if mb_antes > 0 else 0

    logging.info(
        "Memoria: %.1f MB → %.1f MB (%.0f%% reducción).",
        mb_antes, mb_despues, reduccion,
    )
    return df


# ------------------------------------------------------------------ #
# Paso 4 — Orquestador principal                                      #
# ------------------------------------------------------------------ #

def consolidar_cartera(dir_raw: Path = DIR_RAW) -> pd.DataFrame:
    """Consolida todo el Data Lake en un único DataFrame longitudinal.

    Escanea dir_raw recursivamente, lee cada .xlsx, añade trazabilidad
    OFI/RTA, concatena verticalmente, optimiza tipos de datos y exporta
    el resultado como CSV a data/processed/matriz_maestra.csv.

    Args:
        dir_raw: Raíz del Data Lake. Por defecto ``data/raw/``.

    Returns:
        DataFrame maestro consolidado. Vacío si no se encontraron archivos.
    """
    DIR_PROC.mkdir(parents=True, exist_ok=True)

    archivos = _listar_archivos(dir_raw)
    if not archivos:
        logging.warning("No se encontraron archivos. Verifica la extracción.")
        return pd.DataFrame()

    total     = len(archivos)
    fragmentos = [
        _leer_archivo(info, i, total)
        for i, info in enumerate(archivos, start=1)
    ]
    fragmentos = [f for f in fragmentos if f is not None]

    if not fragmentos:
        logging.error("Ningún archivo pudo ser leído. Verifica data/raw/.")
        return pd.DataFrame()

    logging.info("Concatenando %d fragmentos...", len(fragmentos))
    maestro = pd.concat(fragmentos, ignore_index=True)

    maestro = _optimizar_dtypes(maestro)

    logging.info(
        "DataFrame maestro: %d filas × %d columnas.",
        maestro.shape[0], maestro.shape[1],
    )
    logging.info(
        "Oficinas: %s | Rutas: %d",
        sorted(maestro["ofi_id"].unique()),
        maestro["rta_id"].nunique(),
    )

    maestro.to_csv(SALIDA, index=False, encoding="utf-8-sig")
    logging.info("CSV exportado → %s", SALIDA)

    return maestro


# ------------------------------------------------------------------ #
# Punto de entrada                                                     #
# ------------------------------------------------------------------ #

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    consolidar_cartera()
