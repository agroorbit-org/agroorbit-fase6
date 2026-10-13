# 4. Automação inteligente

A decisão combina um **Random Forest real reaproveitado do projeto anterior** com regras explícitas sobre os dados processados. O termo “real” refere-se à execução do algoritmo treinado; tanto seu treinamento como as entradas desta demonstração são sintéticos.

## Modelo

O exportador copia categorias do OneHotEncoder, médias e escalas do StandardScaler e as 300 árvores do artefato `agroorbit-ai/models/best_model.pkl`. A inferência Python percorre as árvores e calcula a média das probabilidades das folhas. A conversão para float32 antes das comparações reproduz o comportamento das árvores do sklearn.

Entrada: estado, cultura, temperatura mínima/máxima, chuva diária, NDVI, NDWI, cobertura de nuvens, chuva de 7/14 dias, amplitude térmica, tendência de NDVI de sete dias, dias sem chuva e mês. São **14 features**. Umidade do solo e luminosidade não são entradas do modelo legado; a umidade também alimenta as regras diretamente.

A paridade foi verificada em 500 entradas determinísticas, incluindo categorias desconhecidas. O relatório `models/export_validation.json` registra hashes de origem/destino, tolerância e erro máximo. Essa comparação verifica a implementação da inferência, **não mede acurácia agronômica nem valida a nova distribuição simulada**.

As métricas do projeto AI anterior são históricas e baseadas em dados sintéticos. Elas não são apresentadas como desempenho da Fase 6. A calibração em dados de campo, a avaliação temporal e por produtor e a revisão dos limiares são necessárias antes de uma aplicação operacional.

## Motor de decisão

| Regra | Condição | Classificação |
| --- | --- | --- |
| Q01 | Último dia ausente ou com menos de 24 leituras válidas | Dados desatualizados; suspender decisão atual |
| R01 | Umidade média do solo <25% | Alto risco |
| R02 | 25% ≤ umidade média <40% | Atenção |
| R03 | Temperatura máxima ≥35 °C e solo <35% | Alto risco |
| R04 | Chuva de 7 dias <10 mm e tendência NDVI <-0,04 | Atenção |
| M01 | Probabilidade do modelo ≥70% | Alto risco |
| M02 | 50% ≤ probabilidade <70% | Atenção |
| R00 | Nenhuma regra de risco acionada | Estável |

Quando mais de uma regra se aplica, vence a maior severidade, preservando **todos os motivos**. Q01 tem precedência sobre recomendações agronômicas atuais. Limiar numérico ausente não é tratado como zero para o modelo. Uma tendência ainda não disponível não dispara R04.

## Saída automatizada

Cada alerta contém lote, propriedade, talhão, data, classificação, recomendação, versão das regras, razões e os 24 `event_id` usados como evidência do dia. O alerta de indisponibilidade usa uma lista vazia de evidências atuais, pois elas não existem.

Exemplo no cenário de seca: “Priorizar inspeção do talhão e avaliar a necessidade de irrigação com o responsável técnico.” O sistema **registra** essa saída; não precisa de clique adicional para classificar ou gerar o alerta. O clique apenas inicia o novo lote simulado.

Não se calcula SHAP nesta entrega. Os motivos mostrados são regras, claramente identificadas na interface. Não há atuação física, envio de mensagens, dosagem nem prescrição de defensivos.
