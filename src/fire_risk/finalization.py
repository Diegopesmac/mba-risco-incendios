"""Congela decisões antes de ler o teste; preserva avaliação final única."""
from datetime import datetime, timezone
from pathlib import Path
from importlib.metadata import version

import duckdb
import joblib
from sklearn.base import clone
from threadpoolctl import threadpool_limits

from .artifacts import read_json, write_json, verify_panel, science_fingerprint
from .validation import sha256
from .panel import FEATURES, LABELS
from .metrics import prediction_metrics, grouped_metrics, bootstrap_days
from .assessment import simulated_cost, cost_sensitivity


def freeze(root):
    folder = root / '.local/course'
    destination = folder / 'final'
    path = destination / 'freeze.json'
    if path.exists():
        return verify_freeze(root)
    summary = verify_panel(root)
    report_path = folder / 'optimization/results.json'
    report = read_json(report_path)
    if (report['panel_sha256'] != summary['panel_sha256']
            or report['plan_sha256'] != sha256(root / 'configs/evaluation-plan.json')
            or report['code_sha256'] != science_fingerprint(root)):
        raise ValueError('Otimização desatualizada; não congelar outra versão.')
    with duckdb.connect() as con:
        development = con.execute("SELECT * FROM read_parquet(?) WHERE split IN ('train','validation')",
                                   [str(folder / 'panel.parquet')]).df()
    destination.mkdir(exist_ok=True)
    artifacts = {}
    with threadpool_limits(limits=1):
        for name in (report['selected'], 'referencia'):
            entry = report['artifacts'][name]
            source = folder / 'optimization' / entry['file']
            if source.name != entry['file'] or sha256(source) != entry['sha256']:
                raise ValueError('Artefato de desenvolvimento divergente.')
            model = clone(joblib.load(source))
            model.fit(development[list(FEATURES)], development['target'])
            output = destination / (name + '.joblib')
            joblib.dump(model, output, compress=3)
            artifacts[name] = {'file': output.name, 'sha256': sha256(output)}
    result = {'schema_version': 1, 'frozen_at': datetime.now(timezone.utc).isoformat(),
              'selected': report['selected'], 'features': list(FEATURES), 'labels': list(LABELS),
              'development_rows': len(development), 'artifacts': artifacts,
              'panel_sha256': summary['panel_sha256'], 'optimization_sha256': sha256(report_path),
              'plan_sha256': report['plan_sha256'], 'code_sha256': science_fingerprint(root),
              'versions': {p: version(p) for p in ('scikit-learn', 'numpy', 'scipy', 'joblib', 'optuna')},
              'target_contract_sha256': sha256(root / 'docs/data-contract.md'),
              'operational_use_validated': False}
    write_json(path, result)
    return result


def verify_freeze(root):
    folder = root / '.local/course'
    record = read_json(folder / 'final/freeze.json')
    summary = verify_panel(root)
    if (record['panel_sha256'] != summary['panel_sha256']
            or record['plan_sha256'] != sha256(root / 'configs/evaluation-plan.json')
            or record['optimization_sha256'] != sha256(folder / 'optimization/results.json')
            or record['target_contract_sha256'] != sha256(root / 'docs/data-contract.md')
            or record['code_sha256'] != science_fingerprint(root)):
        raise ValueError('Congelamento alterado; não reutilizar teste ou modelo sob outro protocolo.')
    for entry in record['artifacts'].values():
        if entry['file'] != Path(entry['file']).name:
            raise ValueError('Nome de artefato inválido.')
        if sha256(folder / 'final' / entry['file']) != entry['sha256']:
            raise ValueError('Modelo final diverge do hash congelado.')
    return record


def evaluate_once(root):
    folder = root / '.local/course'
    record = verify_freeze(root)
    destination = folder / 'final/evaluation.json'
    fingerprint = sha256(folder / 'final/freeze.json')
    if destination.exists():
        previous = read_json(destination)
        if previous['freeze_sha256'] != fingerprint:
            raise ValueError('Avaliação existente pertence a outro congelamento.')
        return previous
    plan = read_json(root / 'configs/evaluation-plan.json')
    with duckdb.connect() as con:
        test = con.execute("SELECT * FROM read_parquet(?) WHERE split='test'",
                            [str(folder / 'panel.parquet')]).df()
    model = joblib.load(folder / 'final' / record['artifacts'][record['selected']]['file'])
    reference = joblib.load(folder / 'final' / record['artifacts']['referencia']['file'])
    with threadpool_limits(limits=1):
        predicted = model.predict(test[list(FEATURES)])
        baseline = reference.predict(test[list(FEATURES)])
        metrics = prediction_metrics(test['target'], predicted, model.predict_proba(test[list(FEATURES)]), model.classes_)
    result = {'freeze_sha256': fingerprint, 'selected': record['selected'], 'test_evaluated': True,
              'metrics': metrics, 'reference': prediction_metrics(test['target'], baseline),
              'groups': grouped_metrics(test, predicted),
              'uncertainty': bootstrap_days(test, predicted, plan['bootstrap_day_samples'], plan['seed']),
              'simulated_cost': simulated_cost(test['target'], predicted, plan['cost_scenario']),
              'reference_simulated_cost': simulated_cost(test['target'], baseline, plan['cost_scenario']),
              'cost_sensitivity': cost_sensitivity(test['target'], predicted, baseline, plan['cost_scenario']),
              'operational_use_validated': False}
    write_json(destination, result)
    return result
