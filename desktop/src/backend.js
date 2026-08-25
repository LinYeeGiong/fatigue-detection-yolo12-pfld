const net = require('node:net');
const path = require('node:path');

function findFreePort() {
  return new Promise((resolve, reject) => {
    const server = net.createServer();
    server.unref();
    server.once('error', reject);
    server.listen(0, '127.0.0.1', () => {
      const {port} = server.address();
      server.close(() => resolve(port));
    });
  });
}

function resolveBackendCommand({packaged, root, resourcesPath, python = 'python'}) {
  if (packaged) {
    return {executable: path.join(resourcesPath, 'server', 'fatigue-server.exe'), args: []};
  }
  return {executable: python, args: ['-m', 'server.app'], cwd: path.resolve(root)};
}

async function waitForHealth(baseUrl, {fetchImpl = fetch, timeoutMs = 120000, intervalMs = 250} = {}) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    try {
      const response = await fetchImpl(`${baseUrl}/api/health`);
      if (response.ok) return await response.json();
    } catch (_) {
      // The sidecar may not have bound its port yet.
    }
    await new Promise(resolve => setTimeout(resolve, intervalMs));
  }
  throw new Error('后端服务启动超时');
}

function stopBackend(child) {
  if (child && !child.killed) child.kill();
}

module.exports = {findFreePort, resolveBackendCommand, waitForHealth, stopBackend};
