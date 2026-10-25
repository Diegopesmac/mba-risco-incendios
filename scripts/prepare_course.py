"""Verifica os arquivos do curso e executa sua preparação exploratória."""
from pathlib import Path
import argparse
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT))
from fire_risk.course import create_course_manifest, verify_course_manifest
from fire_risk.validation import sha256
from preparar_eda_queimadas import prepare


def build(raw_dir):
    manifest = ROOT / '.local/course/manifest.json'
    config = ROOT / 'configs/course-data.json'
    create_course_manifest(raw_dir, config, manifest)
    result = prepare(ROOT, raw_dir=raw_dir, output_dir=ROOT / '.local/course/prepared')
    verify_course_manifest(manifest, raw_dir, config)
    prepared = ROOT / '.local/course/prepared'
    evidence = {'source_manifest_sha256': sha256(manifest),
                'preparation_code_sha256': sha256(ROOT / 'preparar_eda_queimadas.py'),
                'outputs': {p.name: sha256(p) for p in prepared.iterdir()
                            if p.suffix in ('.json', '.parquet')}}
    (manifest.parent / 'preparation.json').write_text(
        json.dumps(evidence, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--raw-dir', type=Path, required=True)
    build(parser.parse_args().raw_dir)
