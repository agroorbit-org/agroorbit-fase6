"""Monta os segmentos capturados com áudio e salva MP4 H.264/AAC."""
import json
import subprocess
from pathlib import Path

import imageio_ffmpeg

ROOT = Path(__file__).resolve().parent.parent
TEMP = ROOT / "tmp" / "video"
OUTPUT = ROOT / "output" / "video"
OUTPUT.mkdir(parents=True, exist_ok=True)
segments = json.loads((TEMP / "recorded.json").read_text())
ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
parts = []
for i, segment in enumerate(segments):
    part = TEMP / f"segment-{i + 1}.mp4"
    subprocess.run([ffmpeg, "-y", "-loglevel", "error", "-i", segment["video"], "-i", segment["audio"], "-vf", "fps=25,format=yuv420p", "-af", "adelay=700|700,apad", "-t", str(segment["duration"]), "-c:v", "libx264", "-preset", "fast", "-crf", "21", "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", str(part)], check=True)
    parts.append(part)
    print(f"Montado segmento {i + 1}", flush=True)
playlist = TEMP / "concat.txt"
playlist.write_text("\n".join(f"file '{p.as_posix()}'" for p in parts) + "\n")
video = OUTPUT / "agroorbit-fase6-demo.mp4"
subprocess.run([ffmpeg, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(playlist), "-c", "copy", "-movflags", "+faststart", str(video)], check=True)
duration = sum(s["duration"] for s in segments)
report = {"duration_seconds": round(duration, 2), "resolution": "1440x1000", "narration": "Luciana (pt-BR), voz sintetizada via macOS say, 200 palavras/minuto", "capture": "Aplicação local real, Chromium + Playwright; seis segmentos sem dados inventados na edição", "file": str(video.relative_to(ROOT)), "size_bytes": video.stat().st_size, "segments": [{"title": s["title"], "duration_seconds": s["duration"]} for s in segments]}
(OUTPUT / "video-info.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report, ensure_ascii=False, indent=2))
