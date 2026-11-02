"""
Reconstrucción del dataset de supervivencia a partir de los pagos diarios.

Sustituye la lógica de feature_engineering.py (que se conserva intacta para
trazabilidad de la V25). Los datos de entrada son los mismos (matriz_maestra.csv);
cambia la forma de medir el tiempo sin pago. feature_engineering.py medía el
silencio según los reportes de 10 días en que aparecía el crédito, pero los
reportes de ATLAS no listan los créditos de forma pareja:

1. Un crédito volado no aparece en los reportes mientras está en silencio, así
   que el cronómetro no avanzaba; el abono de limpieza posterior completaba el
   98% y el volado quedaba como "cura" (183 casos, p. ej. crédito 105720).
2. Otros créditos aparecen en todos los reportes 2020–2026, incluso antes de su
   desembolso, sin un solo abono y con SALDO = 0; el cronómetro corría sobre
   ellos y los marcaba como default (250 casos, p. ej. crédito 69632).
3. SALDO, CUOTAS ATRASADAS y VALOR ÚLTIMO ABONO reflejan el estado del día de la
   descarga (mayo 2026), no el histórico: usarlos como covariables es leakage.
   Aquí saldo y atraso se reconstruyen desde los pagos diarios.
4. El filtro CUOTAS_PACTADAS ≤ 40 dejaba pasar créditos semanales; aquí la
   cohorte se define por días entre cuotas.
5. El crédito tampoco aparece en el reporte de la ventana en que se cierra, así
   que el abono de cierre falta en las columnas diarias. El sistema solo cierra
   un crédito cuando el último abono deja SALDO = 0, de modo que FECHA ÚLTIMO
   ABONO es la fecha de cierre y se agrega como abono por el saldo faltante.
   Solo fija el desenlace, nunca una covariable anterior a él.

Reglas de negocio (confirmadas con la operación):
    Default: 120 días sin ningún pago, contados desde el día del último pago real
             (o desde FECHA CRÉDITO si nunca pagó). La limpieza de volados ocurre
             siempre después de ese umbral, así que no altera el evento.
    Cura:    pago acumulado ≥ 98% del TOTAL CRÉDITO antes de cualquier silencio
             de 120 días.
    Censura: ninguno de los dos antes del corte del estudio.

Vales (CLIENTE empieza con "VALE"): préstamos de la empresa a sus trabajadores,
sin intereses y a muchos días (confirmado con la operación). No son créditos de
clientes y se excluyen.

Créditos sin movimiento (SALDO = 0, ningún abono, último abono en la misma fecha
del desembolso): no hay base para etiquetarlos, se excluyen y se listan en
creditos_sin_movimiento.csv hasta confirmar en ATLAS qué representan.

Salidas:
    survival_dataset_v2_b7.csv   Counting Process en bloques de 7 días desde el
                                 desembolso (versión principal); covariables
                                 calculadas solo con información disponible al
                                 inicio de cada intervalo.
    survival_dataset_v2_b10.csv  Igual, en bloques de 10 días (sensibilidad).
    desenlaces_v2.csv        Una fila por crédito: T, tipo y motivo del desenlace.
"""

import logging
import re
from pathlib import Path

import numpy as np
import pandas as pd

from calendario_cobro import acumulado, uf_de_ruta

# ------------------------------------------------------------------ #
# Constantes                                                          #
# ------------------------------------------------------------------ #

_RAIZ          = Path(__file__).parent.parent
MATRIZ         = _RAIZ / "data" / "processed" / "matriz_maestra.csv"
SALIDA         = _RAIZ / "data" / "processed" / "survival_dataset_v2_b{}.csv"
SALIDA_DESENL  = _RAIZ / "data" / "processed" / "desenlaces_v2.csv"
SALIDA_SIN_MOV = _RAIZ / "data" / "processed" / "creditos_sin_movimiento.csv"

UMBRAL_DEFAULT         = 120                     # días sin pagar
PAGO_TOTAL_TOLERANCIA  = 0.98
FECHA_INICIO_DATOS     = pd.Timestamp("2020-01-01")
FECHA_CORTE            = pd.Timestamp("2026-05-15")
DIAS_BLOQUE            = 7                       # una semana: un ciclo completo de cobro
BLOQUES_SENSIBILIDAD   = (7, 10)                 # 10 = ventana de los reportes ATLAS
MAX_DIAS_POR_CUOTA     = 1.5                     # diario (con domingos libres ≈ 1,2)
EXCLUIR_SIN_MOVIMIENTO = True
PATRON_VALE            = r"^\s*VALE\b"          # préstamo al trabajador, no crédito de cliente
CUOTAS_MAX_NORMAL      = 50                      # plazos: 20, 24, 30, 40 o 50 días
CUOTAS_TIPICAS         = 20                      # plazo más común, para estimar la cuota original
FRAC_INCOMPLETA        = 0.90                    # abono menor que el 90% de la cuota
CHUNK_SIZE             = 5_000

COLS_CREDITO = [
    "CÓDIGO CRÉDITO", "CÓDIGO CLIENTE", "FECHA CRÉDITO", "FECHA VENCIMIENTO",
    "TOTAL CRÉDITO", "CUOTAS PACTADAS", "VALOR CUOTA", "ofi_id", "rta_id",
    "SALDO", "FECHA ÚLTIMO ABONO", "VALOR ÚLTIMO ABONO", "CLIENTE",
]

EVENTO_CENSURA, EVENTO_DEFAULT, EVENTO_CURA = 0, 1, 2


# ------------------------------------------------------------------ #
# Paso 1 — Pagos en formato largo + tabla de créditos                #
# ------------------------------------------------------------------ #

def _norm_codigo(s: pd.Series) -> pd.Series:
    return s.astype(str).str.replace(r"\.0$", "", regex=True)


def _extraer(path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Recorre la matriz en chunks y devuelve (creditos, pagos).

    pagos: una fila por (crédito, día) con abono > 0 dentro de la ventana del
    reporte que lo contiene. creditos: atributos contractuales y estado al día
    de la descarga (último snapshot).
    """
    header    = pd.read_csv(path, nrows=0).columns.tolist()
    cols_pago = [c for c in header if re.fullmatch(r"\d{4}-\d{2}-\d{2}", c)]
    fechas    = pd.to_datetime(cols_pago).values
    logging.info("  %d columnas de pago detectadas.", len(cols_pago))

    creditos, pagos = [], []
    for chunk in pd.read_csv(path, chunksize=CHUNK_SIZE, low_memory=False,
                             usecols=COLS_CREDITO + ["archivo_origen"] + cols_pago):
        chunk = chunk.dropna(subset=["CÓDIGO CRÉDITO"])
        ventana = chunk["archivo_origen"].str.extract(r"(\d{8})_(\d{8})\.xlsx")
        ini = pd.to_datetime(ventana[0], format="%Y%m%d").values
        fin = pd.to_datetime(ventana[1], format="%Y%m%d").values

        valores = chunk[cols_pago].apply(pd.to_numeric, errors="coerce").fillna(0).values
        mascara = (fechas[None, :] >= ini[:, None]) & (fechas[None, :] <= fin[:, None])
        fila, col = np.nonzero((valores > 0) & mascara)

        cod = _norm_codigo(chunk["CÓDIGO CRÉDITO"]).values
        pagos.append(pd.DataFrame({"cred": cod[fila], "fecha": fechas[col],
                                   "valor": valores[fila, col]}))
        c = chunk[COLS_CREDITO].copy()
        c["cred"] = cod
        creditos.append(c.drop_duplicates("cred", keep="last"))

    creditos = pd.concat(creditos).drop_duplicates("cred", keep="last").set_index("cred")
    creditos["fc"]  = pd.to_datetime(creditos["FECHA CRÉDITO"], errors="coerce")
    creditos["fv"]  = pd.to_datetime(creditos["FECHA VENCIMIENTO"], errors="coerce")
    creditos["fua"] = pd.to_datetime(creditos["FECHA ÚLTIMO ABONO"], errors="coerce").dt.normalize()
    for c in ["TOTAL CRÉDITO", "CUOTAS PACTADAS", "VALOR CUOTA", "SALDO", "VALOR ÚLTIMO ABONO"]:
        creditos[c] = pd.to_numeric(creditos[c], errors="coerce")

    pagos = (pd.concat(pagos, ignore_index=True)
             .drop_duplicates(["cred", "fecha"])
             .sort_values(["cred", "fecha"], ignore_index=True))
    logging.info("  %d créditos | %d pagos diarios.", len(creditos), len(pagos))
    return creditos, pagos


# ------------------------------------------------------------------ #
# Paso 2 — Cohorte                                                   #
# ------------------------------------------------------------------ #

def _filtrar_cohorte(creditos: pd.DataFrame, pagos: pd.DataFrame) -> pd.DataFrame:
    n0 = len(creditos)
    c = creditos.dropna(subset=["fc", "fv", "TOTAL CRÉDITO", "CUOTAS PACTADAS"])
    c = c[(c["TOTAL CRÉDITO"] > 0) & (c["CUOTAS PACTADAS"] > 0)]
    sin_datos = n0 - len(c)

    dias_por_cuota = (c["fv"] - c["fc"]).dt.days / c["CUOTAS PACTADAS"]
    no_diario = dias_por_cuota > MAX_DIAS_POR_CUOTA
    previo    = c["fc"] < FECHA_INICIO_DATOS          # historial de pagos incompleto
    posterior = c["fc"] > FECHA_CORTE
    vale      = c["CLIENTE"].astype(str).str.upper().str.match(PATRON_VALE)
    sin_mov   = ((c["SALDO"] == 0) & ~c.index.isin(pagos["cred"])
                 & (c["fua"] <= c["fc"]))

    fuera = no_diario | previo | posterior | vale
    logging.info(
        "Cohorte: %d créditos | excluidos: %d no diarios, %d desembolsados antes de %s, "
        "%d después del corte, %d vales de trabajadores, %d sin datos contractuales.",
        n0, no_diario.sum(), (previo & ~no_diario).sum(), FECHA_INICIO_DATOS.date(),
        (posterior & ~no_diario).sum(), (vale & ~(no_diario | previo | posterior)).sum(), sin_datos,
    )
    sin_mov = sin_mov & ~fuera
    c.loc[sin_mov, ["CÓDIGO CLIENTE", "FECHA CRÉDITO", "TOTAL CRÉDITO", "SALDO",
                    "VALOR ÚLTIMO ABONO", "FECHA ÚLTIMO ABONO", "ofi_id", "rta_id"]
          ].to_csv(SALIDA_SIN_MOV)
    logging.info("  %d créditos sin movimiento (SALDO 0, ningún abono) %s → %s",
                 sin_mov.sum(), "excluidos" if EXCLUIR_SIN_MOVIMIENTO else "incluidos",
                 SALIDA_SIN_MOV.name)
    if EXCLUIR_SIN_MOVIMIENTO:
        fuera = fuera | sin_mov
    return c[~fuera].copy()


# ------------------------------------------------------------------ #
# Paso 3 — Desenlace por crédito                                     #
# ------------------------------------------------------------------ #

def _agregar_abono_cierre(fila, fechas, valores):
    """Completa el último abono registrado por el sistema cuando falta en las
    columnas diarias. Con SALDO = 0 es el abono de cierre y cubre el saldo que
    los abonos capturados no alcanzan a explicar."""
    fua = fila["fua"]
    if pd.isna(fua) or fua < fila["fc"] or fua > FECHA_CORTE:
        return fechas, valores, False
    if fila["SALDO"] == 0:
        fechas  = [f for f in fechas if f <= fua]
        valores = valores[:len(fechas)]
        faltante = max(fila["TOTAL CRÉDITO"] - valores.sum(), 0.0)
        return fechas + [fua], np.append(valores, faltante), faltante > 0
    if fua not in fechas:
        valor = fila["VALOR ÚLTIMO ABONO"] if fila["VALOR ÚLTIMO ABONO"] > 0 else 0.0
        orden = np.argsort(fechas + [fua], kind="stable")
        fechas  = [(fechas + [fua])[i] for i in orden]
        valores = np.append(valores, valor)[orden]
    return fechas, valores, False


def _desenlace(fc, total, fechas, valores, cierre_sintetico) -> tuple[int, int, str]:
    """Devuelve (T en días desde el desembolso, tipo de evento, motivo)."""
    ancla, acumulado = fc, 0.0
    for i, (fecha, valor) in enumerate(zip(fechas, valores)):
        if (fecha - ancla).days >= UMBRAL_DEFAULT:
            motivo = "volado_limpiado" if ancla > fc else "nunca_pago_luego_limpiado"
            return (ancla - fc).days + UMBRAL_DEFAULT, EVENTO_DEFAULT, motivo
        acumulado += valor
        ancla = fecha
        if acumulado >= PAGO_TOTAL_TOLERANCIA * total:
            ultimo = i == len(fechas) - 1
            motivo = "cura_cierre_sistema" if (cierre_sintetico and ultimo) else "cura_pagos"
            return max((fecha - fc).days, 1), EVENTO_CURA, motivo
    if (FECHA_CORTE - ancla).days >= UMBRAL_DEFAULT:
        motivo = "volado_abierto" if ancla > fc else "nunca_pago_abierto"
        return (ancla - fc).days + UMBRAL_DEFAULT, EVENTO_DEFAULT, motivo
    return max((FECHA_CORTE - fc).days, 1), EVENTO_CENSURA, "activo_al_corte"


# ------------------------------------------------------------------ #
# Paso 4 — Counting Process con covariables predecibles              #
# ------------------------------------------------------------------ #

def _intervalos(cred, fila, dias_pago, valores, T, tipo, bloque=DIAS_BLOQUE) -> list[dict]:
    """Bloques (s, s+b] desde el desembolso. Las covariables del bloque usan
    solo pagos con día ≤ s (estado al inicio) y del bloque anterior (s−b, s].

    El atraso se mide en días de cobro (sin domingos ni feriados de la UF de
    la ruta, ver calendario_cobro.py): cobro[k] = días de cobro en (0, k]."""
    total, cuotas, valor_cuota = fila["TOTAL CRÉDITO"], fila["cuotas_modelo"], fila["cuota_modelo"]
    acum  = acumulado(uf_de_ruta(fila["rta_id"]))
    cobro = acum.loc[fila["fc"]: fila["fc"] + pd.Timedelta(days=T + bloque)].to_numpy()
    cobro = cobro - cobro[0]
    incompleto = valores < FRAC_INCOMPLETA * valor_cuota
    filas = []
    for s in range(0, T, bloque):
        hasta_s   = dias_pago <= s
        pagado    = valores[hasta_s].sum()
        ultimo    = dias_pago[hasta_s].max() if hasta_s.any() else 0
        previo    = (dias_pago > s - bloque) & hasta_s
        pagos_blq = np.zeros(bloque)
        if s > 0:
            np.add.at(pagos_blq, dias_pago[previo] - (s - bloque) - 1, valores[previo])
        esperado  = min(cobro[s], cuotas)
        atraso    = max(0.0, esperado - pagado / valor_cuota) if valor_cuota > 0 else 0.0
        stop      = min(s + bloque, T)
        final     = stop == T
        filas.append({
            "CÓDIGO CRÉDITO": cred,
            "t_start": s,
            "t_stop": stop,
            "evento": int(final and tipo == EVENTO_DEFAULT),
            "evento_cura": int(final and tipo == EVENTO_CURA),
            "evento_tipo": tipo if final else EVENTO_CENSURA,
            "dias_sin_pagar": s - ultimo,
            "dias_cobro_sin_pagar": int(cobro[s] - cobro[ultimo]),
            "pct_abono_incompleto": float(incompleto[hasta_s].mean()) if hasta_s.any() else 0.0,
            "dias_sin_cobro_bloque": int((stop - s) - (cobro[stop] - cobro[s])),
            "saldo_relativo": float(np.clip(1 - pagado / total, 0, 1)),
            "cuotas_atrasadas": atraso,
            "ratio_atraso": float(np.clip(atraso / cuotas, 0, 1)),
            "pago_promedio_diario_prev": pagos_blq.mean() if s > 0 else np.nan,
            "dias_con_abono_prev": int((pagos_blq > 0).sum()) if s > 0 else np.nan,
            "variabilidade_pago_prev": pagos_blq.std() if s > 0 else np.nan,
            "intensidad_recuperacion_prev": (
                pagos_blq[pagos_blq > 0][-1] / valor_cuota
                if s > 0 and (pagos_blq > 0).any() and valor_cuota > 0 else 0.0),
        })
    return filas


def _validar(df: pd.DataFrame, desenlaces: pd.DataFrame) -> None:
    g = df.groupby("CÓDIGO CRÉDITO", sort=False)
    assert (df["t_start"] >= 0).all(), "t_start negativo"
    assert (df["t_stop"] > df["t_start"]).all(), "intervalo vacío"
    assert (df["t_start"] == g["t_stop"].shift(1).fillna(0)).all(), "intervalos no contiguos"
    assert (g["evento"].sum() + g["evento_cura"].sum() <= 1).all(), "más de un desenlace"
    assert (df["dias_sin_pagar"] < UMBRAL_DEFAULT).all(), "covariable cruza el umbral antes del evento"
    assert len(desenlaces) == df["CÓDIGO CRÉDITO"].nunique()
    logging.info("  Validación Counting Process: OK")


def _cuota_original(creditos: pd.DataFrame) -> pd.DataFrame:
    """Renegociación con cuota de 1 real: cuando el comerciante cierra el
    negocio a mitad del crédito y después acuerda pagar semanal o quincenal,
    se le alarga el plazo en el MISMO crédito y la cuota queda en 1 real por
    día, para que no pese en el cobro diario de la ruta (confirmado con la
    operación). Como VALOR CUOTA y CUOTAS PACTADAS muestran el estado del día
    de la descarga, esos créditos aparecen con cuota de 1 real desde el
    desembolso, aunque en los primeros días pagaban la cuota normal (204 de
    269). Usar esos campos sería leakage: para las covariables se estima la
    cuota original como TOTAL / 20 cuotas (plazo más común). La marca
    renegociado_1real queda solo para el análisis descriptivo."""
    c = creditos.copy()
    c["renegociado_1real"] = c["CUOTAS PACTADAS"] > CUOTAS_MAX_NORMAL
    c["cuotas_modelo"] = np.where(c["renegociado_1real"], CUOTAS_TIPICAS, c["CUOTAS PACTADAS"])
    c["cuota_modelo"] = np.where(c["renegociado_1real"], c["TOTAL CRÉDITO"] / CUOTAS_TIPICAS,
                                 c["VALOR CUOTA"])
    logging.info("  %d créditos renegociados con cuota de 1 real (cuota original estimada)",
                 c["renegociado_1real"].sum())
    return c


def construir(path: Path = MATRIZ, bloques=BLOQUES_SENSIBILIDAD) -> tuple[dict, pd.DataFrame]:
    """Devuelve ({bloque: dataset Counting Process}, desenlaces). La matriz se
    lee una sola vez; el desenlace no depende del tamaño del bloque."""
    creditos, pagos = _extraer(path)
    creditos = _filtrar_cohorte(creditos, pagos)
    creditos = _cuota_original(creditos)
    pagos    = pagos[pagos["cred"].isin(creditos.index)]
    por_credito = {c: g for c, g in pagos.groupby("cred", sort=False)}

    filas, resumen = {b: [] for b in bloques}, []
    for cred, fila in creditos.iterrows():
        fc = fila["fc"]
        g = por_credito.get(cred)
        if g is not None:
            g = g[(g["fecha"] >= fc) & (g["fecha"] <= FECHA_CORTE)]
            fechas, valores = list(g["fecha"]), g["valor"].to_numpy()
        else:
            fechas, valores = [], np.array([])
        fechas, valores, sintetico = _agregar_abono_cierre(fila, fechas, valores)
        T, tipo, motivo = _desenlace(fc, fila["TOTAL CRÉDITO"], fechas, valores, sintetico)
        dias_pago = np.array([(f - fc).days for f in fechas], dtype=int)
        for b in bloques:
            filas[b].extend(_intervalos(cred, fila, dias_pago, valores, T, tipo, b))
        resumen.append((cred, fila["CÓDIGO CLIENTE"], T, tipo, motivo))

    estaticas = creditos[["CÓDIGO CLIENTE", "TOTAL CRÉDITO", "cuota_modelo",
                          "cuotas_modelo", "renegociado_1real", "ofi_id", "rta_id"]].rename(columns={
        "CÓDIGO CLIENTE": "codigo_cliente", "TOTAL CRÉDITO": "total_credito",
        "cuota_modelo": "valor_cuota", "cuotas_modelo": "cuotas_pactadas"})
    desenlaces = pd.DataFrame(resumen, columns=["CÓDIGO CRÉDITO", "codigo_cliente",
                                                "T", "evento_tipo", "motivo"])
    datasets = {}
    for b in bloques:
        df = pd.DataFrame(filas.pop(b)).merge(estaticas, left_on="CÓDIGO CRÉDITO",
                                              right_index=True, how="left")
        _validar(df, desenlaces)
        logging.info("  Bloque de %2d días: %d intervalos", b, len(df))
        datasets[b] = df

    n = len(desenlaces)
    for nombre, cod in [("Default", EVENTO_DEFAULT), ("Cura", EVENTO_CURA), ("Censura", EVENTO_CENSURA)]:
        k = (desenlaces["evento_tipo"] == cod).sum()
        logging.info("  %-8s %6d (%.2f%%)", nombre, k, 100 * k / n)
    for motivo, k in desenlaces["motivo"].value_counts().items():
        logging.info("    %-28s %6d", motivo, k)
    logging.info("  %d créditos", n)
    return datasets, desenlaces


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    datasets, desenlaces = construir()
    for b, df in datasets.items():
        df.to_csv(str(SALIDA).format(b), index=False)
        logging.info("Guardado %s", Path(str(SALIDA).format(b)).name)
    desenlaces.to_csv(SALIDA_DESENL, index=False)
    logging.info("Guardado %s", SALIDA_DESENL.name)
