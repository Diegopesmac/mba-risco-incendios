"""Materializa somente um bundle confiável, configurado pelo operador do serviço."""
from pathlib import Path
import base64
import hashlib
import json


def materialize(payload, expected_manifest_sha256, destination):
    if not expected_manifest_sha256 or len(payload) > 1_000_000:
        raise ValueError('Bundle requer hash do manifesto e tamanho limitado.')
    packed = json.loads(base64.b64decode(payload, validate=True))
    manifest_bytes = packed['manifest_json'].encode('utf-8')
    if hashlib.sha256(manifest_bytes).hexdigest() != expected_manifest_sha256:
        raise ValueError('Manifesto do bundle inválido.')
    metadata = json.loads(manifest_bytes)
    model_bytes = base64.b64decode(packed['model_base64'], validate=True)
    if metadata.get('file') != 'model.joblib' or hashlib.sha256(model_bytes).hexdigest() != metadata['sha256']:
        raise ValueError('Modelo do bundle inválido.')
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    (destination / 'model.joblib').write_bytes(model_bytes)
    (destination / 'manifest.json').write_bytes(manifest_bytes)
    return destination


def encode_bundle(directory):
    directory = Path(directory)
    packed = {'manifest_json': (directory / 'manifest.json').read_bytes().decode('utf-8'),
              'model_base64': base64.b64encode((directory / 'model.joblib').read_bytes()).decode('ascii')}
    return base64.b64encode(json.dumps(packed, ensure_ascii=False).encode('utf-8')).decode('ascii')
