# Modelo final — classes do índice de risco

## Uso e população

Regressão logística acadêmica para classificar a mediana municipal diária de `risco_fogo` dos registros de detecção. Classes: baixo até 0,40; médio até 0,70; alto acima de 0,70. População condicionada às detecções e à cobertura meteorológica elegível. Dias sem detecção não recebem rótulo baixo. Não estima ocorrência física de fogo na população geral e não deve orientar alertas ou decisões de emergência.

## Dados, tempo e escolha

Quatro CSVs do curso analisados e fixados por hash. O modelo usa chuva, temperatura, umidade e vento meteorológicos em D−2. O atraso de publicação de 24 horas após o encerramento do dia é assumido; disponibilidade histórica não foi comprovada. MapBiomas permanece fora do modelo por incompatibilidade de legenda e período.

Painel com 1.329 exemplos elegíveis: 764 de treino, 183 de validação, 310 de teste e 72 excluídos nos intervalos de separação. Apenas 43 dias de sobreposição bruta. Três famílias e referência foram comparadas; 20 tentativas Optuna por família usaram três folds cronológicos internos ao treino. Seleção pela validação, com F1 macro e desempate por recall alto/nome. Logística otimizada selecionada com F1 macro de validação 0,4528. Modelo final reajustado nos 947 exemplos de desenvolvimento antes da abertura do teste.

Identificador do modelo: `852606b93da31ade`. SHA-256: `852606b93da31adee314de524621736baa049fdf859fa0a8dd2740bfb24cc9d5`. O registro de congelamento vincula escolhas, código científico, contratos, painel e artefatos. Não houve nova escolha de parâmetros a partir do teste.

## Teste temporal final

| Métrica | Logística otimizada | Referência majoritária |
|---|---:|---:|
| F1 macro | 0,4097 | 0,2775 |
| Recall alto | 0,5690 | 0,0000 |
| Acurácia | 0,5355 | 0,7129 |

A referência acerta mais exemplos totais ao prever baixo, mas não identifica nenhum alto. O modelo identifica 33 de 58 altos, subestima 25 e apresenta precisão alta de 0,3548. A classe intermediária tem F1 de apenas 0,1020. O desempenho impede declarar adequação operacional.

Reamostragem por dia do teste, com mil réplicas: intervalo descritivo de 95% do F1 macro entre 0,3659 e 0,4497. Há apenas nove dias de teste e dependência espacial/temporal; esse intervalo não garante generalização futura.

## Interpretação e responsabilidade

Permutação na validação destaca vento, umidade e chuva. Importância global não demonstra causa. O teste exploratório pareado por município, restrito ao treino, encontrou diferença mediana de umidade de −6,0833 entre dias altos e demais, p=0,00836, em 15 municípios elegíveis. A relação do índice com meteorologia, a seleção e a dependência limitam a interpretação.

Resultados por prefixo de UF, semana e cobertura de estações acompanham contagens; grupos com menos de 30 exemplos ou menos de dez altos são marcados esparsos. Isso não comprova equidade nem ausência de viés. Cobertura escassa, sazonalidade não observada, amostragem multissatélite e mudança de distribuição restringem o uso.

## Valor e acompanhamento

Matriz fictícia de penalidades, definida antes do teste: custo simulado total de R$ 5.930 contra R$ 13.150 da referência em 310 decisões sobre o índice. São valores hipotéticos, não economia real ou incêndios evitados. Doze cenários variam penalidades de subestimação e excesso de alerta. O [plano A/B](ab-plan.md) descreve experimento futuro em modo sombra, ainda não executado.

A API sinaliza valores fora das faixas de desenvolvimento e municípios novos, sem tornar essas previsões validadas. Atualizações exigem novo protocolo de desenvolvimento e teste independente. Fontes e população devem ser revistas antes de qualquer extensão operacional.
