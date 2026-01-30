#!/usr/bin/env node
import fs from 'fs';
import path from 'path';
import readline from 'readline/promises';
import { stdin as input, stdout as output } from 'process';
import { spawnSync } from 'child_process';
import url from 'url';
import { EngineClient } from './ipc_client.js';

const __dirname = path.dirname(url.fileURLToPath(import.meta.url));

const rl = readline.createInterface({ input, output });

const engineMode = process.env.HXTRACTOR_ENGINE || 'real';
const enginePath = resolveEnginePath();
if (engineMode === 'real') {
  const check = spawnSync('python3', ['-V']);
  if (check.status !== 0) {
    console.error('ERROR: python3 no disponible. Instala Python 3 y reintenta.');
    process.exit(1);
  }
  const deps = spawnSync(
    'python3',
    ['-c', 'import scrapy, parsel, requests, lxml'],
    { env: withPythonPath(enginePath) }
  );
  if (deps.status !== 0) {
    console.error('ERROR: dependencias Python faltantes. Instala con:');
    console.error('python3 -m pip install scrapy parsel requests lxml');
    process.exit(1);
  }
}

const client = new EngineClient({
  mode: engineMode === 'real' ? 'real' : 'mock',
  enginePath
});
client.start();

let lastCandidates = [];
let lastResult = null;
let ficha = null;

client.onMessage((msg) => {
  if (msg.type === 'status') console.log(`> ${msg.value}`);
  if (msg.type === 'progress') console.log(`> Progreso: ${msg.value}%`);
  if (msg.type === 'log') console.log(`- ${msg.value}`);
  if (msg.type === 'candidates') lastCandidates = msg.value || [];
  if (msg.type === 'result') lastResult = msg.value;
  if (msg.type === 'ficha_update') ficha = msg.value;
  if (msg.type === 'error') console.error(`ERROR: ${msg.value?.message || 'Error'}`);
});

async function menu() {
  console.log('\nHXTRACTOR CLI');
  console.log('1) Analizar componente');
  console.log('2) Ver ficha agregada');
  console.log('3) Exportar ficha');
  console.log('4) Reset ficha');
  console.log('5) Salir');
  const choice = await rl.question('Selecciona opción: ');
  if (choice === '1') return analyze();
  if (choice === '2') return showFicha();
  if (choice === '3') return exportFicha();
  if (choice === '4') return resetFicha();
  if (choice === '5') return exit();
  return menu();
}

async function analyze() {
  const inputText = await rl.question('Introduce modelo/PN/EAN/Texto: ');
  lastCandidates = [];
  lastResult = null;
  client.send('analyze_component', { input: inputText });
  await sleep(300);
  if (lastCandidates.length) {
    console.log('\nCandidatos:');
    lastCandidates.forEach((c, i) => {
      console.log(`${i + 1}) ${c.brand} ${c.model} (${c.part_number || 'N/A'}) [${c.source_domain}] score:${c.score}`);
    });
    const sel = await rl.question('Selecciona candidato (1..N) o 0 para cancelar: ');
    if (sel !== '0') {
      const idx = Math.max(0, parseInt(sel, 10) - 1);
      client.send('select_candidate', { index: idx });
      await sleep(300);
    } else {
      return menu();
    }
  }
  if (lastResult) {
    renderComponent(lastResult);
  }
  const add = await rl.question('¿Añadir este componente a la ficha agregada? (Y/n) ');
  if (add.toLowerCase() !== 'n') client.send('add_to_ficha');
  const exp = await rl.question('¿Exportar ahora? (No / CSV / XLSX / MD) ');
  if (exp.toLowerCase() !== 'no') client.send('export_ficha', { format: exp.toLowerCase() });
  const again = await rl.question('¿Hacer otra búsqueda? (Y/n) ');
  if (again.toLowerCase() !== 'n') return analyze();
  return menu();
}

async function showFicha() {
  client.send('show_ficha');
  await sleep(200);
  console.log('\nFicha agregada:');
  renderFicha(ficha);
  return menu();
}

async function exportFicha() {
  const format = await rl.question('Formato (CSV/XLSX/MD): ');
  const path = await rl.question('Ruta de salida (enter para default): ');
  client.send('export_ficha', { format: format.toLowerCase(), path: path || null });
  return menu();
}

async function resetFicha() {
  const confirm = await rl.question('Esto borrará la ficha actual. ¿Continuar? (y/N) ');
  if (confirm.toLowerCase() === 'y') client.send('reset_ficha');
  return menu();
}

function renderComponent(result) {
  const canonical = result.canonical || {};
  console.log(`\nTIPO: ${result.component_type} | Canonical: ${canonical.brand || ''} ${canonical.model || ''} (${canonical.part_number || 'N/A'})`);
  const rows = (result.specs || []).map((s) => [
    s.label || s.key,
    s.value ?? '',
    statusBadge(s.status),
    tierBadge(s.source_tier),
    truncate(s.source_url || '')
  ]);
  renderTable(['Campo', 'Valor', 'Status', 'Tier', 'Fuente'], rows);
  if ((result.specs || []).some((s) => s.source_tier === 'REFERENCE')) {
    console.log('WARNING: Este componente incluye datos no oficiales (REFERENCE).');
  }
}

function renderFicha(fichaObj) {
  if (!fichaObj || !fichaObj.fields_by_template) {
    console.log('Sin ficha agregada.');
    return;
  }
  if (fichaObj.has_reference) {
    console.log('WARNING: La ficha contiene datos no oficiales (REFERENCE).');
  }
  let current = null;
  for (const field of fichaObj.fields_by_template) {
    if (field.section !== current) {
      current = field.section;
      console.log(`\n[${current}]`);
      renderTable(['Campo', 'Valor', 'Status', 'Tier', 'Fuente'], []);
    }
    renderRow([
      field.field,
      field.value ?? '',
      statusBadge(field.status),
      tierBadge(field.source_tier),
      truncate(field.source_url || '')
    ]);
  }
}

function statusBadge(status) {
  const map = {
    EXTRACTED_OFFICIAL: 'OFFICIAL',
    EXTRACTED_REFERENCE: 'REFERENCE',
    CALCULATED: 'CALCULATED',
    UNKNOWN: 'UNKNOWN',
    NA: 'NA'
  };
  return map[status] || status || '';
}

function tierBadge(tier) {
  const map = { OFFICIAL: 'OFFICIAL', REFERENCE: 'REFERENCE', NONE: '' };
  return map[tier] || tier || '';
}

function truncate(value, max = 60) {
  if (!value) return '';
  if (value.length <= max) return value;
  return value.slice(0, max - 3) + '...';
}

function renderTable(headers, rows) {
  const line = headers.map((h) => h.padEnd(18)).join(' ');
  if (headers.length) console.log(line);
  if (rows.length) {
    for (const row of rows) renderRow(row);
  }
}

function renderRow(row) {
  const line = row.map((c) => String(c).padEnd(18)).join(' ');
  console.log(line);
}

function exit() {
  rl.close();
  process.exit(0);
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function resolveEnginePath() {
  if (process.env.HXTRACTOR_ENGINE_PATH) return process.env.HXTRACTOR_ENGINE_PATH;
  const candidates = [
    path.join(__dirname, 'engine'),
    path.join(__dirname, '..', 'engine'),
    path.resolve(process.cwd(), 'engine'),
    path.resolve(process.cwd(), 'hardwarextractor'),
    path.resolve(__dirname, '..', '..', 'hardwarextractor')
  ];
  for (const candidate of candidates) {
    if (fs.existsSync(path.join(candidate, 'hardwarextractor', '__init__.py'))) {
      return candidate;
    }
  }
  return null;
}

function withPythonPath(engineRoot) {
  const env = { ...process.env };
  if (!engineRoot) return env;
  const current = env.PYTHONPATH || '';
  env.PYTHONPATH = current
    ? `${engineRoot}${path.delimiter}${current}`
    : engineRoot;
  return env;
}

menu();
