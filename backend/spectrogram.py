"""Reuse plot_specs.py's STFT parameters and plotting function unchanged."""
import importlib.util
from pathlib import Path
import threading

import matplotlib
matplotlib.use('Agg')
import librosa
import matplotlib.pyplot as plt
import numpy as np
import soundfile as sf

_spec = importlib.util.spec_from_file_location('project_plot_specs', Path(__file__).resolve().parent.parent / 'plot_specs.py')
_plot = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_plot)
_lock = threading.Lock()


def generate(source, audio_out, image_out):
    """Validate before allocating audio; keep playback rate/channels, plot at 16 kHz."""
    try:
        info = sf.info(source)
    except (RuntimeError, ValueError) as exc:
        raise ValueError('无法读取音频，请上传有效的 WAV、FLAC、OGG 或 MP3 文件。') from exc
    if not (0 < info.duration <= 120):
        raise ValueError('音频时长必须大于 0 且不超过 120 秒。')
    if not (8000 <= info.samplerate <= 96000) or not (1 <= info.channels <= 2):
        raise ValueError('仅支持 8–96 kHz 的单声道或双声道音频。')
    samples, rate = sf.read(source, dtype='float32', always_2d=True)
    if not np.isfinite(samples).all() or np.max(np.abs(samples)) > 1:
        raise ValueError('音频包含无效数值或超出 [-1, 1] 的幅值，请先修复音频。')
    sf.write(audio_out, samples, rate, subtype='PCM_24')
    with _lock:
        try:
            # Same loading, STFT and dB conversion as the user's main().
            audio, _ = librosa.load(source, sr=16000)
            stft = librosa.stft(audio, win_length=600, hop_length=50)
            spec = librosa.amplitude_to_db(abs(stft))
            _plot.plot_spec(spec, str(Path(image_out).with_suffix('')))
        finally:
            plt.close('all')
    return {'duration': round(info.duration, 3), 'sample_rate': rate, 'channels': info.channels}
