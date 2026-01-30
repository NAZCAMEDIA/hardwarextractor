import { test } from 'node:test';
import assert from 'node:assert/strict';
import { EngineClient } from '../src/ipc_client.js';

test('mock engine emits candidates', async () => {
  const client = new EngineClient({ mode: 'mock' });
  client.start();
  let candidates = null;
  client.onMessage((msg) => {
    if (msg.type === 'candidates') candidates = msg.value;
  });
  client.send('analyze_component', { input: 'Intel' });
  assert.ok(candidates);
  assert.equal(candidates[0].brand, 'Mock');
});
