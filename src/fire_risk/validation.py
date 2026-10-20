"""Contratos verificáveis antes de dados serem usados na modelagem."""
from pathlib import Path
import hashlib
import json


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def require_tutor_approval(approval_path, manifest_path):
    """Verifica registro e vínculo ao manifesto; não autentica a pessoa tutora."""
    path = Path(approval_path)
    if not path.is_file():
        raise ValueError('Entrega 0 pendente: falta registro da aprovação real da tutoria.')
    record = json.loads(path.read_text(encoding='utf-8'))
    required = ['approved_by', 'approved_at', 'evidence_ref', 'dataset_manifest_sha256']
    if record.get('status') != 'approved' or any(not record.get(key) for key in required):
        raise ValueError('Aprovação incompleta: registrar decisão e evidência reais, sem simular aceite.')
    if record['dataset_manifest_sha256'] != sha256(manifest_path):
        raise ValueError('A aprovação se refere a outra versão do manifesto de dados.')
    return record


def validate_panel(frame, keys, target, min_rows=10_000, min_class_fraction=0.05):
    if len(frame) < min_rows:
        raise ValueError('Volume inferior ao mínimo definido para a base externa.')
    if frame[keys].isna().any().any() or frame.duplicated(keys).any():
        raise ValueError('A chave região/data deve ser preenchida e única.')
    if frame[target].isna().any():
        raise ValueError('O alvo não pode conter ausências.')
    frequencies = frame[target].value_counts(normalize=True)
    if len(frequencies) < 2 or frequencies.min() < min_class_fraction:
        raise ValueError('Revisar variabilidade e representatividade das classes.')
    if frame.isna().all().any():
        raise ValueError('A base contém coluna inteiramente vazia.')
    return {'rows': len(frame), 'class_fractions': frequencies.to_dict()}


def validate_availability(frame, feature_time, issue_time, target_end):
    """Datas devem ser fornecidas já normalizadas no mesmo fuso."""
    if frame[[feature_time, issue_time, target_end]].isna().any().any():
        raise ValueError('Datas de disponibilidade e previsão devem estar preenchidas.')
    if not ((frame[feature_time] <= frame[issue_time]) & (frame[issue_time] < frame[target_end])).all():
        raise ValueError('Variáveis futuras ou janela do alvo inválida para a emissão da previsão.')
