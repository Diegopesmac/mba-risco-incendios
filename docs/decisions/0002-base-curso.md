# ADR 0002 — escopo e contrato dos dados do curso

Status: aceito. Escopo ativo: Caminho 2.

## Definição

Entradas: quatro CSVs fornecidos para o caso do MBA, fixados por hash. Resultado acadêmico: preparação, EDA, comparação de modelos, avaliação responsável e API com Docker/deploy. Entrega 0 não aplicável; entregas 1 e 2 sujeitas à avaliação do curso.

## Contrato científico

Três classes da mediana diária municipal de `risco_fogo`, com cortes fixos 0,40 e 0,70 em `docs/data-contract.md`. Meteorologia defasada dois dias; separação temporal pré-definida, teste reservado. População condicionada aos registros de detecção. Não imputar rótulos a municípios/dias sem observação.

## Limites de uso

Estima o índice na população observada; não mede incêndios independentes nem probabilidade física de ocorrência. Janela curta, amostragem multissatélite, atraso hipotético de publicação e legenda MapBiomas pendente acompanham os resultados. Uso operacional depende de validação adicional de cobertura e disponibilidade das entradas.
