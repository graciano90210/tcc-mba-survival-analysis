"""
Script que gera o notebook de práctica notebooks/exercicio_gestao_taxi.ipynb
aplicando CRISP-DM ao problema de previsão de duração de corridas de táxi
(NYC TLC), como exercicio de práctica para Gestão Ágil de Projetos II.

Baseado no projeto de referência projeto_taxi_crispdm (Módulo II).
"""
import nbformat as nbf

nb = nbf.v4.new_notebook()
cells = []


def md(text):
    cells.append(nbf.v4.new_markdown_cell(text))


def code(text):
    cells.append(nbf.v4.new_code_cell(text))


# ── 1. Entendimento do Negócio ──────────────────────────────────────────
md("""# Exercício de Práctica — CRISP-DM: Previsão de Duração de Corridas de Táxi (NYC)

**Curso:** Gestão Ágil de Projetos em Ciência de Dados e Inteligência Artificial II
**Baseado em:** projeto_taxi_crispdm (material de referência do Módulo II)

## 1. Entendimento do Negócio

**Pergunta de negócio:** como estimar, com erro aceitável, a duração de uma corrida
de táxi a partir de informações temporais, geográficas e operacionais disponíveis
*antes* do fim da viagem?

**Por que importa:** a duração estimada afeta a expectativa do passageiro, o
planejamento do motorista, a alocação de frota e a análise de eficiência urbana
(ETA — Estimated Time of Arrival).

**Problema de dados:** regressão supervisionada. O *target* é `duration_min`,
calculado como a diferença entre o horário de desembarque e o horário de embarque.

**Fonte:** dados públicos e reais da NYC Taxi & Limousine Commission (TLC).
""")

# ── 2. Setup ──────────────────────────────────────────────────────────
md("## 2. Setup — imports e configuração")

code("""import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_percentage_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

RANDOM_STATE = 42""")

# ── 3. Entendimento dos Dados: carregamento ─────────────────────────────
md("""## 3. Entendimento dos Dados — carregamento

Os dados são publicados mensalmente pela TLC em formato `.parquet`. Para manter
o exercício leve, carregamos apenas 1-2 meses com uma amostra de linhas.
""")

code("""DATA_URLS = {
    '2026-01': 'https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2026-01.parquet',
    '2026-02': 'https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2026-02.parquet',
}

ZONE_URL = 'https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv'

RAW_COLUMNS = [
    'VendorID', 'tpep_pickup_datetime', 'tpep_dropoff_datetime',
    'passenger_count', 'trip_distance', 'RatecodeID', 'store_and_fwd_flag',
    'PULocationID', 'DOLocationID', 'payment_type', 'fare_amount',
    'tip_amount', 'total_amount'
]

USE_MONTHS = ['2026-01', '2026-02']
MAX_ROWS_PER_MONTH = 20_000


def load_month(label, url, max_rows=20_000):
    month = pd.read_parquet(url, columns=RAW_COLUMNS)
    month['source_month'] = label
    if len(month) > max_rows:
        month = month.sample(max_rows, random_state=RANDOM_STATE)
    return month


frames = [load_month(m, DATA_URLS[m], MAX_ROWS_PER_MONTH) for m in USE_MONTHS]
df_raw = pd.concat(frames, ignore_index=True)
zones = pd.read_csv(ZONE_URL)

print(df_raw.shape)
df_raw.head()""")

code("""print('Linhas:', len(df_raw))
print('Colunas:', df_raw.shape[1])
display(df_raw.dtypes.to_frame('dtype'))
display(df_raw.isna().mean().sort_values(ascending=False).to_frame('proporcao_nulos').head(10))""")

# ── 4. Preparação dos Dados ─────────────────────────────────────────────
md("""## 4. Preparação dos Dados

Pontos importantes:
- O *target* é derivado dos timestamps — precisamos validar datas impossíveis.
- Algumas variáveis existem apenas *depois* da corrida (ex.: `tip_amount`,
  `total_amount`) e causariam **vazamento de dados** se usadas como feature
  para prever a duração antes da viagem começar — por isso não entram no
  conjunto de features do modelo.
- Filtros de qualidade (duração, distância, tarifa, passageiros) devem ser
  documentados, pois alteram a população analisada.
""")

code("""def prepare_data(df_raw, zones):
    df = df_raw.copy()
    df['pickup_datetime'] = pd.to_datetime(df['tpep_pickup_datetime'])
    df['dropoff_datetime'] = pd.to_datetime(df['tpep_dropoff_datetime'])
    df['duration_min'] = (df['dropoff_datetime'] - df['pickup_datetime']).dt.total_seconds() / 60

    pu_zones = zones.add_prefix('PU_')
    do_zones = zones.add_prefix('DO_')
    df = df.merge(pu_zones, left_on='PULocationID', right_on='PU_LocationID', how='left')
    df = df.merge(do_zones, left_on='DOLocationID', right_on='DO_LocationID', how='left')

    before = len(df)
    quality_mask = (
        df['duration_min'].between(1, 120)
        & df['trip_distance'].between(0.1, 50)
        & df['fare_amount'].gt(0)
        & df['passenger_count'].between(1, 6)
    )
    df = df.loc[quality_mask].copy()
    after = len(df)

    df['pickup_hour'] = df['pickup_datetime'].dt.hour
    df['pickup_dayofweek'] = df['pickup_datetime'].dt.dayofweek
    df['pickup_month'] = df['pickup_datetime'].dt.month
    df['is_weekend'] = df['pickup_dayofweek'].isin([5, 6]).astype(int)
    df['same_borough'] = (df['PU_Borough'] == df['DO_Borough']).astype(int)
    df['airport_trip'] = (
        df['PU_Zone'].fillna('').str.contains('Airport', case=False)
        | df['DO_Zone'].fillna('').str.contains('Airport', case=False)
    ).astype(int)

    print(f'Registros antes dos filtros: {before:,}')
    print(f'Registros apos filtros: {after:,}')
    print(f'Remocao: {(1 - after / before):.1%}')
    return df


df = prepare_data(df_raw, zones)
df.head()""")

# ── 5. EDA ────────────────────────────────────────────────────────────
md("""## 5. Análise Exploratória (EDA)

Foco: quando as corridas demoram mais, quais segmentos concentram maior
variabilidade e quais variáveis parecem explicar a duração?
""")

code("""summary = df[['duration_min', 'trip_distance', 'passenger_count', 'fare_amount']].describe(
    percentiles=[.01, .05, .5, .95, .99]
).T
display(summary)

fig, axes = plt.subplots(1, 2, figsize=(13, 4))
sns.histplot(df['duration_min'], bins=60, ax=axes[0])
axes[0].set_title('Distribuicao da duracao')
axes[0].set_xlabel('Duracao (min)')

sample_plot = df.sample(min(5_000, len(df)), random_state=RANDOM_STATE)
sns.scatterplot(data=sample_plot, x='trip_distance', y='duration_min', alpha=0.25, ax=axes[1])
axes[1].set_title('Distancia x duracao')
axes[1].set_xlabel('Distancia (milhas)')
axes[1].set_ylabel('Duracao (min)')
plt.tight_layout()
plt.savefig('figures_exercicio_taxi/fig1.png', dpi=100)
plt.show()""")

code("""fig, axes = plt.subplots(1, 2, figsize=(14, 4))

hourly = df.groupby('pickup_hour')['duration_min'].agg(['count', 'mean', 'median']).reset_index()
sns.lineplot(data=hourly, x='pickup_hour', y='median', marker='o', ax=axes[0])
axes[0].set_title('Duracao mediana por hora')
axes[0].set_xlabel('Hora do embarque')
axes[0].set_ylabel('Mediana da duracao (min)')

borough = df.groupby('PU_Borough')['duration_min'].median().sort_values(ascending=False).reset_index()
sns.barplot(data=borough, x='duration_min', y='PU_Borough', ax=axes[1])
axes[1].set_title('Duracao mediana por borough de embarque')
axes[1].set_xlabel('Mediana da duracao (min)')
axes[1].set_ylabel('Borough')
plt.tight_layout()
plt.savefig('figures_exercicio_taxi/fig2.png', dpi=100)
plt.show()""")

# ── 6. Preparação para Modelagem ─────────────────────────────────────────
md("""## 6. Preparação para Modelagem

**Validação temporal:** registros mais antigos para treino, mais recentes para
teste. Mais realista do que um split aleatório quando o produto será usado
sobre dados futuros.
""")

code("""numeric_features = [
    'trip_distance', 'passenger_count', 'pickup_hour', 'pickup_dayofweek',
    'pickup_month', 'is_weekend', 'same_borough', 'airport_trip'
]

categorical_features = [
    'VendorID', 'RatecodeID', 'store_and_fwd_flag',
    'PULocationID', 'DOLocationID', 'PU_Borough', 'DO_Borough'
]

target = 'duration_min'
model_columns = numeric_features + categorical_features

df_model = df.sort_values('pickup_datetime').dropna(subset=[target]).copy()
split_idx = int(len(df_model) * 0.8)

train = df_model.iloc[:split_idx]
test = df_model.iloc[split_idx:]

X_train, y_train = train[model_columns], train[target]
X_test, y_test = test[model_columns], test[target]

print('Treino:', X_train.shape, train['pickup_datetime'].min(), 'a', train['pickup_datetime'].max())
print('Teste:', X_test.shape, test['pickup_datetime'].min(), 'a', test['pickup_datetime'].max())""")

code("""numeric_transformer = Pipeline(steps=[
    ('imputer', SimpleImputer(strategy='median')),
    ('scaler', StandardScaler())
])

categorical_transformer = Pipeline(steps=[
    ('imputer', SimpleImputer(strategy='most_frequent')),
    ('onehot', OneHotEncoder(handle_unknown='ignore', sparse_output=False))
])

preprocessor = ColumnTransformer(transformers=[
    ('num', numeric_transformer, numeric_features),
    ('cat', categorical_transformer, categorical_features)
])""")

# ── 7. Modelagem ─────────────────────────────────────────────────────────
md("""## 7. Modelagem

Comparação entre um baseline ingênuo (mediana) e três modelos, do mais simples
(Ridge, linear) ao mais complexo (HistGradientBoosting). O objetivo não é
apenas ganhar métrica, mas mostrar trade-offs de interpretabilidade, tempo de
treino e risco de overfitting — a mesma lógica do baseline de Cox antes do
DeepSurv no seu TCC.
""")

code("""models = {
    'baseline_mediana': DummyRegressor(strategy='median'),
    'ridge': Ridge(alpha=1.0),
    'random_forest': RandomForestRegressor(
        n_estimators=80, max_depth=18, min_samples_leaf=8,
        random_state=RANDOM_STATE, n_jobs=-1
    ),
    'hist_gradient_boosting': HistGradientBoostingRegressor(
        max_iter=180, learning_rate=0.07, max_leaf_nodes=31,
        l2_regularization=0.05, random_state=RANDOM_STATE
    )
}


def evaluate_predictions(y_true, y_pred):
    ae = np.abs(y_true - y_pred)
    return {
        'MAPE': mean_absolute_percentage_error(y_true, y_pred),
        'RMSE': np.sqrt(mean_squared_error(y_true, y_pred)),
        'R2': r2_score(y_true, y_pred),
        'Erro_p90': np.percentile(ae, 90)
    }


results = []
fitted_models = {}

for name, estimator in models.items():
    pipe = Pipeline(steps=[('preprocess', preprocessor), ('model', estimator)])
    pipe.fit(X_train, y_train)
    preds = pipe.predict(X_test)
    metrics = evaluate_predictions(y_test, preds)
    metrics['modelo'] = name
    results.append(metrics)
    fitted_models[name] = pipe

results_df = pd.DataFrame(results).set_index('modelo').sort_values('MAPE')
display(results_df)""")

# ── 8. Avaliação ─────────────────────────────────────────────────────────
md("""## 8. Avaliação e Interpretação

A avaliação precisa responder se o modelo ajuda a decisão de negócio — não
apenas olhar a média geral, mas os segmentos onde o erro é maior.
""")

code("""best_name = results_df.index[0]
best_model = fitted_models[best_name]
test_eval = test.copy()
test_eval['pred_duration_min'] = best_model.predict(X_test)
test_eval['abs_error'] = (test_eval['duration_min'] - test_eval['pred_duration_min']).abs()

print('Melhor modelo por MAPE:', best_name)
display(test_eval[['duration_min', 'pred_duration_min', 'abs_error']].describe().T)

segment_error = (
    test_eval.groupby('PU_Borough')
    .agg(corridas=('abs_error', 'size'), MAE=('abs_error', 'mean'))
    .query('corridas >= 20')
    .sort_values('MAE', ascending=False)
)
display(segment_error)""")

code("""importance_sample = test_eval.sample(min(1_000, len(test_eval)), random_state=RANDOM_STATE)
perm = permutation_importance(
    best_model, importance_sample[model_columns], importance_sample[target],
    n_repeats=5, random_state=RANDOM_STATE, scoring='neg_mean_absolute_error'
)

importance_df = (
    pd.DataFrame({'feature': model_columns, 'importance_mae': perm.importances_mean})
    .sort_values('importance_mae', ascending=False)
)
display(importance_df)

plt.figure(figsize=(8, 4))
sns.barplot(data=importance_df.head(10), x='importance_mae', y='feature')
plt.title('Permutation importance - impacto no MAE')
plt.tight_layout()
plt.savefig('figures_exercicio_taxi/fig3.png', dpi=100)
plt.show()""")

# ── 9. Gestão do projeto ──────────────────────────────────────────────
md("""## 9. Gestão do Projeto e Riscos

| Risco | Impacto | Mitigação |
|---|---|---|
| Volume de dados alto | Notebook lento ou quebra por memória | Começar com amostra e escalar depois |
| Dados externos indisponíveis | Aula/projeto travado | Baixar amostra local ou ter backup de meses anteriores |
| Vazamento de dados | Resultado artificialmente bom | Separar variáveis disponíveis antes/depois da predição |
| Validação aleatória inadequada | Métrica otimista | Usar split temporal |
| Modelo complexo demais | Difícil explicar no TCC | Comparar com baseline e modelo simples |
| Escopo grande | Atraso no cronograma | Sprint 1 = PoC; Sprint 2 = EDA; Sprint 3 = modelos; Sprint 4 = texto/deployment |

## 10. Conclusão esperada

Ao final da execução, você deve conseguir responder:
- Qual foi o problema de negócio?
- Quais dados foram usados e quais são suas limitações?
- Como o *target* foi construído?
- Quais *features* foram criadas e por quê?
- Qual baseline foi usado?
- Quais modelos foram comparados e qual métrica decidiu o melhor?
- Onde o modelo erra mais?
- Como o modelo seria implantado e monitorado?

**Paralelo com seu TCC:** este mesmo roteiro (Entendimento → Dados → Preparação
→ EDA → Modelagem com baseline → Avaliação por segmento → Deployment) é
exatamente o que você já aplicou com Cox como baseline e DeepSurv como modelo
mais complexo — a diferença é que aqui o alvo é `duration_min` (regressão) e
no seu TCC é tempo até o evento com censura (sobrevivência).
""")

nb['cells'] = cells
with open('/home/juangraciano/Documentos/Cienciadedatos/TCC/notebooks/exercicio_gestao_taxi.ipynb', 'w', encoding='utf-8') as f:
    nbf.write(nb, f)

print("Notebook criado:", len(cells), "células")
