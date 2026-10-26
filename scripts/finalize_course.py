"""Congela modelo, avalia teste e prepara bundle de inferência local."""
from pathlib import Path
import shutil
import sys

import duckdb

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from fire_risk.finalization import freeze, evaluate_once
from fire_risk.artifacts import write_json
from fire_risk.panel import FEATURES, LABELS
from fire_risk.validation import sha256


def build(root=ROOT):
    record = freeze(root)
    result = evaluate_once(root)
    folder = root / '.local/course'
    bundle = folder / 'bundle'
    bundle.mkdir(exist_ok=True)
    entry = record['artifacts'][record['selected']]
    shutil.copyfile(folder / 'final' / entry['file'], bundle / 'model.joblib')
    with duckdb.connect() as con:
        development = con.execute("SELECT * FROM read_parquet(?) WHERE split IN ('train','validation')",
                                   [str(folder / 'panel.parquet')]).df()
    write_json(bundle / 'manifest.json', {
        'schema_version': 1, 'file': 'model.joblib', 'sha256': sha256(bundle / 'model.joblib'),
        'model_id': entry['sha256'][:16], 'selected': record['selected'],
        'features': list(FEATURES), 'labels': list(LABELS), 'versions': record['versions'],
        'training_ranges': {key: [float(development[key].min()), float(development[key].max())] for key in FEATURES},
        'municipalities': sorted(development['id_municipio'].unique().tolist()),
        'freeze_sha256': sha256(folder / 'final/freeze.json'), 'operational_use_validated': False})
    print('Teste final:', result['metrics']['f1_macro'], 'recall alto:', result['metrics']['recall_alto'])
    print('Bundle de inferência local gerado; sem publicação automática.')
    return result


if __name__ == '__main__':
    build()
