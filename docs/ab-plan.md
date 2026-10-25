# Plano de teste A/B — avaliação futura

Status: planejamento acadêmico; experimento não executado. O classificador do índice não está validado como sistema operacional de incêndios.

## Pergunta e desenho

Comparar a priorização de revisão humana apoiada pelo modelo com a priorização habitual, inicialmente em modo sombra. Não suprimir alertas oficiais nem distribuir recursos de emergência com base neste protótipo. A unidade de sorteio deve ser um bloco geográfico de municípios atendido pela mesma equipe, evitando misturar tratamento e controle na mesma rotina. Formar pares de blocos com cobertura e composição regional semelhantes e sortear 1:1 dentro dos pares.

Registrar a semente, os blocos e o plano antes de iniciar. Municípios vizinhos com compartilhamento de equipe entram no mesmo bloco; sem malha/rotas operacionais, essa composição não pode ser determinada pelos arquivos atuais. Registrar trocas de equipe e contaminação; analisar por intenção de tratar e apresentar a análise por protocolo apenas como complemento.

## Métricas

- Primária: proporção de prioridades incorretas segundo avaliação independente da equipe, com critérios estabelecidos antes do piloto. As classes do próprio modelo não são verdade de campo.
- Secundárias: tempo até revisão, volume de prioridades por equipe, carga de trabalho e concordância entre avaliadores.
- Proteção: casos críticos perdidos, atraso operacional e falta de cobertura. Violação de segurança ou ausência de avaliação independente interrompe o piloto para revisão humana.
- Custos: medir custos reais somente no piloto; a matriz financeira deste trabalho é inteiramente fictícia.

## Tamanho e duração ilustrativos

Exemplo de planejamento, sem alegar taxas observadas: erro de referência 10%, alternativa 8%, significância bilateral 5% e poder 80%. Calcular amostra de duas proporções e aplicar efeito de desenho `1 + (m-1) × ICC`. Usando `m=20`, `ICC=0,02` e perda de 10%, a correção é `1,38 / 0,90`. O notebook final calcula os números e arredonda para blocos inteiros.

Esses parâmetros precisam de um piloto real. A base atual, curta e selecionada por detecções, não comprova disponibilidade da amostra necessária. Planejar pelo menos quatro semanas e avaliar cenários de 50, 100 e 200 decisões por braço/dia; encerrar somente quando atingir a amostra pré-definida e a duração mínima. Se isso exceder 12 semanas, revisar o desenho antes da coleta, em vez de parar por significância intermediária.

Não realizar consultas repetidas de significância sem método sequencial pré-especificado. A análise principal deve considerar o sorteio por blocos, dependência temporal, intervalos de confiança e perdas. Registrar exclusões e resultados negativos. Alterações de métrica, tamanho ou critério de encerramento exigem um novo protocolo identificado.
