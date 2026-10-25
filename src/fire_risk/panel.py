"""Painel retrospectivo do índice registrado; ausência de detecção não é classe."""
from datetime import date
import math

import duckdb
import pandas as pd

FEATURES = ('chuva_d2', 'temperatura_d2', 'umidade_d2', 'vento_d2')
LABELS = ('baixo', 'medio', 'alto')
SPLIT_PLAN = {'train_end': '2025-01-25', 'validation_start': '2025-01-27',
              'validation_end': '2025-02-02', 'test_start': '2025-02-04',
              'test_end': '2025-02-12'}


def risk_class(value):
    if value is None or not isinstance(value, (int, float)) or isinstance(value, bool):
        return None
    if not math.isfinite(value) or not 0 <= value <= 1:
        return None
    return 'baixo' if value <= 0.4 else 'medio' if value <= 0.7 else 'alto'


def temporal_split(day):
    day = pd.Timestamp(day).date()
    if date(2025, 1, 1) <= day <= date(2025, 1, 25):
        return 'train'
    if date(2025, 1, 27) <= day <= date(2025, 2, 2):
        return 'validation'
    if date(2025, 2, 4) <= day <= date(2025, 2, 12):
        return 'test'
    return 'gap'


def sql_path(path):
    return "'" + str(path).replace('\\', '/').replace("'", "''") + "'"


def validate_course_panel(frame):
    if frame.empty or frame[['id_municipio', 'data', 'target']].isna().any().any():
        raise ValueError('Painel vazio ou com chave/alvo ausente.')
    if frame.duplicated(['id_municipio', 'data']).any():
        raise ValueError('Chave município/data repetida.')
    if not frame['target'].isin(LABELS).all():
        raise ValueError('Classe inválida.')
    if frame[list(FEATURES)].isna().any().any():
        raise ValueError('Features meteorológicas incompletas.')
    if not frame[list(FEATURES)].map(math.isfinite).all().all():
        raise ValueError('Features não finitas.')
    if not ((frame['weather_date'] + pd.Timedelta(days=2) == frame['data'])
            & (frame['assumed_features_available_at'] <= frame['prediction_issued_at'])
            & (frame['prediction_issued_at'] < frame['target_window_end'])).all():
        raise ValueError('Defasagem ou janela temporal inválida.')


def build_panel_frame(fire_path, weather_path):
    con = duckdb.connect()
    try:
        con.execute("SET memory_limit='1GB'")
        con.execute(f'''CREATE TEMP TABLE records AS
            SELECT id_municipio, cast(data_hora AS TIMESTAMP)::DATE AS data,
              CASE WHEN isfinite(try_cast(risco_fogo AS DOUBLE))
                AND try_cast(risco_fogo AS DOUBLE) BETWEEN 0 AND 1
                THEN try_cast(risco_fogo AS DOUBLE) END AS risk
            FROM read_csv({sql_path(fire_path)}, header=true, delim=';', all_varchar=true)
            WHERE cast(data_hora AS TIMESTAMP)::DATE BETWEEN DATE '2025-01-01' AND DATE '2025-02-12'
        ''')
        con.execute('''CREATE TEMP TABLE targets AS
            SELECT id_municipio, data, median(risk) AS target_index,
              count(*) AS detection_records, count(risk) AS valid_index_records
            FROM records WHERE regexp_full_match(id_municipio, '[0-9]{7}') GROUP BY ALL''')
        con.execute(f'CREATE TEMP TABLE weather AS SELECT * FROM read_parquet({sql_path(weather_path)})')
        if con.execute('''SELECT count(*) FROM (SELECT id_estacao,data FROM weather
            GROUP BY ALL HAVING count(*) > 1)''').fetchone()[0]:
            raise ValueError('Meteorologia tem estação/data duplicada.')
        con.execute('''CREATE TEMP TABLE municipal_weather AS
            SELECT id_municipio, cast(data AS DATE) AS weather_date,
              avg(precipitacao_total_soma) AS chuva_d2,
              avg(temperatura_bulbo_hora_media) AS temperatura_d2,
              avg(umidade_rel_hora_media) AS umidade_d2,
              avg(vento_velocidade_media) AS vento_d2, count(*) AS eligible_stations
            FROM weather
            WHERE regexp_full_match(id_municipio, '[0-9]{7}')
              AND horas_precipitacao_total = 24
              AND horas_temperatura_bulbo_hora >= 18
              AND horas_umidade_rel_hora >= 18 AND horas_vento_velocidade >= 18
              AND isfinite(precipitacao_total_soma) AND precipitacao_total_soma >= 0
              AND isfinite(temperatura_bulbo_hora_media)
              AND isfinite(umidade_rel_hora_media) AND umidade_rel_hora_media BETWEEN 0 AND 100
              AND isfinite(vento_velocidade_media) AND vento_velocidade_media >= 0
            GROUP BY ALL''')
        frame = con.execute('''SELECT t.*, w.* EXCLUDE (id_municipio)
            FROM targets t JOIN municipal_weather w ON t.id_municipio = w.id_municipio
              AND t.data = w.weather_date + INTERVAL 2 DAY
            WHERE t.target_index IS NOT NULL ORDER BY t.data,t.id_municipio''').df()
        frame['data'] = pd.to_datetime(frame['data'])
        frame['weather_date'] = pd.to_datetime(frame['weather_date'])
        frame['target'] = frame['target_index'].map(risk_class)
        frame['split'] = frame['data'].map(temporal_split)
        frame['prediction_issued_at'] = frame['data']
        frame['target_window_end'] = frame['data'] + pd.Timedelta(days=1)
        frame['assumed_features_available_at'] = frame['weather_date'] + pd.Timedelta(days=2)
        frame['historical_publication_verified'] = False
        validate_course_panel(frame)
        target_count, valid_targets = con.execute(
            'SELECT count(*), count(target_index) FROM targets').fetchone()
        records, invalid_indices = con.execute(
            'SELECT count(*), count(*)-count(risk) FROM records').fetchone()
        report = {'source': 'course', 'rows': len(frame), 'features': list(FEATURES),
                  'target': 'median_recorded_fire_risk_3_classes', 'weather_lag_days': 2,
                  'source_detection_records_in_period': records,
                  'invalid_index_records_in_period': invalid_indices,
                  'municipality_days_with_records': target_count,
                  'municipality_days_without_valid_index': target_count-valid_targets,
                  'valid_target_days_without_eligible_weather': valid_targets-len(frame),
                  'classes': frame['target'].value_counts().to_dict(),
                  'split_plan': SPLIT_PLAN,
                  'splits': {name: {'rows': len(part), 'days': int(part['data'].nunique()),
                                    'first_date': str(part['data'].min().date()),
                                    'last_date': str(part['data'].max().date()),
                                    'classes': part['target'].value_counts().to_dict()}
                             for name, part in frame.groupby('split')},
                  'historical_publication_verified': False,
                  'limitation': 'Índice condicionado às detecções; não estima ocorrência física. Atraso de publicação hipotético.'}
        return frame, report
    finally:
        con.close()
