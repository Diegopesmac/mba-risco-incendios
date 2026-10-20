"""Aquisição e perfil estrutural de arquivos anuais públicos do INPE."""
from pathlib import Path
import csv
import io
import json
import urllib.request
import zipfile
from collections import Counter
from datetime import date, timedelta
from .validation import sha256

INPE_BASE = 'https://dataserver-coids.inpe.br/queimadas/queimadas/focos/csv/anual/Brasil_sat_ref/'


def download_reference(year, destination):
    if year not in range(2003, 2026):
        raise ValueError('Ano fora da série verificada; conferir a fonte antes de ampliar.')
    path = Path(destination) / f'focos_br_ref_{year}.zip'
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        part = path.with_suffix('.zip.part')
        with urllib.request.urlopen(INPE_BASE + path.name, timeout=60) as response, part.open('wb') as output:
            if response.status != 200:
                raise ValueError('A fonte não retornou um arquivo disponível.')
            while block := response.read(1024 * 1024):
                output.write(block)
        if not zipfile.is_zipfile(part):
            raise ValueError('Resposta não é um ZIP válido; arquivo parcial preservado para revisão.')
        part.replace(path)
    return path


def profile_reference(path):
    path = Path(path)
    count, dates, states, missing, ids = 0, Counter(), Counter(), Counter(), set()
    duplicate_ids = 0
    with zipfile.ZipFile(path) as archive:
        members = [m for m in archive.infolist() if m.filename.lower().endswith('.csv')]
        if len(members) != 1:
            raise ValueError('A estrutura do arquivo mudou: esperado exatamente um CSV.')
        with archive.open(members[0]) as stream:
            reader = csv.DictReader(io.TextIOWrapper(stream, encoding='utf-8-sig'))
            required = {'id_bdq', 'foco_id', 'lat', 'lon', 'data_pas', 'pais', 'estado', 'municipio', 'bioma'}
            if set(reader.fieldnames or []) != required:
                raise ValueError('O esquema do arquivo difere do contrato auditado.')
            for row in reader:
                count += 1
                for key, value in row.items():
                    missing[key] += int(not value)
                dates[row['data_pas'][:10]] += 1
                states[row['estado']] += 1
                if row['id_bdq'] in ids:
                    duplicate_ids += 1
                ids.add(row['id_bdq'])
    first, last = date.fromisoformat(min(dates)), date.fromisoformat(max(dates))
    calendar = [first + timedelta(days=i) for i in range((last-first).days+1)]
    missing_dates = [day.isoformat() for day in calendar if day.isoformat() not in dates]
    return {'file': path.name, 'source_url': INPE_BASE + path.name,
            'sha256': sha256(path), 'bytes': path.stat().st_size, 'rows': count,
            'columns': sorted(required), 'first_date': min(dates), 'last_date': max(dates),
            'days_with_records': len(dates), 'empty_fields': dict(missing),
            'calendar_days_without_records': missing_dates,
            'repeated_id_bdq': duplicate_ids, 'states': dict(states),
            'target': 'not_defined', 'tutor_approval': 'pending',
            'limitations': 'Detecção registrada não equivale a incêndio independente; zero registros não comprova ausência física de fogo.'}


def candidate_manifest(years, destination):
    destination = Path(destination)
    results = [profile_reference(download_reference(year, destination)) for year in years]
    payload = {'schema_version': 1, 'candidate': 'inpe-reference', 'files': results,
               'total_detection_rows': sum(r['rows'] for r in results),
               'training_authorized': False, 'target_status': 'proposal_pending_tutor'}
    output = destination.parent / 'manifest.json'
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return payload
