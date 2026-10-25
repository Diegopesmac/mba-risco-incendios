"""Bundle exclusivamente fictício para testar API e container sem dados reais."""
from importlib.metadata import version
from pathlib import Path
import argparse
import sys

import joblib
import pandas as pd
from sklearn.linear_model import LogisticRegression
from threadpoolctl import threadpool_limits

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from fire_risk.artifacts import write_json
from fire_risk.panel import FEATURES, LABELS
from fire_risk.validation import sha256


def create(directory):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    frame = pd.DataFrame([{name: float(i % 3 + j) for j, name in enumerate(FEATURES)} for i in range(30)])
    with threadpool_limits(limits=1):
        model = LogisticRegression(max_iter=1000).fit(frame, [LABELS[i % 3] for i in range(30)])
    joblib.dump(model, directory / 'model.joblib')
    write_json(directory / 'manifest.json', {
        'file': 'model.joblib', 'sha256': sha256(directory / 'model.joblib'),
        'model_id': 'synthetic-ci-only', 'selected': 'synthetic-ci-only',
        'features': list(FEATURES), 'labels': list(LABELS),
        'versions': {'scikit-learn': version('scikit-learn')},
        'training_ranges': {key: [float(frame[key].min()), float(frame[key].max())] for key in FEATURES},
        'municipalities': ['0000000'], 'synthetic': True})
    return directory


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    create(parser.parse_args().output)
    print('Bundle fictício de CI criado.')
