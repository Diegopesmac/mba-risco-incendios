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

Matriz fictícia de penalidades, definida antes do teste: em 310 decisões, custo simulado total de R$ 5.930 para o modelo, R$ 13.150 para o Dummy e R$ 5.240 para a persistência D−2. O modelo custa R$ 690 a mais que a persistência neste cenário: a vantagem sobre o Dummy não sustenta economia frente ao baseline mais forte. São valores hipotéticos, não economia real ou incêndios evitados. Os doze cenários comparam as três alternativas usando as mesmas penalidades. O [plano A/B](ab-plan.md) descreve experimento futuro em modo sombra, ainda não executado.

A API sinaliza valores fora das faixas de desenvolvimento e municípios novos, sem tornar essas previsões validadas. Atualizações exigem novo protocolo de desenvolvimento e teste independente. Fontes e população devem ser revistas antes de qualquer extensão operacional.

## Revisão do tutor

Na validação comum de 183 exemplos, persistência da última classe do município até D−2 obteve F1 macro 0,5301, superior à logística otimizada (0,4528). Histórico anterior à junção meteorológica, 23.073 município/dias de desenvolvimento; nenhum fallback foi necessário. Disponibilidade dos rótulos em D−2 é assumida. A comparação é sequencial, com observações anteriores liberadas pelo corte temporal.

A logística sem pesos obteve 0,3813 e com pesos balanceados, 0,4429. O balanceamento já existia e melhora essa comparação, mas não resolve a mudança temporal: alto passa de 31,7% no treino para 17,5% na validação. Teste mantém sua distribuição original. O ganho de otimização (~0,010) não demonstrou relevância ou estabilidade. Não há evidência de superioridade do modelo sobre persistência.

O notebook 03 mantém a análise de desenvolvimento. Após a segunda revisão, o notebook 04 avalia também a regra fixa de persistência nos mesmos 310 exemplos do teste: F1 macro 0,4966, contra 0,4097 do modelo. O histórico inclui datas do teste somente quando anteriores ao corte D−2 da previsão; disponibilidade dos rótulos continua assumida. Não há retreinamento, promoção ou nova seleção pelo teste. Modelo, Dummy e suas evidências congeladas são preservados; a comparação adicional está em `persistence-test.json`.

A revisão treina um candidato com intensidade dos pesos escolhida em CV cronológica do treino. Entre potências 0, 0,5, 1 e 1,5, foi selecionada 1: os pesos balanceados existentes já eram a melhor opção dessa comparação. O ajuste foi executado, mas não produziu ganho adicional. Persistência permanece superior; não se afirma que o declínio temporal foi resolvido.
