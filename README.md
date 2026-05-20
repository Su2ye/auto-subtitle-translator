# Auto Subtitle Translator

桌面端视频中文字幕生成工具 — 拖拽视频 → 自动生成双语字幕。

支持 **日语、英语、韩语** 视频，全部本地 GPU 处理，输出**双语字幕**（原文 + 中文翻译）。

<p align="center">
  <img src="src/gui/resources/icon_128.png" alt="ThinkSub" width="128">
</p>

## 功能

- 拖拽视频文件（MP4 / MKV / AVI / MOV 等），自动提取音频
- 语音识别：日语（kotoba-whisper v2.0）、英语/韩语（Whisper large-v3）
- 语言自动检测，也可手动指定
- 翻译为中文，输出 SSR / ASS **双语字幕**
- 可选将字幕烧录为硬字幕视频（H.264 MP4）
- 高质量 / 快速模式切换
- **所有处理完全本地运行，不上传任何数据**

## 环境要求

| 项目 | 要求 |
|------|------|
| 操作系统 | Windows 10 / 11 |
| 显卡 | NVIDIA GTX 1060 及以上，显存 ≥ 6GB |
| 磁盘 | 应用 ~350MB，模型 ~2-6GB（按需） |
| FFmpeg | 系统需安装，或应用内置（见下方说明） |

## 下载与安装

### 直接下载（推荐）

1. 从 [Releases](../../releases) 页面下载 `ThinkSub_v1.0.zip`
2. 解压到任意目录
3. 双击 `ThinkSub.exe` 启动
4. 首次运行：勾选需要翻译的语言，自动下载模型
5. 拖拽视频 → 开始处理

> 内置 FFmpeg，无需额外安装。

### 从源码运行（开发者）

```bash
git clone https://github.com/Su2ye/auto-subtitle-translator.git
cd thinksub
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
pip install nvidia-cublas-cu12 nvidia-cudnn-cu12
python src/main.py
```

模型由应用在首次运行时自动下载。各语言所需大小参考：

| 语言 | ASR 模型 | 翻译模型 | 合计 |
|------|----------|----------|------|
| 日语 | kotoba-whisper v2.0 (1.5GB) | NLLB-200 共享 (1.2GB) | ~2.7GB |
| 英语 | Whisper large-v3 (3.0GB) | NLLB-200 共享 | ~4.2GB |
| 韩语 | 与英语共享 large-v3 | NLLB-200 共享 | +0 |
| **全部** | — | — | ~5.7GB |

下载使用 HuggingFace 镜像（`hf-mirror.com`），支持断点续传。

## 使用

1. 启动 ThinkSub
2. 拖拽视频文件到窗口，或点击选择
3. 选择输出方式：
   - **字幕文件**：生成 `.ass` 双语字幕文件
   - **字幕 + 烧录**：同时生成字幕文件和烧录好的 MP4 视频
4. 选择处理模式：高质量 / 快速
5. 源语言：自动检测 / 手动指定
6. 点击「开始处理」，等待完成

输出文件在视频同目录下。

## 技术架构

```
视频 → FFmpeg 提取音频 → Silero VAD 语音切分 → 语言检测(日/英/韩)
     → ASR 识别 → NLLB-200 翻译 → 双语 ASS/SRT
     → (可选) FFmpeg 烧录硬字幕 MP4
```

| 模块 | 技术 |
|------|------|
| GUI | PySide6 |
| 推理引擎 | CTranslate2 |
| 日语 ASR | kotoba-whisper v2.0 |
| 英/韩 ASR | Faster-Whisper large-v3 |
| 翻译 | NLLB-200-distilled-600M |
| VAD | Silero VAD (ONNX) |
| 音频/视频 | FFmpeg |

## 常见问题

**Q: "读取失败"？**  
A: 视频文件可能损坏或编码格式不兼容。请确认视频可正常播放。

**Q: 提示模型未找到？**  
A: 应用会在首次运行时自动下载模型。如已跳过，删除 `%APPDATA%\ThinkSub\settings.json` 重新打开即可触发下载。

**Q: 处理很慢？**  
A: 确保 GPU 推理已启用。如果提示 CPU 回退，请安装 CUDA 运行时：`pip install nvidia-cublas-cu12 nvidia-cudnn-cu12`。

**Q: 字幕乱码？**  
A: 使用支持 UTF-8 的播放器（如 PotPlayer, MPC-BE, VLC），并加载 `.ass` 字幕文件。

## 项目文档

| 文档 | 路径 |
|------|------|
| 需求文档 | [docs/requirements.md](docs/requirements.md) |
| 技术方案 | [docs/tech-spec.md](docs/tech-spec.md) |
| 开发计划 | [docs/dev-plan.md](docs/dev-plan.md) |
| 设计规范 | [docs/design-spec.md](docs/design-spec.md) |

## 开发

详见 [CLAUDE.md](CLAUDE.md)。

## License

MIT
