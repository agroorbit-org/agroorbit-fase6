# 2. Coleta de dados do ambiente

A ferramenta equivalente escolhida é o **simulador AgroOrbit em software**, controlado pela tela Sensores & simulação. Ele reproduz sensores virtuais e eventos ambientais; não pretende reproduzir eletricamente uma placa Arduino. O enunciado admite IoT ou simulação, incluindo ferramenta equivalente ao TinkerCad.

| Sensor virtual | Campo / unidade | Comportamento |
| --- | --- | --- |
| Temperatura ambiente | `temperature_c` / °C | Ciclo diário e ruído reprodutível; aumenta na seca |
| Umidade do solo | `soil_moisture_pct` / % relativo | Tendência por propriedade; cai na seca e sobe após chuva |
| Luminosidade | `luminosity_lux` / lux | Ciclo diurno senoidal, próximo de zero à noite |
| Pluviômetro | `rain_mm` / mm no intervalo horário | Eventos de chuva concentrados em horários definidos |

NDVI, NDWI e cobertura de nuvens são **contexto orbital simulado** gerado separadamente do conceito dos sensores físicos. Eles permitem manter o contrato de entrada do modelo anterior; não foram obtidos de Sentinel-2 nesta execução. Não há alegação de calibração entre umidade relativa e umidade volumétrica real.

São três propriedades fictícias e um talhão por propriedade. A janela fixa de 14 dias tem 24 amostras horárias por dia: **3 × 14 × 24 = 1.008 leituras únicas esperadas**. A simulação é executada em lote; não demora 14 dias nem constitui telemetria real em streaming.

## Cenários

- Habitual: gera o monitoramento-base das três propriedades.
- Estresse hídrico: a partir do oitavo dia, altera solo, temperatura, chuva e NDVI apenas no alvo.
- Recuperação após chuva: eleva a umidade, reduz a temperatura e simula recuperação gradual da vegetação apenas no alvo.
- Falha de sensor: as 24 leituras do último dia do alvo têm a umidade ausente e são rejeitadas.

Há ainda uma retransmissão exata e quatro falhas intencionais em todo lote: umidade fora de faixa, temperatura ausente, horário inválido e propriedade desconhecida. Por isso o lote habitual recebe **1.013 eventos**. Essas falhas existem para demonstrar a preparação e os controles de qualidade.

Código: `backend/simulator.py`. Exemplo completo: `data/sample/bronze.jsonl`. Captura: `docs/evidencias/02-simulador.png`.

O identificador do lote deriva da versão do simulador, cenário, propriedade-alvo e semente. Cada fazenda usa seu próprio gerador pseudoaleatório, garantindo isolamento entre cenários.
