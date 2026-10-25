# Contrato dos dados e do alvo — curso

## Origem e população

Quatro arquivos fornecidos para o caso do MBA, identificados por `configs/course-data.json`. Manifesto local com SHA-256, tamanho e vínculo ao contrato. Nenhum bruto alterado ou redistribuído.

Uma linha representa município/data UTC **com índice válido em registros de detecção**, meteorologia anterior utilizável e chave preenchida. Sem detecção ou índice válido, não há rótulo; ausência nunca vira baixo risco. Avaliação condicional à amostragem do acervo, sem comprovar desempenho para todos os municípios/dias.

## Alvo de três classes

Índice contínuo: mediana dos valores `risco_fogo` válidos em [0,1] por município/dia. Negativos, vazios e não finitos são ausências. Mediana reduz a influência de valor extremo isolado, mas permanece ponderada pelos registros multissatélite; não representa incêndios independentes.

Classes fixadas antes do treino:

| Classe | Intervalo da mediana |
|---|---|
| baixo | 0 ≤ RF ≤ 0,40 |
| medio | 0,40 < RF ≤ 0,70 |
| alto | 0,70 < RF ≤ 1 |

Adaptação da [tabela 3.5 do método INPE](https://dataserver-coids.inpe.br/queimadas/queimadas/Publicacoes-Impacto/documentos/2019_Setzer_etal_CalculoRiscoFogo_PRP_INPE.pdf): reunir mínimo/baixo e alto/crítico, preservando médio. Definição deste trabalho, não classificação oficial de três níveis. O alvo reproduz o índice registrado, não ocorrência nem probabilidade calibrada. O método original também considera detecções recentes; essa circularidade acompanha as limitações.

## Emissão, horizonte e features

Emissão simulada: 00 UTC de D. Alvo: índice registrado durante D, janela até D+1 às 00 UTC. Meteorologia: dia D−2, com atraso **hipotético** de publicação de 24 horas após seu encerramento. A defasagem impede usar medições do dia do alvo, mas não comprova atraso real histórico. Uso retrospectivo acadêmico; disponibilidade operacional não validada.

Por estação/dia: chuva somente com 24 medições; temperatura, umidade e vento com ao menos 18. Média municipal das estações elegíveis; nenhuma estação escolhida pelo alvo. Município preservado como texto. Variáveis na escala numérica original, sem conversão silenciosa baseada nas unidades inconsistentes do dicionário.

`risco_fogo`, classe, potência radiativa, precipitação/dias sem chuva na detecção futura, contagem futura e IDs não são features. MapBiomas é analisado, mas não interpretado nem usado no modelo enquanto coleção/legenda/unidade não estiverem confirmadas.

## Validação temporal

Datas do alvo pré-definidas: treino até 25/01/2025; validação de 27/01 a 02/02; teste reservado de 04/02 a 12/02. Dias 26/01 e 03/02 são separações. Início depende de meteorologia D−2 válida, sem preencher dias faltantes.

Hiperparâmetros, imputação, escalas, seleção e limiares usam somente treino/validação. Janela curta não avalia sazonalidade anual nem generalização para municípios novos. Auditar dados, exclusões e classes por divisão antes de avaliar viabilidade do treino.
