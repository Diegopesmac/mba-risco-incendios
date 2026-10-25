"""Verifica saúde, inferência e erros por HTTP real, sem guardar entradas no servidor."""
import argparse
import json
from pathlib import Path
import urllib.request
import urllib.error


def smoke(url, request):
    url = url.rstrip('/')
    with urllib.request.urlopen(url + '/health', timeout=90) as response:
        health = json.load(response)
    if health.get('status') != 'ready' or not health.get('model_id'):
        raise ValueError('Serviço não está pronto com modelo identificado.')
    query = urllib.request.Request(url + '/predict', data=json.dumps(request).encode('utf-8'),
                                   headers={'Content-Type': 'application/json'}, method='POST')
    with urllib.request.urlopen(query, timeout=90) as response:
        prediction = json.load(response)
    if (prediction.get('model_id') != health['model_id'] or prediction.get('uso_operacional_validado') is not False
            or abs(sum(prediction['probabilidades_classes_indice'].values()) - 1) > 1e-8):
        raise ValueError('Resposta não corresponde ao contrato do modelo.')
    bad = {**request, 'umidade_d2': 101}
    try:
        urllib.request.urlopen(urllib.request.Request(url + '/predict', data=json.dumps(bad).encode('utf-8'),
            headers={'Content-Type':'application/json'}, method='POST'), timeout=30)
    except urllib.error.HTTPError as error:
        if error.code != 422:
            raise
    else:
        raise ValueError('Entrada inválida não foi rejeitada.')
    return {'url': url, 'health': health, 'prediction': prediction,
            'invalid_input_status': 422, 'http_verified': True}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', required=True)
    parser.add_argument('--request', type=Path, required=True)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = smoke(args.url, json.loads(args.request.read_text(encoding='utf-8')))
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n', encoding='utf-8')
    print('HTTP real conferido:', result['url'], result['health']['model_id'])
