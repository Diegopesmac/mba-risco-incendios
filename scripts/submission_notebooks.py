"""Compatibilidade: lê células dos notebooks canônicos, sem gerar código."""
from pathlib import Path
import nbformat
ROOT = Path(__file__).resolve().parents[1]
def sections(name):
    return [(c.cell_type, c.source) for c in nbformat.read(ROOT/name, as_version=4).cells]
AUDIT = sections('notebooks/course/01_auditoria_queimadas.ipynb')
EDA = sections('notebooks/course/02_eda_preparacao_queimadas.ipynb')
MODELS = sections('notebooks/course/03_painel_modelos_curso.ipynb')
FINAL = sections('notebooks/04_projeto_final_curso.ipynb')
