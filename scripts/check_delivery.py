"""Separa validação de software de autorização acadêmica para modelagem."""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from fire_risk.validation import require_tutor_approval

if __name__ == '__main__':
    try:
        require_tutor_approval(ROOT / '.local/approvals/entrega0.json', ROOT / '.local/candidates/manifest.json')
    except (ValueError, FileNotFoundError) as error:
        print(error)
        raise SystemExit(2)
    print('Registro acadêmico presente e vinculado ao manifesto. Conferir a evidência humana de aprovação.')
