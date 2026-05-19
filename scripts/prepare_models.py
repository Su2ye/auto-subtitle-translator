"""
ThinkSub 模型准备脚本

首次运行或追加语言时执行，下载并转换所需模型。

用法:
    python scripts/prepare_models.py           # 交互式选择
    python scripts/prepare_models.py --all      # 下载全部
    python scripts/prepare_models.py --ja --en  # 指定语言
"""

import argparse
import hashlib
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import (
    MODELS_DIR,
    WHISPER_MODEL,
    KOTOBA_WHISPER_MODEL,
    TRANSLATION_MODELS,
    HF_ENDPOINT,
)

os.environ.setdefault("HF_ENDPOINT", HF_ENDPOINT)

# 模型依赖声明：每个语言需要哪些 ASR 模型和翻译模型
LANGUAGE_DEPS = {
    "ja": {
        "asr": [KOTOBA_WHISPER_MODEL],
        "translation": ["ja"],
    },
    "en": {
        "asr": [WHISPER_MODEL],
        "translation": ["en"],
    },
    "ko": {
        "asr": [WHISPER_MODEL],  # 与英语共享
        "translation": ["ko"],
    },
}

# OPUS-MT 原始 HF 模型列表（需转换为 CTranslate2 格式）
OPUS_MT_HF = {
    "en": "Helsinki-NLP/opus-mt-en-zh",
    "ja": "Helsinki-NLP/opus-mt-ja-zh",
    "ko": "Helsinki-NLP/opus-mt-ko-zh",
}


def download_whisper_model(model_name: str) -> bool:
    """通过 faster-whisper 下载模型（自动走 CTranslate2）"""
    from faster_whisper import WhisperModel

    print(f"  下载 ASR 模型: {model_name}")
    try:
        WhisperModel(model_name, device="cpu", compute_type="int8",
                     download_root=str(MODELS_DIR))
        return True
    except Exception as e:
        print(f"  错误: {e}")
        return False


def convert_opus_mt(lang: str) -> bool:
    """将 OPUS-MT HF 模型转换为 CTranslate2 格式"""
    import subprocess

    hf_name = OPUS_MT_HF[lang]
    output_dir = TRANSLATION_MODELS[lang]

    if output_dir.exists():
        print(f"  翻译模型已存在: {output_dir}")
        return True

    print(f"  转换翻译模型: {hf_name} -> {output_dir}")
    try:
        subprocess.run(
            [
                sys.executable, "-m", "ctranslate2.convert",
                "--model", hf_name,
                "--output_dir", str(output_dir),
                "--quantization", "float16",
            ],
            check=True,
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"  转换失败: {e}")
        return False


def resolve_deps(languages: list[str]) -> tuple[set[str], set[str]]:
    """解析语言选择 → 需要哪些 ASR 模型和翻译"""
    asr_models: set[str] = set()
    translation_langs: set[str] = set()
    for lang in languages:
        deps = LANGUAGE_DEPS[lang]
        asr_models.update(deps["asr"])
        translation_langs.update(deps["translation"])
    return asr_models, translation_langs


def main():
    parser = argparse.ArgumentParser(description="ThinkSub 模型准备")
    parser.add_argument("--ja", action="store_true", help="日语")
    parser.add_argument("--en", action="store_true", help="英语")
    parser.add_argument("--ko", action="store_true", help="韩语")
    parser.add_argument("--all", action="store_true", help="全部语言")
    args = parser.parse_args()

    if args.all:
        selected = ["ja", "en", "ko"]
    else:
        selected = [l for l in ["ja", "en", "ko"]
                    if getattr(args, l, False)]
        if not selected:
            print("选择语言（输入序号，多选用空格分隔）:")
            print("  1. 日语")
            print("  2. 英语")
            print("  3. 韩语")
            print("  4. 全部")
            choice = input("> ").strip()
            mapping = {"1": ["ja"], "2": ["en"], "3": ["ko"],
                       "4": ["ja", "en", "ko"]}
            selected = mapping.get(choice)
            if not selected:
                # 尝试解析多选
                selected = []
                for c in choice.split():
                    m = {"1": "ja", "2": "en", "3": "ko"}.get(c)
                    if m:
                        selected.append(m)
            if not selected:
                print("无有效选择，退出。")
                return

    asr_models, translation_langs = resolve_deps(selected)

    print(f"\n语言: {', '.join(selected)}")
    print(f"ASR 模型: {', '.join(asr_models)}")
    print(f"翻译模型: {', '.join(translation_langs)}")
    print(f"预计下载大小: ~{estimate_size(asr_models, translation_langs)}\n")

    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    # 下载 ASR 模型
    print("--- ASR 模型 ---")
    for m in asr_models:
        okay = download_whisper_model(m)
        if not okay:
            print(f"  跳过 {m}，请检查网络。")

    # 下载并转换翻译模型（需要临时安装 transformers + torch）
    print("\n--- 翻译模型 ---")
    _install_converter_deps()
    for lang in translation_langs:
        convert_opus_mt(lang)

    print("\n模型准备完成。")


def estimate_size(asr_models: set[str], translation_langs: set[str]) -> str:
    """估算下载大小"""
    size_gb = 0
    for m in asr_models:
        if "kotoba" in m:
            size_gb += 1.5
        elif "large" in m:
            size_gb += 3.0
        else:
            size_gb += 1.5
    size_gb += len(translation_langs) * 0.3
    return f"{size_gb:.1f} GB"


def _install_converter_deps():
    """暂时安装 transformers 用于模型转换，完成后提示可卸载"""
    import subprocess
    try:
        import transformers  # noqa: F401
        import torch  # noqa: F401
    except ImportError:
        print("  安装临时依赖: transformers + torch（转换后可选删除）")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "transformers", "torch",
             "sentencepiece"],
            check=True,
        )


if __name__ == "__main__":
    main()
