"""Verifica o MP4 final, decodifica áudio/vídeo e extrai frames para revisão."""
import json
import re
import subprocess
from pathlib import Path

import imageio_ffmpeg

ROOT = Path(__file__).resolve().parent.parent
video = ROOT / "output" / "video" / "agroorbit-fase6-demo.mp4"
ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
result = subprocess.run([ffmpeg, "-hide_banner", "-i", str(video), "-af", "volumedetect", "-f", "null", "-"], capture_output=True, text=True, check=True)
details = result.stderr
duration = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", details)
if duration is None or "Video: h264" not in details or "Audio: aac" not in details:
    raise ValueError("MP4 sem vídeo H.264, áudio AAC ou duração identificável.")
hours, minutes, seconds = map(float, duration.groups())
total = hours * 3600 + minutes * 60 + seconds
if not 180 <= total <= 300:
    raise ValueError(f"Duração fora de 3-5 minutos: {total}")
volume = float(re.search(r"mean_volume: (-?[\d.]+) dB", details).group(1))
if volume < -45:
    raise ValueError(f"Áudio muito baixo: {volume} dB")
for i, seconds in enumerate((20, 75, 122, 161, 214, 263)):
    subprocess.run([ffmpeg, "-y", "-loglevel", "error", "-ss", str(seconds), "-i", str(video), "-frames:v", "1", str(ROOT / "tmp" / "video" / f"review-{i + 1}.png")], check=True)
report = {"passed": True, "duration_seconds": total, "mean_volume_db": volume, "full_decode_success": True, "video_codec": "h264", "audio_codec": "aac", "frames_for_visual_review": 6}
(ROOT / "output" / "video" / "video-validation.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
