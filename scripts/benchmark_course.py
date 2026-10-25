"""Treina referência e três modelos, com teste final reservado."""
from pathlib import Path
from importlib.metadata import version
import json
import sys

import duckdb
import joblib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from fire_risk.training import compare_models
from fire_risk.validation import sha256


def build():
    folder = ROOT / '.local/course'
    panel = folder / 'panel.parquet'
    summary_path = folder / 'panel-summary.json'
    evidence = json.loads(summary_path.read_text(encoding='utf-8'))
    source = json.loads((folder / 'manifest.json').read_text(encoding='utf-8'))
    preparation = json.loads((folder / 'preparation.json').read_text(encoding='utf-8'))
    if (sha256(panel) != evidence['panel_sha256']
            or sha256(ROOT / 'configs/course-data.json') != source['contract_sha256']
            or sha256(ROOT / 'preparar_eda_queimadas.py') != preparation['preparation_code_sha256']
            or sha256(folder / 'manifest.json') != evidence['source_manifest_sha256']
            or sha256(folder / 'preparation.json') != evidence['preparation_manifest_sha256']
            or sha256(ROOT / 'src/fire_risk/panel.py') != evidence['panel_code_sha256']):
        raise ValueError('Painel desatualizado ou alterado; reconstruir antes do treino.')
    with duckdb.connect() as con:
        # Não carregar linhas do teste final para o benchmark.
        development = con.execute(
            "SELECT * FROM read_parquet(?) WHERE split IN ('train','validation')", [str(panel)]).df()
    models, report = compare_models(development[development['split'] == 'train'],
                                     development[development['split'] == 'validation'])
    destination = folder / 'benchmark'
    destination.mkdir(exist_ok=True)
    artifacts = {}
    for name, model in models.items():
        path = destination / (name + '.joblib')
        joblib.dump(model, path, compress=3)
        artifacts[name] = {'file': path.name, 'sha256': sha256(path)}
    report.update({'panel_sha256': evidence['panel_sha256'],
                   'panel_summary_sha256': sha256(summary_path),
                   'training_code_sha256': sha256(ROOT / 'src/fire_risk/training.py'),
                   'python_version': sys.version.split()[0],
                   'versions': {name: version(name) for name in ('scikit-learn', 'numpy', 'scipy', 'joblib')},
                   'artifacts': artifacts})
    (destination / 'validation.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'selected': report['selected'],
                      'validation': {name: {k: values[k] for k in ('f1_macro', 'recall_alto', 'accuracy')}
                                     for name, values in report['models'].items()},
                      'test_evaluated': False}, ensure_ascii=False))
    return report


if __name__ == '__main__':
    build()
