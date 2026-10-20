"""Casos sintéticos: duplicatas, variantes horárias e chuva incompleta."""
from pathlib import Path
import csv
import hashlib
import tempfile
import unittest
from preparar_eda_queimadas import prepare, ROOT
import duckdb


def write_csv(path, columns, rows, delimiter=','):
    with path.open('w', encoding='utf-8', newline='') as file:
        writer = csv.writer(file, delimiter=delimiter)
        writer.writerow(columns)
        writer.writerows(rows)


class PreparationTest(unittest.TestCase):
    def test_duplicates_variants_and_missing_rain(self):
        temp = tempfile.TemporaryDirectory(dir=ROOT)
        root = Path(temp.name).resolve()
        self.assertTrue(root.is_relative_to(ROOT.resolve()))
        try:
            raw = root / 'dados_brutos_queimadas'
            raw.mkdir()
            cols = ['ano','data','hora','id_estacao','precipitacao_total',
                    'temperatura_bulbo_hora','umidade_rel_hora','vento_velocidade']
            rows = [['2025','2025-01-01',f'{hour:02d}:00:00','TESTE','1','20','80','2'] for hour in range(24)]
            rows += [rows[0].copy()]
            rows += [['2025','2025-01-02','00:00:00','TESTE',rain,'20','80','2'] for rain in ['0','2']]
            rows += [['2025','2025-01-03','00:00:00','TESTE','','20','80','2']]
            write_csv(raw/'BDMEP-2025.csv',cols,rows)
            write_csv(raw/'BDMEP-estacao.csv', ['id_estacao','id_municipio','estacao','altitude'],
                      [['TESTE','0000000','Estação fictícia','10']])
            write_csv(raw/'MapBiomas.csv', ['ano','id_municipio','id_classe','area'],
                      [['2020','0000000','0','1'],['2021','0000000','0','2']])
            write_csv(raw/'queimadas_2024_2025.csv',
                      ['data_hora','id_municipio','satelite','risco_fogo','dias_sem_chuva'],
                      [['2025-01-01 12:00:00','0000000','TESTE_1','-999','-999'],
                       ['2025-01-01 13:00:00','0000000','TESTE_2','0.1','1']], ';')
            before = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in raw.iterdir()}
            summary = prepare(root)
            self.assertEqual(summary['duplicatas_exatas_removidas_derivado'],1)
            self.assertEqual(summary['chaves_com_multiplas_variantes'],1)
            self.assertEqual(summary['linhas_distintas_reservadas_por_chave_multipla'],2)
            self.assertEqual(summary['linhas_horarias_usadas'],25)
            con=duckdb.connect(str(root/'eda_queimadas/preparacao.duckdb'),read_only=True)
            days=con.execute('SELECT data,precipitacao_total_soma,precipitacao_24h_completa FROM meteo_diaria ORDER BY data').fetchall()
            self.assertEqual(len(days),2)
            self.assertEqual(days[0][1:],(24.0,True))
            self.assertEqual(days[1][1:],(None,False))
            self.assertEqual(con.execute('SELECT sum(deteccoes_multissatelite) FROM fogo_diario').fetchone()[0],2)
            self.assertEqual(con.execute("SELECT DISTINCT ano FROM read_parquet(?)",[str(root/'eda_queimadas/mapbiomas_ultimo_ano_sem_legenda.parquet')]).fetchall(),[('2021',)])
            con.close()
            self.assertEqual(before,{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in raw.iterdir()})
        finally:
            # O alvo absoluto foi conferido como descendente da pasta do projeto.
            self.assertTrue(root.is_relative_to(ROOT.resolve()))
            temp.cleanup()


if __name__ == '__main__':
    unittest.main()
