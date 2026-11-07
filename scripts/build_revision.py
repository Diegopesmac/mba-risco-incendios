"""Exporta histórico agregado e ajuste complementar, preservando o teste original."""
from pathlib import Path
import argparse, json, sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
import joblib
import pandas as pd
from fire_risk.course import verify_course_manifest
from fire_risk.submission import read_panel, PANEL_FILE
from fire_risk.revision import build_label_history, development_review, tune_balance, evaluate_test_persistence
from fire_risk.finalization import verify_freeze
from fire_risk.validation import sha256

def build(raw_dir):
    verify_freeze(ROOT)
    verify_course_manifest(ROOT/'.local/course/manifest.json',raw_dir,ROOT/'configs/course-data.json')
    panel=read_panel(ROOT/PANEL_FILE)
    train=panel.loc[panel['split'].eq('train')]
    valid=panel.loc[panel['split'].eq('validation')]
    test=panel.loc[panel['split'].eq('test')]
    full_history=build_label_history(Path(raw_dir)/'queimadas_2024_2025.csv', test['data'].max()-pd.Timedelta(days=2))
    history=full_history.loc[full_history['data'].le(pd.Timestamp('2025-02-02'))].copy()
    history=history.loc[history['id_municipio'].isin(set(train['id_municipio'])|set(valid['id_municipio']))].copy()
    destination=ROOT/'submission/evidence'
    history['data']=history['data'].dt.strftime('%Y-%m-%d')
    (destination/'label-history.json').write_text(history.to_json(orient='records'),encoding='utf-8')
    history['data']=pd.to_datetime(history['data'])
    report=development_review(panel,history)
    model,balance=tune_balance(train,valid)
    report.update(balance_adjustment=balance,source_sha256=sha256(Path(raw_dir)/'queimadas_2024_2025.csv'),history_rows=len(history))
    (destination/'revision.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    test_history=full_history.loc[full_history['id_municipio'].isin(test['id_municipio'])].copy()
    scenario=json.loads((ROOT/'configs/evaluation-plan.json').read_text(encoding='utf-8'))['cost_scenario']
    test_report=evaluate_test_persistence(panel,test_history,scenario)
    test_report.update(source_sha256=report['source_sha256'],history_rows=len(test_history))
    (destination/'persistence-test.json').write_text(json.dumps(test_report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    test_history['data']=test_history['data'].dt.strftime('%Y-%m-%d')
    (destination/'label-history-test.json').write_text(test_history.to_json(orient='records'),encoding='utf-8')
    target=ROOT/'.local/course/revision'
    target.mkdir(exist_ok=True)
    joblib.dump(model,target/'balanced-candidate.joblib')
    print('Persistencia:',report['metrics']['persistencia_d2']['f1_macro'],'fallbacks:',report['fallback_rows'])
    print('Balanceamento:',balance['selected_power'],'F1 validacao:',balance['validation']['f1_macro'])
    print('Historico:',len(history),'linhas agregadas; sem filtro meteorologico.')
    print('Teste persistencia:',test_report['metrics']['f1_macro'],'custo:',test_report['simulated_cost']['total'])
    verify_freeze(ROOT)
if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--raw-dir',type=Path,required=True)
    build(parser.parse_args().raw_dir)
