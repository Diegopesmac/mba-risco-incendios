"""API pública acadêmica; não treina, não adquire fontes e não recebe artefatos."""
from datetime import date, timedelta
from pathlib import Path
import os

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, model_validator

from .serving import ModelService
from .panel import FEATURES


class PredictionInput(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)
    municipio: str = Field(pattern=r'^[0-9]{7}$')
    data_alvo: date
    data_meteorologia: date
    chuva_d2: float = Field(ge=0, le=3000, strict=True)
    temperatura_d2: float = Field(ge=-100, le=100, strict=True)
    umidade_d2: float = Field(ge=0, le=100, strict=True)
    vento_d2: float = Field(ge=0, le=150, strict=True)

    @model_validator(mode='after')
    def validate_dates(self):
        if self.data_meteorologia != self.data_alvo - timedelta(days=2):
            raise ValueError('Meteorologia deve corresponder a D-2 em datas UTC.')
        return self


def create_app(model_dir=None, expected_manifest_sha256=None):
    app = FastAPI(title='MBA — classes do índice de risco', version='1.0.0',
                  description='Protótipo acadêmico retrospectivo. Não é serviço oficial de alerta.')
    app.state.service = None
    app.state.model_state = 'absent'
    @app.exception_handler(RequestValidationError)
    async def invalid_input(request, error):
        return JSONResponse(status_code=422, content={'detail': [
            {'loc': list(item['loc']), 'type': item['type'], 'msg': 'Entrada inválida para o contrato.'}
            for item in error.errors()]})
    if model_dir is not None:
        try:
            app.state.service = ModelService(model_dir, expected_manifest_sha256)
            app.state.model_state = 'ready'
        except (ValueError, OSError, KeyError, TypeError, AttributeError):
            app.state.model_state = 'invalid'

    @app.get('/')
    def index():
        return {'projeto': 'MBA — risco de incêndios', 'docs': '/docs', 'health': '/health',
                'aviso': 'Classificador acadêmico do índice registrado; uso operacional não validado.'}

    @app.get('/health')
    def health():
        if app.state.service is None:
            raise HTTPException(status_code=503, detail={'status': 'model_unavailable', 'state': app.state.model_state})
        return {'status': 'ready', 'model_id': app.state.service.metadata['model_id'],
                'uso_operacional_validado': False}

    @app.post('/predict')
    def predict(payload: PredictionInput):
        if app.state.service is None:
            raise HTTPException(status_code=503, detail='Modelo indisponível.')
        result = app.state.service.predict({key: getattr(payload, key) for key in FEATURES}, payload.municipio)
        return {**result, 'municipio': payload.municipio, 'data_alvo': payload.data_alvo,
                'data_meteorologia': payload.data_meteorologia,
                'disponibilidade_historica_verificada': False,
                'atraso_publicacao_assumido_horas': 24}

    return app


app = create_app(os.environ.get('MODEL_DIR'), os.environ.get('MODEL_MANIFEST_SHA256'))
