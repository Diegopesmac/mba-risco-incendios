"""Otimiza somente em desenvolvimento e registra o plano antes do teste."""
from pathlib import Path
import sys

import duckdb
import joblib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from fire_risk.artifacts import read_json, write_json, verify_panel, science_fingerprint
from fire_risk.optimization import optimize_models
from fire_risk.assessment import explain, humidity_hypothesis
from fire_risk.validation import sha256


def build(root=ROOT):
    folder = root / '.local/course'
    if (folder / 'final/freeze.json').exists() or (folder / 'final/evaluation.json').exists():
        raise ValueError('Decisões congeladas; otimização adicional exige novo protocolo e novo teste.')
    summary = verify_panel(root)
    plan = read_json(root / 'configs/evaluation-plan.json')
    with duckdb.connect() as con:
        frame = con.execute("SELECT * FROM read_parquet(?) WHERE split IN ('train','validation')",
                            [str(folder / 'panel.parquet')]).df()
    train, valid = frame[frame['split'] == 'train'], frame[frame['split'] == 'validation']
    models, report = optimize_models(train, valid, plan)
    report['explanation_validation'] = explain(models[report['selected']], valid, plan)
    report['hypothesis_training'] = humidity_hypothesis(train, plan)
    destination = folder / 'optimization'
    destination.mkdir(exist_ok=True)
    report['artifacts'] = {}
    for name, model in models.items():
        path = destination / (name + '.joblib')
        joblib.dump(model, path, compress=3)
        report['artifacts'][name] = {'file': path.name, 'sha256': sha256(path)}
    report.update(panel_sha256=summary['panel_sha256'],
                  plan_sha256=sha256(root / 'configs/evaluation-plan.json'),
                  code_sha256=science_fingerprint(root))
    write_json(destination / 'results.json', report)
    print('Otimização concluída:', report['selected'], report['validation'][report['selected']]['f1_macro'])
    print('Hipótese:', report['hypothesis_training'])
    return report


if __name__ == '__main__':
    build()
