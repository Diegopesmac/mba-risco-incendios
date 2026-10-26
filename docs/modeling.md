# Comparação e avaliação final de modelos

Fluxo reproduzível:

```sh
python scripts/prepare_course.py --raw-dir <pasta-dos-quatro-csvs>
python scripts/build_course_panel.py --raw-dir <pasta-dos-quatro-csvs>
python scripts/benchmark_course.py
python scripts/build_course_notebook.py
python scripts/optimize_course.py
python scripts/finalize_course.py
python scripts/build_final_notebook.py
```

Painel e contrato temporal: `docs/data-contract.md`. A construção confere os quatro CSVs, hashes dos derivados e versão do código da preparação; não usa fontes externas. A comparação confere painel, manifesto e código, e carrega somente as partições `train` e `validation`.

## Candidatos e seleção

Referência por classe majoritária; regressão logística com escala aprendida no treino e pesos de classe balanceados; floresta com 200 árvores, profundidade máxima 8 e folhas mínimas de 3; boosting por histograma com 150 iterações, taxa 0,07, no máximo 15 folhas e regularização L2 de 1. Pesos de classe aprendem somente frequências do treino. Semente 42, execução limitada a uma thread; boosting sem validação aleatória interna.

Seleção por F1 macro da validação, desempate por recall alto e nome. A referência participa da seleção e pode vencer. Registrar precisão/recall por classe, F1 macro, acurácia, AUC multiclasse OVR, matriz de confusão, tempos de treino e inferência. Todas as partições de desenvolvimento devem conter as três classes. Não usar acurácia isolada como prova de qualidade.

## Evidência e persistência

`.local/course/benchmark/validation.json` contém métricas reais de validação, versões, hashes e regra de seleção. `test_evaluated=false`, `hyperparameter_search_completed=false` e `operational_use_validated=false` permanecem explícitos nesta comparação. Nenhuma métrica do teste final é calculada.

Artefatos locais em joblib, com hash por modelo e versões fixadas; carregar somente arquivos produzidos e conferidos pelo próprio fluxo. Joblib utiliza pickle e não é formato seguro para arquivos não confiáveis, conforme [documentação scikit-learn](https://scikit-learn.org/stable/model_persistence.html). Hash verifica integridade contra o manifesto, não autentica sua origem. Não redistribuir modelos ou dados automaticamente.

O notebook versionado `notebooks/course/03_painel_modelos_curso.ipynb` contém saídas da comparação inicial e otimizada. `scripts/build_submission.py` executa as células em sequência e incorpora resultados e gráficos a partir dos registros científicos. O processo não representa uma interação com a interface Jupyter ao vivo nem repete a busca de parâmetros.

## Otimização e congelamento

Optuna executa 20 tentativas por família em três folds cronológicos internos ao treino, com janelas de validação de quatro dias e intervalo de um dia. Os candidatos iniciais e otimizados são comparados na validação de desenvolvimento. O teste final não entra na busca. A regressão logística otimizada venceu com F1 macro 0,4528, C=0,0211630612 e recall alto 0,28125.

`configs/evaluation-plan.json` fixa hipótese, métricas, reamostragem, grupos e custos antes da abertura do teste. `final/freeze.json` registra modelo selecionado, versões e hashes do código científico, contrato, painel e otimização. O modelo escolhido e a referência são reajustados nos 947 exemplos de treino mais validação. `evaluate_once` grava `final/evaluation.json`; execuções posteriores devolvem o resultado registrado, sem consultar novamente o teste. A otimização recusa execução quando já há congelamento. Para um novo ciclo, definir novo protocolo e teste independente; não remover o registro para reutilizar o teste observado.

## Interpretação e avaliação final

Importância por permutação na validação destaca vento, umidade e chuva. Hipótese de umidade avaliada somente no treino, com comparação pareada por município e teste de Wilcoxon; interpretação exploratória, sem conclusão causal. O teste final usa 310 exemplos, com F1 macro 0,4097 e recall alto 0,5690. Reamostragem por dia e grupos por UF, semana e cobertura acompanham contagens e limitações. Custos são fictícios; o [plano A/B](ab-plan.md) é prospectivo e não foi executado.

O [model card](model-card.md) reúne resultados e restrições. Janela curta, classe intermediária rara e amostragem condicionada impedem declarar generalização operacional. O notebook final executado é `notebooks/04_projeto_final_curso.ipynb`; base, evidências e hashes estão em `submission/`. O gerador lê resultados existentes, sem treinar novamente ou alterar escolhas. O notebook 02 acrescenta distribuição do alvo e correlações Pearson/Spearman exclusivamente no treino, como complemento documental posterior ao congelamento; não houve nova seleção a partir dessa análise. API e Docker são descritos no [guia de publicação](deployment.md); a publicação pública permanece uma verificação separada.

Dependências adicionais: scikit-learn (modelos e métricas, BSD-3-Clause), joblib (persistência local, BSD-3-Clause), threadpoolctl (controle de threads, BSD-3-Clause) e narwhals (dependência do scikit-learn, MIT). Nenhuma dependência substitui o contrato temporal.
