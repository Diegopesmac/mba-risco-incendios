# MBA — risco de incêndios

**Caminho 2:** dados fornecidos pelo curso, diagnóstico e preparação, comparação de modelos, avaliação responsável e API com Docker/deploy.

O caso acadêmico busca estimar baixo/médio/alto para uma região e dia. O contrato utiliza as classes do índice `risco_fogo` registrado no arquivo do curso. A população observada é condicionada às detecções; não se estima probabilidade física de incêndio em qualquer município/dia.

API pública para avaliação: [documentação interativa](https://mba-risco-incendios.onrender.com/docs), [saúde do modelo](https://mba-risco-incendios.onrender.com/health). Serviço gratuito no Render: a primeira resposta após inatividade pode demorar 50 segundos ou mais.

## Entrega para avaliação

Os quatro notebooks abaixo estão executados, com tabelas e gráficos no próprio GitHub:

1. [Auditoria, limpeza e consolidação](notebooks/course/01_auditoria_queimadas.ipynb).
2. [EDA, distribuição do alvo, correlações e hipótese](notebooks/course/02_eda_preparacao_queimadas.ipynb).
3. [Comparação e otimização dos modelos](notebooks/course/03_painel_modelos_curso.ipynb).
4. [Avaliação final, responsabilidade e API](notebooks/04_projeto_final_curso.ipynb).

A [base consolidada de 1.329 linhas](submission/painel_modelagem.csv) e o [dicionário das 17 colunas](docs/data-dictionary.md) acompanham a entrega. `submission/manifest.json` vincula a base e as evidências por hash. Os CSVs originais e os modelos binários não são redistribuídos. Esta cópia do painel destina-se à avaliação no repositório privado.

Para executar a apresentação, instale as dependências abaixo e abra os notebooks em qualquer pasta dentro do clone ou ZIP extraído. Eles usam somente o painel e as evidências incluídas, sem as pastas da máquina original, dados brutos ou treinamento. Leem resultados científicos já congelados. A correlação complementar usa somente o treino e não modifica o modelo escolhido.

```sh
python -m pip install -r requirements.txt
python -m pip install -e . --no-deps
python -c "from pathlib import Path; from fire_risk.submission import verify_submission; print(verify_submission(Path.cwd())[1]['rows'])"
```

## Reconstrução desde os CSVs originais

Python 3.12. Quatro CSVs fornecidos para o caso: `BDMEP-estacao.csv`, `BDMEP-2025.csv`, `MapBiomas.csv` e `queimadas_2024_2025.csv`. Originais somente leitura, sem redistribuição. `configs/course-data.json` fixa os hashes da versão utilizada.

```sh
python -m pip install -r requirements.txt
python -m pip install -e . --no-deps
python scripts/prepare_course.py --raw-dir <pasta-dos-quatro-csvs>
python scripts/check_delivery.py --raw-dir <pasta-dos-quatro-csvs>
python scripts/build_course_panel.py --raw-dir <pasta-dos-quatro-csvs>
python scripts/benchmark_course.py
python scripts/optimize_course.py
python scripts/finalize_course.py
python scripts/build_submission.py
python -m unittest discover -s tests -v
python -m unittest test_preparacao_queimadas -v
python scripts/check_publication.py
```

Manifesto, bancos e derivados ficam em `.local/course/`. A preparação confirma duplicatas por igualdade exata, reserva horários divergentes, preserva ausências e distingue precipitação parcial de 24 horas completas. As rotinas e os notebooks em `notebooks/course/` contêm auditoria e EDA dos quatro arquivos.

A reconstrução completa é destinada a um ambiente novo com os quatro CSVs. No checkout da avaliação já congelada, apenas `build_submission.py` reapresenta resultados existentes; não apague o congelamento nem execute nova otimização. Para compor o ZIP da revisão Git já conferida, use `python scripts/package_submission.py`.

## Documentação

- [Arquitetura](docs/architecture.md)
- [Contrato dos dados e do alvo](docs/data-contract.md)
- [Dicionário completo da base de ML](docs/data-dictionary.md)
- [Fontes](docs/data-sources.md)
- [Entregas](docs/delivery-protocol.md)
- [Rubrica](docs/rubric.md)
- [Escopo técnico](docs/decisions/0002-base-curso.md)
- [Modelagem e reprodução](docs/modeling.md)
- [Modelo final e limitações](docs/model-card.md)
- [API e publicação](docs/deployment.md)
- [Plano A/B](docs/ab-plan.md)

## Estado e limites

Preparação, comparação de três famílias, otimização temporal, avaliação final congelada, explicabilidade, análise por grupos e custos simulados executados. O modelo final obteve F1 macro 0,4097 e recall alto 0,5690 no teste temporal de 310 exemplos. API publicada no Render e verificada por HTTP em 25/10/2026: saúde 200, previsão 200 e entrada inválida 422, com o modelo final `852606b93da31ade`. Entrega 0 não aplicável aos dados do curso; entregas 1 e 2 ainda não submetidas.

Os comandos de otimização devem ser executados antes de congelar a avaliação. Depois de existir `final/freeze.json`, nova otimização é bloqueada; a avaliação final reutiliza seu resultado registrado. Não apagar os registros para ajustar escolhas depois de observar o teste.

Meteorologia e queimadas têm apenas 43 dias de sobreposição. O significado das 28 classes MapBiomas não é inferido da legenda incompatível do material. Variáveis obtidas na detecção futura ou no fim do dia previsto não entram como features. O trabalho não é um serviço oficial de alerta.

Repositório privado. O painel derivado e os notebooks executados integram a entrega acadêmica. Abertura pública, licença, redistribuição dos originais e alteração do serviço exigem revisão própria.
