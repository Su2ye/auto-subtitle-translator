# CLAUDE.md — ThinkSub 项目指引

## 项目概述

ThinkSub 是一款桌面端视频中文字幕生成工具。用户拖拽视频文件（MP4/MKV 等）进入应用，自动提取音频 → 语音识别 → 翻译 → 生成**双语字幕文件**（SRT/ASS），并可选择将双语字幕烧录为硬字幕视频。

- 源语言：英语、日语、韩语（自动检测或手动指定）
- 输出：双语字幕（原文 + 中文翻译）
- 技术栈：PySide6 GUI + Faster-Whisper ASR + OPUS-MT 翻译 + FFmpeg

## 标准文件索引

所有开发必须遵循以下文档中定义的规范：

| 文件 | 路径 | 用途 |
|------|------|------|
| 需求文档 | [docs/requirements.md](docs/requirements.md) | 功能需求、非功能需求、不做范围 |
| 技术方案 | [docs/tech-spec.md](docs/tech-spec.md) | 架构、技术选型、数据流、依赖、目录结构 |
| 开发计划 | [docs/dev-plan.md](docs/dev-plan.md) | 7 个 Phase 的执行步骤、验收标准、里程碑 |
| 设计规范 | [docs/design-spec.md](docs/design-spec.md) | 双语字幕样式、GUI 布局、配色、交互 |

## 开发日志

每次开发会话在 [devlog/](devlog/) 目录下创建 `YYYY-MM-DD.md`。

- 模板：[devlog/template.md](devlog/template.md)
- 内容：今日完成项、遇到的问题和解决方案、明日待办

## 工作约定

### 核心原则
1. **按 Phase 顺序执行** — 不跳阶段，每个 Phase 通过验收再进入下一阶段
2. **最小可验证单元** — 每个任务完成后必须有可运行的验证方式
3. **先文档后代码** — 设计变更必须先更新 docs/ 中的对应文档
4. **本地处理** — 全部在本地完成，不依赖外部 API
5. **简化优先** — 写完代码后主动调用 simplify skill 审查，消除冗余、提升可读性

### 开发流程
1. 从 [docs/dev-plan.md](docs/dev-plan.md) 确认当前 Phase
2. 在 [devlog/](devlog/) 创建当日日志
3. 编写代码，遵循单一职责原则
4. 每个模块写完立即写单元验证
5. 通过对应 Phase 的验收标准
6. 完成功能后运行 simplify skill 检查代码质量

### 代码规范
- **Python**：类型注解（Type Hints），异步用 `async/await`，snake_case 命名
- **配置分离**：所有路径、模型名、阈值在 `src/config.py` 统一管理
- **无第三方 JS**：GUI 用 PySide6，不引入前端框架
- **错误处理**：仅在系统边界（FFmpeg 调用、文件 I/O、模型加载）做异常处理
- **注释原则**：不写 WHAT，只写 WHY（非显而易见的约束、workaround、边界行为）

### Git 约定
- 每个 Phase 完成后打 tag：`phase-0` → `phase-7`
- Commit message：`[Phase-N] 简短描述`
- 不提交：models/、venv/、__pycache__/、build/、*.spec

### 安全准则
- 全部本地处理，不上传视频/音频/字幕到任何服务器
- 处理完成后清理临时音频文件
- 用户设置保存在本地 `%APPDATA%/ThinkSub/`
