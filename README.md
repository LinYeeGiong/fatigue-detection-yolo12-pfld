# 驾驶员疲劳监测系统

本地驾驶员疲劳行为检测与分析系统，支持批量图片、上传视频和摄像头画面。系统识别闭眼、哈欠、低头行为，按正常、轻度、中度、重度四级输出风险，并保存历史记录和实验分析数据。

上传视频会按源顺序处理每一个可解码帧，通过 SSE 连续显示标注后的画面，同时更新进度、EAR、MAR、俯仰角、处理帧率和单帧延迟。分析中心提供等级、行为、来源、任务趋势、指标趋势图，以及 CSV、PNG 和打印/PDF 导出。

## 开发运行

要求 Python 3.11 与 Node.js 20+。

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r server\requirements-dev.txt
$env:FATIGUE_MODEL_DIR="$PWD\models"
.\.venv\Scripts\python.exe -m server.app

cd desktop
npm ci
npm start
```

现有推理权重位于 `models/yolo11_face.onnx` 和 `models/pfld.onnx`。本项目直接使用已有权重，不包含重新训练，也不声明 YOLO12、mAP 提升或无标注依据的准确率。

## Windows 构建

```powershell
.\scripts\build-windows.ps1
```

安装包输出到 `release/`。桌面端自动选择本地端口、等待服务就绪，并将 SQLite 数据保存到 Electron 用户数据目录。CPU 是必需运行基线；存在可用 CUDA Provider 时自动使用 GPU。

## Docker

```powershell
docker compose up --build
# 可选 NVIDIA GPU
docker compose -f compose.yaml -f compose.gpu.yaml up --build
```

启动后访问 `http://localhost:5001`。GPU 配置依赖宿主机驱动、Docker Desktop/WSL2 和 NVIDIA Container Toolkit。

## 测试

```powershell
.\.venv\Scripts\python.exe -m pytest server\tests -v
cd desktop
npm test
```
