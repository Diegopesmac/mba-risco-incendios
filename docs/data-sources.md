# Fontes candidatas, atribuição e disponibilidade

Pesquisa em 20/10/2026. As fontes abaixo foram consultadas diretamente; escolha acadêmica ainda pendente.

## INPE — arquivos anuais do satélite de referência

[Índice oficial](https://dataserver-coids.inpe.br/queimadas/queimadas/focos/csv/anual/Brasil_sat_ref/) com arquivos de 2023, 2024 e 2025 baixados e auditados. [FAQ do programa](https://www.terrabrasilis.dpi.inpe.br/queimadas/portal/pages/secao_informacoes/faq/index.html) explica o objetivo da série, limites da detecção, nuvens e diferença entre foco e incêndio. Partes do FAQ têm referências antigas; não presumir sensor atual somente pelo texto histórico.

A auditoria cobre arquivo, esquema, período e identificadores. A disponibilidade gratuita não é uma licença específica de redistribuição. Atribuir INPE/Programa Queimadas, guardar data/hash de aquisição e verificar termos para qualquer redistribuição. Os ZIPs não são incluídos no repositório.

## Meteorologia — alternativas em avaliação

- [INMET: dados históricos](https://portal.inmet.gov.br/dadoshistoricos): candidato para observações de estações; verificar documentação, cobertura, qualidade e atraso real de disponibilização antes de usar como feature.
- [Open-Meteo: histórico](https://open-meteo.com/en/docs/historical-weather-api): reanálise é candidata para exploração retrospectiva; não presumir que o valor revisado estivesse disponível na data da previsão.
- [Open-Meteo: previsões anteriores](https://open-meteo.com/en/docs/previous-runs-api): permite investigar valores previstos com antecedência. Cobertura, modelo e horário de emissão/publicação devem ser fixados antes do backtest.

[Termos Open-Meteo](https://open-meteo.com/en/terms): a API gratuita é limitada a uso não comercial e tem limites de chamadas; dados exigem atribuição CC BY 4.0. Uso acadêmico e eventual portfólio não devem ser confundidos com produto comercial. Não há assinatura ou custo contratado neste projeto.

## Cobertura do solo

[MapBiomas Brasil](https://brasil.mapbiomas.org/) tem diferentes coleções e resoluções. Não usar a legenda de uma coleção para outra. A exportação anterior do curso tem 28 códigos e documentação incompatível; não foi corrigida por adivinhação. Registrar coleção, versão, legenda, unidade de área e data de publicação antes de integrar. Uma revisão publicada no futuro pode ser adequada para análise retrospectiva, mas não para simular informação conhecida no passado.
