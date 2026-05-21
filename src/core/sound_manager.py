import atexit
import logging
import shutil
import wave
import struct
import math
import tempfile
import os
from PyQt6.QtMultimedia import QSoundEffect
from PyQt6.QtCore import QUrl


class SoundManager:
    """Generate and play simple synth sounds. No external audio files needed."""
    _instance = None

    def __init__(self):
        if SoundManager._instance is not None:
            raise RuntimeError("Use SoundManager.instance()")
        SoundManager._instance = self
        self._enabled = True
        self._volume = 0.5
        self._effects: dict[str, QSoundEffect] = {}
        self._temp_dir = tempfile.mkdtemp(prefix="typehan_sounds_")
        atexit.register(self._cleanup_temp_dir)
        self._generate_all()

    def _cleanup_temp_dir(self):
        """Clean up temporary WAV files on exit."""
        try:
            if os.path.isdir(self._temp_dir):
                shutil.rmtree(self._temp_dir, ignore_errors=True)
        except Exception:
            logging.debug("Failed to clean temp sound dir", exc_info=True)

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def set_enabled(self, enabled: bool):
        self._enabled = enabled
        for e in self._effects.values():
            e.setMuted(not enabled)

    def set_volume(self, vol: float):
        self._volume = max(0.0, min(1.0, vol))
        for e in self._effects.values():
            e.setVolume(self._volume)

    def play(self, name: str):
        if not self._enabled:
            return
        e = self._effects.get(name)
        if e and not e.isPlaying():
            e.play()

    # ---- WAV generation ----

    def _generate_all(self):
        """Create short sound effects: click, correct, wrong, combo, game_over."""
        self._effects["click"] = self._make_sound(
            freq=800, duration_ms=30, volume=0.25, fade_ms=10
        )
        self._effects["correct"] = self._make_sound(
            freq=1200, duration_ms=60, volume=0.30, fade_ms=20
        )
        self._effects["wrong"] = self._make_sound(
            freq=280, duration_ms=150, volume=0.25, fade_ms=40
        )
        self._effects["combo"] = self._make_sound(
            freq=1600, duration_ms=120, volume=0.35, fade_ms=30
        )
        self._effects["game_over"] = self._make_tone_sequence([
            (600, 100), (500, 100), (400, 200)
        ], volume=0.25)

    def _make_sound(self, freq: int, duration_ms: int,
                    volume: float = 0.3, fade_ms: int = 0) -> QSoundEffect:
        sample_rate = 22050
        num_samples = int(sample_rate * duration_ms / 1000)
        samples = []
        for i in range(num_samples):
            t = i / sample_rate
            # Sine wave with fast exponential decay for a pleasant "pluck"
            decay = math.exp(-t * 12)
            val = math.sin(2 * math.pi * freq * t) * decay * volume
            samples.append(int(val * 32767))

        path = self._write_wav(samples, sample_rate)
        effect = QSoundEffect()
        effect.setSource(QUrl.fromLocalFile(path))
        effect.setVolume(self._volume)
        effect.setLoopCount(1)
        return effect

    def _make_tone_sequence(self, tones: list[tuple[int, int]],
                            volume: float = 0.25) -> QSoundEffect:
        sample_rate = 22050
        all_samples = []
        for freq, dur_ms in tones:
            num_samples = int(sample_rate * dur_ms / 1000)
            for i in range(num_samples):
                t = i / sample_rate
                decay = math.exp(-t * 8)
                val = math.sin(2 * math.pi * freq * t) * decay * volume
                all_samples.append(int(val * 32767))

        path = self._write_wav(all_samples, sample_rate)
        effect = QSoundEffect()
        effect.setSource(QUrl.fromLocalFile(path))
        effect.setVolume(self._volume)
        effect.setLoopCount(1)
        return effect

    def _write_wav(self, samples: list[int], sample_rate: int) -> str:
        path = os.path.join(self._temp_dir, f"snd_{len(samples)}_{sample_rate}.wav")
        if os.path.exists(path):
            return path
        with wave.open(path, 'w') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(struct.pack(f'<{len(samples)}h', *samples))
        return path
