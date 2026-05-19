# 开发计划

## 开发原则

- **小步快跑**：每个 Phase 产出可独立验证的结果，不过渡到下一阶段
- **安全优先**：依赖锁定版本，模型下载前检查磁盘空间
- **可回退**：每个 Phase 完成后打 git tag（`phase-0`, `phase-1` ...）
- **单一职责**：模块间通过明确接口通信，修改一个不影响其他

---

## Phase 0 — 环境准备与项目脚手架

**目标**：开发环境就绪，不依赖 PyTorch，CTranslate2 统一引擎可用

### 0.1 Python 环境
- [ ] 创建虚拟环境（Python 3.11+）
- [ ] 安装 CTranslate2 + faster-whisper（CUDA 版）
- [ ] 安装 ONNX Runtime（Silero VAD 推理）
- [ ] 语言检测由 Whisper 内置分类头完成（无需 fastText）
- [ ] 验证 GPU 可用：跑一段 3 秒音频测试 ASR（faster-whisper 直接跑）
- [ ] 安装 FFmpeg（开发期用 winget 系统安装，打包期用便携版内置）
- [ ] 锁定 requirements.txt（不含 torch、transformers）

### 0.2 模型准备
- [ ] 下载 faster-whisper large-v3（英/韩 ASR）
- [ ] 下载 kotoba-whisper v2.0 CTranslate2 版（日语 ASR）
- [ ] 下载 Silero VAD ONNX 模型（推迟到 Phase 1，模型 ~2.3MB）
- [ ] 语言检测由 Whisper 内置分类头完成，无需下载额外模型
- [ ] 下载三组 OPUS-MT 模型，转换为 CTranslate2 格式
- [ ] 编写模型下载/转换脚本 `scripts/prepare_models.py`

### 0.3 项目骨架
- [ ] 创建 src/ 下所有模块的 `__init__.py`
- [ ] 编写 `config.py`（路径、模型名、阈值等集中管理）
- [ ] Git 初始化 + .gitignore（venv、models、__pycache__、build）

### 验证标准
- [ ] `python src/main.py` 弹出 PySide6 空白窗口
- [ ] 3 秒日语音频 → kotoba-whisper 输出正确文本
- [ ] 3 秒英文音频 → faster-whisper large-v3 输出正确文本
- [ ] GPU 推理正常（任务管理器可见 CUDA 使用）
- [ ] `pip list` 中不含 `torch` 和 `transformers`

---

## Phase 1 — 音频提取 + VAD

**目标**：从视频中提取音频并切分出语音段

### 1.1 FFmpeg 音频提取
- [ ] 编写 `audio_extractor.py`，封装 FFmpeg 调用
- [ ] 编写 `utils/ffmpeg_utils.py`，FFmpeg/ffprobe 路径查找与视频信息读取
- [ ] 输入：视频路径 → 输出：16kHz WAV
- [ ] 支持 MP4/MKV/AVI/MOV 格式（所有 FFmpeg 可解码格式自动支持）
- [ ] 错误处理：文件不存在、FFmpeg 未安装、提取失败

### 1.2 Silero VAD 集成
- [ ] 编写 `vad.py`，加载 Silero VAD ONNX 模型（`onnx-community/silero-vad`）
- [ ] 输入：WAV numpy 数组 → 输出：语音段时间戳列表
- [ ] 处理 VAD 模型的 stateful 推理（stateN 输出、sr 标量输入）
- [ ] 参数可调：静音判定阈值、最小语音段长度

### 1.3 集成测试
- [ ] 编写 `scripts/test_phase1.py`，输入视频路径 → 输出 WAV + 语音段数量
- [ ] 默认生成合成测试视频（5 秒正弦波 + 黑色画面）
- [ ] 测试素材：接受命令行参数指定视频文件

### 验证标准
- [ ] 提取的 WAV 为 16kHz 单声道 PCM 格式
- [ ] VAD 推理无错误，正确区分语音/非语音（正弦波概率 ≈ 0.02 = 非语音）
- [ ] 10 分钟视频提取音频 < 30 秒（待更长视频实际测试）

---

## Phase 2 — 语言检测 + 多模型 ASR 管道

**目标**：语音 → 原文文本，日语用 kotoba-whisper，英/韩用 large-v3

### 2.1 语言检测
- [ ] 编写 `language_detect.py`
- [ ] 取前 30 秒音频，用 Whisper large-v3 内置分类头检测语言
- [ ] 返回 ja / en / ko / "uncertain"（低置信度时提示用户手动指定）
- [ ] 若检测为 ja，模型路由器切换为 kotoba-whisper

### 2.2 多模型 ASR 封装
- [ ] 编写 `asr.py`，封装 ASR 路由器
- [ ] ja → 加载 kotoba-whisper v2.0-faster
- [ ] en / ko → 加载 faster-whisper large-v3
- [ ] 统一接口：`transcribe(audio_path, language) → segments`
- [ ] 返回带时间戳的 segments 列表（原文）
- [ ] 处理长音频（> 1 小时）不分段崩溃

### 2.3 处理模式
- [ ] 高质量模式：日语 kotoba-whisper + 英/韩 large-v3
- [ ] 快速模式：日语 kotoba-whisper + 英/韩 medium（medium 需额外模型）
- [ ] 模式控制放在 config 中，用户通过 GUI 切换

### 2.4 管道串联测试
- [ ] 编写管道脚本：WAV → 语言检测 → ASR 路由 → 打印文本

### 验证标准
- [ ] 日语音频 → kotoba-whisper 自动加载，识别准确
- [ ] 英/韩音频 → large-v3 自动加载，识别准确率 > 90%
- [ ] 语言检测准确率 100%（日/英/韩各 3 个样本）
- [ ] 快速模式速度提升 ≥ 2 倍

---

## Phase 3 — 翻译模块（CTranslate2 引擎）

**目标**：日/英/韩文本 → 中文，CTranslate2 推理，不依赖 PyTorch

### 3.1 模型转换（一次性）
- [ ] 下载三组 OPUS-MT HuggingFace 模型（en→zh, ja→zh, ko→zh）
- [ ] 使用 ct2-transformers-converter 转换为 CTranslate2 格式（float16）
- [ ] 写入 Phase 0 的 `scripts/prepare_models.py`

### 3.2 翻译模块
- [ ] 编写 `translator.py`，使用 CTranslate2 加载转换后的 OPUS-MT 模型
- [ ] 根据语言标签路由到对应翻译模型
- [ ] 输入：源语言文本 + 语言标签 → 输出：中文文本
- [ ] 支持批量翻译（合并多个 segment 一次推理，提升效率）

### 3.3 双语文本构造
- [ ] 翻译后保留原文，构造双语结构：`{"original": "...", "chinese": "..."}`
- [ ] 每个 segment 同时持有原文和译文

### 验证标准
- [ ] 日→中：假名/汉字混合句翻译准确（日语优先验证）
- [ ] 英→中：语义通顺，无明显错译
- [ ] 韩→中：日常对话翻译可读
- [ ] 翻译模块不导入 torch

---

## Phase 4 — 字幕文件生成

**目标**：生成双语 SRT/ASS 字幕文件

### 4.1 SRT Writer
- [ ] 编写 `subtitle_writer.py`，支持 SRT 格式
- [ ] 双语格式：第一行原文（小字号），第二行中文（大字号）
- [ ] 实现为 ASS 格式（SRT 不支持样式，双语推荐 ASS）
- [ ] SRT 降级方案：`原文 | 中文` 同屏一行

### 4.2 ASS Writer（重点）
- [ ] 支持双行字幕样式：原文小字灰色，中文大字白色+黑色描边
- [ ] 字体指定："Microsoft YaHei" + "Arial" 回退
- [ ] 位置：底部居中，视频控制栏上方

### 验证标准
- [ ] 生成的 ASS 字幕用 MPC-BE/PotPlayer 加载，双语正常显示
- [ ] 时间轴与音频同步，无明显偏移
- [ ] 中日韩文字无乱码（UTF-8 BOM）

---

## Phase 5 — 硬字幕烧录

**目标**：将双语字幕写入视频

### 5.1 FFmpeg 烧录
- [ ] 编写 `hard_sub.py`，调用 FFmpeg subtitles 滤镜
- [ ] 输入：原视频 + ASS 字幕 → 输出：H.264 MP4
- [ ] CRF 可调（默认 18，高质量），编码速度可调
- [ ] 音频流直接复制（不重新编码）

### 验证标准
- [ ] 输出视频双语字幕清晰可读
- [ ] 音画同步
- [ ] 输出文件大小合理（比原视频增大约 5-15%）

---

## Phase 6 — PySide6 GUI

**目标**：用户可通过 GUI 完成全流程

### 6.1 主窗口布局
- [ ] 拖拽区域：支持拖入视频文件 + 点击选择
- [ ] 文件信息区：显示文件名、时长、分辨率
- [ ] 设置面板：输出类型（字幕/烧录/两者）、处理模式（高质量/快速）、语言（自动/手动）

### 6.2 进度面板
- [ ] 进度条 + 阶段文字（提取中 → 识别中 → 翻译中 → 生成中）
- [ ] 预估剩余时间
- [ ] 取消按钮

### 6.3 结果区域
- [ ] 完成后的操作按钮：打开字幕文件、打开视频所在文件夹
- [ ] 耗时统计展示

### 6.4 主题
- [ ] 深色主题（默认）+ 浅色主题
- [ ] 字体缩放适配高 DPI

### 验证标准
- [ ] 拖入视频 → 选择输出 → 点击开始 → 进度正常 → 输出文件正确
- [ ] UI 不卡顿（处理在子线程）
- [ ] 取消按钮有效

---

## Phase 7 — 安装程序 + 打包发布

**目标**：生成 Windows 安装程序，用户可选择语言按需安装模型

### 7.1 语言选择安装器
- [ ] 编写安装引导 UI（PySide6 弹窗）
- [ ] 语言勾选界面：日语 / 英语 / 韩语（多选）
- [ ] 自动解析依赖：ASR 模型 + 翻译模型
- [ ] 显示预计下载大小
- [ ] 下载进度条 + 断点续传（从 HuggingFace / 国内镜像）
- [ ] 模型完整性校验（SHA256）
- [ ] 安装后更新 config，标记已安装的语言

### 7.2 模型管理（运行时）
- [ ] 设置中可追加/删除某语言的模型
- [ ] 删除前检查是否还有其他语言依赖该模型（如英韩共享 large-v3）

### 7.3 PyInstaller 打包
- [ ] 配置 .spec 文件，仅打包核心（~290MB）
- [ ] 内置便携 FFmpeg + ONNX Runtime DLL
- [ ] 模型文件外置，不打包进 .exe
- [ ] 输出为 ThinkSub_Setup.exe（安装程序）
- [ ] Windows Defender 免杀验证

### 验证标准
- [ ] 在干净 Windows 虚拟机中运行安装程序
- [ ] 选择"仅日语"，安装后总计约 2.1 GB
- [ ] 选择"全部"，安装后总计约 5.7 GB
- [ ] 导入视频 → 处理 → 输出双语字幕，功能完整
- [ ] 不依赖系统 Python/FFmpeg

---

## 里程碑总览

| 阶段 | 产出 | 预计 |
|------|------|------|
| Phase 0 | 环境就绪，无 PyTorch 依赖 | 1 天 |
| Phase 1 | 音频提取 + VAD | 1 天 |
| Phase 2 | 多模型 ASR（kotoba + large-v3） | 2-3 天 |
| Phase 3 | CTranslate2 翻译模块 | 1-2 天 |
| Phase 4 | 双语字幕文件生成 | 1 天 |
| Phase 5 | 硬字幕烧录 | 0.5-1 天 |
| Phase 6 | GUI 完成 | 2-3 天 |
| Phase 7 | 安装程序 + 打包 | 2 天 |

> 总计：11-14 天
