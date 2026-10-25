# API e publicação

Protótipo acadêmico FastAPI para classificar o índice observado. Não é serviço oficial de alerta. A API não treina modelos, recebe artefatos por requisição ou consulta os CSVs originais.

## Contrato HTTP

`GET /` apresenta o projeto; `GET /docs` abre o contrato interativo; `GET /health` retorna 200 com estado `ready` e identificador do modelo. Sem modelo válido, saúde e inferência retornam 503.

`POST /predict` recebe JSON conforme `configs/example-request.json`: código municipal de sete dígitos, data alvo, data meteorológica exatamente dois dias anterior e quatro números finitos. Limites: chuva entre 0 e 3000; temperatura entre −100 e 100; umidade entre 0 e 100; vento entre 0 e 150. Os valores mantêm a escala numérica original dos CSVs, conforme o contrato dos dados; o dicionário apresenta unidades inconsistentes. São fronteiras do contrato, não garantia de unidade física, plausibilidade ou cobertura. Campos extras, datas incompatíveis e valores inválidos retornam 422.

A resposta inclui classe, probabilidades das classes do índice, identificador do modelo, alertas de extrapolação e município fora do desenvolvimento. `uso_operacional_validado` e `disponibilidade_historica_verificada` permanecem falsos. As probabilidades não representam probabilidade física de incêndio. O atraso de publicação de 24 horas é uma hipótese retrospectiva.

## Execução com artefato local

Instalar `requirements-api.txt` em Python 3.12 e configurar `MODEL_DIR` para o bundle produzido por `scripts/finalize_course.py`. Executar `python scripts/start_api.py`. `HOST` e `PORT` controlam a interface e porta; os padrões são `0.0.0.0` e `8000`. Para acesso apenas local, usar `HOST=127.0.0.1`.

```sh
docker build -t mba-fire-risk .
docker run --rm -p 127.0.0.1:8000:8000 -e MODEL_DIR=/model -v "$PWD/.local/course/bundle:/model:ro" mba-fire-risk
python scripts/smoke_api.py --url http://127.0.0.1:8000 --request configs/example-request.json
```

A imagem usa usuário sem privilégios e contém código e dependências, sem dados brutos ou modelo. A construção e o teste HTTP do container usam bundle fictício no CI. A inferência do modelo acadêmico final foi verificada separadamente por HTTP local. A validação pública só é concluída depois do mesmo teste no endereço publicado.

## Railway gratuito

Selecionar somente o repositório do projeto e a branch da entrega. O Dockerfile da raiz fornece construção e inicialização, sem substituir o comando de partida. Configurar health check `/health` e domínio público apontando para a porta `PORT` do provedor.

O modelo é fornecido por configuração do operador: `MODEL_PAYLOAD_B64` contém o bundle codificado e `MODEL_MANIFEST_SHA256` o SHA-256 dos bytes do manifesto. Não incluir o arquivo de configuração no Git. `scripts/start_api.py` materializa o bundle e verifica manifesto e hash do modelo antes de carregar. Codificação base64 não é criptografia; hash confirma integridade, não origem. Somente artefatos confiáveis podem ser carregados, pois joblib utiliza pickle.

O Railway oferece teste sem cartão, com US$ 5 em créditos por até 30 dias, seguido de plano gratuito com US$ 1 de crédito mensal. O consumo pode esgotar o saldo antes do prazo; não há garantia de disponibilidade contínua nesse orçamento. Conferir saldo e acesso próximo à avaliação, sem contratação automática de plano pago. Condições consultadas em 25/10/2026 na [documentação de teste](https://docs.railway.com/pricing/free-trial) e [planos](https://docs.railway.com/pricing/plans).

Em 25/10/2026, a [página de status do provedor](https://status.railway.com/) informa suspensão temporária de novos cadastros. A publicação deste projeto não foi concluída; não há endereço público validado. A disponibilidade do cadastro precisa ser conferida antes de retomar essas instruções.

Depois da publicação, executar `scripts/smoke_api.py` contra o domínio público com exemplo fictício e guardar o resultado local. A URL ativa deve acompanhar a entrega; configurar o serviço não prova que a inferência esteja funcionando.

## Render como alternativa

`render.yaml` preserva a configuração Docker gratuita, com health check e implantação automática desligada. As mesmas duas variáveis transportam o bundle. Na configuração realizada, o provedor solicitou verificação de cartão antes de criar o serviço; não houve publicação. O plano gratuito pode suspender o processo por inatividade, com demora na primeira resposta. Ver [limitações do Render](https://render.com/docs/free).

## Limites de operação

O acesso público é destinado à avaliação acadêmica, sem autenticação e sem compromisso de disponibilidade. Não enviar dados pessoais ou operacionais. O servidor não grava as entradas em arquivo; políticas de retenção e registros da infraestrutura pertencem ao provedor. Suspender ou remover o serviço reverte a publicação; isso não altera os CSVs nem o modelo congelado.
