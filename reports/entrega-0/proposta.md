# Entrega 0 — proposta para validação

**Status: em preparação; não aprovada pela tutoria.**

## Problema e público

Investigar previsão regional de detecções de fogo para apoiar priorização preventiva por gestores e equipes ambientais. A saída pretendida é baixo/médio/alto, com definição do alvo e interpretação operacional ainda a validar.

## Base própria candidata

Aquisição direta dos arquivos oficiais anuais do satélite de referência do INPE. Arquivos originais ficam locais e são rastreados por SHA-256.

| Ano/arquivo | Linhas | Primeiro dia | Último dia | Dias com registro |
|---|---:|---|---|---:|
| focos_br_ref_2023.zip | 189,901 | 2023-01-01 | 2023-12-31 | 365 |
| focos_br_ref_2024.zip | 278,299 | 2024-01-01 | 2024-12-31 | 365 |
| focos_br_ref_2025.zip | 136,393 | 2025-01-01 | 2025-12-31 | 360 |

Total bruto: **604,593 detecções**. Isso não comprova o volume de exemplos supervisionados após integração e rotulagem.

## Qualidade observada

- focos_br_ref_2023.zip: IDs repetidos = 0; campos vazios = 0; datas sem registro nacional entre extremos = nenhuma.
- focos_br_ref_2024.zip: IDs repetidos = 0; campos vazios = 0; datas sem registro nacional entre extremos = 2024-02-02.
- focos_br_ref_2025.zip: IDs repetidos = 0; campos vazios = 0; datas sem registro nacional entre extremos = 2025-02-09, 2025-04-16, 2025-05-26, 2025-05-27, 2025-12-24.

Datas sem registro podem representar problemas de cobertura ou ausência de detecção; não foram convertidas em zero. Não foi comprovada cobertura observacional completa de cada região/dia.

## Proposta de alvo e KPIs

Proposta a discutir: probabilidade de registro de detecção no dia seguinte e três faixas operacionais. Confirmar se o curso exige três classes supervisionadas. Não escolher cortes com base no teste nem criar rótulos para satisfazer balanceamento.

KPIs candidatos: recall da classe/faixa crítica, F1 macro quando aplicável, precisão e volume de alertas dentro da capacidade de resposta. Comparar com referência simples. Valor financeiro será simulado com custos explícitos, não medido como economia real.

## Checklist da validação

- [x] Origem e formato estruturado identificados; hashes registrados.
- [x] Volume bruto acima de 10 mil registros e perfil estrutural executado.
- [x] Mini-notebook com info, describe e qualidade, executado localmente.
- [ ] Painel final pós-limpeza acima de 10 mil exemplos.
- [ ] Alvo preenchido, definição das três classes/faixas e representatividade.
- [ ] Fonte meteorológica, disponibilidade temporal e dicionário final.
- [ ] Política de cobertura e tratamento das datas sem registro.
- [ ] Tutoria 1:1 realizada e aprovação registrada.

## Perguntas para a tutoria

1. É aceitável prever detecção futura e converter probabilidade em três faixas, ou são exigidas três classes supervisionadas?
2. Qual evidência de cobertura é suficiente para os exemplos sem detecção? Pode-se usar alvo de ausência de registro, explicitamente distinto de ausência física de fogo?
3. Qual recorte regional/temporal torna a operação e a validação defensáveis?
4. Uma previsão meteorológica histórica emitida com antecedência é preferível à reanálise para a simulação operacional?

## Reprodutibilidade

SHA-256 do manifesto local auditado: `48cd4d7fcd893097212fe32403de21c3026ecd39b65c85f822435cef3a1be4ad`. Aprovação futura deve citar a versão efetivamente discutida.

Rotinas: `scripts/prepare_candidate.py` e `scripts/build_entrega0.py`. Notebook executado em `.local/deliveries/00_validacao_base_externa.ipynb`; template sem saídas em `notebooks/00_validacao_base_externa.ipynb`. Sem treinamento ou métricas preditivas nesta entrega.
