Olá, Isadora, tudo bem?

Segue em anexo o adiantamento do meu TCC, "Modelagem de Risco de Crédito Dinâmico para Microempreendedores". Muito obrigado pelas recomendações na avaliação de Metodologia e Projeto II. Abaixo explico como cada uma foi atendida nesta versão.

1. Resumo e pipeline de extração: o resumo foi reescrito em linguagem simples, e o Capítulo 4 foi reduzido de 10 para 5 páginas, sem código. A Tabela 1 explica de forma didática as dificuldades da extração e como foram resolvidas, e o termo Data Stitching é definido antes de ser usado (Seção 4.2). O detalhe técnico foi para o Apêndice A.

2. Granularidade diária: a Seção 5.3 justifica o uso dos pagamentos diários e mostra a vantagem com dados: blocos semanais dão o alerta mais cedo do que blocos de 10 dias (73% contra 61% dos defaults capturados no 14º dia).

3. Referências recentes e contexto socioeconômico: o Capítulo 2 foi reescrito com fontes de 2025 e 2026 (Mapa de Empresas, Sebrae e Banco Central). A comparação entre classes sociais será feita cruzando a localização dos clientes com a renda do setor censitário do IBGE, anunciada na Seção 6.2 e prevista para o próximo Sprint.

4. Travessões: foram retirados de todo o texto, junto com setas e outros símbolos desnecessários.

5. Artigos contemporâneos e métricas: o Capítulo 2 inclui trabalhos recentes de análise de sobrevivência em crédito (Dirick et al., 2017; Frydman e Matuszyk, 2022; Blumenstock et al., 2022), métricas que consideram a censura (Uno et al., 2011) e a mudança regulatória da Resolução CMN nº 4.966, que passou a exigir a estimação da perda esperada.

6. Significado prático das covariáveis que mudam no tempo: a Seção 5.3 explica, com um exemplo semana a semana (Tabela 5), que o risco de cada cliente é atualizado toda semana, o que permite uma lista semanal de clientes para acompanhar.

7. Dados ausentes e inconsistentes: a Seção 4.3 traz uma auditoria completa dos dados (Tabela 2), com cada problema encontrado, como foi identificado e o tratamento aplicado.

8. Itálico: todos os termos em língua estrangeira foram padronizados em itálico.

9. Transição da análise exploratória para a modelagem: a Seção 6.6 liga cada resultado da análise exploratória a uma decisão de modelagem, incluindo a motivação para os modelos de aprendizado de máquina e Deep Learning.

Além disso, o trabalho já traz os primeiros resultados (Capítulo 7): com a informação disponível no 21º dia do crédito, o modelo de Fine e Gray coloca 81% dos futuros defaults entre os 10% de clientes de maior risco, cerca de quatro meses antes de a perda se confirmar.

Fico à disposição para qualquer comentário.

Atenciosamente,
Juan Fernando Graciano Pinzón
