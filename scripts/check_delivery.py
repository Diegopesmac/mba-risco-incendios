"""Verifica os requisitos de entrada da fonte selecionada."""
from pathlib import Path
import argparse
import json
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from fire_risk.validation import require_tutor_approval
from fire_risk.course import verify_course_manifest


def check(config, raw_dir=None):
    if config.get('path') == '2' and config.get('data_source') == 'course':
        if raw_dir is None:
            raise ValueError('Informar --raw-dir para conferir os arquivos do curso.')
        verify_course_manifest(ROOT / '.local/course/manifest.json', raw_dir,
                               ROOT / 'configs/course-data.json')
        return 'Arquivos do curso conferidos. Entrega 0 não aplicável; revisões das entregas permanecem obrigatórias.'
    if config.get('path') == '4' and config.get('data_source', 'external') == 'external':
        require_tutor_approval(ROOT / '.local/approvals/entrega0.json', ROOT / '.local/candidates/manifest.json')
        return 'Registro acadêmico presente e vinculado ao manifesto. Conferir a evidência humana de aprovação.'
    raise ValueError('Caminho e fonte incompatíveis ou não suportados.')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--raw-dir', type=Path)
    args = parser.parse_args()
    try:
        result = check(json.loads((ROOT / 'configs/delivery-status.json').read_text(encoding='utf-8')), args.raw_dir)
    except (ValueError, FileNotFoundError) as error:
        print(error)
        raise SystemExit(2)
    print(result)
