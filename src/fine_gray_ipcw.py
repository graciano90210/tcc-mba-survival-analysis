"""
Modelo de Fine e Gray com ponderação pela probabilidade inversa de censura
(IPCW) e comparação dos escritórios pela incidência acumulada (Sprint 5).

No capítulo 7 da V27 o modelo de Fine e Gray foi ajustado de forma
simplificada: os créditos quitados ficavam no conjunto de risco até o fim do
seguimento com peso 1, o que só é exato sem censura. Aqui a quitação entra como
manda o método: depois de quitado, o crédito continua no conjunto de risco com
peso G(t) / G(T_i), em que G é a curva de Kaplan-Meier da censura. A base é
expandida em intervalos entre os tempos de default (Geskus, 2011, a mesma
preparação do crprep do R) e ajustada com um Cox ponderado com entrada
tardia; os intervalos de 95% vêm de um bootstrap por cliente.

1. Landmark no dia 21, validação temporal (treino até 2024, teste jan a set
   de 2025): versão simplificada contra versão IPCW.
2. Escritórios: modelo de Fine e Gray (IPCW) só com o escritório, desde o
   desembolso; um teste de Wald com a covariância do bootstrap (2 graus de
   liberdade) compara as incidências acumuladas de default,
   uma versão baseada no modelo do teste de Gray (1988).

Saídas em reports/modelagem_v2/: fine_gray_ipcw_temporal.csv,
fine_gray_ipcw_coeficientes.csv e fine_gray_ipcw_escritorios.csv
"""

import logging

import numpy as np
import pandas as pd
from lifelines import CoxPHFitter, KaplanMeierFitter
from lifelines.exceptions import ConvergenceError
from scipy import stats
from sklearn.metrics import roc_auc_score

from cox_v2 import BASE, OUT_DIR, SEMILLA, _captura_top, _cargar, _preparar
from reconstruir_dataset import SALIDA_DESENL
from validacao_temporal import FIM_TESTE, FIM_TREINO, INICIO_TESTE

LANDMARK = 21
BLOQUE   = 7


def expandir_fine_gray(df, dur="dur", status="status", grade=None):
    """Base no formato de Fine e Gray com pesos IPCW.

    status: 0 = censura, 1 = default (evento de interesse), 2 = quitação.
    Devolve colunas inicio, fim, evento, peso, mais as demais colunas de df.
    """
    km = KaplanMeierFitter().fit(df[dur], event_observed=(df[status] == 0))

    def G(t):
        return km.survival_function_at_times(np.asarray(t)).to_numpy()

    if grade is None:
        grade = np.sort(df.loc[df[status] == 1, dur].unique())
    grade = np.asarray(grade, dtype=float)
    base = df.assign(inicio=0.0, fim=df[dur].astype(float),
                     evento=(df[status] == 1).astype(int), peso=1.0)
    # quitados: um intervalo extra entre cada par de tempos de default depois de T_i
    comp = df[df[status] == 2]
    t_i = comp[dur].to_numpy(dtype=float)
    k0 = np.searchsorted(grade, t_i, side="right")
    n = len(grade) - k0
    if n.sum() == 0:
        return base
    quem = np.repeat(np.arange(len(comp)), n)
    pos = np.concatenate([np.arange(a, len(grade)) for a in k0[n > 0]])
    primeiro = np.concatenate([[True] + [False] * (m - 1) for m in n[n > 0]])
    inicios = np.where(primeiro, t_i[quem], grade[np.maximum(pos - 1, 0)])
    extra = comp.iloc[quem].reset_index(drop=True).assign(
        inicio=inicios, fim=grade[pos], evento=0, peso=G(inicios) / G(t_i)[quem])
    longo = pd.concat([base, extra], ignore_index=True)
    return longo[longo["peso"] > 0]


def _grade_semanal(dados):
    """Tempos de default arredondados para a semana. Sem penalização, os
    coeficientes coincidem com os da grade completa (1,371 contra 1,373 em
    ratio_atraso) com um terço das linhas."""
    return np.unique(np.ceil(dados.loc[dados["status"] == 1, "dur"] / 7) * 7)


def _ajustar(longo, covs, penalizer=0.0, step_size=None):
    """Cox ponderado com entrada tardia. Sem erros-padrão robustos (o sanduíche
    do lifelines é lento demais com centenas de milhares de linhas): a incerteza
    vem do bootstrap por cliente, que também refaz a curva de censura.

    Sem penalização na base expandida: o lifelines divide a verossimilhança pela
    soma dos pesos, e as linhas extras dos quitados multiplicam essa soma, o que
    torna o mesmo penalizer muito mais forte (com 0,01 a razão de risco de
    ratio_atraso caía de 1,37 para 1,03)."""
    m = CoxPHFitter(penalizer=penalizer)
    m.fit(longo[covs + ["inicio", "fim", "evento", "peso"]], duration_col="fim",
          event_col="evento", entry_col="inicio", weights_col="peso",
          fit_options={"step_size": step_size} if step_size else None)
    return m


def _bootstrap(dados, covs, n, grade_semanal=True, penalizer=0.0):
    """Intervalos de 95% das razões de risco por bootstrap de clientes."""
    rng = np.random.default_rng(SEMILLA)
    clientes = dados["codigo_cliente"].unique()
    amostras, falhas = [], 0
    for b in range(n):
        escolhidos = rng.choice(clientes, len(clientes), replace=True)
        cont = pd.Series(escolhidos).value_counts()
        amostra = dados.merge(cont.rename("rep"), left_on="codigo_cliente", right_index=True)
        amostra = amostra.loc[amostra.index.repeat(amostra["rep"])]
        grade = _grade_semanal(amostra) if grade_semanal else None
        longo = expandir_fine_gray(amostra[covs + ["dur", "status"]], grade=grade)
        try:
            amostras.append(_ajustar(longo, covs, penalizer).params_)
        except ConvergenceError:
            try:   # passo de Newton menor antes de desistir da réplica
                amostras.append(_ajustar(longo, covs, penalizer, step_size=0.2).params_)
            except ConvergenceError:
                falhas += 1
        if (b + 1) % 25 == 0:
            logging.info("    bootstrap %d/%d", b + 1, n)
    logging.info("    réplicas sem convergência (descartadas): %d de %d", falhas, n)
    return pd.DataFrame(amostras)


def comparar_temporal():
    df = _cargar(BLOQUE)
    datas = pd.read_csv(SALIDA_DESENL, parse_dates=["fecha_credito"]).set_index("CÓDIGO CRÉDITO")
    df = df.join(datas["fecha_credito"], on="CÓDIGO CRÉDITO")
    fin = df.groupby("CÓDIGO CRÉDITO").agg(T=("t_stop", "max"), y=("evento", "max"),
                                            cura=("evento_cura", "max"))
    inicio = (LANDMARK // BLOQUE) * BLOQUE
    foto = df[df["t_start"] == inicio].join(fin, on="CÓDIGO CRÉDITO")
    foto["dur"] = foto["T"] - inicio
    foto["status"] = np.where(foto["y"] == 1, 1, np.where(foto["cura"] == 1, 2, 0))
    t_max = foto["dur"].max()
    treino = foto[foto["fecha_credito"] < FIM_TREINO]
    teste = foto[(foto["fecha_credito"] >= INICIO_TESTE) & (foto["fecha_credito"] < FIM_TESTE)]
    tr, te, _ = _preparar(treino.copy(), teste.copy(), BASE)

    simples = tr.assign(inicio=0.0, fim=np.where(tr["status"] == 2, t_max, tr["dur"]).astype(float),
                        evento=(tr["status"] == 1).astype(int), peso=1.0)
    longo = expandir_fine_gray(tr[BASE + ["dur", "status"]])
    logging.info("  base expandida: %d linhas (de %d créditos)", len(longo), len(tr))

    linhas, coefs = [], []
    # o simplificado mantém o penalizer 0,01 da V27 (uma linha por crédito)
    for nome, base, pen in [("simplificado", simples, 0.01), ("ipcw", longo, 0.0)]:
        m = _ajustar(base, BASE, pen)
        r = m.predict_partial_hazard(te[BASE]).to_numpy()
        y = te["y"].to_numpy()
        linhas.append({"modelo": nome, "auc": roc_auc_score(y, r), "captura_top10": _captura_top(y, r)})
        c = m.summary[["exp(coef)", "exp(coef) lower 95%", "exp(coef) upper 95%", "p"]].copy()
        c.columns = ["shr", "ic95_inf", "ic95_sup", "p"]
        coefs.append(c.assign(modelo=nome))
    return pd.DataFrame(linhas), pd.concat(coefs)


N_BOOT = 200


def coeficientes_ipcw():
    """Razões de risco do Fine e Gray IPCW no dia 21 com todos os créditos e
    intervalos de 95% por bootstrap de clientes."""
    df = _cargar(BLOQUE)
    fin = df.groupby("CÓDIGO CRÉDITO").agg(T=("t_stop", "max"), y=("evento", "max"),
                                            cura=("evento_cura", "max"))
    inicio = (LANDMARK // BLOQUE) * BLOQUE
    foto = df[df["t_start"] == inicio].join(fin, on="CÓDIGO CRÉDITO")
    foto["dur"] = foto["T"] - inicio
    foto["status"] = np.where(foto["y"] == 1, 1, np.where(foto["cura"] == 1, 2, 0))
    tr, _, _ = _preparar(foto.copy(), foto.iloc[:1].copy(), BASE)
    longo = expandir_fine_gray(tr[BASE + ["dur", "status"]], grade=_grade_semanal(tr))
    m = _ajustar(longo, BASE)
    boot = _bootstrap(tr[BASE + ["dur", "status", "codigo_cliente"]], BASE, N_BOOT)
    out = pd.DataFrame({"shr": np.exp(m.params_),
                        "ic95_inf": np.exp(boot.quantile(0.025)),
                        "ic95_sup": np.exp(boot.quantile(0.975)),
                        "p_boot": 2 * np.minimum((boot > 0).mean(), (boot < 0).mean())})
    return out


def comparar_escritorios():
    """Incidência acumulada de default por escritório, desde o desembolso, com
    teste de Wald usando a covariância do bootstrap (2 graus de liberdade)."""
    d = pd.read_csv(SALIDA_DESENL)
    ofi = _cargar(BLOQUE).groupby("CÓDIGO CRÉDITO")["ofi_id"].first()
    d = d.join(ofi, on="CÓDIGO CRÉDITO", how="inner")
    d["status"] = d["evento_tipo"]
    d["dur"] = d["T"].astype(float)
    d["ofi_31"] = (d["ofi_id"] == 31).astype(int)
    d["ofi_44"] = (d["ofi_id"] == 44).astype(int)
    covs = ["ofi_31", "ofi_44"]
    longo = expandir_fine_gray(d[covs + ["dur", "status"]], grade=_grade_semanal(d))
    logging.info("  escritórios: base expandida com %d linhas", len(longo))
    m = _ajustar(longo, covs)
    boot = _bootstrap(d[covs + ["dur", "status", "codigo_cliente"]], covs, 100)
    beta = m.params_.to_numpy()
    wald = float(beta @ np.linalg.solve(boot.cov().to_numpy(), beta))
    out = pd.DataFrame({"shr": np.exp(m.params_),
                        "ic95_inf": np.exp(boot.quantile(0.025)),
                        "ic95_sup": np.exp(boot.quantile(0.975))})
    out.loc["teste_wald_2gl", ["shr", "ic95_inf"]] = [wald, stats.chi2.sf(wald, df=2)]
    return out


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    met, coefs_t = comparar_temporal()
    met.round(4).to_csv(OUT_DIR / "fine_gray_ipcw_temporal.csv", index=False)
    print(met.round(3)); print(coefs_t.round(3).sort_index())
    coefs = coeficientes_ipcw()
    coefs.round(4).to_csv(OUT_DIR / "fine_gray_ipcw_coeficientes.csv")
    esc = comparar_escritorios()
    esc.round(5).to_csv(OUT_DIR / "fine_gray_ipcw_escritorios.csv")
    with pd.option_context("display.width", 200):
        print(met.round(3))
        print(coefs.round(3).sort_index())
        print(esc.round(4))


if __name__ == "__main__":
    main()
