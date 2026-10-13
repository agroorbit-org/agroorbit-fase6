// Captura a aplicação real; a montagem sincroniza cada trecho com sua narração.
import { createRequire } from 'node:module';
import { readFile, mkdir, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const require = createRequire(import.meta.url);
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const output = path.join(root, 'tmp', 'video');
const segments = JSON.parse(await readFile(path.join(output, 'segments.json'), 'utf8'));
const browser = await chromium.launch({ headless: true, ...(process.env.CHROME_PATH ? { executablePath: process.env.CHROME_PATH } : {}) });
const url = process.env.AGROORBIT_URL || 'http://127.0.0.1:8766';
const reset = await browser.newContext();
await reset.request.post(url + '/api/simulate', { data: { scenario: 'baseline', target: 'faz-002', seed: 42 } });
await reset.close();
try {
  for (let i = 0; i < segments.length; i++) {
    const context = await browser.newContext({ viewport: { width: 1440, height: 1000 }, recordVideo: { dir: output, size: { width: 1440, height: 1000 } }, deviceScaleFactor: 1, reducedMotion: 'reduce' });
    const page = await context.newPage();
    const start = Date.now();
    const at = async seconds => { const delay = seconds * 1000 - (Date.now() - start); if (delay > 0) await page.waitForTimeout(delay); };
    const navigate = async name => page.getByRole('navigation').getByRole('button', { name: new RegExp('^' + name) }).click();
    const run = async scenario => { await navigate('Sensores & simulação'); await page.getByLabel('Cenário da simulação').selectOption(scenario); const response = page.waitForResponse(r => r.url().endsWith('/api/simulate') && r.request().method() === 'POST'); await page.getByRole('button', { name: 'Executar simulação', exact: true }).click(); if (!(await response).ok()) throw new Error('Falha na simulação'); await page.getByRole('status').waitFor(); };
    await page.goto(url);
    await page.getByRole('heading', { name: 'Visão do campo.' }).waitFor();
    await page.evaluate(() => document.fonts.ready);
    console.log(`Gravando ${i + 1}/6: ${segments[i].title} (${segments[i].duration}s)`);
    if (i === 0) { await at(25); await page.locator('.farms-card').scrollIntoViewIfNeeded(); }
    if (i === 1) { await navigate('Fluxo de dados'); await at(23); await page.locator('.quality-list').scrollIntoViewIfNeeded(); }
    if (i === 2) { await navigate('Sensores & simulação'); await at(14); await run('seca'); await at(29); await page.locator('table').scrollIntoViewIfNeeded(); }
    if (i === 3) { await navigate('Inteligência & alertas'); await at(28); await page.locator('.alerts-list').scrollIntoViewIfNeeded(); }
    if (i === 4) { await page.getByLabel('Indicador do gráfico').selectOption('temperature_c'); await at(10); await run('chuva'); await at(15); await page.getByLabel('Fechar aviso').click(); await navigate('Visão do campo'); }
    if (i === 5) { await run('falha'); await at(10); await page.getByLabel('Fechar aviso').click(); await navigate('Visão do campo'); await at(22); await navigate('Fluxo de dados'); await page.locator('table').scrollIntoViewIfNeeded(); }
    await at(segments[i].duration + 1);
    const video = page.video();
    await context.close();
    segments[i].video = await video.path();
  }
  const finish = await browser.newContext();
  await finish.request.post(url + '/api/simulate', { data: { scenario: 'baseline', target: 'faz-002', seed: 42 } });
  await finish.close();
  await writeFile(path.join(output, 'recorded.json'), JSON.stringify(segments, null, 2));
} finally { await browser.close(); }
