# 6. Demonstração da plataforma

Duração: **3min43s**, com a plataforma rodando em `http://127.0.0.1:8766`. O vídeo usa captura da aplicação real e narração neural em português brasileiro, identificada na entrega. Pode ser substituído por uma gravação narrada pelos integrantes se a disciplina assim exigir.

| Tempo aproximado | Tela / ação | Conteúdo |
| --- | --- | --- |
| 0:00–0:36 | Visão do campo | Problema, continuidade da Fase 5, três propriedades e dados sintéticos |
| 0:36–1:14 | Fluxo de dados | Sensores, Bronze, Silver, Gold, modelo, regras e qualidade |
| 1:14–1:50 | Sensores: executar seca em Boa Vista | Descrever os sensores, cenário, semente e execução integrada |
| 1:50–2:28 | Inteligência & alertas | Probabilidade, regras acionadas, evidência e validação humana |
| 2:28–3:04 | Visão do campo e recuperação | Histórico, filtros e comparação após chuva |
| 3:04–3:43 | Falha de sensor e conclusão | Quarentena, indisponibilidade de dados e evolução para Fase 7 |

## Conferência da gravação

- A propriedade-alvo é Fazenda Boa Vista e a semente é 42.
- Mostrar a confirmação de conclusão ao executar cada cenário.
- Explicar que os dados e o contexto orbital são sintéticos e que o processamento é executado em lote.
- Distinguir risco do modelo de classificação final pelas regras.
- Distinguir um mapa ilustrativo de uma imagem orbital real.
- Deixar explícito que a automação registra alertas e recomendações, sem acionar irrigação real.
- Conferir áudio, legibilidade e duração de 3 a 5 minutos antes do upload.

O link público está em `entrega.json`. Se a instituição restringir os serviços aceitos, publique o mesmo MP4 em YouTube não listado ou Drive e atualize o link.

## Como a nova narração foi produzida

A versão inicial usava a voz Luciana do macOS. Esta revisão usa o modelo neural aberto [Kokoro](https://huggingface.co/hexgrad/Kokoro-82M), com a voz brasileira `pf_dora`, por meio do [kokoro-onnx](https://github.com/thewh1teagle/kokoro-onnx). A geração acontece localmente, sem API de voz, conta paga ou clonagem de voz de pessoa específica. A voz continua sendo sintética. O modelo é Apache 2.0; a biblioteca é MIT.

O texto foi reescrito em linguagem de apresentação, mantendo os resultados e limites do projeto. A velocidade de síntese é `1.05`; cada trecho tem apenas 0,8 segundo de margem, com entrada da voz após 0,25 segundo. O volume é normalizado para -16 LUFS, com pico-alvo de -1,5 dBTP. A tela é recapturada na duração de cada trecho, sem acelerar artificialmente a voz pronta.

Para reproduzir, instale `requirements-video.txt` em um ambiente Python 3.12 isolado e baixe os pesos oficiais para `tmp/tts-model/`:

- [kokoro-v1.0.onnx](https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.1/kokoro-v1.0.onnx), SHA-256 `beb0d1848dee9a49da392cc3df26958d46cfa35d321edf434f52949153f0df3a`.
- [voices-v1.0.bin](https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.1/voices-v1.0.bin), SHA-256 `bca610b8308e8d99f32e6fe4197e7ec01679264efed0cac9140fe9c29f1fbf7d`.

Execute `python scripts/prepare_video.py`, grave a aplicação com `node scripts/record_video.mjs` (requer Playwright/Chromium e a API local), monte com `python scripts/assemble_video.py` e valide com `python scripts/check_video.py`. `PLAYWRIGHT_MODULE` e `CHROME_PATH` permitem indicar instalações existentes. Os pesos de voz e temporários não são incluídos no Git nem no ZIP; não são necessários para assistir ao MP4 ou executar a plataforma.
