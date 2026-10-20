"""Concilia arquivos auditados e produz diagnóstico local da candidata UF/dia."""
from pathlib import Path
import csv
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from fire_risk.coverage import diagnose_state_days, REGISTRY_URL
from fire_risk.validation import sha256


def build():
    folder = ROOT / '.local/candidates'
    manifest_path = folder / 'manifest.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    files, expected_rows = {}, 0
    for item in manifest['files']:
        match = re.fullmatch(r'focos_br_ref_(\d{4})\.zip', item['file'])
        if not match or int(match[1]) in files:
            raise ValueError('Manifesto com nome inesperado ou ano repetido.')
        path = folder / 'inpe' / item['file']
        if sha256(path) != item['sha256']:
            raise ValueError('Arquivo diverge do hash auditado; interrompido.')
        files[int(match[1])] = path
        expected_rows += item['rows']
    rows, report = diagnose_state_days(files)
    if report['source_detection_rows'] != expected_rows or expected_rows != manifest['total_detection_rows']:
        raise ValueError('Contagens do diagnóstico divergem do manifesto.')
    output = folder / 'state-days.csv'
    with output.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    report.update({'schema_version': 1, 'manifest_sha256': sha256(manifest_path),
                   'population_source': REGISTRY_URL, 'output_sha256': sha256(output),
                   'input_sha256': {item['file']: item['sha256'] for item in manifest['files']}})
    (folder / 'state-days-summary.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({key: report[key] for key in ('source_detection_rows', 'calendar_region_days',
                     'region_count', 'archive_status_counts', 'target_created')}, ensure_ascii=False))
    return report


if __name__ == '__main__':
    build()
