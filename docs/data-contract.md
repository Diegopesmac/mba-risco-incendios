# Contrato proposto de dados e alvo

## População e previsão

Proposta para discussão: região/dia, com previsão de registro de detecção de fogo no dia seguinte. A região poderá ser município ou célula espacial, escolhida por operação e observabilidade antes da análise de desempenho. Não selecionar apenas locais que tiveram incêndio para fabricar negativos fáceis.

Um alvo binário de detecção futura permitiria estimar probabilidade e produzir três faixas operacionais. É necessário confirmar com a tutoria se isso atende ao pedido de baixo/médio/alto ou se exige alvo supervisionado de três classes. Não fixar faixas arbitrárias nem reproduzir `risco_fogo` sem explicitar que seria outro problema.

## Exigências do painel final

- Chave regional/temporal preenchida e única; pelo menos 10 mil exemplos depois da preparação.
- Alvo preenchido, variado e com representatividade das classes; 5% é um limiar inicial de verificação a discutir, não uma garantia de adequação.
- Identificação de `prediction_issued_at`, `features_available_at`, `target_window_end`, fuso e política de cobertura.
- Variável disponível na emissão; não basta deslocar uma reanálise revisada em um dia e chamá-la de operacional.
- Zeros significam ausência de registro no acervo sob política explícita de cobertura; não são prova de ausência física de fogo. Dias sem cobertura conhecida ficam fora da rotulagem ou são marcados como desconhecidos.
- IDs do acervo, potência radiativa da detecção futura e índice que reproduz o alvo não são features.
- Pré-processamento, seleção de variáveis, rebalanceamento e limiares ajustados somente em treino/validação.
- Validação por tempo com separação compatível com horizonte; teste espacial adicional conforme a pergunta de generalização.

## Campos do arquivo INPE auditado

`id_bdq` e `foco_id`: identificadores; `lat`/`lon`: coordenadas; `data_pas`: data/hora da detecção, sem assumir disponibilidade instantânea; `pais`, `estado`, `municipio`, `bioma`: categorias originais. Tipos e unidades finais serão normalizados com documentação da fonte. Identificadores são preservados como texto.

As datas sem qualquer registro nacional encontradas pela auditoria precisam de investigação. Preencher um painel completo de zeros antes disso é proibido pelo contrato científico.
