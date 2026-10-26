"""Contrato portátil da entrega acadêmica, independente do treinamento."""
from pathlib import Path
import hashlib
import json

import pandas as pd

from .panel import FEATURES, LABELS, risk_class, temporal_split, validate_course_panel

NOTEBOOKS = (
    'notebooks/course/01_auditoria_queimadas.ipynb',
    'notebooks/course/02_eda_preparacao_queimadas.ipynb',
    'notebooks/course/03_painel_modelos_curso.ipynb',
    'notebooks/04_projeto_final_curso.ipynb',
)
PANEL_FILE = 'submission/painel_modelagem.csv'
DATE_COLUMNS = ('data', 'weather_date', 'prediction_issued_at',
                'target_window_end', 'assumed_features_available_at')
DICTIONARY = {
    'id_municipio': ('texto de 7 dígitos', 'chave', 'Código IBGE do município; não é feature.'),
    'data': ('data UTC', 'chave', 'Dia D do índice registrado; chave com id_municipio.'),
    'target_index': ('real [0,1]', 'alvo contínuo', 'Mediana dos índices válidos das detecções no município/dia; nunca feature.'),
    'detection_records': ('inteiro positivo', 'auditoria', 'Quantidade de registros multissatélite em D; não são incêndios independentes, nunca feature.'),
    'valid_index_records': ('inteiro positivo', 'auditoria', 'Registros em D com índice válido; nunca feature.'),
    'weather_date': ('data UTC', 'disponibilidade', 'Dia das medições meteorológicas: D−2.'),
    'chuva_d2': ('real não negativo, escala original', 'feature', 'Média municipal dos totais diários de chuva das estações elegíveis; exige 24 medições por estação.'),
    'temperatura_d2': ('real, escala original', 'feature', 'Média municipal das médias diárias de temperatura; ao menos 18 medições por estação.'),
    'umidade_d2': ('real [0,100], escala original', 'feature', 'Média municipal das médias diárias de umidade; ao menos 18 medições por estação.'),
    'vento_d2': ('real não negativo, escala original', 'feature', 'Média municipal das médias diárias de velocidade do vento; ao menos 18 medições por estação.'),
    'eligible_stations': ('inteiro positivo', 'cobertura', 'Número de estações que atendem simultaneamente aos critérios das quatro features; não é feature.'),
    'target': ('baixo, medio ou alto', 'alvo categórico', 'target_index ≤0,40: baixo; >0,40 e ≤0,70: medio; >0,70: alto. Ausência não vira baixo.'),
    'split': ('train, validation, test ou gap', 'partição', 'Partição temporal predefinida; gap é excluído do ajuste e da avaliação.'),
    'prediction_issued_at': ('instante UTC', 'disponibilidade', 'Emissão simulada: 00:00 de D.'),
    'target_window_end': ('instante UTC', 'disponibilidade', 'Fim exclusivo da janela prevista: 00:00 de D+1.'),
    'assumed_features_available_at': ('instante UTC', 'disponibilidade', 'Disponibilidade assumida: 00:00 de D; atraso histórico não comprovado.'),
    'historical_publication_verified': ('booleano', 'limitação', 'Sempre falso nesta versão; disponibilidade histórica não foi comprovada.'),
}


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def read_panel(path):
    frame = pd.read_csv(path, dtype={'id_municipio': str})
    if set(frame.columns) != set(DICTIONARY):
        raise ValueError('Esquema da base consolidada diverge do dicionário.')
    for name in DATE_COLUMNS:
        frame[name] = pd.to_datetime(frame[name], errors='raise')
    validate_course_panel(frame)
    if (frame.isna().any().any()
            or not frame['id_municipio'].str.fullmatch(r'[0-9]{7}').all()
            or not frame['target_index'].map(risk_class).eq(frame['target']).all()
            or not frame['data'].map(temporal_split).eq(frame['split']).all()
            or not frame[['detection_records', 'valid_index_records', 'eligible_stations']].map(
                lambda value: isinstance(value, (int, float)) and value > 0 and value == int(value)).all().all()
            or not frame['valid_index_records'].le(frame['detection_records']).all()):
        raise ValueError('Valores ou classificação da base consolidada inválidos.')
    if (not frame['split'].isin(['train', 'validation', 'test', 'gap']).all()
            or frame['historical_publication_verified'].isna().any()
            or not frame['historical_publication_verified'].eq(False).all()):
        raise ValueError('Partição ou declaração de disponibilidade inválida.')
    return frame


def training_correlations(frame):
    """Não inspeciona valores do teste nem orienta nova seleção de variáveis."""
    training = frame.loc[frame['split'].eq('train')].copy()
    if training.empty:
        raise ValueError('Treino ausente para EDA.')
    training['target_ordinal'] = training['target'].map(dict(zip(LABELS, range(3))))
    if training['target_ordinal'].isna().any():
        raise ValueError('Classe de treino inválida.')
    columns = [*FEATURES, 'target_index', 'target_ordinal']
    correlations = {method: training[columns].corr(method=method)
                    for method in ('pearson', 'spearman')}
    return training, correlations


def verify_submission(root):
    root = Path(root)
    manifest = json.loads((root / 'submission/manifest.json').read_text(encoding='utf-8'))
    if PANEL_FILE not in manifest['files']:
        raise ValueError('Base consolidada ausente do manifesto.')
    for name, expected in manifest['files'].items():
        if '..' in Path(name).parts or not name.startswith(('submission/', 'docs/')):
            raise ValueError('Caminho inválido no manifesto de entrega.')
        if sha256_bytes((root / name).read_bytes()) != expected:
            raise ValueError('Arquivo de entrega alterado: ' + name)
    panel = read_panel(root / PANEL_FILE)
    if len(panel) != manifest['rows']:
        raise ValueError('Contagem da base consolidada divergente.')
    if panel['split'].value_counts().to_dict() != manifest['splits']:
        raise ValueError('Partições da base consolidada divergentes.')
    if 'submission/evidence/freeze.json' in manifest['files']:
        freeze_path = root / 'submission/evidence/freeze.json'
        freeze = json.loads(freeze_path.read_text(encoding='utf-8'))
        evaluation = json.loads((root / 'submission/evidence/evaluation.json').read_text(encoding='utf-8'))
        if (evaluation['freeze_sha256'] != sha256_bytes(freeze_path.read_bytes())
                or manifest['model_id'] != freeze['artifacts'][freeze['selected']]['sha256'][:16]):
            raise ValueError('Avaliação ou modelo não corresponde ao congelamento incluído.')
        for name, expected in freeze['code_sha256'].items():
            if sha256_bytes((root / 'src/fire_risk' / name).read_bytes()) != expected:
                raise ValueError('Código científico diverge do congelamento incluído.')
    return panel, manifest
