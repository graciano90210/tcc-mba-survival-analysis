"""
Feature Engineering — construcción del dataset de supervivencia.

Transforma matriz_maestra.csv (panel de snapshots de 10 días) en un
dataset longitudinal formato Counting Process apto para
lifelines.CoxTimeVaryingFitter y pycox (DeepSurv).

Definición de evento (E=1):
    dias_sin_pagar >= 120 días calendario sin ningún abono.
    Equivale al "castigo de cartera" operativo de la entidad:
    4 meses de inactividad financiera total.

    NO se usa CUOTAS_ATRASADAS como umbral porque su techo es ~40
    (máximo de cuotas del crédito) y no distingue mora transitoria
    de abandono real.

Cierre por pago total (censura correcta):
    Cuando el pago acumulado real de un crédito alcanza su TOTAL CRÉDITO,
    el crédito se considera saldado y su trayectoria se trunca ahí (censura
    en lugar de evento). Sin esta regla, un cliente que ya pagó todo y no
    vuelve a tener abonos (porque no debe nada) queda indistinguible de un
    cliente que dejó de pagar estando en mora: el contador dias_sin_pagar
    sigue corriendo por forward-fill y termina cruzando el umbral de 120
    días meses después de que el crédito ya estaba saldado, generando un
    evento=1 falso. Verificado empíricamente: ~140 créditos con patrón de
    pago orgánico completo (abonos frecuentes sumando ~100% del total)
    aparecían con evento=1 y dias_sin_pagar de 300+ días.

Lectura en chunks para evitar cargar ~6 GB de columnas de pago en RAM.
Los agregados de pago (pago_promedio_diario, dias_con_abono) se calculan
al vuelo por chunk y las columnas de fecha se descartan antes de concatenar.
"""

import logging
from pathlib import Path

import numpy as np
import pandas as pd

# ------------------------------------------------------------------ #
# Constantes                                                          #
# ------------------------------------------------------------------ #

_RAIZ           = Path(__file__).parent.parent
MATRIZ          = _RAIZ / "data" / "processed" / "matriz_maestra.csv"
SALIDA_SURVIVAL = _RAIZ / "data" / "processed" / "survival_dataset.csv"

# E=1 cuando el crédito lleva >= 120 días calendario sin ningún abono
DIAS_SIN_PAGAR_UMBRAL = 120

# Créditos con CUOTAS_PACTADAS > 40 son semanales/quincenales → excluir
CUOTAS_MAX_DIARIO = 40

# Fracción del TOTAL CRÉDITO a partir de la cual se considera "pago total"
# (tolerancia para redondeos/intereses menores)
PAGO_TOTAL_TOLERANCIA = 0.98

CHUNK_SIZE = 5_000  # filas por chunk (~100 MB RAM)

COLS_ESTATICAS = [
    "CÓDIGO CRÉDITO",
    "FECHA CRÉDITO",
    "TOTAL CRÉDITO",
    "SALDO",
    "CUOTAS PACTADAS",
    "CUOTAS ATRASADAS",
    "VALOR CUOTA",
    "VALOR ÚLTIMO ABONO",
    "ofi_id",
    "rta_id",
    "archivo_origen",
]


# ------------------------------------------------------------------ #
# Paso 1 — Carga en chunks con agregados de pago al vuelo            #
# ------------------------------------------------------------------ #

def _es_fecha(s: str) -> bool:
    try:
        pd.to_datetime(s)
        return True
    except (ValueError, TypeError):
        return False


def _cargar_matriz(path: Path) -> pd.DataFrame:
    """Lee la matriz en chunks, calcula pago_promedio_diario y dias_con_abono
    usando solo las columnas de pago del rango del bloque (máscara vectorizada),
    y devuelve un DataFrame liviano sin las ~2.330 columnas de fecha.
    """
    logging.info("Cargando %s en chunks de %d filas...", path, CHUNK_SIZE)

    header    = pd.read_csv(path, nrows=0)
    cols_pago = [c for c in header.columns if _es_fecha(c)]
    pago_dates = pd.to_datetime(cols_pago)
    # Ordenar por fecha ascendente: necesario para identificar o último dia
    # com abono dentro do bloco (o CSV não garante ordem cronológica das colunas).
    _orden     = np.argsort(pago_dates.values)
    cols_pago  = [cols_pago[i] for i in _orden]
    pago_dates = pago_dates[_orden]
    logging.info("  %d columnas de pago detectadas.", len(cols_pago))

    fragmentos  = []
    filas_total = 0

    for chunk in pd.read_csv(
        path,
        chunksize=CHUNK_SIZE,
        parse_dates=["FECHA CRÉDITO"],
        low_memory=False,
    ):
        filas_total += len(chunk)

        # Fechas del bloque desde nombre de archivo
        fechas = chunk["archivo_origen"].str.extract(r"(\d{8})_(\d{8})\.xlsx")
        ini    = pd.to_datetime(fechas[0], format="%Y%m%d")
        fin    = pd.to_datetime(fechas[1], format="%Y%m%d")

        # Máscara vectorizada: (n_filas × n_cols_pago)
        ini_arr   = ini.values[:, np.newaxis]
        fin_arr   = fin.values[:, np.newaxis]
        dates_arr = pago_dates.values[np.newaxis, :]
        mascara   = (dates_arr >= ini_arr) & (dates_arr <= fin_arr)

        pagos_vals   = (
            chunk[cols_pago]
            .apply(pd.to_numeric, errors="coerce")
            .fillna(0)
            .values
        )
        pagos_bloque  = pagos_vals * mascara
        n_dias_bloque = mascara.sum(axis=1)
        n_dias_bloque = np.where(n_dias_bloque == 0, 1, n_dias_bloque)
        media_masc    = pagos_bloque.sum(axis=1) / n_dias_bloque

        # Variabilidade do pagamento diário dentro do bloco (desvio padrão
        # mascarado — só considera os dias efetivamente dentro do bloco).
        diff          = mascara * (pagos_vals - media_masc[:, np.newaxis])
        variabilidade = np.sqrt((diff ** 2).sum(axis=1) / n_dias_bloque)

        # Recência do último abono dentro do bloco (complementa dias_sem_pagar,
        # que é a recência ao longo de todo o histórico do crédito).
        pago_dia   = (pagos_vals > 0) & mascara
        idx_arr    = np.arange(pagos_vals.shape[1])
        idx_matrix = np.where(pago_dia, idx_arr[np.newaxis, :], -1)
        last_idx   = idx_matrix.max(axis=1)
        tem_pago   = last_idx != -1
        fecha_ultimo_pago_bloco = pago_dates.values[np.clip(last_idx, 0, None)]
        dias_desde_ultimo = (
            (fin.values - fecha_ultimo_pago_bloco) / np.timedelta64(1, "D")
        )
        dias_desde_ultimo = np.where(tem_pago, dias_desde_ultimo, n_dias_bloque)

        lean = chunk[COLS_ESTATICAS].copy()
        lean["fecha_ini_bloque"]     = ini.values
        lean["fecha_fin_bloque"]     = fin.values
        lean["pago_promedio_diario"] = media_masc.astype("float32")
        lean["dias_con_abono"] = (pagos_bloque > 0).sum(axis=1).astype("int16")
        lean["variabilidade_pago_diario"] = variabilidade.astype("float32")
        lean["dias_desde_ultimo_abono_no_bloco"] = dias_desde_ultimo.astype("float32")

        fragmentos.append(lean)

    df = pd.concat(fragmentos, ignore_index=True)
    logging.info("Carga completa: %d filas × %d columnas.", *df.shape)

    antes = len(df)
    df = df.dropna(subset=["CÓDIGO CRÉDITO"])
    df = df.drop_duplicates(subset=["CÓDIGO CRÉDITO", "archivo_origen"])
    logging.info("  %d filas eliminadas (subtotales + duplicados).", antes - len(df))

    return df


# ------------------------------------------------------------------ #
# Paso 2 — Filtro cohorte diaria                                     #
# ------------------------------------------------------------------ #

def _filtrar_cohorte_diaria(df: pd.DataFrame) -> pd.DataFrame:
    cuotas_max = (
        df.groupby("CÓDIGO CRÉDITO")["CUOTAS PACTADAS"]
        .max()
        .reset_index()
        .rename(columns={"CUOTAS PACTADAS": "_max"})
    )
    diarios   = cuotas_max.loc[cuotas_max["_max"] <= CUOTAS_MAX_DIARIO, "CÓDIGO CRÉDITO"]
    n_total   = df["CÓDIGO CRÉDITO"].nunique()
    n_ret     = diarios.nunique()

    logging.info(
        "Cohorte diaria (≤%d cuotas): %d / %d créditos retenidos (%.1f%%) | %d excluidos.",
        CUOTAS_MAX_DIARIO, n_ret, n_total, 100 * n_ret / n_total, n_total - n_ret,
    )
    return df[df["CÓDIGO CRÉDITO"].isin(diarios)].copy()


# ------------------------------------------------------------------ #
# Paso 3 — Cronómetro de inactividad (forward-fill por crédito)      #
# ------------------------------------------------------------------ #

def _calcular_dias_sin_pagar(df: pd.DataFrame) -> pd.DataFrame:
    """Calcula dias_sin_pagar para cada intervalo.

    Lógica:
    - fecha_ultimo_pago_efectivo se actualiza a fecha_fin_bloque cuando
      el bloque tiene dias_con_abono > 0 (hubo al menos un abono).
    - Si no hubo abono, se arrastra (forward-fill) la fecha anterior.
    - La semilla para el primer bloque de cada crédito es FECHA CRÉDITO.
    - dias_sin_pagar = (fecha_fin_bloque - fecha_ultimo_pago_efectivo).days

    Esto captura mora transitoria (gaps cortos) vs abandono real (>= 120 días).
    """
    df = df.sort_values(["CÓDIGO CRÉDITO", "fecha_ini_bloque"]).copy()

    # Candidata a "fecha de pago": fin del bloque si hubo abono, NaT si no
    df["_fecha_pago"] = df["fecha_fin_bloque"].where(df["dias_con_abono"] > 0, pd.NaT)

    # Primera fila de cada crédito sin pago → semilla = FECHA CRÉDITO
    primera         = ~df["CÓDIGO CRÉDITO"].duplicated(keep="first")
    sin_pago_primera = primera & df["_fecha_pago"].isna()
    df.loc[sin_pago_primera, "_fecha_pago"] = df.loc[sin_pago_primera, "FECHA CRÉDITO"]

    # Forward-fill dentro de cada crédito
    df["fecha_ultimo_pago_efectivo"] = (
        df.groupby("CÓDIGO CRÉDITO")["_fecha_pago"]
        .transform(lambda x: x.ffill())
    )

    df["dias_sin_pagar"] = (
        (df["fecha_fin_bloque"] - df["fecha_ultimo_pago_efectivo"])
        .dt.days.clip(lower=0)
        .astype("int16")
    )

    return df.drop(columns=["_fecha_pago"])


# ------------------------------------------------------------------ #
# Paso 4 — Dataset de supervivencia (Counting Process)               #
# ------------------------------------------------------------------ #

def _construir_survival_df(df: pd.DataFrame) -> pd.DataFrame:
    """Genera intervalos (t_start, t_stop) con correcciones de
    Left Truncation y continuidad via shift(). Aplica la nueva
    definición de evento basada en dias_sin_pagar >= 120.
    """
    # Cronómetro de inactividad (antes del sort para preservar orden)
    df = _calcular_dias_sin_pagar(df)

    # ── t_stop / t_start ────────────────────────────────────────────────
    df["t_stop"] = (
        (df["fecha_fin_bloque"] - df["FECHA CRÉDITO"]).dt.days + 1
    )
    df["t_start"] = df.groupby("CÓDIGO CRÉDITO")["t_stop"].shift(1)
    primera        = df["t_start"].isna()
    df.loc[primera, "t_start"] = (
        (df.loc[primera, "fecha_ini_bloque"] - df.loc[primera, "FECHA CRÉDITO"])
        .dt.days.clip(lower=0)
    )
    df["t_start"] = df["t_start"].astype(int)
    df["t_stop"]  = df["t_stop"].astype(int)

    inv = df["t_stop"] <= df["t_start"]
    if inv.sum():
        logging.warning("%d intervalos con t_stop <= t_start eliminados.", inv.sum())
        df = df[~inv]

    # ── Evento: 120 días calendario sin ningún abono ─────────────────────
    df["evento"] = (df["dias_sin_pagar"] >= DIAS_SIN_PAGAR_UMBRAL).astype(int)

    # ── Covariables tiempo-variantes ────────────────────────────────────
    cuotas_atr  = pd.to_numeric(df["CUOTAS ATRASADAS"], errors="coerce").fillna(0)
    valor_cuota = pd.to_numeric(df["VALOR CUOTA"], errors="coerce").replace(0, np.nan)
    ultimo_abono= pd.to_numeric(df["VALOR ÚLTIMO ABONO"], errors="coerce").fillna(0)
    cuotas_pact = pd.to_numeric(df["CUOTAS PACTADAS"], errors="coerce").replace(0, np.nan)
    total_cred  = pd.to_numeric(df["TOTAL CRÉDITO"], errors="coerce").replace(0, np.nan)
    saldo       = pd.to_numeric(df["SALDO"], errors="coerce").fillna(0)

    # ── Cierre por pago total: detiene el cronómetro cuando el crédito ya
    #    fue saldado, para no confundir "no debe nada" con "abandonó el pago" ──
    n_dias_bloque   = (df["fecha_fin_bloque"] - df["fecha_ini_bloque"]).dt.days + 1
    pago_bloque     = df["pago_promedio_diario"] * n_dias_bloque
    pago_acumulado  = pago_bloque.groupby(df["CÓDIGO CRÉDITO"]).cumsum()
    df["_saldado"]  = (pago_acumulado >= PAGO_TOTAL_TOLERANCIA * total_cred).astype(int)

    df["cuotas_atrasadas"]        = cuotas_atr.astype("float32")
    df["intensidad_recuperacion"] = (ultimo_abono / valor_cuota).clip(0, 10).fillna(0).astype("float32")
    df["ratio_atraso"]            = (cuotas_atr / cuotas_pact).clip(0, 1).fillna(0).astype("float32")
    df["saldo_relativo"]          = (saldo / total_cred).clip(0, 1).fillna(0).astype("float32")
    df["total_credito"]           = total_cred.astype("float32")
    df["valor_cuota"]             = valor_cuota.astype("float32")
    df["cuotas_pactadas"]         = cuotas_pact.astype("float32")

    # ── Regla de censura: truncar trayectoria tras el primer cierre, sea
    #    por default (dias_sin_pagar >= 120) o por cura (pago total) — lo
    #    que ocurra primero cronológicamente. Cuando el cierre es por pago
    #    total, el bloque necesariamente tuvo abono reciente (dias_con_abono
    #    > 0), así que "evento" (default) ya es 0 ahí de forma natural.
    filas_antes  = len(df)
    n_saldados   = df.loc[df["_saldado"] == 1, "CÓDIGO CRÉDITO"].nunique()
    df["_cierre"] = np.maximum(df["evento"], df["_saldado"])
    df["_ecum"]   = df.groupby("CÓDIGO CRÉDITO")["_cierre"].cumsum()
    df = df[df["_ecum"] <= 1].copy()

    # ── Riscos Competitivos: evento_tipo = 0 (censurado) | 1 (default) |
    #    2 (cura/pagamento total). "evento" (binário) se mantém por
    #    compatibilidade com uso de Cox de evento único.
    df["evento_tipo"] = 0
    df.loc[df["evento"] == 1, "evento_tipo"] = 1
    df.loc[(df["_saldado"] == 1) & (df["evento"] == 0), "evento_tipo"] = 2
    df["evento_cura"] = (df["evento_tipo"] == 2).astype(int)

    df = df.drop(columns=["_ecum", "_cierre", "_saldado"])
    logging.info(
        "Censura aplicada: %d filas eliminadas post-cierre (default o cura).",
        filas_antes - len(df),
    )
    logging.info(
        "Créditos por desfecho — Default: %d | Cura: %d | (candidatos a cura antes de truncar: %d)",
        int((df["evento_tipo"] == 1).sum()), int((df["evento_tipo"] == 2).sum()), n_saldados,
    )

    cols_salida = [
        "CÓDIGO CRÉDITO", "t_start", "t_stop", "evento", "evento_tipo", "evento_cura",
        "dias_sin_pagar",
        "cuotas_atrasadas", "pago_promedio_diario", "dias_con_abono",
        "variabilidade_pago_diario", "dias_desde_ultimo_abono_no_bloco",
        "intensidad_recuperacion", "ratio_atraso", "saldo_relativo",
        "total_credito", "valor_cuota", "cuotas_pactadas",
        "ofi_id", "rta_id",
    ]
    return df[cols_salida].reset_index(drop=True)


# ------------------------------------------------------------------ #
# Paso 5 — Validación estadística                                    #
# ------------------------------------------------------------------ #

def _validar_dataset(df: pd.DataFrame) -> None:
    n_creditos   = df["CÓDIGO CRÉDITO"].nunique()
    n_intervalos = len(df)
    n_eventos    = df["evento"].sum()
    tasa_evento  = 100 * n_eventos / n_creditos if n_creditos else 0
    con_evento   = df[df["evento"] == 1]["CÓDIGO CRÉDITO"].nunique()
    t_fin        = df.groupby("CÓDIGO CRÉDITO")["t_stop"].max()

    n_default  = int((df["evento_tipo"] == 1).sum())
    n_cura     = int((df["evento_tipo"] == 2).sum())
    n_censura  = n_creditos - n_default - n_cura

    logging.info("══ VALIDACIÓN DEL DATASET DE SUPERVIVENCIA ══")
    logging.info("  Definição evento:         dias_sin_pagar >= %d", DIAS_SIN_PAGAR_UMBRAL)
    logging.info("  Créditos únicos:           %d", n_creditos)
    logging.info("  Intervalos (filas):        %d", n_intervalos)
    logging.info("  Eventos (E=1):             %d  (tasa: %.1f%%)", n_eventos, tasa_evento)
    logging.info("  Créditos con evento:       %d", con_evento)
    logging.info("  Créditos censurados:       %d", n_creditos - con_evento)
    logging.info(
        "  Riscos Competitivos —      Default: %d (%.1f%%) | Cura: %d (%.1f%%) | Censura verdadera: %d (%.1f%%)",
        n_default, 100 * n_default / n_creditos,
        n_cura, 100 * n_cura / n_creditos,
        n_censura, 100 * n_censura / n_creditos,
    )
    logging.info("  T mediana (días):          %.0f", t_fin.median())
    logging.info("  T min / T max:             %.0f / %.0f", t_fin.min(), t_fin.max())
    logging.info(
        "  Intervalos por crédito:    media=%.1f  max=%d",
        n_intervalos / n_creditos if n_creditos else 0,
        df.groupby("CÓDIGO CRÉDITO").size().max(),
    )
    logging.info(
        "  dias_sin_pagar — mediana=%.0f  p95=%.0f  max=%.0f",
        df["dias_sin_pagar"].median(),
        df["dias_sin_pagar"].quantile(0.95),
        df["dias_sin_pagar"].max(),
    )

    if n_eventos < 100:
        logging.warning(
            "ALERTA: solo %d eventos — Cox puede ser inestable. "
            "Considerar reducir DIAS_SIN_PAGAR_UMBRAL (actual: %d).",
            n_eventos, DIAS_SIN_PAGAR_UMBRAL,
        )


# ------------------------------------------------------------------ #
# Orquestador                                                         #
# ------------------------------------------------------------------ #

def construir_dataset_supervivencia() -> pd.DataFrame:
    df = _cargar_matriz(MATRIZ)
    df = _filtrar_cohorte_diaria(df)
    survival_df = _construir_survival_df(df)
    _validar_dataset(survival_df)

    survival_df.to_csv(SALIDA_SURVIVAL, index=False, encoding="utf-8-sig")
    logging.info("CSV exportado → %s", SALIDA_SURVIVAL)
    return survival_df


# ------------------------------------------------------------------ #
# Punto de entrada                                                    #
# ------------------------------------------------------------------ #

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    construir_dataset_supervivencia()
