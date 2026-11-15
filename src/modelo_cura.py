"""
Modelo de fração de cura (mixture cure model) no landmark do dia 21 (Sprint 5).

O modelo separa duas perguntas que o Fine e Gray responde juntas:
  incidência  quem vai terminar em default? Probabilidade pi(x) de o crédito ser
              "suscetível", por regressão logística;
  latência    entre os suscetíveis, quando o default acontece? Modelo de Weibull
              com covariáveis (tempo acelerado), para o tempo contado a partir do
              dia 120, isto é, o momento em que o cliente deixou de pagar.

Particularidade desta base: a quitação revela que o crédito está curado (nunca
mais pode terminar em default). Só os créditos ainda abertos têm o estado
desconhecido. A verossimilhança de cada crédito é:
    default  : pi(x) * f(u | x)
    quitado  : 1 - pi(x)
    aberto   : pi(x) * S(u | x) + 1 - pi(x)
com u = T - 119 dias (o default só pode ocorrer a partir do dia 120).

Mesmo desenho de validacao_temporal.py (treino até 2024, teste jan a set de
2025). O risco usado para ordenar é pi(x), a probabilidade de o crédito
terminar em default em algum momento.

Saídas em reports/modelagem_v2/: cura_temporal.csv (métricas com IC por
bootstrap) e cura_coeficientes.csv (razões de chances da incidência e razões
de tempo da latência, ajustadas com todos os créditos).
"""

import logging

import numpy as np
import pandas as pd
from lifelines import CoxPHFitter
from scipy import optimize, stats
from scipy.special import expit
from sklearn.metrics import roc_auc_score

from cox_v2 import BASE, OUT_DIR, SEMILLA, _captura_top, _cargar, _preparar
from reconstruir_dataset import SALIDA_DESENL
from validacao_temporal import BLOQUE, FIM_TESTE, FIM_TREINO, INICIO_TESTE

LANDMARK    = 21
INICIO_DEF  = 119      # u = T - 119 >= 1 para os defaults
PENAL       = 0.01     # penalização L2 leve nos coeficientes (não no intercepto)
N_BOOTSTRAP = 1000
LATENCIA    = ["ratio_atraso", "saldo_relativo", "dias_con_abono_prev",
               "pago_relativo_prev", "ofi_31", "ofi_44", "primeiro_credito"]


class ModeloCura:
    """Logística (incidência) + Weibull de tempo acelerado (latência)."""

    def __init__(self, inc_cols, lat_cols, penal=PENAL):
        self.inc_cols, self.lat_cols, self.penal = inc_cols, lat_cols, penal

    def _partes(self, theta):
        p = len(self.inc_cols) + 1
        q = len(self.lat_cols) + 1
        return theta[:p], theta[p:p + q], theta[p + q]

    def _loglik(self, theta, Xi, Xl, u, st):
        b, g, log_sigma = self._partes(theta)
        pi = np.clip(expit(Xi @ b), 1e-10, 1 - 1e-10)
        k = np.exp(-log_sigma)                         # forma da Weibull
        z = (np.log(u) - Xl @ g) * k                   # log(t / lambda) * k
        log_S = -np.exp(z)
        log_f = np.log(k) - np.log(u) + z + log_S
        ll = np.where(st == 1, np.log(pi) + log_f,
             np.where(st == 2, np.log1p(-pi),
                      np.logaddexp(np.log(pi) + log_S, np.log1p(-pi))))
        return ll

    def _objetivo(self, theta, *dados):
        b, g, _ = self._partes(theta)
        pen = self.penal * (np.sum(b[1:] ** 2) + np.sum(g[1:] ** 2))
        return -self._loglik(theta, *dados).sum() + pen

    def _matrizes(self, df):
        Xi = np.column_stack([np.ones(len(df)), df[self.inc_cols].to_numpy(float)])
        Xl = np.column_stack([np.ones(len(df)), df[self.lat_cols].to_numpy(float)])
        return Xi, Xl

    def fit(self, df):
        Xi, Xl = self._matrizes(df)
        u = np.maximum(df["T"].to_numpy(float) - INICIO_DEF, 1.0)
        st = df["status"].to_numpy()
        theta0 = np.zeros(Xi.shape[1] + Xl.shape[1] + 1)
        theta0[0] = np.log(st.__eq__(1).mean() / (1 - st.__eq__(1).mean()))
        theta0[Xi.shape[1]] = np.log(np.median(u[st == 1]))
        dados = (Xi, Xl, u, st)
        r = optimize.minimize(self._objetivo, theta0, args=dados, method="BFGS",
                              options={"maxiter": 5000, "gtol": 1e-6})
        # o BFGS costuma parar por perda de precisão já no ótimo; o L-BFGS-B
        # confirma a convergência (mesmo valor da função e dos coeficientes)
        r = optimize.minimize(self._objetivo, r.x, args=dados, method="L-BFGS-B")
        self.theta_, self.convergiu_ = r.x, r.success
        self._dados = dados
        return self

    def erros_padrao(self):
        """Erros-padrão pela inversa da hessiana numérica da verossimilhança."""
        f = lambda th: self._objetivo(th, *self._dados)
        n, eps = len(self.theta_), 1e-4
        H = np.zeros((n, n))
        for i in range(n):
            for j in range(i, n):
                ei, ej = np.eye(n)[i] * eps, np.eye(n)[j] * eps
                H[i, j] = H[j, i] = (f(self.theta_ + ei + ej) - f(self.theta_ + ei - ej)
                                     - f(self.theta_ - ei + ej) + f(self.theta_ - ei - ej)) / (4 * eps ** 2)
        return np.sqrt(np.diag(np.linalg.inv(H)))

    def incidencia(self, df):
        Xi, _ = self._matrizes(df)
        return expit(Xi @ self._partes(self.theta_)[0])


def _foto():
    df = _cargar(BLOQUE)
    datas = pd.read_csv(SALIDA_DESENL, parse_dates=["fecha_credito"]).set_index("CÓDIGO CRÉDITO")
    df = df.join(datas["fecha_credito"], on="CÓDIGO CRÉDITO")
    fin = df.groupby("CÓDIGO CRÉDITO").agg(T=("t_stop", "max"), y=("evento", "max"),
                                            cura=("evento_cura", "max"))
    t_max = fin["T"].max()
    inicio = (LANDMARK // BLOQUE) * BLOQUE
    foto = df[df["t_start"] == inicio].join(fin, on="CÓDIGO CRÉDITO")
    foto["status"] = np.where(foto["y"] == 1, 1, np.where(foto["cura"] == 1, 2, 0))
    foto["dur_fg"] = np.where(foto["cura"] == 1, t_max, foto["T"]) - inicio
    return foto


def comparar_temporal(foto, rng):
    treino = foto[foto["fecha_credito"] < FIM_TREINO]
    teste = foto[(foto["fecha_credito"] >= INICIO_TESTE) & (foto["fecha_credito"] < FIM_TESTE)]
    tr, te, _ = _preparar(treino.copy(), teste.copy(), BASE)
    cura = ModeloCura(BASE, LATENCIA).fit(tr)
    logging.info("  modelo de cura convergiu: %s", cura.convergiu_)
    fg = CoxPHFitter(penalizer=0.01).fit(tr[BASE + ["dur_fg", "y"]], "dur_fg", "y")
    riscos = {"fracao_cura": cura.incidencia(te),
              "fine_gray": fg.predict_partial_hazard(te[BASE]).to_numpy()}
    y = te["y"].to_numpy()
    boot = {k: {"auc": [], "cap": []} for k in list(riscos) + ["dif"]}
    for _ in range(N_BOOTSTRAP):
        i = rng.integers(0, len(y), len(y))
        if not 0 < y[i].sum() < len(y):
            continue
        for nome, r in riscos.items():
            boot[nome]["auc"].append(roc_auc_score(y[i], r[i]))
            boot[nome]["cap"].append(_captura_top(y[i], r[i]))
        boot["dif"]["cap"].append(boot["fracao_cura"]["cap"][-1] - boot["fine_gray"]["cap"][-1])
    linhas = []
    for nome, r in riscos.items():
        linhas.append({"modelo": nome, "auc": roc_auc_score(y, r),
                       "auc_ic_inf": np.percentile(boot[nome]["auc"], 2.5),
                       "auc_ic_sup": np.percentile(boot[nome]["auc"], 97.5),
                       "captura_top10": _captura_top(y, r),
                       "captura_ic_inf": np.percentile(boot[nome]["cap"], 2.5),
                       "captura_ic_sup": np.percentile(boot[nome]["cap"], 97.5)})
    d = np.asarray(boot["dif"]["cap"])
    linhas.append({"modelo": "dif_cura_menos_fg",
                   "captura_top10": linhas[0]["captura_top10"] - linhas[1]["captura_top10"],
                   "captura_ic_inf": np.percentile(d, 2.5), "captura_ic_sup": np.percentile(d, 97.5)})
    return pd.DataFrame(linhas)


def coeficientes(foto):
    """Ajuste com todos os créditos: razões de chances (incidência) e razões de
    tempo (latência), com intervalos de Wald pela hessiana."""
    tr, _, _ = _preparar(foto.copy(), foto.iloc[:1].copy(), BASE)
    m = ModeloCura(BASE, LATENCIA).fit(tr)
    ep = m.erros_padrao()
    nomes = ([("incidencia", "intercepto")] + [("incidencia", c) for c in BASE]
             + [("latencia", "intercepto")] + [("latencia", c) for c in LATENCIA]
             + [("latencia", "log_sigma")])
    out = pd.DataFrame({"coef": m.theta_, "ep": ep},
                       index=pd.MultiIndex.from_tuples(nomes, names=["parte", "variavel"]))
    out["razao"] = np.exp(out["coef"])
    out["ic95_inf"] = np.exp(out["coef"] - 1.96 * out["ep"])
    out["ic95_sup"] = np.exp(out["coef"] + 1.96 * out["ep"])
    out["p"] = 2 * stats.norm.sf(np.abs(out["coef"] / out["ep"]))
    pi = m.incidencia(tr)
    logging.info("  fração suscetível média estimada: %.4f (default observado: %.4f)",
                 pi.mean(), (tr["status"] == 1).mean())
    return out


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    rng = np.random.default_rng(SEMILLA)
    foto = _foto()
    met = comparar_temporal(foto, rng)
    met.round(4).to_csv(OUT_DIR / "cura_temporal.csv", index=False)
    coefs = coeficientes(foto)
    coefs.round(4).to_csv(OUT_DIR / "cura_coeficientes.csv")
    with pd.option_context("display.width", 200, "display.max_rows", 60):
        print(met.round(3))
        print(coefs[["razao", "ic95_inf", "ic95_sup", "p"]].round(3))


if __name__ == "__main__":
    main()
