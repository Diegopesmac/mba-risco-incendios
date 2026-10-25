"""Vínculos entre fontes, contratos, preparação e painel."""
from pathlib import Path
import json

from .validation import sha256


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def verify_panel(root):
    folder = root / '.local/course'
    summary = read_json(folder / 'panel-summary.json')
    source = read_json(folder / 'manifest.json')
    preparation = read_json(folder / 'preparation.json')
    pairs = [(folder / 'panel.parquet', summary['panel_sha256']),
             (folder / 'manifest.json', summary['source_manifest_sha256']),
             (folder / 'preparation.json', summary['preparation_manifest_sha256']),
             (root / 'configs/course-data.json', source['contract_sha256']),
             (root / 'preparar_eda_queimadas.py', preparation['preparation_code_sha256']),
             (root / 'src/fire_risk/panel.py', summary['panel_code_sha256'])]
    if any(sha256(path) != expected for path, expected in pairs):
        raise ValueError('Fonte, código ou painel divergem da versão auditada.')
    return summary


def science_fingerprint(root):
    names = ('panel.py', 'training.py', 'optimization.py', 'assessment.py', 'metrics.py', 'finalization.py')
    return {name: sha256(root / 'src/fire_risk' / name) for name in names}
