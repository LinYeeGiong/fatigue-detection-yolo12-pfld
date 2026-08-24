const {app, BrowserWindow, dialog, Menu, shell} = require('electron');
const {spawn} = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');
const {findFreePort, resolveBackendCommand, waitForHealth, stopBackend} = require('./backend');

let backendProcess = null;
let mainWindow = null;

async function startApplication() {
  Menu.setApplicationMenu(null);
  const port = await findFreePort();
  const root = path.resolve(__dirname, '..', '..');
  const bundledPython = path.join(root, '.venv', 'Scripts', 'python.exe');
  const command = resolveBackendCommand({
    packaged: app.isPackaged,
    root,
    resourcesPath: process.resourcesPath,
    python: process.env.FATIGUE_PYTHON || (fs.existsSync(bundledPython) ? bundledPython : 'python'),
  });
  const dataDir = path.join(app.getPath('userData'), 'data');
  backendProcess = spawn(command.executable, command.args, {
    cwd: command.cwd || path.dirname(command.executable),
    windowsHide: true,
    env: {
      ...process.env,
      PORT: String(port),
      FATIGUE_DATA_DIR: dataDir,
      FATIGUE_MODEL_DIR: app.isPackaged ? path.join(process.resourcesPath, 'models') : path.join(root, 'models'),
      FATIGUE_DEVICE: process.env.FATIGUE_DEVICE || 'auto',
    },
    stdio: app.isPackaged ? 'ignore' : 'inherit',
  });
  backendProcess.once('exit', code => {
    if (code && mainWindow) dialog.showErrorBox('服务异常退出', `后端进程退出，代码 ${code}`);
  });

  const baseUrl = `http://127.0.0.1:${port}`;
  await waitForHealth(baseUrl);
  mainWindow = new BrowserWindow({
    width: 1380,
    height: 860,
    minWidth: 1024,
    minHeight: 700,
    show: false,
    backgroundColor: '#f4f6f9',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
    },
  });
  mainWindow.webContents.setWindowOpenHandler(({url}) => {
    if (url.startsWith('https://')) shell.openExternal(url);
    return {action: 'deny'};
  });
  mainWindow.webContents.on('will-navigate', (event, url) => {
    if (!url.startsWith(baseUrl)) event.preventDefault();
  });
  await mainWindow.loadURL(baseUrl);
  mainWindow.show();
}

app.whenReady().then(startApplication).catch(error => {
  dialog.showErrorBox('启动失败', error.message);
  app.quit();
});
app.on('window-all-closed', () => app.quit());
app.on('before-quit', () => stopBackend(backendProcess));
