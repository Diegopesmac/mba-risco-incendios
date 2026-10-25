# MBA — risco de incêndios

**Caminho 2:** dados fornecidos pelo curso, diagnóstico e preparação, comparação de modelos, avaliação responsável e API com Docker/deploy.

O caso acadêmico busca estimar baixo/médio/alto para uma região e dia. O contrato utiliza as classes do índice `risco_fogo` registrado no arquivo do curso. A população observada é condicionada às detecções; não se estima probabilidade física de incêndio em qualquer município/dia.

## Dados e preparação

Python 3.12. Quatro CSVs fornecidos para o caso: `BDMEP-estacao.csv`, `BDMEP-2025.csv`, `MapBiomas.csv` e `queimadas_2024_2025.csv`. Originais somente leitura, sem redistribuição. `configs/course-data.json` fixa os hashes da versão utilizada.

```sh
python -m pip install -r requirements.txt
python -m pip install -e . --no-deps
python scripts/prepare_course.py --raw-dir <pasta-dos-quatro-csvs>
python scripts/check_delivery.py --raw-dir <pasta-dos-quatro-csvs>
python scripts/build_course_panel.py --raw-dir <pasta-dos-quatro-csvs>
python scripts/benchmark_course.py
python scripts/build_course_notebook.py
python -m unittest discover -s tests -v
python -m unittest test_preparacao_queimadas -v
python scripts/check_publication.py
```

Manifesto, bancos e derivados ficam em `.local/course/`. A preparação confirma duplicatas por igualdade exata, reserva horários divergentes, preserva ausências e distingue precipitação parcial de 24 horas completas. As rotinas e os notebooks em `notebooks/course/` contêm auditoria e EDA dos quatro arquivos.

## Documentação

- [Arquitetura](docs/architecture.md)
- [Contrato dos dados e do alvo](docs/data-contract.md)
- [Fontes](docs/data-sources.md)
- [Entregas](docs/delivery-protocol.md)
- [Rubrica](docs/rubric.md)
- [Escopo técnico](docs/decisions/0002-base-curso.md)
- [Modelagem e reprodução](docs/modeling.md)

## Estado e limites

Preparação, painel supervisionado e comparação inicial de referência mais três modelos implementados. Otimização e avaliação final pendentes; API e deploy planejados. Entrega 0 não aplicável aos dados do curso; submissão e aprovação das entregas 1 e 2 são registradas somente quando ocorrerem.

Meteorologia e queimadas têm apenas 43 dias de sobreposição. O significado das 28 classes MapBiomas não é inferido da legenda incompatível do material. Variáveis obtidas na detecção futura ou no fim do dia previsto não entram como features. O trabalho não é um serviço oficial de alerta.

Repositório privado. Abertura pública, licença, redistribuição de dados e publicação de serviço exigem revisão própria.
