"""Gera notebook executado e figuras da exploração inicial."""
from pathlib import Path
import os
import sys
import io
import contextlib
import base64
import json

ROOT = Path(__file__).resolve().parent
if (ROOT / '.deps_queimadas').exists():
    sys.path.insert(0, str(ROOT / '.deps_queimadas'))
os.environ['MPLCONFIGDIR'] = str(ROOT / 'eda_queimadas' / '.plot_cache')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import nbformat


def build():
    cells = []
    def md(text):
        cells.append(nbformat.v4.new_markdown_cell(text))
    def code(text):
        cells.append(nbformat.v4.new_code_cell(text))

    md('''# Projeto final do MBA — exploração e preparação inicial

**Pergunta de negócio:** como apoiar a priorização preventiva de regiões e dias com risco de incêndio?

**Escopo deste notebook:** investigar a qualidade e a cobertura das quatro fontes, preparar meteorologia diária e explorar relações meteorológicas. As classes baixo/médio/alto e o horizonte ainda precisam ser definidos. Não há previsão ou avaliação de modelo.

KPI técnico candidato: recall da classe alta e F1 macro. KPI operacional candidato: eventos detectados dentro de uma capacidade fixa de resposta. As definições finais dependem do alvo e dos custos de erro; nenhum custo foi inventado.

Fontes: [pasta fornecida pelo curso](https://drive.google.com/drive/folders/1f0aGrjkidz1P7Fns9OlPUCukNRuw-1BD) e [Base dos Dados](https://basedosdados.org/search).''')
    code('''from pathlib import Path
import sys, os, json
ROOT = Path.cwd()
if (ROOT / '.deps_queimadas').exists():
    sys.path.insert(0, str(ROOT / '.deps_queimadas'))
OUT = ROOT / 'eda_queimadas'
FIG = OUT / 'figuras'
FIG.mkdir(parents=True, exist_ok=True)
os.environ['MPLCONFIGDIR'] = str(OUT / '.plot_cache')
import duckdb
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import wilcoxon
from preparar_eda_queimadas import prepare
REPROCESSAR = False
if REPROCESSAR or not (OUT / 'resumo_preparacao.json').exists():
    prepare(ROOT)
resumo = json.loads((OUT / 'resumo_preparacao.json').read_text(encoding='utf-8'))
perfil = json.loads((ROOT / 'auditoria_queimadas' / 'perfil_bases.json').read_text(encoding='utf-8'))
con = duckdb.connect(str(OUT / 'preparacao.duckdb'), read_only=True)
def frame(name):
    return con.execute("SELECT * FROM read_parquet(?)", [str(OUT / name)]).df()
plt.rcParams.update({'figure.figsize': (10, 4.8), 'font.size': 11, 'axes.spines.top': False, 'axes.spines.right': False})
def finish(name):
    plt.tight_layout()
    plt.savefig(FIG / name, dpi=150, bbox_inches='tight')
    plt.show()
print('Fontes:', len(perfil['bases']), '| preparação carregada.')''')
    md('''## 1. Limpeza rastreável e população disponível

Os CSVs originais não são alterados. A preparação compara **todas as colunas como valores textuais lidos do CSV** e elimina apenas repetições exatas no derivado. Representações numéricas diferentes não são equiparadas automaticamente.

Se uma mesma estação/data/hora tem mais de uma linha distinta, todas as variantes são preservadas em arquivo separado e o horário não entra na agregação inicial. Isso é uma seleção conservadora, que pode afetar a representatividade e deve ser revisada. Não se presume que toda diferença seja erro; não há imputação.''')
    code('''fluxo = pd.DataFrame([
    ['Linhas originais', resumo['meteorologia_linhas_originais']],
    ['Duplicatas exatas removidas no derivado', resumo['duplicatas_exatas_removidas_derivado']],
    ['Linhas distintas reservadas por horário múltiplo', resumo['linhas_distintas_reservadas_por_chave_multipla']],
    ['Linhas horárias usadas', resumo['linhas_horarias_usadas']],
    ['Pares estação/dia', resumo['estacoes_dias']],
    ['Pares estação/dia com 24 medições de chuva', resumo['estacoes_dias_precipitacao_24h']],
], columns=['Etapa', 'Quantidade'])
print(fluxo.to_string(index=False))
assert resumo['meteorologia_linhas_originais'] == resumo['duplicatas_exatas_removidas_derivado'] + resumo['linhas_distintas_reservadas_por_chave_multipla'] + resumo['linhas_horarias_usadas']
print('Reconciliação das contagens: OK.')''')
    md('''## 2. Cobertura temporal e observabilidade

A meteorologia tem dados de janeiro a junho de 2025, mas a última detecção no arquivo de fogo é de 12/02/2025. Fevereiro de 2025 é parcial. O gráfico mostra **detecções de múltiplos satélites**, não incêndios independentes. Não interpretar ausência de linhas após o fim da série como ausência de fogo.''')
    code('''mensal = frame('deteccoes_mensais.parquet')
cores = ['#db8a39' if str(m)[:7] == '2025-02' else '#207e89' for m in mensal['mes']]
plt.figure()
plt.bar(mensal['mes'].dt.strftime('%Y-%m'), mensal['deteccoes'] / 1_000_000, color=cores)
plt.xticks(rotation=45, ha='right')
plt.ylabel('Milhões de detecções multissatélite')
plt.title('Detecções observadas por mês — fev/2025 termina no dia 12')
finish('01_deteccoes_mensais.png')
cobertura = frame('cobertura_meteorologia.parquet')
plt.figure()
plt.plot(cobertura['data'], cobertura['estacoes_com_registro'], label='Algum registro horário', color='#207e89')
plt.plot(cobertura['data'], cobertura['estacoes_chuva_completa'], label='24 medições de precipitação', color='#db8a39')
plt.axvline(pd.Timestamp('2025-02-12'), color='#8d3a46', linestyle='--', label='Fim do arquivo de fogo')
plt.ylabel('Estações'); plt.title('Cobertura meteorológica diária — disponibilidade não é completude')
plt.legend(fontsize=9); finish('02_cobertura_diaria.png')
print('Dias com registro meteorológico:', len(cobertura))
print('Faixa de estações com alguma observação:', int(cobertura.estacoes_com_registro.min()), 'a', int(cobertura.estacoes_com_registro.max()))''')
    md('''**Interpretação:** o recorte temporal é condicionado pelos arquivos efetivamente recebidos. Antes de construir uma população município/dia com classes de risco, é preciso justificar a janela de 43 dias ou obter uma extensão compatível. Uma queda de detecções em um mês parcial não demonstra queda real do risco.''')
    md('''## 3. Ausências após a deduplicação

O percentual abaixo usa as linhas horárias selecionadas, sem misturar o denominador com as duplicatas originais. Precipitação ausente não é convertida em zero; um total parcial permanece identificado pela contagem de horas.''')
    code('''variaveis = ['precipitacao_total', 'temperatura_bulbo_hora', 'umidade_rel_hora', 'vento_velocidade', 'radiacao_global']
ausencias = []
for coluna in variaveis:
    n, faltantes = con.execute(f'SELECT count(*), count(*) FILTER (WHERE "{coluna}" IS NULL) FROM meteo_inequivoca').fetchone()
    ausencias.append({'variavel': coluna, 'faltantes': faltantes, 'percentual': 100*faltantes/n})
ausencias = pd.DataFrame(ausencias).sort_values('percentual')
print(ausencias.to_string(index=False))
plt.figure(); plt.barh(ausencias.variavel, ausencias.percentual, color='#207e89')
plt.xlabel('% de registros ausentes'); plt.xlim(0,100)
plt.title('Ausências nas observações horárias selecionadas')
finish('03_ausencias.png')''')
    md('''## 4. Distribuições e extremos no recorte exploratório de janeiro

As distribuições abaixo são restritas a janeiro de 2025 para reservar fevereiro da análise de relações meteorológicas nesta etapa. Isso **não constitui uma divisão final de treino/teste**. Totais de precipitação usam somente dias com 24 valores. As unidades do dicionário precisam ser corrigidas; mantemos as escalas originais sem converter.

Extremos pelo critério de 1,5 IQR são sinais descritivos, não prova de erro. Nenhuma observação é removida por esse critério.''')
    code('''janeiro = frame('meteorologia_janeiro_exploracao.parquet')
cols = ['precipitacao_total_soma', 'temperatura_bulbo_hora_media', 'umidade_rel_hora_media', 'vento_velocidade_media']
limites = []
plt.figure(figsize=(11,8))
for i,coluna in enumerate(cols,1):
    x = janeiro.loc[janeiro.precipitacao_24h_completa, coluna] if coluna == 'precipitacao_total_soma' else janeiro[coluna]
    x=x.dropna()
    q1,q3=x.quantile([.25,.75]); iqr=q3-q1
    limites.append({'variavel':coluna, 'n':len(x), 'min':x.min(), 'mediana':x.median(), 'max':x.max(), 'fora_1_5_IQR':int(((x<q1-1.5*iqr)|(x>q3+1.5*iqr)).sum())})
    plt.subplot(2,2,i); plt.hist(x,bins=40,color='#207e89'); plt.title(coluna.replace('_',' '),fontsize=10); plt.ylabel('Estação/dia')
plt.suptitle('Distribuições em janeiro de 2025 — escalas originais')
finish('04_distribuicoes_janeiro.png')
print(pd.DataFrame(limites).to_string(index=False))''')
    md('''## 5. Teste de hipótese exploratório: precipitação e umidade

**Premissa operacional:** informações de chuva e umidade podem representar condições relacionadas, devendo ser investigadas antes de combiná-las como preditores. O teste avalia uma relação meteorológica, não o efeito sobre incêndios.

Critérios definidos antes do cálculo: janeiro de 2025; 24 medições de chuva e pelo menos 18 de umidade no dia; dia com chuva se soma > 0; dia sem chuva se soma = 0; no mínimo cinco dias de cada tipo por estação. Cada estação fornece um par de médias de umidade.

H0: a distribuição das diferenças pareadas é simétrica em torno de zero. H1: não é simétrica em torno de zero. Alpha = 0,05. Teste bilateral de Wilcoxon, com diferença arredondada a seis casas para reduzir efeitos de precisão numérica.

Independência entre estações e condições do teste não foram comprovadas; dependência espacial e condições sazonais limitam a inferência. O resultado será apresentado como exploratório, sem extrapolação nacional ou causal. [Método e premissas: documentação SciPy](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.wilcoxon.html).''')
    code('''elegiveis = janeiro.loc[janeiro.precipitacao_24h_completa & (janeiro.horas_umidade_rel_hora >= 18)].copy()
elegiveis['com_chuva'] = elegiveis.precipitacao_total_soma > 0
grupos = elegiveis.groupby(['id_estacao','com_chuva']).umidade_rel_hora_media.agg(['mean','count']).unstack('com_chuva')
pares = grupos.dropna()
pares = pares.loc[(pares['count'][False] >= 5) & (pares['count'][True] >= 5)]
assert len(pares) >= 10, 'Poucos pares para esta exploração.'
diferencas = (pares['mean'][True] - pares['mean'][False]).round(6)
teste = wilcoxon(diferencas.to_numpy(), alternative='two-sided', zero_method='wilcox', method='auto')
hipotese = {'estacoes_pareadas': len(pares), 'alpha': .05, 'estatistica': float(teste.statistic), 'p_valor': float(teste.pvalue), 'mediana_diferenca_umidade_escala_original': float(diferencas.median()), 'fracao_estacoes_diferenca_positiva': float((diferencas>0).mean()), 'carater':'exploratorio; independencia espacial nao comprovada; nao testa risco de incendio'}
assert np.isfinite(teste.pvalue)
(OUT/'hipotese_exploratoria.json').write_text(json.dumps(hipotese,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(hipotese,ensure_ascii=False,indent=2))
print('Decisão condicional às premissas:', 'rejeitar H0' if teste.pvalue < .05 else 'não rejeitar H0')
plt.figure(); plt.hist(diferencas,bins=30,color='#207e89'); plt.axvline(0,color='#8d3a46',linestyle='--')
plt.xlabel('Umidade média em dias com chuva − sem chuva (escala original)')
plt.ylabel('Estações'); plt.title('Comparação pareada por estação — janeiro/2025')
finish('05_hipotese_umidade.png')''')
    md('''**Interpretação:** o tamanho e o sinal da diferença devem ser lidos junto do p-valor e da seleção das estações. A agregação por estação evita tratar todos os dias como pares independentes, mas não elimina a dependência espacial. Este teste não valida o modelo futuro nem determina as classes de risco. A hipótese ligada diretamente ao alvo final deverá ser revista após a definição operacional desse alvo.''')
    md('''## 6. Base preparada e próximos limites

Arquivos derivados:
- `meteorologia_diaria.parquet`: uma linha por estação/data, identificador municipal quando disponível, estatísticas observadas e contagem de horas válidas.
- `meteorologia_horarios_multiplos.parquet`: variantes preservadas para decisão posterior.
- `deteccoes_municipio_dia.parquet`: contagens de detecções por município/data em UTC, sem preenchimento de dias sem foco.
- `mapbiomas_ultimo_ano_sem_legenda.parquet`: ano mais recente disponível, mantendo os códigos originais de classe e área sem tradução ou conversão.

Não houve junção automática entre tabelas, imputação, criação de classes ou treinamento. Dados de um dia completo não podem prever o início desse mesmo dia. Se usados para o dia seguinte, devem respeitar atraso de publicação e o horizonte definido.

Pendências para consolidar a Entrega 1: alvo e classes, legenda/coleção MapBiomas, unidades corretas, população observável município/dia, política para estações/horários ambíguos, recorte temporal e integração. O total de detecções multissatélite não é número de incêndios independentes.''')
    code('''assert con.execute('SELECT count(*) FROM meteo_diaria').fetchone()[0] == resumo['estacoes_dias']
assert con.execute('SELECT count(*) FROM (SELECT id_estacao,data,count(*) n FROM meteo_diaria GROUP BY ALL HAVING n>1)').fetchone()[0] == 0
assert con.execute('SELECT max(horas_observadas) FROM meteo_diaria').fetchone()[0] <= 24
assert con.execute('SELECT sum(deteccoes_multissatelite) FROM fogo_diario').fetchone()[0] == resumo['linhas_deteccoes']
print('Reconciliação, chave diária, limite de horas e conservação de detecções: OK.')
con.close()''')
    namespace = {'__name__': '__notebook__'}
    for i, cell in enumerate((c for c in cells if c.cell_type == 'code'), 1):
        print('Executando célula', i, flush=True)
        outputs = []
        def show():
            for num in plt.get_fignums():
                fig=plt.figure(num); data=io.BytesIO()
                fig.savefig(data,format='png',dpi=120,bbox_inches='tight')
                outputs.append(nbformat.v4.new_output('display_data',data={'image/png':base64.b64encode(data.getvalue()).decode('ascii')},metadata={}))
            plt.close('all')
        plt.show = show
        text = io.StringIO()
        with contextlib.redirect_stdout(text):
            exec(compile(cell.source, '<notebook>', 'exec'), namespace)
        if text.getvalue():
            outputs.insert(0,nbformat.v4.new_output('stream',name='stdout',text=text.getvalue()))
        cell.execution_count=i
        cell.outputs=outputs
    nb=nbformat.v4.new_notebook(cells=cells,metadata={'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},'language_info':{'name':'python','version':sys.version.split()[0]}})
    nbformat.validate(nb)
    nbformat.write(nb,ROOT/'02_eda_preparacao_queimadas.ipynb')
    print('Notebook executado e validado.',flush=True)


if __name__ == '__main__':
    build()
