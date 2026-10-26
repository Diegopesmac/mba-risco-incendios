"""Entrada compatível para gerar os notebooks atuais da entrega acadêmica."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent / 'scripts'))
from build_submission import build

if __name__ == '__main__':
    build()
