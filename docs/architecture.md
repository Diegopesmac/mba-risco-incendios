# Arquitetura

## Identidade

Solução acadêmica com as quatro bases do curso para classificar o índice de risco em baixo/médio/alto por município/dia, avaliar modelos e servir inferência por API. Não é serviço oficial de alerta nem estima ocorrência física fora da população observada.

## Fluxo ativo

CSVs do curso → contrato/hash → preparação exploratória → painel rotulado e contrato temporal → separação temporal → pré-processamento aprendido no treino → comparação/otimização → teste reservado → explicabilidade/viés → artefato validado → FastAPI → Docker → deploy.

## Responsabilidades

- `src/fire_risk/course.py`: integridade dos quatro arquivos fornecidos.
- `src/fire_risk/panel.py`: alvo, junção conservadora, defasagem e divisões temporais fixas.
- `src/fire_risk/training.py`: referência e três modelos com validação temporal; não acessa teste final nem fontes brutas.
- `preparar_eda_queimadas.py`: deduplicação exata, reserva de versões ambíguas e agregação descritiva. Recebe diretórios de entrada/saída; não modifica CSVs.
- `src/fire_risk/validation.py`: chaves, alvo e disponibilidade temporal; validação de base externa independente do fluxo do curso.
- `scripts/prepare_course.py`: adaptador de preparação, manifesto e derivados em `.local/course/`.
- `scripts/build_course_panel.py`, `benchmark_course.py` e `build_course_notebook.py`: evidência de painel, comparação e narrativa executada local, sem publicação automática.
- `scripts/check_delivery.py`: seleção explícita de contrato por caminho/fonte; não declara aprovação de entrega.
- `notebooks/course/`: auditoria e narrativa exploratória; regras críticas ficam em código reutilizável.
- `.local/`: dados, resultados, bancos, modelos e execuções não versionados.
- `sources.py`, `coverage.py` e rotinas de base externa: ferramentas independentes, fora do fluxo ativo do curso.

Features, treinamento, avaliação e API recebem contratos explícitos. A API carrega artefato validado e não executa treino por requisição.

## Dependências e reprodução

Python 3.12; pandas, NumPy, DuckDB, Matplotlib, SciPy e nbformat na preparação. Bibliotecas de modelos, otimização, explicabilidade e API entram junto da respectiva implementação. Teste temporal reservado; nenhuma estatística aprendida usa o teste final.
