"""HTTP real com modelo fornecido e encerramento do próprio servidor de teste."""
from pathlib import Path
import argparse
import json
import socket
import sys
import threading
import time

import uvicorn

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from fire_risk.api import create_app
from fire_risk.validation import sha256
from smoke_api import smoke


def build(bundle, request, port, output):
    listener = socket.socket()
    listener.bind(('127.0.0.1', port))
    listener.listen(32)
    server = uvicorn.Server(uvicorn.Config(create_app(bundle, sha256(bundle / 'manifest.json')),
        host='127.0.0.1', port=port, access_log=False, log_level='warning'))
    thread = threading.Thread(target=server.run, kwargs={'sockets':[listener]}, daemon=True)
    try:
        thread.start()
        for _ in range(100):
            if server.started:
                break
            if not thread.is_alive():
                raise RuntimeError('Servidor de teste não iniciou.')
            time.sleep(0.1)
        if not server.started:
            raise RuntimeError('Tempo limite de inicialização.')
        result = smoke(f'http://127.0.0.1:{port}', json.loads(request.read_text(encoding='utf-8')))
    finally:
        server.should_exit = True
        if thread.is_alive():
            thread.join(timeout=10)
        listener.close()
    if thread.is_alive():
        raise RuntimeError('Servidor de teste não encerrou.')
    result['test_server_stopped'] = True
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('HTTP real local validado e encerrado:', result['health']['model_id'])
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--bundle', type=Path, required=True)
    parser.add_argument('--request', type=Path, required=True)
    parser.add_argument('--port', type=int, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    build(args.bundle, args.request, args.port, args.output)
