"""Prepara evidência estrutural para a Entrega 0; não treina modelos."""
from pathlib import Path
import argparse
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from fire_risk.sources import candidate_manifest

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--years', nargs='+', type=int, default=[2023, 2024, 2025])
    args = parser.parse_args()
    result = candidate_manifest(args.years, ROOT / '.local/candidates/inpe')
    for item in result['files']:
        print(item['file'], item['rows'], item['first_date'], item['last_date'])
    print('Entrega 0 em preparação. Alvo e aprovação da tutoria continuam pendentes.')
