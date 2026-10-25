# ADR 0001 — base própria e entrega completa

Status: histórico. Escopo ativo definido na ADR 0002.

## Contexto

As bases oferecidas inicialmente têm apenas 43 dias de sobreposição entre meteorologia e detecções, legenda de solo inconsistente e duplicatas meteorológicas. O objetivo é produzir um trabalho reproduzível, apto a futura apresentação pública e com API ao final.

## Decisão

Adotar o Caminho 4, investigar a série oficial de referência do INPE em 2023–2025 e fontes meteorológicas temporalmente compatíveis. Reutilizar os diagnósticos e tratamentos anteriores como baseline, sem confundi-los com a nova base. Manter o repositório privado, avançar em preparação e contratos e obter aprovação acadêmica antes das etapas dependentes.

## Consequências

Há uma Entrega 0 adicional. Alvo, observabilidade e disponibilidade real das features precisam de evidência. O treinamento e a API dependem dessas decisões. A licença do código e a abertura pública serão decisões posteriores; não redistribuir dados brutos sem conferir direitos.
