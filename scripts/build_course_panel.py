"""Constrói painel do curso após conferir fontes e preparação."""
from pathlib import Path
import argparse
import json
import sys
import duckdb

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from fire_risk.course import verify_course_manifest
from fire_risk.panel import build_panel_frame, sql_path
from fire_risk.validation import sha256


def build(raw_dir):
    folder = ROOT / '.local/course'
    manifest = folder / 'manifest.json'
    verify_course_manifest(manifest, raw_dir, ROOT / 'configs/course-data.json')
    preparation = folder / 'preparation.json'
    evidence = json.loads(preparation.read_text(encoding='utf-8'))
    if (evidence['source_manifest_sha256'] != sha256(manifest)
            or evidence['preparation_code_sha256'] != sha256(ROOT / 'preparar_eda_queimadas.py')):
        raise ValueError('Preparação desatualizada em relação à fonte/código.')
    for name, expected in evidence['outputs'].items():
        if Path(name).name != name or sha256(folder / 'prepared' / name) != expected:
            raise ValueError('Derivado da preparação alterado ou inválido.')
    weather = folder / 'prepared/meteorologia_diaria.parquet'
    if weather.name not in evidence['outputs']:
        raise ValueError('Meteorologia ausente do manifesto da preparação.')
    frame, report = build_panel_frame(Path(raw_dir) / 'queimadas_2024_2025.csv', weather)
    output = folder / 'panel.parquet'
    with duckdb.connect() as con:
        con.register('panel', frame)
        con.execute(f'COPY panel TO {sql_path(output)} (FORMAT PARQUET, COMPRESSION ZSTD)')
    report.update({'source_manifest_sha256': sha256(manifest),
                   'preparation_manifest_sha256': sha256(preparation),
                   'panel_sha256': sha256(output),
                   'panel_code_sha256': sha256(ROOT / 'src/fire_risk/panel.py')})
    (folder / 'panel-summary.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: report[k] for k in ('rows', 'classes', 'splits')}, ensure_ascii=False))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--raw-dir', type=Path, required=True)
    build(parser.parse_args().raw_dir)
