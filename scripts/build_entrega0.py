"""Produz proposta factual e mini-notebook local, sem aprovar ou rotular dados."""
from pathlib import Path
import sys
import json
import io
import contextlib
import copy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
import nbformat
from fire_risk.validation import sha256


def regional_evidence(folder, manifest_path):
    summary_path = folder / 'state-days-summary.json'
    if not summary_path.exists():
        return None
    summary = json.loads(summary_path.read_text(encoding='utf-8'))
    if (summary['manifest_sha256'] != sha256(manifest_path)
            or summary['output_sha256'] != sha256(folder / 'state-days.csv')):
        raise ValueError('Diagnóstico regional desatualizado; executar diagnose_regions.py novamente.')
    return summary


def build():
    path = ROOT / '.local/candidates/manifest.json'
    data = json.loads(path.read_text(encoding='utf-8'))
    lines = ['# Entrega 0 — proposta para validação', '',
             '**Status: em preparação; não aprovada pela tutoria.**', '',
             '## Problema e público', '',
             'Investigar previsão regional de detecções de fogo para apoiar priorização preventiva por gestores e equipes ambientais. A saída pretendida é baixo/médio/alto, com definição do alvo e interpretação operacional ainda a validar.', '',
             '## Base própria candidata', '',
             'Aquisição direta dos arquivos oficiais anuais do satélite de referência do INPE. Arquivos originais ficam locais e são rastreados por SHA-256.', '',
             '| Ano/arquivo | Linhas | Primeiro dia | Último dia | Dias com registro |',
             '|---|---:|---|---|---:|']
    for file in data['files']:
        lines.append(f"| {file['file']} | {file['rows']:,} | {file['first_date']} | {file['last_date']} | {file['days_with_records']} |")
    lines += ['', f"Total bruto: **{data['total_detection_rows']:,} detecções**. Isso não comprova o volume de exemplos supervisionados após integração e rotulagem.", '',
              '## Qualidade observada', '']
    for file in data['files']:
        lines.append(f"- {file['file']}: IDs repetidos = {file['repeated_id_bdq']}; campos vazios = {sum(file['empty_fields'].values())}; datas sem registro nacional entre extremos = {', '.join(file['calendar_days_without_records']) or 'nenhuma'}.")
    lines += ['', 'Datas sem registro podem representar problemas de cobertura ou ausência de detecção; não foram convertidas em zero. Não foi comprovada cobertura observacional completa de cada região/dia.', '',
              '## Proposta de alvo e KPIs', '',
              'Proposta a discutir: probabilidade de registro de detecção no dia seguinte e três faixas operacionais. Confirmar se o curso exige três classes supervisionadas. Não escolher cortes com base no teste nem criar rótulos para satisfazer balanceamento.', '',
              'KPIs candidatos: recall da classe/faixa crítica, F1 macro quando aplicável, precisão e volume de alertas dentro da capacidade de resposta. Comparar com referência simples. Valor financeiro será simulado com custos explícitos, não medido como economia real.', '',
              '## Checklist da validação', '',
              '- [x] Origem e formato estruturado identificados; hashes registrados.',
              '- [x] Volume bruto acima de 10 mil registros e perfil estrutural executado.',
              '- [x] Mini-notebook com info, describe e qualidade, executado localmente.',
              '- [ ] Painel final pós-limpeza acima de 10 mil exemplos.',
              '- [ ] Alvo preenchido, definição das três classes/faixas e representatividade.',
              '- [ ] Fonte meteorológica, disponibilidade temporal e dicionário final.',
              '- [ ] Política de cobertura e tratamento das datas sem registro.',
              '- [ ] Tutoria 1:1 realizada e aprovação registrada.', '',
              '## Perguntas para a tutoria', '',
              '1. É aceitável prever detecção futura e converter probabilidade em três faixas, ou são exigidas três classes supervisionadas?',
              '2. Qual evidência de cobertura é suficiente para os exemplos sem detecção? Pode-se usar alvo de ausência de registro, explicitamente distinto de ausência física de fogo?',
              '3. Qual recorte regional/temporal torna a operação e a validação defensáveis?',
              '4. Uma previsão meteorológica histórica emitida com antecedência é preferível à reanálise para a simulação operacional?', '',
              '## Reprodutibilidade', '',
              f"SHA-256 do manifesto local auditado: `{sha256(path)}`. Aprovação futura deve citar a versão efetivamente discutida.", '',
              'Rotinas: `scripts/prepare_candidate.py` e `scripts/build_entrega0.py`. Notebook executado em `.local/deliveries/00_validacao_base_externa.ipynb`; template sem saídas em `notebooks/00_validacao_base_externa.ipynb`. Sem treinamento ou métricas preditivas nesta entrega.']
    regional = regional_evidence(path.parent, path)
    if regional:
        statuses = regional['archive_status_counts']
        lines += ['', '## Diagnóstico de viabilidade UF/dia', '',
                  f"Calendário candidato: {regional['calendar_region_days']:,} combinações de {regional['region_count']} UFs e dias, sem seleção de regiões por ocorrência.", '',
                  f"- Com detecção registrada: {statuses.get('recorded_detection', 0):,}.",
                  f"- Sem registro regional, mas com registro nacional no dia: {statuses.get('no_regional_record', 0):,}.",
                  f"- Combinações UF/dia em datas sem registro nacional: {statuses.get('national_archive_gap', 0):,}.", '',
                  'As contagens sem registro permanecem vazias, sem zeros imputados. Cobertura regional não comprovada; nenhum alvo criado. O volume do calendário não atende, por si, ao requisito de exemplos supervisionados. UF é unidade de diagnóstico, não seleção definitiva da região operacional.', '',
                  f"População fixa: [cadastro oficial do IBGE]({regional['population_source']}). Detecções conciliadas com o manifesto auditado. Reprodução: `python scripts/diagnose_regions.py`; contrato em `docs/regional-diagnostic.md`."]
    (ROOT / 'reports/entrega-0/proposta.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    setup = """from pathlib import Path
import sys, json, zipfile
ROOT = Path.cwd()
while not (ROOT/'src/fire_risk').exists() and ROOT.parent != ROOT:
    ROOT = ROOT.parent
import pandas as pd
manifesto=json.loads((ROOT/'.local/candidates/manifest.json').read_text(encoding='utf-8'))
print('Aprovação da tutoria: pendente. Alvo: não definido.')
"""
    cells = [nbformat.v4.new_markdown_cell('# Entrega 0 — validação inicial da base externa\n\nMini-notebook para discussão com a tutoria. Datas, campos e contagens são observados; a base ainda não é um painel supervisionado aprovado.'),
             nbformat.v4.new_code_cell(setup),
             nbformat.v4.new_code_cell("""partes=[]
for item in manifesto['files']:
    with zipfile.ZipFile(ROOT/'.local/candidates/inpe'/item['file']) as z:
        csv_name=next(n for n in z.namelist() if n.lower().endswith('.csv'))
        with z.open(csv_name) as f:
            partes.append(pd.read_csv(f,dtype='string'))
df=pd.concat(partes,ignore_index=True)
df.info()
print('Linhas:', len(df), '| duplicatas completas:', int(df.duplicated().sum()))
"""),
             nbformat.v4.new_code_cell("""print(df[['lat','lon']].astype(float).describe().to_string())
print('Vazios:',df.isna().sum().to_dict())
for item in manifesto['files']:
    print(item['file'], 'dias sem registro:',item['calendar_days_without_records'])
"""),
             nbformat.v4.new_markdown_cell('## Alvo e decisão pendentes\n\nA distribuição da variável alvo não pode ser mostrada enquanto ela não existir. Não substituímos alvo por ID, bioma ou contagem bruta sem aprovação. Datas sem registro e regiões não observadas exigem política de cobertura. Campos de detecção futura não são features disponíveis antecipadamente. Ver proposta e contrato para as perguntas de validação.')]
    notebook=nbformat.v4.new_notebook(cells=cells,metadata={'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'}})
    template=copy.deepcopy(notebook)
    nbformat.write(template,ROOT/'notebooks/00_validacao_base_externa.ipynb')
    namespace={}
    for number,cell in enumerate((c for c in notebook.cells if c.cell_type=='code'),1):
        output=io.StringIO()
        with contextlib.redirect_stdout(output): exec(compile(cell.source,'<entrega0>','exec'),namespace)
        cell.execution_count=number
        cell.outputs=[nbformat.v4.new_output('stream',name='stdout',text=output.getvalue())]
    destination=ROOT/'.local/deliveries'
    destination.mkdir(exist_ok=True,parents=True)
    nbformat.validate(notebook)
    nbformat.write(notebook,destination/'00_validacao_base_externa.ipynb')
    print('Proposta gerada e três células executadas. Aprovação e alvo continuam pendentes.')


if __name__ == '__main__': build()
