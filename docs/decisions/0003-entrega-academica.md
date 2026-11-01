# ADR 0003 — artefatos da entrega acadêmica

Status: aceito para o repositório privado de avaliação.

O enunciado pede notebooks com resultados, base consolidada, dicionário e EDA do alvo no GitHub. A entrega inclui os quatro notebooks executados nos caminhos canônicos, o painel municipal derivado em `submission/painel_modelagem.csv`, o dicionário de todas as colunas e evidências sem modelos binários. Os CSVs originais não são redistribuídos.

`scripts/build_submission.py` verifica o congelamento, exporta o mesmo painel e compõe uma apresentação portátil. Os notebooks leem o painel e os registros incluídos, validam hashes e não otimizam nem refazem o teste congelado; após revisão do tutor, o notebook 03 reproduz treinamento somente em desenvolvimento e compara persistência e pesos de classe. O notebook de EDA calcula correlações exclusivamente no treino; essa análise complementar posterior ao congelamento não altera decisões científicas.

O gate permite saídas apenas nos quatro caminhos de notebooks definidos e exige execução completa sem erros. A exceção de CSV é restrita ao painel com esquema fechado, contagens, partições e hash vinculados ao manifesto da mesma revisão Git. Demais dados locais, modelos e notebooks com saídas continuam bloqueados. Essa entrega não altera a licença nem a visibilidade do repositório.

As evidências JSON são cópias byte a byte dos registros originais, incluindo finais de linha CRLF. O atributo Git específico impede conversão dessas evidências e reconhece CR no final da linha; assim a referência ao hash do congelamento permanece verificável. Código, documentação e demais arquivos continuam normalizados em LF.

A apresentação é reproduzível desde o clone ou ZIP sem a organização de diretórios da máquina original. A reconstrução integral desde os quatro CSVs é uma opção separada; ela produz novos registros em um ambiente limpo e não substitui o teste já registrado nesta entrega. Remover esta entrega por reversão de commit não altera a API nem o modelo congelado.

Revisão do tutor: gráficos e tabelas usam execução IPython e backend inline nativos. Comparações complementares vivem em revision.py, sem alterar o código vinculado ao congelamento. Novos resultados de desenvolvimento não promovem automaticamente um modelo.

Os arquivos .ipynb são agora a fonte canônica editável; submission_notebooks.py é somente um leitor de compatibilidade, sem código em strings. build_submission.py executa os notebooks existentes. label-history.json contém somente agregados município/dia anteriores ao teste, extraídos de todas as detecções válidas, incluindo as sem meteorologia elegível; o manifesto vincula os bytes da entrega.
