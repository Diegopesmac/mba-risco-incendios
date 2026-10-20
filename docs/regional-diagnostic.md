# Diagnóstico regional da base candidata

Executar `python scripts/diagnose_regions.py` depois da aquisição e auditoria. O diagnóstico compara a candidata com um calendário completo por UF, sem escolher regiões em função de terem apresentado detecções. As 27 unidades são fixadas pelo [cadastro oficial do IBGE](https://servicodados.ibge.gov.br/api/v1/localidades/estados), consultado em 20/10/2026. Essa população serve ao diagnóstico; a unidade final da previsão depende da decisão científica e da tutoria.

## Contrato da saída local

| Campo | Significado |
|---|---|
| `state`, `date` | Chave única UF/dia; calendário anual completo, inclusive 29 de fevereiro |
| `recorded_detection_count` | Número de registros do acervo quando positivo; vazio quando não há registro |
| `archive_status` | `recorded_detection`, `no_regional_record` ou `national_archive_gap` |
| `coverage_status` | `unverified` em todas as linhas; a existência de registro nacional não demonstra cobertura completa de uma UF |

`national_archive_gap` identifica dias sem registros em todo o acervo fornecido. Não determina se ocorreu falha do satélite, ausência de fogo detectável ou outro problema. `no_regional_record` significa apenas que não há registro daquela UF no dia. Nenhum dos dois vira zero, classe negativa ou feature disponível operacionalmente. A data deriva do campo `data_pas`; disponibilidade real da observação e fuso operacional ainda precisam ser documentados.

O comando bloqueia arquivos cujo hash diverge do manifesto, contagens divergentes, esquemas inesperados, regiões fora da população, datas fora do ano declarado, campos ausentes e IDs repetidos entre arquivos. Repetição de ID exige investigação; não é descartada silenciosamente. Diferentes IDs não provam incêndios físicos independentes.

O resumo registra hashes das entradas, do manifesto e do CSV, população, contagens e datas nacionais sem registro. A reprodução usa os mesmos arquivos auditados e não altera o manifesto original. Os derivados ficam fora do Git. Mais de 10 mil linhas de calendário não comprovam mais de 10 mil exemplos supervisionados válidos.

## Próximas decisões científicas

Antes de construir o painel supervisionado: validar região, horizonte e alvo com a tutoria; investigar observabilidade e datas sem registro; escolher meteorologia com disponibilidade temporal demonstrada; decidir como avaliar generalização temporal e espacial. Não treinar com as linhas deste diagnóstico como se fossem uma base rotulada.
