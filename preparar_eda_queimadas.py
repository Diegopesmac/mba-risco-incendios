"""Preparação exploratória, sem alvo, imputação ou treinamento."""
from pathlib import Path
import sys
import json

ROOT = Path(__file__).resolve().parent
if (ROOT / '.deps_queimadas').exists():
    sys.path.insert(0, str(ROOT / '.deps_queimadas'))
import duckdb


def sqlpath(path):
    return "'" + path.as_posix().replace("'", "''") + "'"


def export(con, query, path):
    con.execute(f'COPY ({query}) TO {sqlpath(path)} (FORMAT PARQUET, COMPRESSION ZSTD)')


def prepare(root=ROOT):
    raw = root / 'dados_brutos_queimadas'
    out = root / 'eda_queimadas'
    out.mkdir(exist_ok=True)
    con = duckdb.connect(str(out / 'preparacao.duckdb'))
    con.execute("SET memory_limit='1GB'")
    con.execute('SET threads=4')
    con.execute(f"SET temp_directory={sqlpath(out / 'temporarios')}")
    read_weather = f"read_csv({sqlpath(raw / 'BDMEP-2025.csv')}, header=true, delim=',', all_varchar=true)"
    print('Confirmando duplicatas por igualdade de todas as colunas...', flush=True)
    total = con.execute(f'SELECT count(*) FROM {read_weather}').fetchone()[0]
    con.execute(f'CREATE OR REPLACE TABLE meteo_distinta AS SELECT DISTINCT * FROM {read_weather}')
    distinct = con.execute('SELECT count(*) FROM meteo_distinta').fetchone()[0]
    con.execute('''CREATE OR REPLACE TABLE chaves_multiplas AS
        SELECT id_estacao, data, hora, count(*) AS variantes
        FROM meteo_distinta GROUP BY ALL HAVING count(*) > 1''')
    multiple_keys, multiple_rows = con.execute('SELECT count(*), coalesce(sum(variantes),0) FROM chaves_multiplas').fetchone()
    con.execute('''CREATE OR REPLACE TABLE meteo_inequivoca AS
        SELECT * FROM meteo_distinta
        QUALIFY count(*) OVER (PARTITION BY id_estacao, data, hora) = 1''')
    kept = con.execute('SELECT count(*) FROM meteo_inequivoca').fetchone()[0]
    assert total >= distinct and distinct == kept + multiple_rows
    export(con, 'SELECT d.* FROM meteo_distinta d JOIN chaves_multiplas USING(id_estacao,data,hora)',
           out / 'meteorologia_horarios_multiplos.parquet')
    print('Agregando observações inequívocas por estação e dia...', flush=True)
    station_reader = f"read_csv({sqlpath(raw / 'BDMEP-estacao.csv')}, header=true, all_varchar=true)"
    con.execute(f'CREATE OR REPLACE VIEW estacoes AS SELECT * FROM {station_reader}')
    invalid_times = con.execute('''SELECT count(*) FROM meteo_inequivoca
        WHERE try_cast(data AS DATE) IS NULL OR try_cast(hora AS TIME) IS NULL OR id_estacao IS NULL''').fetchone()[0]
    assert invalid_times == 0, 'Revisar datas/horas/estação inválidas antes de agregar.'
    non_hourly = con.execute('''SELECT count(*) FROM meteo_inequivoca
        WHERE extract(minute FROM cast(hora AS TIME)) <> 0 OR extract(second FROM cast(hora AS TIME)) <> 0''').fetchone()[0]
    assert non_hourly == 0, 'A contagem de horas pressupõe horários inteiros.'
    fields = {'precipitacao_total': ('soma', 'sum'), 'temperatura_bulbo_hora': ('media', 'avg'),
              'umidade_rel_hora': ('media', 'avg'), 'vento_velocidade': ('media', 'avg')}
    aggregates = []
    for field, (suffix, function) in fields.items():
        aggregates += [f'{function}(try_cast({field} AS DOUBLE)) AS {field}_{suffix}',
                       f'count(try_cast({field} AS DOUBLE)) AS horas_{field}']
    con.execute(f'''CREATE OR REPLACE TABLE meteo_diaria AS
        WITH dias AS (
          SELECT id_estacao, cast(data AS DATE) AS data, count(*) AS horas_observadas,
            {', '.join(aggregates)}
          FROM meteo_inequivoca GROUP BY id_estacao, cast(data AS DATE)
        )
        SELECT d.*, e.id_municipio, e.estacao, e.altitude,
          horas_precipitacao_total = 24 AS precipitacao_24h_completa
        FROM dias d LEFT JOIN estacoes e USING(id_estacao)''')
    assert con.execute('SELECT max(horas_observadas) FROM meteo_diaria').fetchone()[0] <= 24
    assert con.execute('SELECT count(*) FROM meteo_diaria').fetchone()[0] == con.execute(
        'SELECT count(*) FROM (SELECT DISTINCT id_estacao,data FROM meteo_diaria)').fetchone()[0]
    # Bases diárias são descritivas. Só podem ser usadas para prever outro dia,
    # respeitando atraso de disponibilização e corte temporal ainda a definir.
    export(con, 'SELECT * FROM meteo_diaria ORDER BY id_estacao,data', out / 'meteorologia_diaria.parquet')
    export(con, '''SELECT data, count(*) AS estacoes_com_registro,
        sum(precipitacao_24h_completa::INT) AS estacoes_chuva_completa,
        avg(horas_observadas) AS media_horas
        FROM meteo_diaria GROUP BY data ORDER BY data''', out / 'cobertura_meteorologia.parquet')

    print('Resumindo detecções de fogo, sem criar dias artificiais sem foco...', flush=True)
    fire_reader = f"read_csv({sqlpath(raw / 'queimadas_2024_2025.csv')}, header=true, delim=';', all_varchar=true)"
    con.execute(f'CREATE OR REPLACE VIEW fogo_raw AS SELECT * FROM {fire_reader}')
    con.execute('''CREATE OR REPLACE TABLE fogo_diario AS
        SELECT cast(data_hora AS TIMESTAMP)::DATE AS data, id_municipio,
          count(*) AS deteccoes_multissatelite,
          count(DISTINCT satelite) AS satelites_distintos
        FROM fogo_raw GROUP BY ALL''')
    export(con, 'SELECT * FROM fogo_diario ORDER BY id_municipio,data', out / 'deteccoes_municipio_dia.parquet')
    export(con, '''SELECT date_trunc('month',data)::DATE AS mes,
        sum(deteccoes_multissatelite) AS deteccoes
        FROM fogo_diario GROUP BY mes ORDER BY mes''', out / 'deteccoes_mensais.parquet')
    fire_counts = con.execute('''SELECT count(*) AS linhas,
        count(*) FILTER (WHERE try_cast(risco_fogo AS DOUBLE) = -999) AS risco_menos999,
        count(*) FILTER (WHERE risco_fogo IS NULL) AS risco_vazio,
        count(*) FILTER (WHERE try_cast(dias_sem_chuva AS DOUBLE) = -999) AS dias_menos999,
        min(cast(data_hora AS TIMESTAMP)::DATE), max(cast(data_hora AS TIMESTAMP)::DATE)
        FROM fogo_raw''').fetchone()
    map_reader = f"read_csv({sqlpath(raw / 'MapBiomas.csv')}, header=true, all_varchar=true)"
    export(con, f'''SELECT ano, id_municipio, id_classe, try_cast(area AS DOUBLE) AS area_original
        FROM {map_reader} WHERE ano = (SELECT max(ano) FROM {map_reader})''', out / 'mapbiomas_ultimo_ano_sem_legenda.parquet')
    # Exportações pequenas para diagnóstico. Não aprendem parâmetros para ML.
    export(con, '''SELECT * FROM meteo_diaria WHERE data < DATE '2025-02-01'
        ORDER BY id_estacao,data''', out / 'meteorologia_janeiro_exploracao.parquet')
    stats = {
        'meteorologia_linhas_originais': total, 'meteorologia_linhas_distintas': distinct,
        'duplicatas_exatas_removidas_derivado': total-distinct,
        'chaves_com_multiplas_variantes': multiple_keys,
        'linhas_distintas_reservadas_por_chave_multipla': multiple_rows,
        'linhas_horarias_usadas': kept,
        'estacoes_dias': con.execute('SELECT count(*) FROM meteo_diaria').fetchone()[0],
        'estacoes_dias_precipitacao_24h': con.execute('SELECT count(*) FROM meteo_diaria WHERE precipitacao_24h_completa').fetchone()[0],
        'estacoes_dias_sem_municipio': con.execute('SELECT count(*) FROM meteo_diaria WHERE id_municipio IS NULL').fetchone()[0],
        'linhas_deteccoes': fire_counts[0], 'risco_fogo_menos999': fire_counts[1],
        'risco_fogo_vazio': fire_counts[2], 'dias_sem_chuva_menos999': fire_counts[3],
        'inicio_queimadas': str(fire_counts[4]), 'fim_queimadas': str(fire_counts[5]),
        'municipios_dias_com_deteccao': con.execute('SELECT count(*) FROM fogo_diario').fetchone()[0],
        'politica': 'Igualdade exata de valores em todas as colunas. Chaves com múltiplas variantes separadas, sem escolha arbitrária. Sem imputação. Somatórios parciais não equivalem a totais de 24 horas. Datas de fogo em UTC; fontes ainda não unidas. Sem rótulos ou modelos.',
    }
    assert con.execute('SELECT sum(deteccoes_multissatelite) FROM fogo_diario').fetchone()[0] == fire_counts[0]
    (out/'resumo_preparacao.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2),encoding='utf-8')
    con.close()
    print(json.dumps(stats,ensure_ascii=False,indent=2),flush=True)
    return stats


if __name__ == '__main__':
    prepare()
