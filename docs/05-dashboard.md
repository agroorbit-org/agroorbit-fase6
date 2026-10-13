# 5. Dashboard analítico

O dashboard React lê `/api/dashboard` e usa os mesmos resultados exportados nos arquivos Silver, Gold e alertas. Os botões de simulação chamam `POST /api/simulate`; a resposta publica o novo lote inteiro de uma vez.

| Indicador | Cálculo e significado |
| --- | --- |
| Umidade do solo | Média das 24 leituras do último dia completo do talhão selecionado |
| Temperatura | Média diária; máxima diária apresentada no texto de apoio |
| Chuva acumulada | Soma da precipitação dos últimos sete dias da propriedade |
| Risco de seca | Probabilidade produzida pelas 300 árvores após 14 dias completos |
| NDVI | Contexto orbital sintético do último dia, exibido na tabela das propriedades |
| Condição atual | Maior severidade das regras e do modelo, ou indisponível quando a coleta está incompleta |
| Taxa de aceitação | Leituras aceitas divididas por todos os eventos recebidos |
| Alertas atuais | Propriedades em atenção, alto risco ou com dados desatualizados no lote |

O usuário pode filtrar a propriedade, escolher janela de 7 ou 14 dias e trocar o gráfico entre umidade, temperatura e chuva. Os dois primeiros usam médias diárias; chuva usa soma diária. Os eixos apresentam unidades e datas. Dias sem dados não são interpolados. O mapa é ilustrativo e está explicitamente rotulado; não é uma imagem de satélite nem um contorno geográfico real.

## Telas

1. **Visão do campo**: KPIs, série temporal, contexto da área e comparação entre propriedades.
2. **Sensores & simulação**: sensores virtuais, cenário, semente, execução e últimas leituras válidas.
3. **Fluxo de dados**: arquitetura executada, reconciliação, quarentena e downloads do lote atual.
4. **Inteligência & alertas**: probabilidade, regras, recomendações e evidências.
5. **Guia da demonstração**: roteiro navegável de 3–5 minutos.

Sem a API, o snapshot versionado serve apenas para leitura. A interface sinaliza esse modo e desativa execução/downloads dinâmicos. Não se apresenta uma simulação desconectada como operação bem-sucedida.

Capturas em `docs/evidencias/` foram obtidas da aplicação executada, com cenários habitual, seca, chuva e falha. A interface inclui responsividade, rótulos de formulários, navegação por teclado, foco visível e mensagens de status.
