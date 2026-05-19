"""翻译模块 — CTranslate2 NLLB-200 + HF tokenizer（单模型多语言直译）"""

import ctranslate2
from transformers import NllbTokenizerFast

from src.config import (
    TRANSLATION_MODEL,
    NLLB_LANG_CODES,
    NLLB_TARGET_LANG,
    SUPPORTED_LANGUAGES,
)


class Translator:
    """日/英/韩 → 中文翻译引擎"""

    def __init__(self):
        if not TRANSLATION_MODEL.exists():
            raise FileNotFoundError(
                f"翻译模型未找到: {TRANSLATION_MODEL}\n"
                f"请运行: python scripts/prepare_models.py --all"
            )
        self._model = ctranslate2.Translator(
            str(TRANSLATION_MODEL), device="cpu", compute_type="int8"
        )
        self._tokenizer = NllbTokenizerFast.from_pretrained(
            str(TRANSLATION_MODEL)
        )
        # 缓存目标语言前缀 token
        target_id = self._tokenizer.convert_tokens_to_ids(NLLB_TARGET_LANG)
        self._target_prefix = [
            self._tokenizer.convert_ids_to_tokens([target_id])
        ]
        self._last_src_code: str | None = None

    def translate(self, text: str, src_lang: str) -> str:
        if not text.strip():
            return ""
        return self.translate_batch([text], src_lang)[0]

    def translate_batch(self, texts: list[str], src_lang: str) -> list[str]:
        src_code = NLLB_LANG_CODES.get(src_lang, src_lang)

        # 一次遍历：strip + 收集非空
        non_empty: list[tuple[int, str]] = []
        for i, t in enumerate(texts):
            stripped = t.strip()
            if stripped:
                non_empty.append((i, stripped))

        if not non_empty:
            return [""] * len(texts)

        # 仅语言变化时更新 tokenizer
        if self._last_src_code != src_code:
            self._tokenizer.src_lang = src_code
            self._tokenizer.tgt_lang = NLLB_TARGET_LANG
            self._last_src_code = src_code

        source = [t for _, t in non_empty]
        enc = self._tokenizer(source, padding=True)
        batch_tokens = [
            self._tokenizer.convert_ids_to_tokens(ids)
            for ids in enc["input_ids"]
        ]

        results = self._model.translate_batch(
            batch_tokens,
            target_prefix=self._target_prefix,
            beam_size=3,
            max_decoding_length=256,
        )

        # 批量解码
        all_out_tokens = [r.hypotheses[0] for r in results]
        all_out_ids = [self._tokenizer.convert_tokens_to_ids(t) for t in all_out_tokens]
        translated = [
            self._tokenizer.decode(ids, skip_special_tokens=True)
            for ids in all_out_ids
        ]

        output = [""] * len(texts)
        for (i, _), t in zip(non_empty, translated):
            output[i] = t
        return output


_translator: Translator | None = None


def get_translator() -> Translator:
    global _translator
    if _translator is None:
        _translator = Translator()
    return _translator


def translate_segments(segments: list[dict], language: str) -> list[dict]:
    """翻译 ASR 片段，返回双语结构"""
    if language not in SUPPORTED_LANGUAGES:
        raise ValueError(f"不支持的语言: {language}")
    t = get_translator()
    source_texts = [s["text"] for s in segments]
    translations = t.translate_batch(source_texts, language)
    return [
        {"start": s["start"], "end": s["end"],
         "original": s["text"], "chinese": tr}
        for s, tr in zip(segments, translations)
    ]
