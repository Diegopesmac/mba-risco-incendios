import csv
from pathlib import Path
import sys
import tempfile
import unittest

import duckdb
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from fire_risk.panel import FEATURES, build_panel_frame, risk_class, temporal_split


class PanelTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=ROOT / '.local')
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.fire = self.folder / 'fire.csv'
        self.weather = self.folder / 'weather.parquet'
        self.records = [('2025-01-03 12:00:00', '0000001', '0.1'),
                        ('2025-01-03 13:00:00', '0000001', '0.5'),
                        ('2025-01-03 14:00:00', '0000001', '0.9'),
                        ('2025-01-04 12:00:00', '0000001', '-999'),
                        ('2025-01-04 13:00:00', '0000001', '0'),
                        ('2025-01-03 12:00:00', '0000002', '-999'),
                        ('2025-01-03 13:00:00', '0000003', '1'),
                        ('2024-12-31 12:00:00', '0000001', '1')]
        self.daily = pd.DataFrame([
            dict(id_estacao='FICTICIA', id_municipio='0000001', data=day,
                 precipitacao_total_soma=12.0, temperatura_bulbo_hora_media=22.0,
                 umidade_rel_hora_media=60.0, vento_velocidade_media=2.0,
                 horas_precipitacao_total=24, horas_temperatura_bulbo_hora=24,
                 horas_umidade_rel_hora=24, horas_vento_velocidade=24)
            for day in ['2025-01-01', '2025-01-02']])

    def save(self):
        with self.fire.open('w', encoding='utf-8', newline='') as stream:
            writer = csv.writer(stream, delimiter=';')
            writer.writerow(['data_hora', 'id_municipio', 'risco_fogo'])
            writer.writerows(self.records)
        with duckdb.connect() as con:
            con.register('daily', self.daily)
            con.execute('COPY daily TO ? (FORMAT PARQUET)', [str(self.weather)])

    def test_fixed_class_boundaries_and_missing_are_not_low(self):
        for value, expected in [(0, 'baixo'), (0.4, 'baixo'), (0.40001, 'medio'),
                                (0.7, 'medio'), (0.70001, 'alto'), (1, 'alto'),
                                (-999, None), (float('nan'), None), (float('inf'), None),
                                (None, None), (True, None), ('0', None), (1.1, None)]:
            with self.subTest(value=value):
                self.assertEqual(risk_class(value), expected)

    def test_median_labels_lag_and_no_artificial_negatives(self):
        self.save()
        frame, report = build_panel_frame(self.fire, self.weather)
        self.assertEqual(frame['target'].tolist(), ['medio', 'baixo'])
        self.assertEqual(frame['target_index'].tolist(), [0.5, 0.0])
        self.assertEqual(frame['id_municipio'].tolist(), ['0000001', '0000001'])
        self.assertTrue((frame['data'] - frame['weather_date'] == pd.Timedelta(days=2)).all())
        self.assertTrue((frame['assumed_features_available_at'] <= frame['prediction_issued_at']).all())
        self.assertFalse(frame['historical_publication_verified'].any())
        self.assertEqual(report['invalid_index_records_in_period'], 2)
        self.assertEqual(report['municipality_days_without_valid_index'], 1)
        self.assertEqual(report['valid_target_days_without_eligible_weather'], 1)
        self.assertEqual(report['source_detection_records_in_period'], 7)
        self.assertFalse(set(FEATURES) & {'target', 'target_index', 'detection_records', 'id_municipio'})

    def test_partial_rain_and_insufficient_humidity_excluded(self):
        for column, value in [('horas_precipitacao_total', 23),
                              ('horas_umidade_rel_hora', 17), ('umidade_rel_hora_media', 101)]:
            with self.subTest(column=column):
                original = self.daily.copy()
                self.daily.loc[0, column] = value
                self.save()
                frame, _ = build_panel_frame(self.fire, self.weather)
                self.assertEqual(frame['target'].tolist(), ['baixo'])
                self.daily = original

    def test_current_day_weather_is_never_used_as_lag(self):
        self.daily['data'] = ['2025-01-03', '2025-01-04']
        self.save()
        with self.assertRaisesRegex(ValueError, 'vazio'):
            build_panel_frame(self.fire, self.weather)

    def test_duplicate_station_days_block_instead_of_overweighting(self):
        self.daily = pd.concat([self.daily, self.daily.iloc[:1]], ignore_index=True)
        self.save()
        with self.assertRaisesRegex(ValueError, 'duplicada'):
            build_panel_frame(self.fire, self.weather)

    def test_split_dates_have_explicit_gaps(self):
        for day, expected in [('2025-01-25', 'train'), ('2025-01-26', 'gap'),
                              ('2025-01-27', 'validation'), ('2025-02-02', 'validation'),
                              ('2025-02-03', 'gap'), ('2025-02-04', 'test'),
                              ('2025-02-12', 'test'), ('2025-02-13', 'gap')]:
            self.assertEqual(temporal_split(day), expected)


if __name__ == '__main__':
    unittest.main()
