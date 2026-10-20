"""Auditoria estrutural dos CSVs do projeto final. Não limpa nem treina modelos."""
from collections import Counter
from pathlib import Path
import hashlib
import json

import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
FILES = ['BDMEP-estacao.csv', 'MapBiomas.csv', 'BDMEP-2025.csv', 'queimadas_2024_2025.csv']
KEYS = {
    'BDMEP-estacao.csv': ['id_estacao'],
    'MapBiomas.csv': ['ano', 'id_municipio', 'id_classe'],
    'BDMEP-2025.csv': ['id_estacao', 'data', 'hora'],
}
TEXT_COLUMNS = {
    'id_municipio', 'id_municipio_nome', 'id_estacao', 'estacao', 'sigla_uf',
    'sigla_uf_nome', 'bioma', 'satelite', 'id_classe', 'data', 'data_hora',
    'data_fundacao', 'hora',
}


def profile(path, chunksize=100_000):
    info = {'arquivo': path.name, 'bytes': path.stat().st_size, 'linhas': 0}
    with path.open(encoding='utf-8-sig') as file:
        header = file.readline()
    separator = ';' if header.count(';') > header.count(',') else ','
    info['separador'] = separator
    digest = hashlib.sha256()
    with path.open('rb') as file:
        for block in iter(lambda: file.read(4 * 1024 * 1024), b''):
            digest.update(block)
    info['sha256'] = digest.hexdigest()
    missing, values, numeric, dates = Counter(), {}, {}, {}
    row_hashes, key_hashes = [], []
    for chunk in pd.read_csv(path, sep=separator, dtype='string', keep_default_na=False, chunksize=chunksize):
        if 'colunas' not in info:
            info['colunas'] = list(chunk.columns)
        info['linhas'] += len(chunk)
        missing.update({c: int(chunk[c].eq('').sum()) for c in chunk})
        row_hashes.append(pd.util.hash_pandas_object(chunk, index=False).to_numpy())
        keys = KEYS.get(path.name)
        if keys:
            key_hashes.append(pd.util.hash_pandas_object(chunk[keys], index=False).to_numpy())
        for col in ['ano', 'sigla_uf', 'id_municipio', 'id_estacao', 'id_classe', 'bioma', 'satelite']:
            if col in chunk:
                values.setdefault(col, Counter()).update(chunk[col].value_counts().to_dict())
        for col in ['data', 'data_hora', 'data_fundacao']:
            if col not in chunk:
                continue
            # ISO date prefixes suffice for coverage; no timezone conversion is performed.
            parsed = pd.to_datetime(chunk[col].str[:10], format='%Y-%m-%d', errors='coerce')
            valid = parsed.dropna()
            st = dates.setdefault(col, {'min': None, 'max': None, 'invalidos_nao_vazios': 0})
            st['invalidos_nao_vazios'] += int((parsed.isna() & chunk[col].ne('')).sum())
            if len(valid):
                lo, hi = valid.min().strftime('%Y-%m-%d'), valid.max().strftime('%Y-%m-%d')
                st['min'] = min(st['min'] or lo, lo)
                st['max'] = max(st['max'] or hi, hi)
        for col in chunk:
            if col in TEXT_COLUMNS:
                continue
            x = pd.to_numeric(chunk[col].replace('', pd.NA), errors='coerce')
            st = numeric.setdefault(col, {'min': None, 'max': None, 'negativos': 0, 'invalidos_nao_vazios': 0})
            st['negativos'] += int(x.lt(0).sum())
            st['invalidos_nao_vazios'] += int((x.isna() & chunk[col].ne('')).sum())
            valid = x.dropna()
            if len(valid):
                lo, hi = float(valid.min()), float(valid.max())
                st['min'] = min(st['min'] if st['min'] is not None else lo, lo)
                st['max'] = max(st['max'] if st['max'] is not None else hi, hi)
    hashes = np.concatenate(row_hashes)
    info['duplicatas_hash64'] = int(len(hashes) - len(np.unique(hashes)))
    if key_hashes:
        hashes = np.concatenate(key_hashes)
        info['chave_candidata'] = KEYS[path.name]
        info['repeticoes_chave_hash64'] = int(len(hashes) - len(np.unique(hashes)))
    info['vazios'] = dict(missing)
    info['datas'] = dates
    info['numericos'] = numeric
    info['categorias'] = {c: dict(v) for c, v in values.items()}
    return info


def audit(root=BASE_DIR):
    source = root / 'dados_brutos_queimadas'
    paths = [source / name for name in FILES]
    absent = [p.name for p in paths if not p.is_file()]
    if absent:
        raise FileNotFoundError('CSVs ainda ausentes: ' + ', '.join(absent))
    results = []
    for path in paths:
        print('Auditando:', path.name, flush=True)
        results.append(profile(path))
        print('Linhas:', results[-1]['linhas'], flush=True)
    station = pd.read_csv(paths[0], dtype='string', keep_default_na=False)
    measured = set(results[2]['categorias'].get('id_estacao', {})) - {''}
    catalog = set(station.id_estacao) - {''}
    weather_municipalities = set(station.loc[station.id_estacao.isin(measured), 'id_municipio']) - {''}
    fire_municipalities = set(results[3]['categorias'].get('id_municipio', {})) - {''}
    land_municipalities = set(results[1]['categorias'].get('id_municipio', {})) - {''}
    joins = {
        'estacoes_medidas': len(measured),
        'estacoes_medidas_sem_cadastro': sorted(measured - catalog),
        'municipios_com_estacao_medida': len(weather_municipalities),
        'municipios_queimadas': len(fire_municipalities),
        'municipios_mapbiomas': len(land_municipalities),
        'municipios_intersecao_tres_fontes': len(weather_municipalities & fire_municipalities & land_municipalities),
    }
    output = root / 'auditoria_queimadas'
    output.mkdir(exist_ok=True)
    payload = {'bases': results, 'ligacoes': joins,
               'metodo': 'Varredura integral em blocos. Vazios = campos vazios; códigos sentinela não são imputados. Duplicatas estimadas por hash de 64 bits, sem verificação de colisões. Nenhuma linha foi removida.'}
    (output / 'perfil_bases.json').write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    lines = ['# Auditoria inicial — bases de queimadas', '',
             'Varredura integral dos quatro arquivos; etapa estrutural, anterior à limpeza, definição final do alvo e modelagem.', '',
             '| Arquivo | Linhas | Colunas | Duplicatas por hash |', '|---|---:|---:|---:|']
    for item in results:
        lines.append(f"| {item['arquivo']} | {item['linhas']:,} | {len(item['colunas'])} | {item['duplicatas_hash64']:,} |")
    lines += ['', '## Cobertura e qualidade']
    for item in results:
        lines += ['', '### ' + item['arquivo'], '',
                  '- Datas: ' + json.dumps(item['datas'], ensure_ascii=False),
                  '- Anos observados: ' + ', '.join(sorted(item['categorias'].get('ano', {}))),
                  '- Campos vazios: ' + json.dumps({c: n for c, n in item['vazios'].items() if n}, ensure_ascii=False),
                  '- Repetições da chave candidata por hash: ' + str(item.get('repeticoes_chave_hash64', 'não definida'))]
    lines += ['', '## Ligações entre bases', '', '```json', json.dumps(joins, ensure_ascii=False, indent=2), '```', '',
              '## Limitações desta auditoria', '',
              '- Contagens de duplicatas usam hash de 64 bits; confirmar igualdade das linhas candidatas antes de excluir dados.',
              '- Cobertura de datas não comprova observações completas em todos os dias ou municípios.',
              '- Esta auditoria não valida o significado científico do alvo ou das unidades.',
              '- Valores negativos foram contados no JSON e precisam de interpretação por variável, sem remoção automática.',
              '- Ausência de detecção não é prova de ausência de incêndio; não foi criada classe de baixo risco.',
              '- A interseção municipal não comprova cobertura diária; não houve junção nem imputação.',
              '- Não houve treino, seleção de modelos ou avaliação de desempenho.']
    (output / 'RELATORIO_AUDITORIA.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    add_findings(payload, output)
    print(json.dumps({'bases': [{k: b[k] for k in ['arquivo', 'linhas', 'duplicatas_hash64', 'datas']} for b in results], 'ligacoes': joins}, ensure_ascii=False, indent=2))
    return payload


def add_findings(payload, output):
    """Acrescenta conclusões rastreáveis, sem repetir a varredura dos arquivos."""
    by_name = {b['arquivo']: b for b in payload['bases']}
    fire = by_name['queimadas_2024_2025.csv']
    weather = by_name['BDMEP-2025.csv']
    land = by_name['MapBiomas.csv']
    start = max(fire['datas']['data_hora']['min'], weather['datas']['data']['min'])
    end = min(fire['datas']['data_hora']['max'], weather['datas']['data']['max'])
    days = max(0, (pd.Timestamp(end) - pd.Timestamp(start)).days + 1)
    marker = '\n## Achados que afetam a modelagem\n'
    path = output / 'RELATORIO_AUDITORIA.md'
    base = path.read_text(encoding='utf-8').split(marker)[0]
    items = [
        f'1. Sobreposição das datas extremas: **{start} a {end}, {days} dias**. Isso não comprova cobertura contínua. Não preencher o período posterior ao fim do arquivo de queimadas como ausência de fogo.',
        f"2. Meteorologia: **{weather['duplicatas_hash64']:,} repetições por hash ({100 * weather['duplicatas_hash64'] / weather['linhas']:.2f}%)**; a chave estação/data/hora também se repete. Investigar igualdade exata e divergências por chave antes de deduplicar ou agregar.",
        f"3. MapBiomas: **{len(land['categorias']['id_classe'])} códigos de classe**, incluindo 0, 15, 33 e 62. O dicionário recebido descreve somente 1 a 7; ele não corresponde aos códigos observados. Obter coleção e legenda corretas antes de atribuir significados.",
        f"4. MapBiomas termina em **{max(land['categorias']['ano'])}**. Seu uso em 2025 deve ser identificado como informação histórica, com disponibilidade de publicação verificada.",
        f"5. São **{len(payload['ligacoes']['estacoes_medidas_sem_cadastro'])} estações medidas sem cadastro** e **{payload['ligacoes']['municipios_intersecao_tres_fontes']} municípios na interseção nominal**. A ligação por município restringe a cobertura; associação por distância exige decisão e validação próprias.",
        f"6. Queimadas: risco_fogo apresenta mínimo **{fire['numericos']['risco_fogo']['min']}** e dias_sem_chuva mínimo **{fire['numericos']['dias_sem_chuva']['min']}**. Valores -999 são candidatos a códigos de ausência, a confirmar na documentação; não são risco ou dias válidos.",
        f"7. O arquivo contém **{len(fire['categorias']['satelite'])} nomes de satélite/algoritmo**. Linhas são detecções: não equivalem necessariamente a incêndios independentes. Definir tratamento de múltiplas observações do mesmo evento.",
        '8. As classes baixo/médio/alto ainda não estão definidas. Usar risco_fogo como alvo significaria reproduzir um índice existente; construir classes a partir de ocorrência é outro problema. Confirmar a interpretação esperada com a tutoria antes de rotular.',
        '9. Para previsão antecipada, potência radiativa e medidas obtidas somente na detecção não podem entrar como variáveis explicativas. Meteorologia do dia completo também não está disponível no início desse dia.',
    ]
    path.write_text(base + marker + '\n' + '\n\n'.join(items) + '\n', encoding='utf-8')


if __name__ == '__main__':
    audit()
