const assert = require('node:assert/strict');
const test = require('node:test');
const net = require('node:net');
const path = require('node:path');

const { findFreePort, resolveBackendCommand, waitForHealth } = require('../src/backend');

test('findFreePort returns a localhost port that can be rebound', async () => {
  const port = await findFreePort();
  assert.ok(port > 0);
  await new Promise((resolve, reject) => {
    const server = net.createServer();
    server.once('error', reject);
    server.listen(port, '127.0.0.1', () => server.close(resolve));
  });
});

test('resolveBackendCommand uses Python module in development', () => {
  const command = resolveBackendCommand({ packaged: false, root: 'C:\\project', python: 'python.exe' });
  assert.deepEqual(command, {
    executable: 'python.exe',
    args: ['-m', 'server.app'],
    cwd: path.resolve('C:\\project'),
  });
});

test('resolveBackendCommand uses bundled executable when packaged', () => {
  const command = resolveBackendCommand({ packaged: true, resourcesPath: 'C:\\app\\resources' });
  assert.equal(command.executable, path.join('C:\\app\\resources', 'server', 'fatigue-server.exe'));
  assert.deepEqual(command.args, []);
});

test('waitForHealth retries until service reports ready', async () => {
  let calls = 0;
  const fakeFetch = async () => ({ok: ++calls === 3, json: async () => ({status: 'ready'})});
  const result = await waitForHealth('http://localhost:5001', {fetchImpl: fakeFetch, timeoutMs: 100, intervalMs: 1});
  assert.equal(result.status, 'ready');
  assert.equal(calls, 3);
});

test('waitForHealth rejects after timeout', async () => {
  const fakeFetch = async () => { throw new Error('offline'); };
  await assert.rejects(
    waitForHealth('http://localhost:5001', {fetchImpl: fakeFetch, timeoutMs: 10, intervalMs: 1}),
    /后端服务启动超时/,
  );
});
