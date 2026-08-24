# 驾驶员疲劳监测系统

基于现有 YOLO11-face 与 PFLD ONNX 权重的本地疲劳监测系统。支持批量图片、视频文件和摄像头画面，输出闭眼、哈欠、低头事件及正常、轻度、中度、重度四级状态。本项目不包含模型重新训练，也不声明 YOLO12 或训练精度提升。

## 开发运行

要求 Python 3.11 与 Node.js 20+。

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r server\requirements-dev.txt
$env:FATIGUE_MODEL_DIR="$PWD\models"
.\.venv\Scripts\python.exe -m server.app

cd desktop
npm install
npm start
```

模型文件必须位于 `models/yolo11_face.onnx` 和 `models/pfld.onnx`。缺失时系统会明确显示 `demo`，该模式只能用于界面开发，不能用于正式验收。

## Windows 构建

```powershell
.\scripts\build-windows.ps1
```

安装包输出到 `release/`。桌面端自动选择空闲端口、等待后端就绪，并把数据库保存在 Electron 用户数据目录。有 CUDA Provider 时自动使用 GPU，否则回退 CPU。

## Docker

```powershell
docker compose up --build
# 可选 NVIDIA GPU：
docker compose -f compose.yaml -f compose.gpu.yaml up --build
```

启动后访问 `http://localhost:5001`。CPU 配置是正式支持基线，GPU 配置依赖宿主机驱动、Docker Desktop/WSL2 和 NVIDIA Container Toolkit。

## 测试

```powershell
.\.venv\Scripts\python.exe -m pytest server\tests -v
cd desktop
npm test
```
