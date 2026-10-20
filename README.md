# MBA — previsão de risco de incêndios

Projeto acadêmico para investigar previsão regional de detecções de fogo e apresentar risco baixo/médio/alto. Caminho 4: base própria validada pela tutoria, análise, modelos, IA responsável e API.

**Estado:** estrutura e auditorias implementadas; Entrega 0 em preparação. Ainda não há base externa aprovada, modelo treinado ou API publicada. O repositório permanece privado; tornar público é uma decisão futura separada.

## Identidade e fronteiras

Este projeto é uma solução acadêmica de ciência de dados para apoio à priorização preventiva. Não é um sistema oficial de alerta, serviço de emergência ou medida de incêndios reais únicos. A primeira candidata vem de arquivos anuais oficiais de detecções do INPE; fontes meteorológicas ainda estão em avaliação. Integrações externas limitam-se às fontes documentadas e ao futuro serviço de inferência. Conteúdos de outras atividades não fazem parte do projeto.

## Comece aqui

- [Protocolo de entregas e Git](docs/delivery-protocol.md)
- [Rubrica e critérios de aceite](docs/rubric.md)
- [Arquitetura](docs/architecture.md)
- [Fontes, licenças e disponibilidade](docs/data-sources.md)
- [Proposta para a Entrega 0](reports/entrega-0/proposta.md)
- [Contrato dos dados e do alvo](docs/data-contract.md)

## Execução

Python 3.12. A partir da raiz:

```sh
python -m pip install -r requirements.txt
python -m pip install -e . --no-deps
python scripts/prepare_candidate.py --years 2023 2024 2025
python scripts/build_entrega0.py
python -m unittest discover -s tests -v
python -m unittest test_preparacao_queimadas -v
python scripts/check_publication.py
```

Os dados reais ficam em `.local/`, fora do Git. O download candidato tem cerca de 24 MB compactados. O notebook executado da Entrega 0 fica em `.local/deliveries/`; o modelo de notebook versionado fica em `notebooks/`. Não é necessário autenticar no INPE para os arquivos anuais selecionados.

As quatro rotinas na raiz e `notebooks/course/` preservam o trabalho anterior com os arquivos oferecidos pelo curso. Para reproduzir essa análise, disponibilizar os quatro CSVs em `dados_brutos_queimadas/`; esses CSVs e os resultados não são incluídos no Git. Os notebooks versionados estão sem saídas; as execuções locais existentes continuam preservadas no material acadêmico original.

## Controles de avanço

A validação do código não aprova a base acadêmica. `python scripts/check_delivery.py` retorna bloqueio enquanto faltar o registro real de aprovação da Entrega 0, vinculado ao hash do manifesto. Esse registro não autentica a identidade da tutoria e deve ser acompanhado da evidência humana. Não criar aprovações fictícias para liberar desenvolvimento científico.

## Licenciamento e portfólio

Nenhum dado bruto é redistribuído. As fontes e suas condições estão em `docs/data-sources.md`. A licença de distribuição do código será escolhida antes da abertura pública. O futuro portfólio deverá mostrar resultados reproduzíveis, limitações, documentação e evidências revisadas, sem prometer uso operacional que não tenha sido validado.
