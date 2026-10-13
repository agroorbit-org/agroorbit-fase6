// npm install --no-save playwright (optional QA dependency), then:
// node scripts/browser_check.mjs
// PLAYWRIGHT_MODULE and CHROME_PATH may select an existing local runtime.
import { createRequire } from 'node:module';
import { mkdir, writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import assert from 'node:assert/strict';

const require = createRequire(import.meta.url);
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const output = path.join(root, 'docs', 'evidencias');
await mkdir(output, { recursive: true });
const browser = await chromium.launch({ headless: true, ...(process.env.CHROME_PATH ? { executablePath: process.env.CHROME_PATH } : {}) });
const context = await browser.newContext({ viewport: { width: 1440, height: 1080 }, deviceScaleFactor: 1, reducedMotion: 'reduce' });
const page = await context.newPage();
const errors = [];
page.on('pageerror', e => errors.push(e.message));
const url = process.env.AGROORBIT_URL || 'http://127.0.0.1:8766';
const results = [];
async function check(name, action) { await action(); results.push({ name, passed: true }); console.log('PASS', name); }
async function screenshot(name) { await page.evaluate(() => document.fonts.ready); await page.screenshot({ path: path.join(output, name), fullPage: true, animations: 'disabled' }); }
async function navigate(label) { await page.getByRole('navigation').getByRole('button', { name: new RegExp('^' + label) }).click(); }
async function run(scenario) {
  await navigate('Sensores & simulação');
  await page.getByLabel('Cenário da simulação').selectOption(scenario);
  const response = page.waitForResponse(r => r.url().endsWith('/api/simulate') && r.request().method() === 'POST');
  await page.getByRole('button', { name: 'Executar simulação', exact: true }).click();
  assert.equal((await response).status(), 200);
  await page.getByRole('status').waitFor();
  await page.getByLabel('Fechar aviso').click();
  return (await context.request.get(url + '/api/dashboard')).json();
}
try {
  await context.request.post(url + '/api/simulate', { data: { scenario: 'baseline', target: 'faz-002', seed: 42 } });
  await page.goto(url);
  await page.getByRole('heading', { name: 'Visão do campo.' }).waitFor();
  await check('Dashboard e indicadores calculados', async () => {
    assert.equal(await page.locator('.metric-card').count(), 4);
    assert.equal(await page.locator('tbody tr').count(), 3);
    assert.equal(await page.getByText('Pipeline conectado', { exact: true }).count(), 1);
    await screenshot('01-dashboard.png');
  });
  await check('Filtro de propriedade e série de 7 dias', async () => {
    await page.getByLabel('Propriedade selecionada').selectOption('faz-001');
    await page.getByRole('button', { name: '7 dias', exact: true }).click();
    await page.getByLabel('Indicador do gráfico').selectOption('temperature_c');
    assert.match(await page.locator('.history-chart').getAttribute('aria-label'), /Sítio Horizonte, últimos 7 dias/);
    await page.getByLabel('Indicador do gráfico').selectOption('chuva_mm');
    assert.match(await page.locator('.history-chart').getAttribute('aria-label'), /Precipitação/);
    await page.getByLabel('Propriedade selecionada').selectOption('faz-002');
    await page.getByRole('button', { name: '14 dias', exact: true }).click();
    await page.getByLabel('Indicador do gráfico').selectOption('soil_moisture_pct');
  });
  let dryProbability;
  await check('Simulação de seca → inferência → alertas', async () => {
    const data = await run('seca');
    const farm = data.farms.find(f => f.id === 'faz-002');
    assert.equal(farm.decision.level, 'alto');
    dryProbability = farm.latest.risk_probability;
    await screenshot('02-simulador.png');
    await navigate('Inteligência & alertas');
    assert.match(await page.locator('.evidence-list').innerText(), /R01/);
    await screenshot('03-automacao-seca.png');
    await navigate('Visão do campo');
    await screenshot('04-dashboard-seca.png');
  });
  await check('Recuperação após chuva reduz estimativa do modelo', async () => {
    const data = await run('chuva');
    assert.ok(data.farms[1].latest.risk_probability < dryProbability);
    await navigate('Visão do campo');
    await screenshot('05-dashboard-chuva.png');
  });
  await check('Falha de sensor suspende os indicadores atuais', async () => {
    const data = await run('falha');
    assert.equal(data.farms[1].available, false);
    await navigate('Visão do campo');
    assert.equal(await page.locator('.metric-number').first().innerText(), '—%');
    await screenshot('06-falha-sensor.png');
    await navigate('Fluxo de dados');
    await screenshot('07-pipeline-qualidade.png');
  });
  await check('Download real de dataset do lote atual', async () => {
    const downloadPromise = page.waitForEvent('download');
    await page.getByRole('link', { name: 'gold.csv', exact: true }).click();
    const download = await downloadPromise;
    assert.equal(download.suggestedFilename(), 'gold.csv');
    assert.equal(await download.failure(), null);
  });
  await check('Navegação e layout responsivo em 390px', async () => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.getByLabel('Abrir navegação').click();
    await navigate('Visão do campo');
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth));
    await screenshot('08-mobile.png');
    await page.getByLabel('Abrir navegação').click();
    await navigate('Sensores & simulação');
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth));
  });
  await check('Snapshot desconectado explicitamente somente leitura', async () => {
    await page.route('**/api/dashboard', route => route.abort());
    await page.reload();
    await page.getByText(/Exibindo o dataset versionado/).waitFor();
    await page.getByLabel('Abrir navegação').click();
    await navigate('Sensores & simulação');
    assert.equal(await page.getByRole('button', { name: 'Executar simulação', exact: true }).isDisabled(), true);
    await page.unroute('**/api/dashboard');
  });
  await check('Nenhum erro JavaScript na execução', async () => assert.deepEqual(errors, []));
  await context.request.post(url + '/api/simulate', { data: { scenario: 'baseline', target: 'faz-002', seed: 42 } });
  await writeFile(path.join(output, 'browser-validation.json'), JSON.stringify({ checks: results, total: results.length, passed: results.length, javascript_errors: errors, viewport_desktop: '1440x1080', viewport_mobile: '390x844' }, null, 2) + '\n');
} finally {
  await browser.close();
}
