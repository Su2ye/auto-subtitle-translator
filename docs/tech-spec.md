# 技术方案文档

## 设计目标

- **统一推理引擎**：全部模型运行在 CTranslate2 上，项目不依赖 PyTorch
- **核心轻量**：应用程序本体约 290MB，模型按需下载
- **日语优先**：日语用专用模型 kotoba-whisper，准确率最高优先级

## 总体架构

```
┌──────────────────────────────────────────────────┐
│                 PySide6 GUI                       │
│  ┌─────────────┐  ┌──────────┐  ┌─────────────┐  │
│  │ 拖拽区域     │  │ 设置面板  │  │ 进度/结果    │  │
│  └─────────────┘  └──────────┘  └─────────────┘  │
└──────────────────────┬───────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────┐
│              Processing Pipeline                  │
│  所有模型推理统一走 CTranslate2 引擎                │
│                                                   │
│  ① FFmpeg 提取音频 ──▶ 16kHz WAV                  │
│  ② Silero VAD (ONNX) ──▶ 语音段时间戳              │
│  ③ Whisper ──▶ 语言标签 (ja/en/ko)                │
│  ④ ASR (CTranslate2) ──▶ 原文 + 时间戳              │
│     ├─ ja → kotoba-whisper v2.0                   │
│     └─ en/ko → faster-whisper large-v3             │
│  ⑤ OPUS-MT (CTranslate2) ──▶ 中文翻译               │
│  ⑥ SRT/ASS Writer ──▶ 双语字幕文件                  │
│  ⑦ (可选) FFmpeg subtitles ──▶ 烧录 MP4             │
└──────────────────────────────────────────────────┘
```

## 统一引擎：CTranslate2

### 为什么去掉 PyTorch

| 模块 | 原依赖 | 新方案 | 效果 |
|------|--------|--------|------|
| ASR（语音识别） | faster-whisper → CTranslate2 | **不变**（faster-whisper 本身就是 CTranslate2） | — |
| VAD（语音检测） | PyTorch → Silero VAD | **ONNX Runtime**（5MB） | 去 2.5GB |
| 语言检测 | Whisper 内置语言分类头 | 音频特征直接检测，复用 ASR 引擎 | 零额外依赖 |
| 翻译 | transformers + PyTorch | OPUS-MT 模型 → CTranslate2 转换 | 去 2.5GB |

转换命令（一次性的模型准备）：
```bash
ct2-transformers-converter --model Helsinki-NLP/opus-mt-en-zh \
    --output_dir models/opus-mt-en-zh-faster --quantization float16
```

### 压缩效果

| 组件 | 原占 | 压缩后 |
|------|------|--------|
| PyTorch + CUDA 运行时 | 2.5 GB | **0** |
| Python 运行时 | 40 MB | 40 MB |
| PySide6（裁剪后） | 100 MB | ~60 MB |
| CTranslate2 | 60 MB | 60 MB |
| ONNX Runtime | — | ~5 MB |
| FFmpeg 最小构建 | 80 MB | ~25 MB |
| numpy + soundfile + 其他 | 80 MB | ~50 MB |
| **核心合计** | **~3.1 GB** | **~290 MB** |

---

## 模型策略

### 按语言分模型

| 语言 | 优先级 | ASR 模型 | 大小 | 翻译模型 | 大小 |
|------|--------|----------|------|----------|------|
| 日语 | ★★★ | kotoba-whisper v2.0 | 1.5 GB | OPUS-MT ja→zh | 0.3 GB |
| 英语 | ★★ | faster-whisper large-v3 | 3.0 GB | OPUS-MT en→zh | 0.3 GB |
| 韩语 | ★ | ↑ 共享 ↑ | — | OPUS-MT ko→zh | 0.3 GB |

> 英语和韩语共享 faster-whisper large-v3，同时选两者不重复计算 ASR 模型。

### 日语专用模型：kotoba-whisper

- 基础：Whisper large-v3 教师模型 + ReazonSpeech（35,000 小时日语语音）蒸馏
- 日语文档 CER/WER **显著优于** vanilla whisper-large-v3
- 已有 CTranslate2 版本：[kotoba-whisper-v2.0-faster](https://huggingface.co/kotoba-tech/kotoba-whisper-v2.0-faster)
- 直接通过 faster-whisper API 加载，无需改动代码

### 按需安装策略

```
安装程序
    │
    ▼
用户勾选语言组合（多选）：
  □ 日语（+ 1.8 GB）
  □ 英语（+ 3.3 GB）
  □ 韩语（+ 3.3 GB）
    │
    ▼
自动解析依赖 → 从 HuggingFace/镜像下载模型 → 完成
```

| 选择 | ASR 模型 | 翻译模型 | 总追加 | 安装后总计 |
|------|----------|----------|--------|-----------|
| 仅日语 | kotoba（1.5 GB） | ja→zh（0.3 GB） | +1.8 GB | **2.1 GB** |
| 仅英语 | large-v3（3.0 GB） | en→zh（0.3 GB） | +3.3 GB | **3.6 GB** |
| 仅韩语 | large-v3（3.0 GB） | ko→zh（0.3 GB） | +3.3 GB | **3.6 GB** |
| 日+英 | kotoba + large-v3（4.5 GB） | ja→zh + en→zh（0.6 GB） | +5.1 GB | **5.4 GB** |
| 日+韩 | kotoba + large-v3（4.5 GB） | ja→zh + ko→zh（0.6 GB） | +5.1 GB | **5.4 GB** |
| 英+韩 | large-v3（3.0 GB） | en→zh + ko→zh（0.6 GB） | +3.6 GB | **3.9 GB** |
| 全部 | kotoba + large-v3（4.5 GB） | 三组（0.9 GB） | +5.4 GB | **5.7 GB** |

---

## 核心依赖

```
# requirements.txt (核心 ~290MB)

# GUI
PySide6==6.7.3

# 推理引擎 (替代 PyTorch)
ctranslate2>=4.5.0,<5.0.0
faster-whisper==1.1.1

# VAD
onnxruntime==1.21.0

# 语言检测由 Whisper 内置分类头完成，无需额外依赖

# 音频处理
numpy==2.1.3
soundfile==0.12.1

# 工具
tqdm==4.67.1

# 翻译模型转换工具（开发/安装期使用，非运行时）
# ct2-transformers-converter（来自 huggingface_hub + transformers，安装阶段用后可选删除）
```

> 注意：`torch`、`transformers`、`sentencepiece` **不在运行时依赖中**。仅在模型准备阶段用于将 OPUS-MT HuggingFace 模型转换为 CTranslate2 格式，转换完成后即可删除。

---

## 运行时需求总结

| 维度 | 值 |
|------|-----|
| 核心磁盘占用 | ~290 MB |
| 模型磁盘占用 | 1.8 ~ 5.4 GB（按需） |
| GPU 显存峰值 | ~3 GB（加载一个 ASR 模型时） |
| 操作系统 | Windows 10/11 |
| GPU 要求 | NVIDIA GTX 1060+，显存 6GB+ |
| Python 版本 | 3.14（关键包均支持） |
