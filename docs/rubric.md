# Rubrica e aceite — Caminho 2

| Unidade | Evidência exigida | Estado |
|---|---|---|
| Fonte | Quatro arquivos do curso, versão e hashes | Contrato definido |
| E1: negócio | Problema, público, alvo, horizonte e KPIs | Contrato do índice definido |
| E1: preparação | Ausências, duplicatas, chaves, exclusões e dicionário | Painel completo em submission/painel_modelagem.csv e dicionário de todas as colunas em docs/data-dictionary.md |
| E1: EDA | Distribuições, correlações com alvo, extremos, ausências, gráficos e hipótese | Notebook 02 executado; Pearson/Spearman e hipótese exclusivamente no treino |
| E1: GitHub | README, notebooks, código, dependências e instruções dos dados | Quatro notebooks com saídas e apresentação portátil, sem diretórios históricos |
| E2: modelos | Três modelos mais referência, validação temporal comum | Comparação e teste temporal executados após congelamento |
| E2: valor | Custos simulados, premissas, sensibilidade e plano A/B | Matriz fictícia, 12 cenários e plano prospectivo documentados |
| E2: otimização | Optuna sem consultar teste final | 20 tentativas por família, três folds internos cronológicos |
| E2: responsabilidade | Explicabilidade, três variáveis, vieses e limites | Permutação na validação, grupos com suporte e model card |
| Etapa 4 | FastAPI, request, Docker, dependências e API ativa | API local, container no CI e API pública no Render verificados; saúde/previsão 200, inválida 422 |
| Revisões | Feedback real e notebooks executados | Não submetido |

Entrega 0 não aplicável aos dados do curso. Testes não significam aprovação acadêmica nem serviço publicado.
