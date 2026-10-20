"""Diagnóstico do acervo por região/dia, sem criar negativos ou alvo."""
from collections import Counter
from datetime import date, timedelta
import csv
import io
import zipfile

# População fixa: unidades federativas do cadastro oficial do IBGE.
STATES = tuple(sorted(('ACRE|ALAGOAS|AMAPÁ|AMAZONAS|BAHIA|CEARÁ|DISTRITO FEDERAL|'
    'ESPÍRITO SANTO|GOIÁS|MARANHÃO|MATO GROSSO|MATO GROSSO DO SUL|MINAS GERAIS|'
    'PARÁ|PARAÍBA|PARANÁ|PERNAMBUCO|PIAUÍ|RIO DE JANEIRO|RIO GRANDE DO NORTE|'
    'RIO GRANDE DO SUL|RONDÔNIA|RORAIMA|SANTA CATARINA|SÃO PAULO|SERGIPE|TOCANTINS').split('|')))
REGISTRY_URL = 'https://servicodados.ibge.gov.br/api/v1/localidades/estados'
FIELDS = {'id_bdq', 'foco_id', 'lat', 'lon', 'data_pas', 'pais', 'estado', 'municipio', 'bioma'}


def diagnose_state_days(files_by_year, regions=STATES):
    """Um arquivo por ano; nenhum zero é inferido de um registro ausente."""
    regions = tuple(regions)
    if not regions or len(set(regions)) != len(regions):
        raise ValueError('População regional vazia ou repetida.')
    if not files_by_year:
        raise ValueError('Informar pelo menos um arquivo anual.')
    counts, national, seen = Counter(), Counter(), set()
    source_rows = 0
    for year, path in sorted(files_by_year.items()):
        with zipfile.ZipFile(path) as archive:
            members = [m for m in archive.infolist() if m.filename.lower().endswith('.csv')]
            if len(members) != 1:
                raise ValueError('Esperado exatamente um CSV por arquivo anual.')
            with archive.open(members[0]) as stream:
                reader = csv.DictReader(io.TextIOWrapper(stream, encoding='utf-8-sig'))
                if set(reader.fieldnames or []) != FIELDS or len(reader.fieldnames) != len(FIELDS):
                    raise ValueError('Esquema diferente do contrato INPE.')
                for row in reader:
                    if None in row or any(value is None or not value.strip() for value in row.values()):
                        raise ValueError('Linha incompleta no acervo.')
                    day = date.fromisoformat(row['data_pas'][:10])
                    if day.year != year or row['estado'] not in regions:
                        raise ValueError('Data ou região fora da população declarada.')
                    if row['id_bdq'] in seen:
                        raise ValueError('ID repetido entre os arquivos; revisar antes de agregar.')
                    seen.add(row['id_bdq'])
                    counts[(row['estado'], day)] += 1
                    national[day] += 1
                    source_rows += 1
    rows = []
    for year in sorted(files_by_year):
        day, end = date(year, 1, 1), date(year + 1, 1, 1)
        while day < end:
            for region in regions:
                count = counts[(region, day)]
                status = ('recorded_detection' if count else
                          'no_regional_record' if national[day] else 'national_archive_gap')
                rows.append({'state': region, 'date': day.isoformat(),
                             'recorded_detection_count': count if count else None,
                             'archive_status': status, 'coverage_status': 'unverified'})
            day += timedelta(days=1)
    statuses = Counter(row['archive_status'] for row in rows)
    return rows, {'source_detection_rows': source_rows, 'region_count': len(regions),
                  'calendar_region_days': len(rows), 'archive_status_counts': dict(statuses),
                  'regions': list(regions), 'years': sorted(files_by_year),
                  'target_created': False, 'training_authorized': False,
                  'national_days_without_records': sorted({row['date'] for row in rows
                      if row['archive_status'] == 'national_archive_gap'}),
                  'date_convention': 'Data do campo data_pas; não comprova horário de disponibilidade.',
                  'limitation': 'Calendário candidato não é painel supervisionado. Cobertura regional não comprovada.'}
