import { spawn } from 'child_process';
import path from 'path';
import readline from 'readline';
import url from 'url';

const __dirname = path.dirname(url.fileURLToPath(import.meta.url));

export class EngineClient {
  constructor({ mode = 'mock', pythonBin = 'python3', enginePath } = {}) {
    this.mode = mode;
    this.pythonBin = pythonBin;
    this.enginePath = enginePath || path.join(__dirname, 'engine');
    this.proc = null;
    this.rl = null;
    this.handlers = [];
  }

  start() {
    if (this.mode === 'mock') {
      this.proc = { stdin: null };
      return;
    }
    const args = ['-m', 'hardwarextractor.cli_engine'];
    const env = { ...process.env };
    if (this.enginePath) {
      const current = env.PYTHONPATH || '';
      env.PYTHONPATH = current
        ? `${this.enginePath}${path.delimiter}${current}`
        : this.enginePath;
    }
    this.proc = spawn(this.pythonBin, args, { stdio: ['pipe', 'pipe', 'pipe'], env });
    this.rl = readline.createInterface({ input: this.proc.stdout });
    this.rl.on('line', (line) => {
      try {
        const msg = JSON.parse(line);
        for (const handler of this.handlers) handler(msg);
      } catch {
        // ignore non-json
      }
    });
  }

  onMessage(handler) {
    this.handlers.push(handler);
  }

  send(command, payload = {}) {
    if (this.mode === 'mock') {
      return this._mockResponse(command, payload);
    }
    const data = JSON.stringify({ command, payload });
    this.proc.stdin.write(data + '\n');
  }

  _mockResponse(command, payload) {
    const emit = (msg) => {
      for (const handler of this.handlers) handler(msg);
    };
    if (command === 'analyze_component') {
      emit({ type: 'status', value: 'Normalizando' });
      emit({ type: 'status', value: 'Clasificando' });
      emit({ type: 'status', value: 'Resolviendo' });
      emit({ type: 'candidates', value: [{ brand: 'Mock', model: 'Mock 1', part_number: 'M1', score: 0.9, source_domain: 'example.com' }] });
      return;
    }
    if (command === 'select_candidate') {
      emit({ type: 'status', value: 'Scrapeando' });
      emit({ type: 'result', value: { component_type: 'CPU', canonical: { brand: 'Mock', model: 'Mock 1', part_number: 'M1' }, specs: [] } });
      return;
    }
    if (command === 'show_ficha') {
      emit({ type: 'ficha_update', value: { fields_by_template: [] } });
      return;
    }
  }
}
