"""Compõe o notebook final a partir de evidências já congeladas."""
from pathlib import Path
import base64
import contextlib
import copy
import io

import nbformat

ROOT = Path(__file__).resolve().parents[1]
SECTIONS = [
('markdown', '# Projeto final — risco de incêndios\n\nCaminho 2; quatro bases do curso. Objetivo: classificar o índice de risco registrado em baixo/médio/alto por município/dia e disponibilizar uma API acadêmica. Público: avaliação do trabalho e demonstração de priorização analítica. Não é um serviço oficial de alerta. Métricas: F1 macro, recall alto, precisão, acurácia e AUC; valor financeiro apenas simulado.'),
('code', '''from pathlib import Path
import sys, json, math
import duckdb, numpy as np, pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT = Path.cwd()
while not (ROOT/'src/fire_risk').exists() and ROOT.parent != ROOT:
    ROOT = ROOT.parent
sys.path.insert(0,str(ROOT/'src'))
from fire_risk.artifacts import read_json
from fire_risk.finalization import verify_freeze
from fire_risk.validation import sha256
folder = ROOT/'.local/course'
freeze = verify_freeze(ROOT)
evaluation = read_json(folder/'final/evaluation.json')
assert evaluation['freeze_sha256'] == sha256(folder/'final/freeze.json')
panel = read_json(folder/'panel-summary.json')
preparation = read_json(folder/'prepared/resumo_preparacao.json')
optimization = read_json(folder/'optimization/results.json')
plan = read_json(ROOT/'configs/evaluation-plan.json')
print('Modelo congelado:',freeze['selected'])
print('Versões:',freeze['versions'])
print('Fontes:',[(f['file'],f['sha256']) for f in read_json(folder/'manifest.json')['files']])
'''),
('markdown', '## Dados, preparação e EDA\n\nOs quatro CSVs originais são preservados. Duplicatas meteorológicas exatas são removidas somente dos derivados; versões divergentes de um horário são reservadas. Chuva diária exige 24 medições e as demais médias ao menos 18. MapBiomas foi analisado: códigos observados incompatíveis com a legenda e série encerrada em 2021; não entrou como feature. A sobreposição bruta é de 43 dias. Consultar os notebooks 01 e 02 do curso para a auditoria e EDA originais.'),
('code', '''print(pd.Series(preparation).to_string())
print('Painel:',panel['rows'],'classes:',panel['classes'])
print('Exclusões:',{k:panel[k] for k in ['municipality_days_without_valid_index','valid_target_days_without_eligible_weather']})
with duckdb.connect() as con:
    monthly = con.execute('SELECT * FROM read_parquet(?)',[str(folder/'prepared/deteccoes_mensais.parquet')]).df()
    coverage = con.execute('SELECT * FROM read_parquet(?)',[str(folder/'prepared/cobertura_meteorologia.parquet')]).df()
    development = con.execute("SELECT * FROM read_parquet(?) WHERE split IN ('train','validation')",[str(folder/'panel.parquet')]).df()
fig,axes=plt.subplots(1,2,figsize=(12,4),layout='constrained')
axes[0].plot(monthly['mes'],monthly['deteccoes'],marker='o')
axes[0].set_title('Registros multissatélite — mês final parcial')
axes[0].tick_params(axis='x',rotation=30)
axes[0].set_ylabel('Detecções registradas')
axes[1].plot(coverage['data'],coverage['estacoes_com_registro'],label='Algum registro')
axes[1].plot(coverage['data'],coverage['estacoes_chuva_completa'],label='Chuva completa')
axes[1].set_title('Cobertura meteorológica observada'); axes[1].legend()
axes[1].tick_params(axis='x',rotation=30)
print(development[['chuva_d2','temperatura_d2','umidade_d2','vento_d2']].describe().to_string())
'''),
('markdown', '## Alvo, população e tempo\n\nMediana municipal diária dos índices válidos em [0,1]. Baixo até 0,40; médio acima de 0,40 até 0,70; alto acima de 0,70. Adaptação da tabela 3.5 do método INPE, reunindo mínimo/baixo e alto/crítico. Sem detecção ou índice válido não há classe negativa. A população é condicionada aos registros de detecção e à meteorologia elegível. Entrada em D−2; atraso de publicação de 24 horas após o dia meteorológico é hipótese, não disponibilidade histórica comprovada. Escalas originais preservadas. Teste temporal foi separado antes das escolhas de desempenho; dois dias de separação ficam fora do ajuste.'),
('code', '''print(pd.DataFrame(panel['splits']).T.to_string())
print('Folds cronológicos dentro do treino:')
print(pd.DataFrame(optimization['folds']).to_string(index=False))
print('Hipótese exploratória em municípios pareados, somente treino:')
print(json.dumps(optimization['hypothesis_training'],ensure_ascii=False,indent=2))
'''),
('markdown', '## Modelagem, Optuna e congelamento\n\nReferência por classe majoritária, regressão logística, floresta e boosting. Optuna executa 20 tentativas por família, com três folds cronológicos do treino e intervalo de separação. Comparação em validação inclui configurações iniciais e otimizadas. Seleção por F1 macro, desempate recall alto e nome. Após selecionar, o estimador é reajustado em treino+validação. Modelo, contratos, plano e código são vinculados por hashes antes de ler o teste. A rotina reutiliza o relatório final existente sem reabrir o teste.'),
('code', '''ranking=pd.DataFrame(optimization['validation']).T
print(ranking[['f1_macro','accuracy','precision_macro','recall_macro','recall_alto','auc_ovr_macro']].to_string())
print('Melhores parâmetros CV:',{k:v['best_params'] for k,v in optimization['studies'].items()})
print('Congelamento:',freeze['frozen_at'],'linhas de desenvolvimento:',freeze['development_rows'])
print('TESTE FINAL:',json.dumps(evaluation['metrics'],ensure_ascii=False,indent=2))
print('Referência:',evaluation['reference'])
print('Incerteza por reamostragem de dias:',evaluation['uncertainty'])
'''),
('markdown', '## Explicabilidade, vieses e erros\n\nImportância global por permutação na validação, usando queda de F1 macro; valores negativos também são mantidos. Não equivale a efeito causal ou importância individual. As três primeiras variáveis são destacadas. A avaliação por prefixo de UF, semana e cobertura de estações inclui contagens e marca grupos esparsos; diferenças pequenas ou sem suporte crítico suficiente não comprovam viés nem ausência dele.'),
('code', '''importance=pd.DataFrame(optimization['explanation_validation'])
print('Três variáveis principais:',importance.head(3).to_string(index=False))
print('Grupos:',json.dumps(evaluation['groups'],ensure_ascii=False,indent=2))
fig,axes=plt.subplots(1,2,figsize=(11,4),layout='constrained')
axes[0].barh(importance['feature'],importance['mean_f1_decrease'],xerr=importance['std'])
axes[0].set_title('Importância por permutação — validação'); axes[0].set_xlabel('Queda média de F1 macro')
matrix=np.asarray(evaluation['metrics']['confusion_matrix'])
axes[1].imshow(matrix,cmap='Blues')
for i in range(3):
    for j in range(3):
        axes[1].text(j,i,str(matrix[i,j]),ha='center',va='center',color='white' if matrix[i,j]>matrix.max()/2 else 'black')
axes[1].set_xticks(range(3),['baixo','médio','alto']); axes[1].set_yticks(range(3),['baixo','médio','alto'])
axes[1].set_xlabel('Previsto'); axes[1].set_ylabel('Registrado'); axes[1].set_title('Matriz de confusão — teste final')
'''),
('markdown', '## Valor simulado e plano A/B\n\nA matriz de custos é fictícia e foi definida antes do teste. Linhas são classes registradas e colunas previstas; penalidades maiores para subestimar alto. A unidade é uma decisão sobre a classe do índice, não um incêndio evitado. Diferenças de custos não são economia real. O plano A/B em docs/ab-plan.md propõe revisão humana em modo sombra, blocos geográficos, controle de contaminação, avaliação independente, proteção, amostra, duração e encerramento pré-definidos.'),
('code', '''print('Matriz fictícia:',plan['cost_scenario'])
print('Modelo:',evaluation['simulated_cost'],'referência:',evaluation['reference_simulated_cost'])
print(pd.DataFrame(evaluation['cost_sensitivity']).to_string(index=False))
from scipy.stats import norm
p0,p1,alpha,power=0.10,0.08,0.05,0.80
pbar=(p0+p1)/2
n=((norm.ppf(1-alpha/2)*math.sqrt(2*pbar*(1-pbar))+norm.ppf(power)*math.sqrt(p0*(1-p0)+p1*(1-p1)))**2)/(p0-p1)**2
cluster_count=math.ceil(n*(1+19*0.02)/0.90/20)
print('A/B ilustrativo: decisões independentes por braço:',math.ceil(n))
print('Blocos por braço após efeito de desenho/perdas:',cluster_count,'decisões:',cluster_count*20)
print('Dias por braço para taxas hipotéticas:',{daily:math.ceil(cluster_count*20/daily) for daily in [50,100,200]})
'''),
('markdown', '## API, reprodução e conclusão\n\nAPI FastAPI com contrato de entrada, rejeição de dados inválidos, identificação/hash do modelo e estado 503 quando não houver artefato válido. Bundle separado do código, conferido antes do carregamento. Docker sem dados brutos e com usuário sem privilégios. API pública verificada em 25/10/2026 no Render: https://mba-risco-incendios.onrender.com/docs . Saúde e inferência responderam 200; entrada inválida foi rejeitada com 422. Modelo final 852606b93da31ade. O plano gratuito pode demorar 50 segundos ou mais para responder após inatividade. A ausência de distribuição futura/cobertura comprovada impede declarar uso operacional. Avaliação acadêmica e relatórios de revisão do curso permanecem etapas humanas.'),
('code', '''deployment=folder/'deployment.json'
print('Publicação:',read_json(deployment) if deployment.exists() else {'status':'pending'})
print('Conclusão: avaliação reproduzível concluída, com desempenho e limitações explícitos.')
print('O modelo classifica o índice observado na amostra; não estima probabilidade física de fogo em todo município/dia.')
''')]


def build():
    cells=[]
    for index,(kind,source) in enumerate(SECTIONS):
        if kind=='code': compile(source,'<final-notebook>','exec')
        factory=nbformat.v4.new_code_cell if kind=='code' else nbformat.v4.new_markdown_cell
        cells.append(factory(source,id=f'final-{index:02}'))
    notebook=nbformat.v4.new_notebook(cells=cells,metadata={'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'}})
    nbformat.write(notebook,ROOT/'notebooks/04_projeto_final_curso.ipynb')
    executed=copy.deepcopy(notebook); namespace={}
    for count,cell in enumerate((c for c in executed.cells if c.cell_type=='code'),1):
        buffer=io.StringIO()
        with contextlib.redirect_stdout(buffer): exec(compile(cell.source,'<final-notebook>','exec'),namespace)
        cell.execution_count=count
        cell.outputs=[nbformat.v4.new_output('stream',name='stdout',text=buffer.getvalue())]
        plt=namespace.get('plt')
        if plt:
            for number in plt.get_fignums():
                data=io.BytesIO(); plt.figure(number).savefig(data,format='png',dpi=130)
                cell.outputs.append(nbformat.v4.new_output('display_data',data={'image/png':base64.b64encode(data.getvalue()).decode('ascii')}))
                plt.close(number)
    nbformat.validate(executed)
    destination=ROOT/'.local/deliveries/04_projeto_final_curso.ipynb'
    nbformat.write(executed,destination)
    print('Notebook final executado:',count,'células de código.')


if __name__=='__main__': build()
