"""Empacota a revisão Git com notebooks executados e painel auditado."""
from pathlib import Path
import hashlib
import io
import json
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from fire_risk.submission import NOTEBOOKS, verify_submission


def build():
    verify_submission(ROOT)
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip()
    archived = subprocess.check_output(['git', 'archive', '--format=zip', 'HEAD'], cwd=ROOT)
    with zipfile.ZipFile(io.BytesIO(archived)) as source:
        entries = {n: source.read(n) for n in source.namelist() if not n.endswith('/')
                   and not n.startswith(('.github/', 'reports/entrega-0/'))}
    for name in [*NOTEBOOKS, 'submission/painel_modelagem.csv', 'submission/manifest.json']:
        local = (ROOT / name).read_bytes()
        equal = json.loads(entries[name]) == json.loads(local) if name.endswith('.ipynb') else entries[name] == local
        if not equal:
            raise ValueError('Commit e entrega local divergem: ' + name)
    entries['LEIA-ME.txt'] = (
        f'Entrega acadêmica — Caminho 2\nCódigo: {revision}\n\n'
        'Leia README.md para a ordem dos quatro notebooks executados.\n'
        'Base consolidada: submission/painel_modelagem.csv; dicionário: docs/data-dictionary.md.\n'
        'Notebook 02 contém distribuição, correlações e hipótese, somente no treino.\n'
        'A apresentação executa com os arquivos incluídos, sem CSVs brutos ou modelos binários.\n'
        'Instale requirements.txt e abra o notebook dentro do clone ou pasta extraída.\n'
        'A reconstrução desde os quatro CSVs originais é uma rotina separada no README.\n'
        'Modelo e teste permanecem congelados; não reotimizar com o teste observado.\n'
        'API: https://mba-risco-incendios.onrender.com/docs\n'
        'Não houve submissão ou aprovação acadêmica; o estudante realiza o envio.\n'
    ).encode('utf-8')
    entries['SHA256SUMS.txt'] = ''.join(
        f'{hashlib.sha256(data).hexdigest()}  {name}\n' for name, data in sorted(entries.items())
    ).encode('utf-8')
    output = ROOT / '.local/deliveries/MBA-caminho2-entrega-tecnica.zip'
    output.parent.mkdir(exist_ok=True, parents=True)
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as archive:
        for name, data in sorted(entries.items()):
            archive.writestr(name, data)
    with zipfile.ZipFile(output) as archive:
        if archive.testzip() is not None:
            raise ValueError('ZIP inválido.')
        for line in archive.read('SHA256SUMS.txt').decode().splitlines():
            expected, name = line.split('  ', 1)
            if hashlib.sha256(archive.read(name)).hexdigest() != expected:
                raise ValueError('Hash divergente no ZIP: ' + name)
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    output.with_suffix('.zip.sha256').write_text(f'{digest}  {output.name}\n', encoding='utf-8')
    print('Pacote íntegro:', len(entries), 'arquivos; SHA-256:', digest)


if __name__ == '__main__':
    build()
