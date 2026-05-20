"""翻译模块 — NLLB-200 HF 直接推理（已弃用 CTranslate2）"""

import os

from src.config import (
    TRANSLATION_MODEL,
    NLLB_LANG_CODES,
    NLLB_TARGET_LANG,
    SUPPORTED_LANGUAGES,
)

os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")


class Translator:
    """日/英/韩 → 中文，NLLB-200 HuggingFace 推理"""

    def __init__(self):
        from transformers import NllbTokenizerFast, AutoModelForSeq2SeqLM

        if not TRANSLATION_MODEL.exists():
            raise FileNotFoundError(
                f"翻译模型未找到: {TRANSLATION_MODEL}"
            )

        self._tokenizer = NllbTokenizerFast.from_pretrained(
            str(TRANSLATION_MODEL)
        )
        self._model = AutoModelForSeq2SeqLM.from_pretrained(
            str(TRANSLATION_MODEL)
        )
        self._model.eval()
        self._tgt_id = self._tokenizer.convert_tokens_to_ids(NLLB_TARGET_LANG)

    def translate(self, text: str, src_lang: str) -> str:
        if not text.strip():
            return ""
        return self.translate_batch([text], src_lang)[0]

    def translate_batch(self, texts: list[str], src_lang: str) -> list[str]:
        src_code = NLLB_LANG_CODES.get(src_lang, src_lang)
        self._tokenizer.src_lang = src_code

        non_empty = [(i, t.strip()) for i, t in enumerate(texts) if t.strip()]
        if not non_empty:
            return [""] * len(texts)

        source = [t for _, t in non_empty]
        enc = self._tokenizer(source, return_tensors="pt", padding=True)

        outputs = self._model.generate(
            **enc,
            forced_bos_token_id=self._tgt_id,
            max_length=256,
            num_beams=4,
            no_repeat_ngram_size=3,
        )
        translated = self._tokenizer.batch_decode(outputs, skip_special_tokens=True)

        result = [""] * len(texts)
        for (i, _), t in zip(non_empty, translated):
            result[i] = t
        return result


_translator: Translator | None = None


def get_translator() -> Translator:
    global _translator
    if _translator is None:
        _translator = Translator()
    return _translator


def translate_segments(segments: list[dict], language: str) -> list[dict]:
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
