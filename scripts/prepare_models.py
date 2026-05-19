"""
ThinkSub 模型准备脚本

首次运行或追加语言时执行，下载并转换所需模型。

用法:
    python scripts/prepare_models.py           # 交互式选择
    python scripts/prepare_models.py --all      # 下载全部
    python scripts/prepare_models.py --ja --en  # 指定语言
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import (
    MODELS_DIR,
    WHISPER_MODEL,
    KOTOBA_WHISPER_MODEL,
    HF_ENDPOINT,
)

os.environ.setdefault("HF_ENDPOINT", HF_ENDPOINT)

# 语言选择映射
LANG_MAP = {"1": "ja", "2": "en", "3": "ko"}

# 模型大小常量（GB）
KOTOBA_SIZE_GB = 1.5
LARGE_V3_SIZE_GB = 3.0
NLLB_SIZE_GB = 1.2

# 翻译模型（共享一个 NLLB-200）
TRANSLATION_HF = "facebook/nllb-200-distilled-600M"
TRANSLATION_OUTPUT = MODELS_DIR / "nllb-200-faster"

# 模型依赖声明
LANGUAGE_DEPS = {
    "ja": {
        "asr": [KOTOBA_WHISPER_MODEL],
        "needs_translation": True,
    },
    "en": {
        "asr": [WHISPER_MODEL],
        "needs_translation": True,
    },
    "ko": {
        "asr": [WHISPER_MODEL],
        "needs_translation": True,
    },
}



def download_whisper_model(model_name: str) -> bool:
    """通过 faster-whisper 下载 CTranslate2 模型（不加载到内存）"""
    from faster_whisper.utils import download_model

    print(f"  下载 ASR 模型: {model_name}")
    try:
        download_model(model_name, output_dir=str(MODELS_DIR))
        return True
    except Exception as e:
        print(f"  错误: {e}")
        return False


def convert_nllb() -> bool:
    """将 NLLB-200 HF 模型转换为 CTranslate2 格式"""
    if TRANSLATION_OUTPUT.exists():
        print(f"  翻译模型已存在: {TRANSLATION_OUTPUT}")
        return True

    print(f"  转换翻译模型: {TRANSLATION_HF} -> {TRANSLATION_OUTPUT}")
    try:
        subprocess.run(
            [
                sys.executable, "-m", "ctranslate2.converters.transformers",
                "--model", TRANSLATION_HF,
                "--output_dir", str(TRANSLATION_OUTPUT),
                "--quantization", "float16",
            ],
            check=True,
        )
        _cleanup_hf_cache(TRANSLATION_HF)
        return True
    except subprocess.CalledProcessError as e:
        print(f"  转换失败: {e}")
        return False


def _cleanup_hf_cache(hf_model_name: str) -> None:
    """删除 HF 缓存中指定模型的副本（转换完成后无需保留）"""
    try:
        from huggingface_hub import try_to_load_from_cache, scan_cache_dir

        cached = try_to_load_from_cache(hf_model_name, "config.json")
        if cached:
            hf_cache = scan_cache_dir()
            for repo in hf_cache.repos:
                if repo.repo_id == hf_model_name:
                    print(f"  清理 HF 缓存: {hf_model_name}")
                    shutil.rmtree(str(repo.repo_path), ignore_errors=True)
                    break
    except Exception:
        pass  # 缓存清理失败不影响主流程


def resolve_deps(languages: list[str]) -> tuple[set[str], bool]:
    """解析语言选择 → 需要的 ASR 模型和是否需要翻译模型"""
    asr_models: set[str] = set()
    needs_translation = False
    for lang in languages:
        deps = LANGUAGE_DEPS[lang]
        asr_models.update(deps["asr"])
        if deps["needs_translation"]:
            needs_translation = True
    return asr_models, needs_translation


def _estimate_size(asr_models: set[str], needs_translation: bool) -> str:
    """估算下载大小"""
    size_gb = 0.0
    for m in asr_models:
        if "kotoba" in m:
            size_gb += KOTOBA_SIZE_GB
        elif "large" in m:
            size_gb += LARGE_V3_SIZE_GB
        else:
            size_gb += KOTOBA_SIZE_GB
    if needs_translation:
        size_gb += NLLB_SIZE_GB
    return f"{size_gb:.1f} GB"


def _install_converter_deps() -> bool:
    """临时安装翻译模型转换所需的依赖（转换后可手动删除）"""
    try:
        import transformers  # noqa: F401
        import torch  # noqa: F401
        import sentencepiece  # noqa: F401
        return True
    except ImportError:
        print("  安装临时依赖: transformers + torch + sentencepiece")
        print("  （转换完成后可用 pip uninstall 删除以节省空间）")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install",
             "transformers", "torch", "sentencepiece"],
            check=False,
        )
        return result.returncode == 0


def _parse_choices(args: argparse.Namespace) -> list[str] | None:
    """解析命令行参数或交互式输入，返回语言列表"""
    if args.all:
        return ["ja", "en", "ko"]

    selected = [l for l in ["ja", "en", "ko"]
                if getattr(args, l, False)]
    if selected:
        return selected

    # 交互式选择
    print("选择语言（输入序号，多选用空格分隔）:")
    print("  1. 日语")
    print("  2. 英语")
    print("  3. 韩语")
    print("  4. 全部")
    choice = input("> ").strip()

    if choice == "4":
        return ["ja", "en", "ko"]

    result = []
    for c in choice.split():
        lang = LANG_MAP.get(c)
        if lang:
            result.append(lang)
    return result or None


def main():
    parser = argparse.ArgumentParser(description="ThinkSub 模型准备")
    parser.add_argument("--ja", action="store_true", help="日语")
    parser.add_argument("--en", action="store_true", help="英语")
    parser.add_argument("--ko", action="store_true", help="韩语")
    parser.add_argument("--all", action="store_true", help="全部语言")
    args = parser.parse_args()

    selected = _parse_choices(args)
    if not selected:
        print("无有效选择，退出。")
        return

    asr_models, needs_translation = resolve_deps(selected)

    print(f"\n语言: {', '.join(selected)}")
    print(f"ASR 模型: {', '.join(asr_models)}")
    print(f"翻译模型: NLLB-200 (共享)")
    print(f"预计下载大小: {_estimate_size(asr_models, needs_translation)}\n")

    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    # 下载 ASR 模型
    print("--- ASR 模型 ---")
    for m in asr_models:
        if not download_whisper_model(m):
            print(f"  下载失败: {m}，请检查网络后重试。")

    # 下载并转换翻译模型（NLLB-200，所有语言共享一个）
    print("\n--- 翻译模型 ---")
    if not _install_converter_deps():
        print("  临时依赖安装失败，跳过翻译模型转换。")
        print("  请手动安装: pip install transformers torch sentencepiece")
        return

    convert_nllb()

    print("\n模型准备完成。")


if __name__ == "__main__":
    main()
