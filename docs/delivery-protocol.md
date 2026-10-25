# Protocolo de entregas, revisão e Git

## Estados e responsabilidades

Cada entrega passa por: planejada → em preparação → verificada localmente → em revisão no GitHub → submetida ao curso → aprovada ou devolvida. Commit, push e CI verde não significam submissão ou aprovação acadêmica. Registrar submissão, feedback e aprovação apenas quando tiverem ocorrido.

O estudante justifica decisões e entrega evidências; a tutoria aprova a base externa; a revisão do curso aprova as entregas. O mantenedor revisa e faz o merge. Aprovação, feedback, métricas e evidências devem corresponder a registros reais.

## Ciclo de uma unidade

1. Escolher um item pequeno da rubrica, resultado observável e verificações necessárias.
2. Criar branch de trabalho a partir da baseline adequada, preservando trabalho alheio.
3. Reutilizar o que já existe, implementar o item e atualizar sua documentação técnica.
4. Rodar testes proporcionais; separar testes com dados fictícios, uso de dados reais, execução de notebook e validação de deploy.
5. Revisar o diff e o recorte: sem dados brutos, credenciais, dependências instaladas, bancos locais ou arquivos de outras atividades.
6. Adicionar arquivos seletivamente ao índice; executar `python scripts/check_publication.py --staged`.
7. Fazer commit descritivo, com referência ao item. Publicar apenas no repositório privado confirmado.
8. Abrir Draft PR com problema, resultado, evidências, limitações, risco e reversão. Acompanhar CI e corrigir falhas na mesma branch.
9. Depois da revisão do mantenedor e merge, preparar o pacote acadêmico correspondente. Tags/releases e mudança de visibilidade exigem decisão específica do responsável.
10. Submeter pela plataforma quando autorizado. Incluir os relatórios reais dos revisores na entrega seguinte, com a publicação de seu conteúdo revisada.

## Dados do curso — Caminho 2

O fluxo ativo utiliza `configs/course-data.json` e os quatro arquivos fornecidos pelo curso. `prepare_course.py` gera manifesto e derivados; `check_delivery.py --raw-dir <pasta>` verifica hashes e vínculo ao contrato. Entrega 0 não aplicável. Conferir entradas não representa aprovação das entregas 1 ou 2.

## Entrega 0 — aplicável somente à base externa

Evidências: origem, atribuição/licença, problema e público, dicionário, volume pós-tratamento, alvo e classes, ausências/duplicatas, cobertura, variáveis disponíveis na previsão, KPIs propostos e mini-notebook executado.

O pacote inicial deve diferenciar dados brutos de painel supervisionado: 600 mil detecções não significam 600 mil exemplos válidos para prever risco. A regra de alvo deve ser explícita, preenchida e defensável; não escolher faixas só para balancear classes. Dias sem detecção não comprovam ausência física de fogo.

Gate: aprovação real da tutoria e registro ligado ao hash do manifesto. O formulário privado fica em `.local/approvals/entrega0.json`, com `status`, `approved_by`, `approved_at`, `evidence_ref` e `dataset_manifest_sha256`. Ele é um registro de evidência humana, não um mecanismo de autenticação. Mudança material de fonte, alvo ou população exige nova confirmação. O comando `check_delivery.py` deve bloquear antes dessa aprovação.

## Entrega 1 — diagnóstico e preparação

Fechar unidade regional, instante/horizonte da previsão, alvo e KPIs. Construir painel com máscara de cobertura; documentar join, timezone, ausências, duplicatas e exclusões. Reservar teste temporal antes de escolhas orientadas por resultados. EDA deve interpretar distribuições, relações, extremos e ausências; fazer teste de hipótese ligado ao negócio, com H0/H1, método, efeito e limitações. Entregar base consolidada reproduzível, dicionário e README.

Gate: notebook executado sem erro, contrato dos dados validado, rubrica coberta e primeira revisão do curso. Só avançar formalmente após aprovação ou liberação explícita com ajustes menores.

## Entrega 2 — etapas 2 e 3

Comparar referência simples e pelo menos três modelos com a mesma validação temporal. Documentar desbalanceamento, limiares, recall da classe crítica, F1 macro, precisão, acurácia e AUC quando aplicável. Apresentar custo simulado com premissas auditáveis e análise de sensibilidade, sem chamar simulação de economia comprovada.

Usar Optuna no desenvolvimento/validação; explicar três variáveis principais por método apropriado; avaliar desempenho por regiões, períodos e grupos de cobertura. Planejar A/B com unidade de sorteio, contaminação espacial, amostra, duração, métricas e encerramento. Congelar decisões antes de avaliar o teste final e registrar as limitações.

Gate: métricas reais, comparação reproduzível, teste reservado, evidência de explicabilidade e vieses, plano A/B e documentação do modelo. Nunca fabricar uma meta atingida.

## Etapa 4 — incluída na entrega final

FastAPI com validação de entradas, contrato de resposta, exemplo real de request, identificador/hash do modelo e comportamento explícito quando não houver modelo. Testar serialização, inferência, fronteiras e erros. Incluir dependências, Dockerfile, health check e instruções de execução. Deploy somente após escolher destino, custos e acesso; repositório privado não implica que uma API na internet seja privada.

Gate: imagem construída e smoke test executado, request real no serviço publicado, ausência de segredos, README com URL ativa e limitações. Não confundir TestClient em processo com API publicada.

## Pacotes e futuro portfólio

Os notebooks de desenvolvimento versionados ficam limpos. Para cada submissão, produzir cópia executada, tabelas/gráficos revisados, manifesto e instruções em `.local/deliveries/`. O notebook final precisa manter resultados, conforme a rubrica; sua disponibilização por arquivo ou release privado será revisada antes da submissão. Se for decidido versionar saídas, ajustar o gate em mudança explícita, com revisão de conteúdo.

A futura abertura pública exige revisão de direitos de dados/código, conteúdo e histórico, retirada de referências privadas, testes reproduzíveis, model/data cards e avaliação do serviço externo. Nenhuma mudança automática de visibilidade está prevista.

## Comandos de uma unidade já revisada

```sh
git fetch origin
git switch -c <branch-da-unidade> origin/main
# Implementar e validar; adicionar somente arquivos conhecidos da unidade.
git add -- <arquivos-revisados>
python scripts/check_publication.py --staged
git diff --cached --check
git commit -m "feat(escopo): descreva o resultado"
gh repo view --json visibility
git push -u origin <branch-da-unidade>
gh pr create --draft --base main --body-file <descricao-revisada>
```

Interromper antes do push se a visibilidade não for PRIVATE ou se os gates falharem. O primeiro envio inaugura uma baseline vazia para permitir revisão da estrutura inicial por PR; não implica merge automático. Datas de submissão e aprovação são registradas somente depois das ações reais.
