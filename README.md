# ThinkSub

**桌面端视频中文字幕生成工具** — 拖拽视频，自动生成双语字幕。

支持日语、英语、韩语视频，全部本地 GPU 处理，生成双语字幕文件（SRT/ASS），可烧录为硬字幕视频。

## 核心功能

- 拖拽视频文件（MP4/MKV/AVI 等），自动提取音频
- 语音识别：日语（kotoba-whisper）、英语/韩语（Whisper large-v3）
- 自动检测源语言，也支持手动指定
- 翻译为中文，输出**双语字幕**（原文 + 中文）
- 导出 SRT/ASS 字幕文件，可选烧录为硬字幕视频
- 高质量 / 快速模式切换
- 所有处理完全本地运行，不上传任何数据

## 技术架构

```
视频 → FFmpeg 提取音频 → VAD 语音切分 → 语言检测(日/英/韩)
     → CTranslate2 ASR 推理 → CTranslate2 翻译 → 双语 ASS/SRT
     → (可选) FFmpeg 烧录硬字幕 MP4
```

- **GUI**：PySide6
- **推理引擎**：CTranslate2（统一引擎，不依赖 PyTorch）
- **ASR**：kotoba-whisper v2.0（日语）、Faster-Whisper large-v3（英/韩）
- **翻译**：OPUS-MT（en/ja/ko → zh），CTranslate2 格式
- **音频处理**：FFmpeg + Silero VAD (ONNX)
- **语言检测**：fastText

## 安装

1. 下载 `ThinkSub_Setup.exe`（约 300MB）
2. 运行安装程序，勾选需要的语言：
   - 日语（+1.8 GB）
   - 英语（+3.3 GB）
   - 韩语（+3.3 GB）
3. 安装程序自动下载对应模型，完成后即可使用

### 磁盘占用

| 语言选择 | 安装后总计 |
|----------|-----------|
| 仅日语 | ~2.1 GB |
| 仅英语 或 仅韩语 | ~3.6 GB |
| 日语 + 英语 | ~5.4 GB |
| 全部 | ~5.7 GB |

## 环境要求

- Windows 10/11
- NVIDIA 显卡（GTX 1060+，显存 ≥ 6GB）
- 无需安装 Python 或 FFmpeg（已内置）

## 使用

1. 启动 ThinkSub
2. 拖拽视频到窗口，或点击选择文件
3. 选择输出方式：字幕文件 / 烧录视频 / 两者
4. 选择处理模式：高质量 / 快速
5. 点击"开始处理"，等待完成

## 开发

项目文档位于 `docs/`：

| 文档 | 说明 |
|------|------|
| [requirements.md](docs/requirements.md) | 需求文档 |
| [tech-spec.md](docs/tech-spec.md) | 技术方案 |
| [dev-plan.md](docs/dev-plan.md) | 开发计划 |
| [design-spec.md](docs/design-spec.md) | 设计规范 |

开发指引见 [CLAUDE.md](CLAUDE.md)。

### 开发环境搭建

```bash
# Python 3.11
python -m venv venv
source venv/Scripts/activate  # Windows

# 安装依赖（不含 PyTorch）
pip install -r requirements.txt

# 准备模型
python scripts/prepare_models.py
```

### 项目结构

```
thinks/
├── src/
│   ├── main.py              # 应用入口
│   ├── config.py             # 全局配置
│   ├── gui/                  # PySide6 界面
│   ├── pipeline/             # 处理管道
│   └── utils/                # 工具模块
├── scripts/                  # 工具脚本
├── docs/                     # 项目文档
├── devlog/                   # 开发日志
└── models/                   # 模型目录（gitignore）
```

## License

MIT
