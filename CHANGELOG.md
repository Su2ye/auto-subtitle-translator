# 更新日志

## 2026-05-20

### v1.0 — 首次发布
- 首次运行自动模型下载向导（勾选语言即可，无需命令行）
- 内置 FFmpeg（用户无需手动安装）
- 双语字幕输出（ASS/SRT，原文 + 中文翻译）
- 硬字幕烧录（双语字幕写入视频）
- 拖拽导入视频，自动解析文件信息
- 语言自动检测 + 手动指定（日 / 英 / 韩）
- 高质量 / 快速模式切换
- 蓝色 T 应用图标
- 日语：kotoba-whisper v2.0 / 英韩：Whisper large-v3 / 翻译：NLLB-200
- PySide6 + CTranslate2 + Catppuccin 深色主题

### 修复
- FFmpeg full_build → essentials，exe 从 447MB 降至 353MB
- 单选按钮互斥 Bug（QButtonGroup 隔离输出类型 / 处理模式）
- 单实例锁（QLockFile）防止多窗口
- 模型下载失败（使用正确 HF repo ID，exe 内直接调用转换）
- 模型路径持久化（移至 `%APPDATA%\ThinkSub\models\`）
- 每次启动提示首次使用的问题（检查 settings.json）

### 新增
- 启动淡入动画（窗口透明度 0→1，0.4 秒）
- `CHANGELOG.md` 更新日志
- 模型存放路径可自定义
- 视频输出路径可自定义

## 2026-05-19

- 项目搭建、技术方案确定、全部文档编写
- Phase 0-7 开发完成：音频提取 → VAD → 语言检测 → ASR → 翻译 → 字幕生成 → 烧录 → GUI → 打包
- 12 个核心模块、5 个 GUI 模块、5 个集成测试脚本
