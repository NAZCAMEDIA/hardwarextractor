import fs from 'fs';
import path from 'path';
import url from 'url';

const __dirname = path.dirname(url.fileURLToPath(import.meta.url));
const root = path.resolve(__dirname, '..');
const src = path.join(root, 'src');
const dist = path.join(root, 'dist');
const repoRoot = path.resolve(root, '..', '..');
const engineSource = path.join(repoRoot, 'hardwarextractor');
const engineTarget = path.join(dist, 'engine', 'hardwarextractor');

fs.mkdirSync(dist, { recursive: true });
for (const file of fs.readdirSync(src)) {
  if (!file.endsWith('.js')) continue;
  fs.copyFileSync(path.join(src, file), path.join(dist, file));
}

if (fs.existsSync(engineSource)) {
  copyDir(engineSource, engineTarget, (entry) => {
    if (entry.name === '__pycache__') return false;
    if (entry.name === '.pytest_cache') return false;
    if (entry.name === 'tests') return false;
    return true;
  });
}

function copyDir(from, to, filter) {
  fs.mkdirSync(to, { recursive: true });
  for (const entry of fs.readdirSync(from, { withFileTypes: true })) {
    if (filter && !filter(entry)) continue;
    const srcPath = path.join(from, entry.name);
    const dstPath = path.join(to, entry.name);
    if (entry.isDirectory()) {
      copyDir(srcPath, dstPath, filter);
    } else if (entry.isFile()) {
      fs.copyFileSync(srcPath, dstPath);
    }
  }
}
