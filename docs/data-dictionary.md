# Dicionário da base consolidada

Arquivo: `submission/painel_modelagem.csv`, UTF-8, separador vírgula. Uma linha por município/data UTC com índice e meteorologia elegíveis. 1.329 linhas e 17 colunas nesta versão; todas as linhas do painel original são preservadas, incluindo 72 de intervalo (`gap`).

Somente `chuva_d2`, `temperatura_d2`, `umidade_d2` e `vento_d2` entram no modelo. Alvos, IDs, contagens em D e controles temporais não são features. As unidades meteorológicas do material de origem são inconsistentes: preservamos a escala original, sem afirmar mm, °C ou m/s sem confirmação.

| Coluna | Tipo/escala | Papel | Significado e regra |
|---|---|---|---|
| `id_municipio` | texto de 7 dígitos | chave | Código IBGE do município; não é feature. |
| `data` | data UTC | chave | Dia D do índice registrado; chave com id_municipio. |
| `target_index` | real [0,1] | alvo contínuo | Mediana dos índices válidos das detecções no município/dia; nunca feature. |
| `detection_records` | inteiro positivo | auditoria | Quantidade de registros multissatélite em D; não são incêndios independentes, nunca feature. |
| `valid_index_records` | inteiro positivo | auditoria | Registros em D com índice válido; nunca feature. |
| `weather_date` | data UTC | disponibilidade | Dia das medições meteorológicas: D−2. |
| `chuva_d2` | real não negativo, escala original | feature | Média municipal dos totais diários de chuva das estações elegíveis; exige 24 medições por estação. |
| `temperatura_d2` | real, escala original | feature | Média municipal das médias diárias de temperatura; ao menos 18 medições por estação. |
| `umidade_d2` | real [0,100], escala original | feature | Média municipal das médias diárias de umidade; ao menos 18 medições por estação. |
| `vento_d2` | real não negativo, escala original | feature | Média municipal das médias diárias de velocidade do vento; ao menos 18 medições por estação. |
| `eligible_stations` | inteiro positivo | cobertura | Número de estações que atendem simultaneamente aos critérios das quatro features; não é feature. |
| `target` | baixo, medio ou alto | alvo categórico | target_index ≤0,40: baixo; >0,40 e ≤0,70: medio; >0,70: alto. Ausência não vira baixo. |
| `split` | train, validation, test ou gap | partição | Partição temporal predefinida; gap é excluído do ajuste e da avaliação. |
| `prediction_issued_at` | instante UTC | disponibilidade | Emissão simulada: 00:00 de D. |
| `target_window_end` | instante UTC | disponibilidade | Fim exclusivo da janela prevista: 00:00 de D+1. |
| `assumed_features_available_at` | instante UTC | disponibilidade | Disponibilidade assumida: 00:00 de D; atraso histórico não comprovado. |
| `historical_publication_verified` | booleano | limitação | Sempre falso nesta versão; disponibilidade histórica não foi comprovada. |

## Ausências, origem e partições

O painel não tem ausências. Índices inválidos, municípios/dias sem índice e meteorologia insuficiente são excluídos antes da junção; a exclusão não cria rótulo baixo. Ver `submission/evidence/panel-summary.json` e o notebook de auditoria para denominadores.

Treino: 764 exemplos (03–25/01/2025); validação: 183 (27/01–02/02); teste: 310 (04–12/02); intervalos: 72 (26/01 e 03/02). CSV não permite inferir tipos: leia id_municipio como texto para preservar zeros. `fire_risk.submission.read_panel` preserva o código e converte datas; `verify_submission` verifica hashes e partições.

A base é derivada dos quatro arquivos fornecidos pelo curso, sem nomes de pessoas, credenciais ou registros individuais de detecção. Esta cópia acompanha a avaliação no repositório privado; não concede licença de redistribuição pública dos originais.
