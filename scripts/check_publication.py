"""Checagem local do recorte versionado; nunca imprime conteúdo suspeito."""
from pathlib import Path
import argparse
import json
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BLOCKED_PARTS = {'.local', '.env', 'data', 'models', 'outputs', 'dados_brutos_queimadas',
                 'eda_queimadas', 'auditoria_queimadas', '__pycache__', '.deps_queimadas'}
BLOCKED_SUFFIXES = {'.csv', '.zip', '.parquet', '.duckdb', '.sqlite', '.pkl', '.joblib'}
PATTERNS = [re.compile(p) for p in [
    r'gh[pousr]_[A-Za-z0-9]{30,}', r'github_pat_[A-Za-z0-9_]{40,}',
    r'AKIA[0-9A-Z]{16}', r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',
    r'(?i)(?:api_key|access_token|password)\s*[:=]\s*[\x22\x27][A-Za-z0-9_\-/+=]{24,}[\x22\x27]',
    r'(?i)C:[\\/]+Users[\\/]+',
]]


def check_file(root, name, contents=None):
    path = root / name
    if any(part in BLOCKED_PARTS for part in Path(name).parts) or path.suffix.lower() in BLOCKED_SUFFIXES:
        return ['caminho ou formato local não publicável']
    if contents is None and not path.is_file():
        return []
    if contents is None:
        contents = path.read_bytes()
    if len(contents) > 5_000_000:
        return ['arquivo maior que o limite de revisão de 5 MB']
    try:
        content = contents.decode('utf-8')
    except UnicodeDecodeError:
        return ['binário não permitido neste recorte inicial']
    errors = []
    for line_number, line in enumerate(content.splitlines(), 1):
        if any(pattern.search(line) for pattern in PATTERNS):
            errors.append(f'conteúdo suspeito na linha {line_number}; valor omitido')
    if path.suffix == '.ipynb':
        notebook = json.loads(content)
        if any(c.get('outputs') or c.get('execution_count') is not None for c in notebook['cells'] if c['cell_type'] == 'code'):
            errors.append('notebook com saídas; revisar e limpar antes do push')
    return errors


def main(staged=False):
    command = ['git', 'diff', '--cached', '--name-only', '--diff-filter=ACMR', '-z'] if staged else ['git', 'ls-tree', '-r', '--name-only', '-z', 'HEAD']
    names = subprocess.check_output(command, cwd=ROOT).decode('utf-8').strip('\0').split('\0')
    findings = []
    for name in filter(None, names):
        revision = ':' + name if staged else 'HEAD:' + name
        contents = subprocess.check_output(['git', 'show', revision], cwd=ROOT)
        findings.extend((name, error) for error in check_file(ROOT, name, contents))
    for name, error in findings:
        print(f'{name}: {error}')
    if findings:
        raise SystemExit(1)
    print('Recorte versionado verificado; esta checagem não garante ausência de todo dado sensível.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--staged', action='store_true')
    main(parser.parse_args().staged)
