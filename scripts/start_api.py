"""Inicializa a API com artefato explicitamente fornecido pelo operador."""
from pathlib import Path
import os
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from fire_risk.bundle import materialize


def main():
    payload = os.environ.get('MODEL_PAYLOAD_B64')
    if payload:
        directory = Path(os.environ.get('MODEL_DIR', str(Path(tempfile.gettempdir()) / 'fire-risk-model')))
        materialize(payload, os.environ.get('MODEL_MANIFEST_SHA256'), directory)
        os.environ['MODEL_DIR'] = str(directory)
    import uvicorn
    uvicorn.run('fire_risk.api:app', host=os.environ.get('HOST', '0.0.0.0'),
                port=int(os.environ.get('PORT', '8000')), access_log=False, workers=1)


if __name__ == '__main__':
    main()
