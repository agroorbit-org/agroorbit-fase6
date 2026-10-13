# 8. Proveniência e continuidade

| Fonte | Commit usado | Uso nesta entrega |
| --- | --- | --- |
| https://github.com/agroorbit-org/agroorbit-fase5 | `7342e24cfe76614288d60977ea27ffbc89ca559f` | Marca Horizon, propriedades, conceitos de contrato e camadas de dados |
| https://github.com/agroorbit-org/agroorbit-ai | `94bdf06312fdbf12568166bb692ac24a243c3e9f` | Modelo Random Forest e pré-processadores treinados |
| https://github.com/agroorbit-org/agroorbit-vision | `0ae7cbc85cbb38380b68cd6cbb881dfb1917ad5f` | Referência do módulo orbital; não executado no fluxo principal |

Os três repositórios originais foram consultados e preservados. Esta Fase 6 possui código próprio para simulação, processamento, inferência portátil, automação e interface.

## Artefato do modelo

O arquivo `models/export_validation.json` registra o SHA-256 do `.pkl` original e do JSON comprimido. `scripts/export_model.py` é a receita de exportação e validação. O ambiente opcional usa as versões de numpy, pandas, joblib e scikit-learn do projeto AI original. A exportação não retreina o modelo, não altera seus pesos e não converte suas probabilidades em acurácia.

## Escopo da integração

**Ativo e demonstrado:** sensor virtual → preparação → features → Random Forest → regras → alertas e dashboard. Organização Bronze/Silver/Gold implementada em arquivos locais.

**Planejado para Fase 7:** adaptação de sensores físicos ou MQTT; fontes orbitais/climáticas reais; integração em execução com a CNN de cobertura do solo; autenticação; banco persistente; avaliação em dados reais; validação agronômica e monitoramento de deriva. Esses itens não são apresentados como já entregues.

O conjunto desta Fase 6 não contém tiles EuroSAT, imagens recoloridas, chamadas Sentinel-2, NASA POWER ou previsões meteorológicas reais. O diagrama do sensor, o mapa ilustrativo e o dashboard são elementos vetoriais/code-native criados para esta entrega.

## Apoio de ferramentas

Código, documentação e materiais de apresentação foram preparados com assistência de IA e devem ser revisados pelo autor. A narração automatizada do vídeo, quando presente, é voz sintetizada, não gravação do autor. As métricas e capturas são provenientes de execuções do código; os dados de entrada são simulados.
