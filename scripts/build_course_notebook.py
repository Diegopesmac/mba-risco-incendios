"""Gera narrativa do curso limpa e cópia local executada com gráficos."""
from pathlib import Path
import base64
import contextlib
import copy
import io
import json

import nbformat

ROOT = Path(__file__).resolve().parents[1]


SECTIONS = [
    ('markdown', '# Risco de incêndios — dados do curso\n\nCaminho 2. Classificação retrospectiva do índice registrado por município/dia. Resultados de validação inicial; teste final reservado. Não é probabilidade física de incêndio.'),
    ('code', '''from pathlib import Path
import sys, json
import duckdb
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT = Path.cwd()
while not (ROOT/'src/fire_risk').is_dir() and ROOT.parent != ROOT:
    ROOT = ROOT.parent
sys.path.insert(0, str(ROOT/'src'))
from fire_risk.validation import sha256
folder = ROOT/'.local/course'
panel = json.loads((folder/'panel-summary.json').read_text(encoding='utf-8'))
benchmark = json.loads((folder/'benchmark/validation.json').read_text(encoding='utf-8'))
assert sha256(folder/'panel.parquet') == panel['panel_sha256']
assert benchmark['panel_sha256'] == panel['panel_sha256']
assert benchmark['panel_summary_sha256'] == sha256(folder/'panel-summary.json')
assert not benchmark['test_evaluated']
print('Fonte: quatro arquivos do curso. Painel:', panel['rows'])
print('Somente desenvolvimento e validação nesta comparação.')
'''),
    ('markdown', '## Alvo, qualidade e tempo\n\nMediana municipal diária de risco_fogo em [0,1], com baixo até 0,40, médio até 0,70 e alto acima de 0,70. Ausência de detecção/índice não vira baixo risco. Meteorologia D−2; publicação com atraso hipotético de 24 horas após o encerramento do dia. Não foi comprovada disponibilidade operacional histórica. MapBiomas foi analisado separadamente; legenda incompatível impede interpretação segura no modelo.'),
    ('code', '''print('Municípios/dia com registros:', panel['municipality_days_with_records'])
print('Sem índice válido:', panel['municipality_days_without_valid_index'])
print('Índice válido sem meteorologia elegível:', panel['valid_target_days_without_eligible_weather'])
for name in ('train','validation','test','gap'):
    print(name, panel['splits'].get(name, {}))
with duckdb.connect() as con:
    development = con.execute("SELECT * FROM read_parquet(?) WHERE split IN ('train','validation')", [str(folder/'panel.parquet')]).df()
print(development[['chuva_d2','temperatura_d2','umidade_d2','vento_d2']].describe().to_string())
'''),
    ('markdown', '## Comparação temporal inicial\n\nMesmas quatro features e mesmas partições para referência, regressão logística, floresta e boosting. Escala aprendida somente no treino. F1 macro é o critério principal; recall alto e nome desempataram conforme regra pré-definida. Acurácia isolada favorece a classe majoritária. Hiperparâmetros ainda não foram otimizados; resultados não são o teste final.'),
    ('code', '''metrics = pd.DataFrame(benchmark['models']).T
columns = ['f1_macro','accuracy','precision_macro','recall_macro','recall_alto','auc_ovr_macro']
print(metrics[columns].to_string())
print('Selecionado nesta comparação:', benchmark['selected'])
fig, axes = plt.subplots(1,2,figsize=(11,4.5),layout='constrained')
metrics[['f1_macro','recall_alto']].astype(float).rename(columns={'f1_macro':'F1 macro','recall_alto':'Recall alto'}).plot.bar(ax=axes[0],ylim=(0,1),rot=20)
axes[0].set_title('Validação: F1 macro e recall alto')
axes[0].set_ylabel('Escore')
best = benchmark['models'][benchmark['selected']]
matrix = best['confusion_matrix']
axes[1].imshow(matrix,cmap='Blues')
for i,row in enumerate(matrix):
    for j,value in enumerate(row): axes[1].text(j,i,str(value),ha='center',va='center',color='white' if value > max(map(max,matrix))/2 else 'black')
axes[1].set_xticks(range(3),['baixo','médio','alto'])
axes[1].set_yticks(range(3),['baixo','médio','alto'])
axes[1].set_xlabel('Previsto'); axes[1].set_ylabel('Registrado')
axes[1].set_title('Matriz de confusão — validação')
'''),
    ('markdown', '## Interpretação e limites\n\nA comparação mostra desempenho inicial, sem assegurar qualidade suficiente para uso operacional. Avaliar o recall alto junto de falsos alertas, não apenas acurácia. São poucos dias e exemplos de municípios com registros e meteorologia elegível; seleção pode introduzir viés. O índice tem relação com variáveis meteorológicas e detecções recentes no método de origem. Próximos requisitos: otimização somente em desenvolvimento, explicabilidade, vieses, custo simulado e plano A/B; congelar decisões antes do teste final. API, Docker e deploy permanecem etapas próprias.'),
]


def build():
    cells = []
    for index, (kind, content) in enumerate(SECTIONS):
        if kind == 'code':
            compile(content, '<course-notebook>', 'exec')
        factory = nbformat.v4.new_code_cell if kind == 'code' else nbformat.v4.new_markdown_cell
        cells.append(factory(content, id=f'course-{index:02}'))
    notebook = nbformat.v4.new_notebook(cells=cells, metadata={
        'kernelspec': {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'}})
    template = ROOT / 'notebooks/course/03_painel_modelos_curso.ipynb'
    nbformat.write(notebook, template)
    executed = copy.deepcopy(notebook)
    namespace = {}
    for count, cell in enumerate((c for c in executed.cells if c.cell_type == 'code'), 1):
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            exec(compile(cell.source, '<course-notebook>', 'exec'), namespace)
        cell.execution_count = count
        cell.outputs = [nbformat.v4.new_output('stream', name='stdout', text=buffer.getvalue())]
        plt = namespace.get('plt')
        if plt:
            for number in plt.get_fignums():
                output = io.BytesIO()
                plt.figure(number).savefig(output, format='png', dpi=120)
                cell.outputs.append(nbformat.v4.new_output('display_data', data={
                    'image/png': base64.b64encode(output.getvalue()).decode('ascii')}))
                plt.close(number)
    nbformat.validate(executed)
    destination = ROOT / '.local/deliveries'
    destination.mkdir(exist_ok=True, parents=True)
    nbformat.write(executed, destination / '03_painel_modelos_curso.ipynb')
    print('Notebook limpo e cópia local com três células executadas e gráfico gerados.')


if __name__ == '__main__':
    build()
