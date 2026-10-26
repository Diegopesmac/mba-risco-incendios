"""Narrativas da entrega que executam sem CSVs brutos ou modelos binários."""
BOOTSTRAP = '''from pathlib import Path
import json, sys
ROOT = next((p for p in (Path.cwd(), *Path.cwd().parents)
             if (p/'submission/manifest.json').is_file() and (p/'src/fire_risk').is_dir()), None)
if ROOT is None:
    raise RuntimeError('Abra o notebook dentro da pasta extraída ou do clone completo do projeto.')
sys.path.insert(0, str(ROOT/'src'))
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from fire_risk.submission import verify_submission, training_correlations
panel, manifest = verify_submission(ROOT)
def evidence(name):
    return json.loads((ROOT/'submission/evidence'/name).read_text(encoding='utf-8'))
print('Base consolidada íntegra:', len(panel), 'municípios/dia; partições:', manifest['splits'])
print('Modelo congelado:', manifest['model_id'])
'''

AUDIT = [
('markdown', '# Auditoria e preparação — Caminho 2\n\nObjetivo: classificar o índice registrado em baixo/médio/alto por município/dia com meteorologia anterior. A limpeza e a consolidação foram concluídas. Este notebook apresenta os registros auditados da preparação e verifica a base entregue; para refazer a leitura dos quatro CSVs, use `scripts/prepare_course.py` e `scripts/build_course_panel.py` conforme o README. Não é previsão física de ocorrência.'),
('code', BOOTSTRAP),
('markdown', '## Fontes e limpeza rastreável\n\nAs quatro fontes do curso estão identificadas por hash. A preparação compara todas as colunas, remove repetições exatas somente dos derivados e reserva horários com versões divergentes. Não há imputação de chuva ausente como zero. Chuva exige 24 registros; temperatura, umidade e vento, ao menos 18. O manifesto da fonte e o resumo abaixo são evidências da execução original, não uma nova leitura dos CSVs neste notebook.'),
('code', '''sources = evidence('manifest.json')
print(pd.DataFrame(sources['files'])[['file','sha256']].to_string(index=False))
preparation = evidence('resumo_preparacao.json')
print(pd.Series(preparation).to_string())
assert preparation['meteorologia_linhas_originais'] == (preparation['duplicatas_exatas_removidas_derivado'] + preparation['linhas_distintas_reservadas_por_chave_multipla'] + preparation['linhas_horarias_usadas'])
'''),
('markdown', '## Consolidação e dicionário\n\nO painel entregue contém todas as colunas descritas em `docs/data-dictionary.md`: chaves, alvo, quatro features, cobertura, disponibilidade e partições. A junção exige município e D−2. Ausência de detecção não recebe rótulo baixo. As contagens permitem rastrear o descarte por índice inválido e por meteorologia não elegível. Os 72 exemplos de intervalo estão preservados e marcados `gap`, sem entrar no ajuste.'),
('code', '''summary = evidence('panel-summary.json')
print(pd.Series({k:summary[k] for k in ['municipality_days_with_records','municipality_days_without_valid_index','valid_target_days_without_eligible_weather','rows']}).to_string())
print(panel.groupby('split').agg(exemplos=('target','size'),inicio=('data','min'),fim=('data','max')).to_string())
print('Ausências no painel:', int(panel.isna().sum().sum()))
print('Duplicatas município/dia:', int(panel.duplicated(['id_municipio','data']).sum()))
assert not panel.isna().any().any()
assert not panel.duplicated(['id_municipio','data']).any()
'''),
('markdown', '## Conclusões e limites\n\nA preparação e o painel estão concluídos. A janela bruta comum é de 43 dias e o painel elegível tem 1.329 linhas. MapBiomas foi auditado e excluído das features porque legenda/coleção e período são incompatíveis. As escalas meteorológicas originais são preservadas; as unidades físicas não foram inferidas. O atraso de publicação de 24 horas é uma hipótese, não comprovação operacional. Modelagem e API constam dos notebooks seguintes. Submissão e aprovação do curso são etapas separadas.'),
]

EDA = [
('markdown', '# EDA — distribuição, correlações e hipótese de negócio\n\nO alvo é a classe da mediana municipal diária de `risco_fogo`. KPIs: F1 macro e recall da classe alta, interpretados com precisão e matriz de confusão. Todas as análises exploratórias abaixo usam somente os 764 exemplos de treino. A análise foi acrescentada após o congelamento para completar a documentação acadêmica; não houve nova escolha de features, limites, parâmetros ou modelos.'),
('code', BOOTSTRAP + '\ntraining, correlations = training_correlations(panel)\nprint("Amostra de EDA:", len(training), "exemplos; teste excluído.")'),
('markdown', '## Distribuição do alvo e desbalanceamento\n\nOs gráficos distinguem o índice contínuo de suas três classes ordenadas. Baixo: até 0,40; médio: acima de 0,40 até 0,70; alto: acima de 0,70. São classes do índice observado na amostra selecionada, não ausência/presença física de incêndio. O desbalanceamento justifica métricas por classe e a referência majoritária.'),
('code', '''counts = training['target'].value_counts().reindex(['baixo','medio','alto'], fill_value=0)
print(pd.DataFrame({'n':counts,'percentual':100*counts/len(training)}).to_string())
fig, axes = plt.subplots(1,2,figsize=(10,4),layout='constrained')
axes[0].hist(training['target_index'],bins=20); axes[0].set_title('Índice no treino'); axes[0].set_xlabel('Mediana do índice'); axes[0].set_ylabel('Municípios/dia')
counts.plot.bar(ax=axes[1],rot=0); axes[1].set_title('Classes no treino'); axes[1].set_ylabel('Municípios/dia')
'''),
('markdown', '## Ausências, distribuições e extremos das features\n\nAs regras de cobertura foram aplicadas antes do painel. O número de faltantes aqui se refere somente aos exemplos elegíveis, não aos CSVs originais. O critério 1,5 IQR descreve extremos; não exclui linhas nem altera o modelo. Consultar a auditoria para as ausências e exclusões nas fontes.'),
('code', '''features = ['chuva_d2','temperatura_d2','umidade_d2','vento_d2']
print(training[features].describe().to_string())
print('Ausências:', training[features].isna().sum().to_dict())
q1,q3 = training[features].quantile(.25),training[features].quantile(.75)
iqr=q3-q1
print('Extremos 1,5 IQR:',((training[features]<q1-1.5*iqr)|(training[features]>q3+1.5*iqr)).sum().to_dict())
training[features].hist(bins=25,figsize=(10,7)); plt.suptitle('Features D−2 — escala original, somente treino')
'''),
('markdown', '## Correlação com o alvo: Pearson e Spearman\n\nPearson mede associação linear; Spearman mede associação monotônica por postos. O índice contínuo evita impor distância entre classes. A coluna ordinal baixo=0, medio=1, alto=2 é uma análise complementar; Pearson nessa codificação pressupõe espaçamento artificial. As quatro features e os alvos aparecem nos dois mapas. Município, contagens em D e indicadores futuros são excluídos das features. Associação não demonstra causa ou capacidade de prever fora da amostra; o índice de origem já depende de meteorologia.'),
('code', '''fig, axes=plt.subplots(1,2,figsize=(14,5),layout='constrained')
for ax,(method,matrix) in zip(axes,correlations.items()):
    print(method, matrix.loc[features,['target_index','target_ordinal']].round(4).to_string())
    im=ax.imshow(matrix,vmin=-1,vmax=1,cmap='coolwarm')
    ax.set_xticks(range(len(matrix)),matrix.columns,rotation=70); ax.set_yticks(range(len(matrix)),matrix.index)
    for i in range(len(matrix)):
        for j in range(len(matrix)): ax.text(j,i,f'{matrix.iloc[i,j]:.2f}',ha='center',va='center',fontsize=8)
    ax.set_title(method+' — treino'); fig.colorbar(im,ax=ax)
rho=correlations['spearman'].loc[features,'target_index']
for name,value in rho.items():
    print(f'{name}: associação monotônica {"positiva" if value>0 else "negativa"} com o índice, rho={value:.3f}.')
print('Estas associações descrevem o treino; não alteram as escolhas congeladas e não comprovam causalidade.')
'''),
('markdown', '## Hipótese de negócio: umidade e índice alto\n\nPremissa: dias classificados como altos apresentam umidade diferente dos demais dentro de municípios comparáveis. H0: diferenças pareadas simétricas em torno de zero; H1: não simétricas em torno de zero. Wilcoxon bilateral, alfa 0,05, pareamento por município, somente treino. Reutilizamos o resultado registrado antes do teste final; a associação é exploratória e não valida alertas operacionais.'),
('code', '''hypothesis=evidence('optimization.json')['hypothesis_training']
print(json.dumps(hypothesis,ensure_ascii=False,indent=2))
print('Interpretação: diferença mediana de umidade',round(hypothesis['median_difference_original_scale'],3),
      '; p-valor',round(hypothesis['p_value'],5),'; rejeita H0 sob as premissas:',hypothesis['reject_under_assumptions'])
print('Seleção por detecções, dependência espacial e construção meteorológica do índice limitam a inferência.')
'''),
]

MODELS = [
('markdown', '# Comparação de modelos — desenvolvimento\n\nComparação inicial e otimizada já concluídas. Referência majoritária, regressão logística, floresta e boosting utilizam as mesmas quatro features e validação temporal. O notebook apresenta evidências registradas, sem retreinar ou consultar o teste. A avaliação final está no notebook 04.'),
('code', BOOTSTRAP),
('markdown', '## Separação e prevenção de vazamento\n\nTreino até 25/01, validação de 27/01 a 02/02, teste de 04/02 a 12/02. Os dias 26/01 e 03/02 são intervalos. A escala e pesos são aprendidos somente no ajuste. Optuna utiliza três folds cronológicos internos ao treino, 20 tentativas por família. A seleção usa F1 macro e desempate por recall alto e nome, nunca o teste.'),
('code', '''optimization=evidence('optimization.json')
metrics=pd.DataFrame(optimization['validation']).T
print(metrics[['f1_macro','accuracy','precision_macro','recall_macro','recall_alto','auc_ovr_macro']].to_string())
print('Folds:',pd.DataFrame(optimization['folds']).to_string(index=False))
print('Parâmetros:',{name:entry['best_params'] for name,entry in optimization['studies'].items()})
metrics[['f1_macro','recall_alto']].astype(float).plot.bar(figsize=(10,4),rot=25,ylim=(0,1)); plt.title('Validação comum — F1 macro e recall alto')
'''),
('markdown', '## Interpretação\n\nA logística otimizada foi selecionada por F1 macro de validação 0,4528, frente a 0,2901 da referência. O recall alto de validação permanece limitado: otimizar não garante ganho em todas as classes. A avaliação final foi congelada antes de observar o teste e é apresentada no notebook seguinte; não há seleção adicional baseada na EDA complementar.'),
]

FINAL = [
('markdown', '# Avaliação final, responsabilidade e API\n\nModelo congelado `852606b93da31ade`. Este notebook apresenta a avaliação registrada em 310 exemplos temporais, sem reabrir seleção nem refazer o teste. As probabilidades representam classes do índice na população condicionada às detecções, não probabilidade física de incêndio. API: https://mba-risco-incendios.onrender.com/docs .'),
('code', BOOTSTRAP),
('markdown', '## Resultado final e erros\n\nO modelo vence a referência em F1 macro e identifica parte da classe alta, mas tem acurácia menor e desempenho fraco na classe média. O resultado não sustenta uso operacional. Reamostragem por dia considera parcialmente a dependência temporal, com apenas nove dias de teste; não garante generalização futura.'),
('code', '''evaluation=evidence('evaluation.json')
print(json.dumps({'modelo':evaluation['metrics'],'referencia':evaluation['reference'],'incerteza':evaluation['uncertainty']},ensure_ascii=False,indent=2))
matrix=evaluation['metrics']['confusion_matrix']
plt.figure(figsize=(5,4)); plt.imshow(matrix,cmap='Blues')
for i,row in enumerate(matrix):
    for j,value in enumerate(row): plt.text(j,i,str(value),ha='center',va='center')
plt.xticks(range(3),['baixo','medio','alto']); plt.yticks(range(3),['baixo','medio','alto']); plt.xlabel('Previsto'); plt.ylabel('Registrado'); plt.title('Teste temporal congelado')
'''),
('markdown', '## Explicabilidade e vieses\n\nImportância por permutação na validação: queda do F1 macro, incluindo valores negativos. As três primeiras variáveis são destacadas; importância global não é efeito causal ou explicação individual. Análises por UF, semana e cobertura incluem suporte e sinalizam grupos esparsos. Não afirmamos equidade ou ausência de viés com amostras insuficientes.'),
('code', '''importance=pd.DataFrame(evidence('optimization.json')['explanation_validation'])
print('Três variáveis principais:',importance.head(3).to_string(index=False))
print('Grupos:',json.dumps(evaluation['groups'],ensure_ascii=False,indent=2))
plt.figure(figsize=(7,3)); plt.barh(importance['feature'],importance['mean_f1_decrease'],xerr=importance['std']); plt.xlabel('Queda de F1 macro na validação'); plt.title('Importância por permutação')
'''),
('markdown', '## Valor simulado e plano A/B\n\nCustos são fictícios e foram definidos antes do teste; não são economia comprovada ou incêndios evitados. O plano completo em `docs/ab-plan.md` define sorteio por blocos geográficos, proteção contra contaminação, métricas independentes, amostra, duração e critérios de parada. O enunciado pede planejar o A/B, não executá-lo.'),
('code', '''print('Custos: modelo',evaluation['simulated_cost'],'referência',evaluation['reference_simulated_cost'])
print(pd.DataFrame(evaluation['cost_sensitivity']).to_string(index=False))
'''),
('markdown', '## Publicação, reprodução e conclusão\n\nFastAPI com validação, exemplo em `configs/example-request.json`, dependências e Dockerfile. A evidência abaixo identifica o commit do serviço e o modelo; esta execução não faz chamadas de rede. O plano gratuito pode demorar após inatividade. A entrega está preparada para revisão acadêmica, ainda sem submissão ou aprovação. A reprodução desta apresentação usa o painel e evidências incluídos; a reconstrução desde os quatro CSVs está no README. Limites: janela curta, meteorologia D−2 com disponibilidade assumida, seleção por detecções e ausência de sazonalidade anual.'),
('code', '''print(json.dumps(evidence('deployment.json'),ensure_ascii=False,indent=2))
print('Conclusão: protótipo acadêmico reproduzível para o índice observado, sem validação operacional.')
'''),
]
