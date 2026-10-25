# Comparação inicial de modelos

Fluxo reproduzível:

```sh
python scripts/prepare_course.py --raw-dir <pasta-dos-quatro-csvs>
python scripts/build_course_panel.py --raw-dir <pasta-dos-quatro-csvs>
python scripts/benchmark_course.py
python scripts/build_course_notebook.py
```

Painel e contrato temporal: `docs/data-contract.md`. A construção confere os quatro CSVs, hashes dos derivados e versão do código da preparação; não usa fontes externas. A comparação confere painel, manifesto e código, e carrega somente as partições `train` e `validation`.

## Candidatos e seleção

Referência por classe majoritária; regressão logística com escala aprendida no treino e pesos de classe balanceados; floresta com 200 árvores, profundidade máxima 8 e folhas mínimas de 3; boosting por histograma com 150 iterações, taxa 0,07, no máximo 15 folhas e regularização L2 de 1. Pesos de classe aprendem somente frequências do treino. Semente 42, execução limitada a uma thread; boosting sem validação aleatória interna.

Seleção por F1 macro da validação, desempate por recall alto e nome. A referência participa da seleção e pode vencer. Registrar precisão/recall por classe, F1 macro, acurácia, AUC multiclasse OVR, matriz de confusão, tempos de treino e inferência. Todas as partições de desenvolvimento devem conter as três classes. Não usar acurácia isolada como prova de qualidade.

## Evidência e persistência

`.local/course/benchmark/validation.json` contém métricas reais de validação, versões, hashes e regra de seleção. `test_evaluated=false`, `hyperparameter_search_completed=false` e `operational_use_validated=false` permanecem explícitos nesta comparação. Nenhuma métrica do teste final é calculada.

Artefatos locais em joblib, com hash por modelo e versões fixadas; carregar somente arquivos produzidos e conferidos pelo próprio fluxo. Joblib utiliza pickle e não é formato seguro para arquivos não confiáveis, conforme [documentação scikit-learn](https://scikit-learn.org/stable/model_persistence.html). Hash verifica integridade contra o manifesto, não autentica sua origem. Não redistribuir modelos ou dados automaticamente.

O notebook versionado `notebooks/course/03_painel_modelos_curso.ipynb` fica sem saídas. A cópia executada e o gráfico ficam em `.local/deliveries/`. O gerador executa as células em sequência no processo Python e incorpora saídas; não representa execução de interface Jupyter ao vivo.

## Pendências científicas

Otimização com Optuna, análise de variáveis, viés por regiões/cobertura, custos simulados e plano A/B são incrementos posteriores. Uma pontuação de validação não comprova generalização; janela curta, classe intermediária rara e amostragem condicionada devem acompanhar as conclusões. O teste final só entra depois de congelar escolhas. API, serialização em serviço, Docker e deploy requerem validação própria.

Dependências adicionais: scikit-learn (modelos e métricas, BSD-3-Clause), joblib (persistência local, BSD-3-Clause), threadpoolctl (controle de threads, BSD-3-Clause) e narwhals (dependência do scikit-learn, MIT). Nenhuma dependência substitui o contrato temporal.
