"""Verifica o MP4 final, decodifica áudio/vídeo e extrai frames para revisão."""
import json
import re
import subprocess
from pathlib import Path

import imageio_ffmpeg

ROOT = Path(__file__).resolve().parent.parent
video = ROOT / "output" / "video" / "agroorbit-fase6-demo.mp4"
ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
result = subprocess.run([ffmpeg, "-hide_banner", "-i", str(video), "-af", "volumedetect,silencedetect=noise=-42dB:d=1.5", "-f", "null", "-"], capture_output=True, text=True, check=True)
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
long_pauses = [float(value) for value in re.findall(r"silence_duration: ([\d.]+)", details)]
if any(pause > 3 for pause in long_pauses):
    raise ValueError(f"Narração contém pausa maior que 3 segundos: {long_pauses}")
info = json.loads((ROOT / "output" / "video" / "video-info.json").read_text())
if abs(total - info["duration_seconds"]) > 0.3:
    raise ValueError("A duração do MP4 não corresponde à montagem dos segmentos.")
offset, review_times = 0, []
for i, segment in enumerate(info["segments"]):
    seconds = offset + segment["duration_seconds"] * 0.55
    frame = ROOT / "tmp" / "video" / f"review-{i + 1}.png"
    subprocess.run([ffmpeg, "-y", "-loglevel", "error", "-ss", str(seconds), "-i", str(video), "-frames:v", "1", str(frame)], check=True)
    if not frame.is_file() or frame.stat().st_size == 0:
        raise ValueError(f"Frame de revisão ausente no instante {seconds}")
    review_times.append(round(seconds, 2))
    offset += segment["duration_seconds"]
report = {"passed": True, "duration_seconds": total, "mean_volume_db": volume, "full_decode_success": True, "video_codec": "h264", "audio_codec": "aac", "pauses_over_1_5_seconds": long_pauses, "silence_threshold_db": -42, "frames_for_visual_review": len(review_times), "review_frame_times_seconds": review_times}
(ROOT / "output" / "video" / "video-validation.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
