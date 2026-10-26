"""Exporta o painel revisado e executa os quatro notebooks da entrega."""
from pathlib import Path
import argparse
import base64
import contextlib
import io
import json
import os
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
os.environ.setdefault('MPLCONFIGDIR', str(ROOT / '.local/matplotlib'))
import duckdb
import matplotlib.pyplot as plt
import nbformat
import pandas as pd

from fire_risk.artifacts import read_json
from fire_risk.finalization import verify_freeze
from fire_risk.submission import DICTIONARY, NOTEBOOKS, PANEL_FILE, read_panel, sha256_bytes
from submission_notebooks import AUDIT, EDA, MODELS, FINAL


def export_evidence(folder, destination):
    files = {
        'manifest.json': 'manifest.json', 'panel-summary.json': 'panel-summary.json',
        'prepared/resumo_preparacao.json': 'resumo_preparacao.json',
        'optimization/results.json': 'optimization.json', 'final/freeze.json': 'freeze.json',
        'final/evaluation.json': 'evaluation.json',
    }
    destination.mkdir(exist_ok=True, parents=True)
    for source, name in files.items():
        (destination / name).write_bytes((folder / source).read_bytes())
    deployment = folder / 'deployment.json'
    output = destination / 'deployment.json'
    if deployment.is_file():
        output.write_bytes(deployment.read_bytes())
    else:
        output.write_text(json.dumps({
            'status': 'not_deployed', 'http_verified': False,
            'note': 'Reconstrução local sem registro de publicação; não comprova API ativa para este modelo.'
        }, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')


def execute_notebook(notebook, cwd):
    namespace = {}
    previous = Path.cwd()
    try:
        os.chdir(cwd)
        for count, cell in enumerate((c for c in notebook.cells if c.cell_type == 'code'), 1):
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                exec(compile(cell.source, '<academic-notebook>', 'exec'), namespace)
            cell.execution_count = count
            cell.outputs = [nbformat.v4.new_output('stream', name='stdout', text=output.getvalue())]
            for number in plt.get_fignums():
                data = io.BytesIO()
                plt.figure(number).savefig(data, format='png', dpi=120, bbox_inches='tight')
                cell.outputs.append(nbformat.v4.new_output('display_data', data={
                    'image/png': base64.b64encode(data.getvalue()).decode('ascii')}))
                plt.close(number)
        nbformat.validate(notebook)
        return notebook
    finally:
        plt.close('all')
        os.chdir(previous)


def build(root=ROOT):
    folder = root / '.local/course'
    freeze = verify_freeze(root)
    evaluation = read_json(folder / 'final/evaluation.json')
    if evaluation['freeze_sha256'] != sha256_bytes((folder / 'final/freeze.json').read_bytes()):
        raise ValueError('Avaliação não corresponde ao congelamento.')
    destination = root / 'submission'
    destination.mkdir(exist_ok=True)
    with duckdb.connect() as con:
        panel = con.execute('SELECT * FROM read_parquet(?) ORDER BY data,id_municipio',
                            [str(folder / 'panel.parquet')]).df()
    panel.to_csv(root / PANEL_FILE, index=False, date_format='%Y-%m-%dT%H:%M:%S', lineterminator='\n')
    exported = read_panel(root / PANEL_FILE)
    pd.testing.assert_frame_equal(exported, panel, check_dtype=False, atol=1e-12, rtol=1e-12)
    dictionary = [
        '# Dicionário da base consolidada', '',
        'Arquivo: `submission/painel_modelagem.csv`, UTF-8, separador vírgula. Uma linha por município/data UTC com índice e meteorologia elegíveis. '
        '1.329 linhas e 17 colunas nesta versão; todas as linhas do painel original são preservadas, incluindo 72 de intervalo (`gap`).', '',
        'Somente `chuva_d2`, `temperatura_d2`, `umidade_d2` e `vento_d2` entram no modelo. '
        'Alvos, IDs, contagens em D e controles temporais não são features. '
        'As unidades meteorológicas do material de origem são inconsistentes: preservamos a escala original, sem afirmar mm, °C ou m/s sem confirmação.', '',
        '| Coluna | Tipo/escala | Papel | Significado e regra |', '|---|---|---|---|',
    ]
    dictionary += [f'| `{name}` | {kind} | {role} | {description} |'
                   for name, (kind, role, description) in DICTIONARY.items()]
    dictionary += ['', '## Ausências, origem e partições', '',
                   'O painel não tem ausências. Índices inválidos, municípios/dias sem índice e meteorologia insuficiente são excluídos antes da junção; '
                   'a exclusão não cria rótulo baixo. Ver `submission/evidence/panel-summary.json` e o notebook de auditoria para denominadores.', '',
                   'Treino: 764 exemplos (03–25/01/2025); validação: 183 (27/01–02/02); teste: 310 (04–12/02); '
                   'intervalos: 72 (26/01 e 03/02). CSV não permite inferir tipos: leia id_municipio como texto para preservar zeros. '
                   '`fire_risk.submission.read_panel` preserva o código e converte datas; `verify_submission` verifica hashes e partições.', '',
                   'A base é derivada dos quatro arquivos fornecidos pelo curso, sem nomes de pessoas, credenciais ou registros individuais de detecção. '
                   'Esta cópia acompanha a avaliação no repositório privado; não concede licença de redistribuição pública dos originais.']
    (root / 'docs/data-dictionary.md').write_text('\n'.join(dictionary) + '\n', encoding='utf-8', newline='\n')
    export_evidence(folder, destination / 'evidence')
    files = [root / PANEL_FILE, root / 'docs/data-dictionary.md',
             *sorted((destination / 'evidence').glob('*.json'))]
    manifest = {
        'schema_version': 1, 'rows': len(panel), 'splits': panel['split'].value_counts().to_dict(),
        'model_id': freeze['artifacts'][freeze['selected']]['sha256'][:16],
        'original_panel_sha256': sha256_bytes((folder / 'panel.parquet').read_bytes()),
        'source': 'course_derived_panel', 'submission_status': 'not_submitted',
        'files': {p.relative_to(root).as_posix(): sha256_bytes(p.read_bytes()) for p in files},
    }
    (destination / 'manifest.json').write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
    for name, sections in zip(NOTEBOOKS, (AUDIT, EDA, MODELS, FINAL)):
        cells = []
        for index, (kind, text) in enumerate(sections):
            if kind == 'code':
                compile(text, '<academic-notebook>', 'exec')
            factory = nbformat.v4.new_code_cell if kind == 'code' else nbformat.v4.new_markdown_cell
            cells.append(factory(text, id=f'academic-{index:02}'))
        notebook = nbformat.v4.new_notebook(cells=cells, metadata={
            'kernelspec': {'name': 'python3', 'display_name': 'Python 3', 'language': 'python'}})
        path = root / name
        path.parent.mkdir(exist_ok=True, parents=True)
        execute_notebook(notebook, path.parent)
        nbformat.write(notebook, path)
    verify_freeze(root)
    print('Entrega: base íntegra, dicionário completo e quatro notebooks executados; congelamento preservado.')


if __name__ == '__main__':
    build()
