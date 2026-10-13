# 3. Processamento e preparação

O pipeline é executado em Python usando apenas a biblioteca padrão. O mesmo código é utilizado pelo terminal, pelos testes e pela API acionada pelo dashboard.

1. Preservar cada evento no Bronze JSONL.
2. Exigir identificadores, `telemetry.v2`, `simulated=true` e propriedade/talhão cadastrados.
3. Validar horários com timezone, em intervalos inteiros de hora dentro da janela demonstrativa.
4. Validar números finitos e faixas. Valores booleanos, ausentes, NaN e infinito não são aceitos como medidas.
5. Remover retransmissões exatas por `source + event_id`. Conteúdo conflitante ou mais de uma leitura por talhão/hora vai para quarentena.
6. Gravar Silver ordenada por propriedade e horário.
7. Agregar por propriedade/dia e construir Gold com features, risco e decisão.
8. Gerar alertas, resumo de qualidade, snapshot do dashboard e hashes SHA-256.

| Medida | Faixa válida |
| --- | --- |
| Temperatura | -20 a 60 °C |
| Umidade relativa do solo | 0 a 100% |
| Luminosidade | 0 a 150.000 lux |
| Chuva por intervalo | 0 a 300 mm |
| NDVI / NDWI | -1 a 1 |
| Cobertura de nuvens | 0 a 100% |

As unidades são definidas no contrato. Não se tenta adivinhar ou converter silenciosamente uma unidade diferente; dados de outro contrato devem passar por um adaptador explícito.

## Agregações

- Solo, temperatura e luz: média aritmética diária das leituras válidas.
- Temperatura mínima/máxima: extremos observados no dia.
- Chuva diária: **soma**, não média, dos incrementos horários.
- Chuva de 7/14 dias: soma por propriedade na janela de calendário, incluindo o dia atual.
- Dias sem chuva: sequência de dias completos com menos de 1 mm/dia; uma lacuna torna a sequência desconhecida até um novo dia com chuva.
- NDVI/NDWI: contexto sintético diário; tendência de NDVI = dia atual menos o dia de sete dias antes.
- Amplitude térmica: máxima menos mínima.

Janelas iniciais de chuva são parciais. O campo `ml_ready` é falso até haver 14 dias completos, tendência de sete dias disponível e sequência seca calculável. Uma decisão diária também é indisponível quando há menos de 24 leituras. O dashboard atual exige um dia completo na data final da janela; não usa um dia antigo como atual.

## Reconciliação e replay

No cenário habitual, semente 42: **1.013 recebidos = 1.008 aceitos + 4 em quarentena + 1 duplicata**. Resultam 42 linhas Gold, uma por propriedade/dia. A taxa de aceitação é 1.008 / 1.013 = **99,51%**; o denominador inclui retransmissões.

`python3 -m backend.pipeline --input data/sample/bronze.jsonl --output data/runs/replay` reprocessa os eventos preservados. O teste de idempotência compara os hashes de todos os artefatos de dados e exige igualdade. Datas não são substituídas pelo relógio do computador.
