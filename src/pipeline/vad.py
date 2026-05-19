"""Silero VAD 语音活动检测"""

import os

import numpy as np
import onnxruntime

from src.config import (
    HF_ENDPOINT,
    MODELS_DIR,
    SAMPLE_RATE,
    SILENCE_THRESHOLD,
    MIN_SPEECH_DURATION_MS,
    MAX_SPEECH_GAP_MS,
)

os.environ.setdefault("HF_ENDPOINT", HF_ENDPOINT)

_SESSION: onnxruntime.InferenceSession | None = None

WINDOW_SIZE = 512
CONTEXT_SIZE = 64
FRAME_MS = WINDOW_SIZE / SAMPLE_RATE * 1000  # 32ms


def _get_model() -> onnxruntime.InferenceSession:
    """加载 Silero VAD ONNX 模型（单例）"""
    global _SESSION
    if _SESSION is not None:
        return _SESSION

    model_path = MODELS_DIR / "silero_vad.onnx"
    if not model_path.exists():
        _download_vad_model(model_path)

    _SESSION = onnxruntime.InferenceSession(
        str(model_path),
        providers=["CPUExecutionProvider"],
    )
    return _SESSION


def _download_vad_model(dest: "Path") -> None:
    """下载 Silero VAD 模型"""
    from huggingface_hub import hf_hub_download

    print("下载 Silero VAD 模型 ...")
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    try:
        path = hf_hub_download(
            repo_id="onnx-community/silero-vad",
            filename="silero_vad.onnx",
            local_dir=str(MODELS_DIR),
        )
        import shutil
        if path != str(dest):
            shutil.move(path, str(dest))
    except Exception:
        raise RuntimeError(
            "VAD 模型下载失败。请手动下载 silero_vad.onnx 放入 models/ 目录。\n"
            "下载地址: https://github.com/snakers4/silero-vad/raw/master/"
            "src/silero_vad/data/silero_vad.onnx"
        )


def detect_speech_segments(
    audio: np.ndarray,
    threshold: float = SILENCE_THRESHOLD,
    min_speech_duration_ms: int = MIN_SPEECH_DURATION_MS,
    max_speech_gap_ms: int = MAX_SPEECH_GAP_MS,
) -> list[tuple[int, int]]:
    """
    检测音频中的语音段。

    Args:
        audio: float32 numpy 数组，范围 [-1, 1]，采样率 16kHz
        threshold: 语音概率阈值 (0-1)
        min_speech_duration_ms: 最短有效语音段（毫秒）
        max_speech_gap_ms: 最大句间间隔（毫秒）

    Returns:
        [(start_ms, end_ms), ...] 语音段时间戳列表
    """
    if audio.ndim > 1:
        audio = audio.squeeze()
    audio = audio.astype(np.float32)

    model = _get_model()
    sr_array = np.array(SAMPLE_RATE, dtype=np.int64)

    num_windows = (len(audio) - CONTEXT_SIZE) // WINDOW_SIZE
    if num_windows <= 0:
        return []

    speech_probs = np.empty(num_windows, dtype=np.float32)
    chunk = np.empty(WINDOW_SIZE + CONTEXT_SIZE, dtype=np.float32)
    state = np.zeros((2, 1, 128), dtype=np.float32)

    for i in range(num_windows):
        start = i * WINDOW_SIZE
        end = start + WINDOW_SIZE + CONTEXT_SIZE
        if end > len(audio):
            break
        chunk[:end - start] = audio[start:end]
        ort_inputs = {
            "input": chunk.reshape(1, -1),
            "sr": sr_array,
            "state": state,
        }
        output, state = model.run(["output", "stateN"], ort_inputs)
        speech_probs[i] = output.item()

    return _probs_to_segments(
        speech_probs, threshold, min_speech_duration_ms, max_speech_gap_ms
    )


def _probs_to_segments(
    speech_probs: np.ndarray,
    threshold: float,
    min_speech_ms: int,
    max_gap_ms: int,
) -> list[tuple[int, int]]:
    """将帧级别的语音概率转换为时间段列表"""
    speech_mask = speech_probs > threshold
    segments: list[tuple[int, int]] = []
    in_speech = False
    seg_start = 0

    for i, is_speech in enumerate(speech_mask):
        if is_speech and not in_speech:
            seg_start = i
            in_speech = True
        elif not is_speech and in_speech:
            end_ms = int(i * FRAME_MS)
            start_ms = int(seg_start * FRAME_MS)
            if end_ms - start_ms >= min_speech_ms:
                _append_or_merge(segments, start_ms, end_ms, max_gap_ms)
            in_speech = False

    if in_speech:
        start_ms = int(seg_start * FRAME_MS)
        end_ms = int(len(speech_probs) * FRAME_MS)
        if end_ms - start_ms >= min_speech_ms:
            _append_or_merge(segments, start_ms, end_ms, max_gap_ms)

    return segments


def _append_or_merge(
    segments: list[tuple[int, int]],
    start_ms: int,
    end_ms: int,
    max_gap_ms: int,
) -> None:
    """追加或合并到前一段"""
    if segments and start_ms - segments[-1][1] < max_gap_ms:
        segments[-1] = (segments[-1][0], end_ms)
    else:
        segments.append((start_ms, end_ms))
