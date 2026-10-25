"""Identidade e integridade dos quatro arquivos do curso."""
from datetime import datetime, timezone
from pathlib import Path
import json

from .validation import sha256

COURSE_FILES = frozenset(('BDMEP-estacao.csv', 'MapBiomas.csv',
                          'BDMEP-2025.csv', 'queimadas_2024_2025.csv'))


def course_contract(config_path):
    config = json.loads(Path(config_path).read_text(encoding='utf-8'))
    files = config.get('files', {})
    if config.get('source') != 'course' or set(files) != COURSE_FILES:
        raise ValueError('Contrato deve identificar os quatro arquivos do curso.')
    if any(not isinstance(value, str) or len(value) != 64
           or any(c not in '0123456789abcdef' for c in value) for value in files.values()):
        raise ValueError('Hash inválido no contrato do curso.')
    return config


def create_course_manifest(raw_dir, config_path, destination):
    raw_dir = Path(raw_dir)
    config = course_contract(config_path)
    files = []
    for name, expected in config['files'].items():
        path = raw_dir / name
        if not path.is_file() or sha256(path) != expected:
            raise ValueError('Arquivo ausente ou divergente do curso: ' + name)
        files.append({'file': name, 'sha256': expected, 'bytes': path.stat().st_size})
    result = {'schema_version': 1, 'source': 'course',
              'contract_sha256': sha256(config_path), 'files': files,
              'verified_at': datetime.now(timezone.utc).isoformat(),
              'external_validation': 'not_applicable'}
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return result


def verify_course_manifest(manifest_path, raw_dir, config_path):
    config = course_contract(config_path)
    manifest = json.loads(Path(manifest_path).read_text(encoding='utf-8'))
    if manifest.get('source') != 'course' or manifest.get('contract_sha256') != sha256(config_path):
        raise ValueError('Manifesto não corresponde ao contrato do curso.')
    entries = manifest.get('files', [])
    if len(entries) != 4 or {x['file'] for x in entries} != COURSE_FILES:
        raise ValueError('Manifesto deve conter os quatro arquivos, sem duplicatas.')
    for entry in entries:
        path = Path(raw_dir) / entry['file']
        if (entry['sha256'] != config['files'][entry['file']] or not path.is_file()
                or sha256(path) != entry['sha256'] or path.stat().st_size != entry['bytes']):
            raise ValueError('Integridade inválida no arquivo do curso: ' + entry['file'])
    return manifest
