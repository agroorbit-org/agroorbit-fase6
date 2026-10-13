"""Prepara narração sintetizada por segmento no macOS (opcional)."""
import json
import subprocess
import wave
from pathlib import Path

import imageio_ffmpeg

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "tmp" / "video"
OUTPUT.mkdir(parents=True, exist_ok=True)
segments = json.loads((ROOT / "docs" / "narracao-video.json").read_text(encoding="utf-8"))
ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
for i, segment in enumerate(segments):
    aiff = OUTPUT / f"voice-{i + 1}.aiff"
    wav = OUTPUT / f"voice-{i + 1}.wav"
    subprocess.run(["/usr/bin/say", "-v", "Luciana", "-r", "200", "-o", str(aiff), segment["text"]], check=True)
    subprocess.run([ffmpeg, "-y", "-loglevel", "error", "-i", str(aiff), "-ar", "22050", "-ac", "1", str(wav)], check=True)
    with wave.open(str(wav), "rb") as source:
        duration = source.getnframes() / source.getframerate()
    segment["audio_duration"] = duration
    segment["duration"] = round(max(32, duration + 2), 2)
    segment["audio"] = str(wav)
    print(f"Segmento {i + 1}: áudio {duration:.1f}s / vídeo {segment['duration']:.1f}s", flush=True)
total = sum(s["duration"] for s in segments)
if not 180 <= total <= 300:
    raise ValueError(f"Duração fora do intervalo: {total}")
(OUTPUT / "segments.json").write_text(json.dumps(segments, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Duração total prevista: {total:.1f} segundos")
