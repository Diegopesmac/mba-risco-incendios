# Arquitetura

## Fluxo científico

Fonte externa → aquisição com origem/hash → perfil e contrato → validação da base pela tutoria → painel temporal observável → separação temporal → pré-processamento aprendido no treino → comparação/otimização → teste reservado → explicabilidade/viés → artefato versionado → FastAPI → Docker → deploy.

## Responsabilidades

- `src/fire_risk/sources.py`: somente aquisição pública e perfil da candidata INPE. Não define alvo nem treina.
- `src/fire_risk/validation.py`: chaves, alvo, classes, disponibilidade temporal e vínculo de aprovação ao manifesto.
- `scripts/`: pontos de entrada de aquisição, preparação da Entrega 0 e verificação do recorte publicável.
- `notebooks/`: narrativa analítica reproduzível; não deve ser o único lugar de regras críticas de tratamento.
- Rotinas e `notebooks/course/`: baseline anterior, preservado para comparação e reaproveitamento, sem misturar sua aprovação com a da nova base.
- `.local/`: dados, aprovações, execuções e trabalho local. Nenhum módulo depende de arquivos de outras atividades.
- Futuras camadas `features`, `training`, `evaluation` e `api` serão implementadas em unidades posteriores. A API consumirá artefato validado e contrato de features, sem refazer treino por requisição.

## Dependências

Bibliotecas já usadas na análise anterior: pandas, NumPy, DuckDB, Matplotlib, SciPy e nbformat. Python padrão faz aquisição, hashes e leitura de ZIP. Isso evita dependência nova de autenticação ou de serviços de nuvem na Entrega 0.

Optuna, biblioteca de modelos, explicabilidade, FastAPI e infraestrutura de deploy entram quando sua unidade for implementada e validada. Nenhum endpoint falso ou modelo demonstrativo será apresentado como resultado real.

## Reprodutibilidade

Manifestos registram arquivos, hashes, período, colunas e limitações. Esquemas ou arquivos alterados exigem nova auditoria; aprovação vinculada a um manifesto antigo não libera outro. Pré-processamento, limiares e seleção de modelo só usam desenvolvimento/validação. O teste fica reservado até o congelamento das decisões.
