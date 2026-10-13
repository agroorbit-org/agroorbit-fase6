# 9. Validação da entrega

## Backend

Executado: `npm test` (Python 3.9.6). Resultado: **16 testes aprovados**.

Cobertura dos comportamentos relevantes:

- geração determinística e isolamento entre propriedades;
- reconciliação de contagens e preservação da quarentena;
- rejeição de valores ausentes, não finitos, booleanos e horários inválidos;
- conflito entre eventos com a mesma identificação;
- chuva como soma diária, não média;
- janela mínima de 14 dias para a inferência;
- risco maior na seca e menor na recuperação;
- falha de sensor sem apresentação de dados antigos como atuais;
- fronteiras das regras de classificação;
- replay com todos os hashes idênticos;
- probabilidades iguais aos casos de referência do modelo original;
- saúde da API, execução de cenários, downloads e lote consistente;
- payload inválido sem alterar o lote corrente;
- restrição de origem nas escritas e allowlist de arquivos para download.

O lote habitual também foi reconstruído em Python 3.12, produzindo os mesmos checksums da execução em Python 3.9.

## Navegador

Resultado: **9 verificações aprovadas**, sem erros JavaScript capturados. Relatório: `docs/evidencias/browser-validation.json`.

Foram usados Chromium/Chrome, viewport desktop de 1440×1080 e mobile de 390×844. Os testes exercitaram o frontend conectado ao backend, incluindo mudança de propriedade, período e indicador, cenários de seca/chuva/falha, download de CSV e modo somente leitura quando a API não está disponível.

As capturas em `docs/evidencias/` são saídas de navegador, não montagens representando funcionalidades inexistentes.

## Modelo e material de apresentação

- Modelo: 500 entradas comparadas com o Random Forest original. Erro máximo `3.3306690738754696e-16`, menor que `1e-12`. Detalhes em `models/export_validation.json`.
- Interface: `npm run build` concluído. As dependências do projeto não apresentaram vulnerabilidades no audit da instalação.
- PDF: gerado por ReportLab, renderizado e revisado visualmente; nove páginas.
- Vídeo: captura real da aplicação, narrada por voz sintetizada. Duração, codecs e verificação de decodificação em `output/video/video-info.json` e `video-validation.json`.
- ZIP: o empacotador reabre o arquivo, verifica CRC e confere SHA-256 de todos os itens contra o manifesto.

Esses resultados comprovam o funcionamento de software dentro do cenário demonstrativo. Não são resultados de sensores físicos nem avaliação agronômica em dados reais.
