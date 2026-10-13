"""Gera narração neural pt-BR inteiramente local com Kokoro ONNX.

Opcional: instalar requirements-video.txt em um ambiente isolado.
Não é necessário para executar a plataforma ou assistir ao MP4 pronto.
"""
import argparse
import json
import subprocess
import wave
from pathlib import Path

import imageio_ffmpeg
import onnxruntime as ort
import soundfile as sf
from kokoro_onnx import Kokoro

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "tmp" / "video"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--voice", default="pf_dora")
    parser.add_argument("--speed", type=float, default=1.05)
    parser.add_argument("--model-dir", type=Path, default=ROOT / "tmp" / "tts-model")
    args = parser.parse_args()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    segments = json.loads((ROOT / "docs" / "narracao-video.json").read_text(encoding="utf-8"))
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    model_path = args.model_dir / "kokoro-v1.0.onnx"
    voices_path = args.model_dir / "voices-v1.0.bin"
    if not model_path.is_file() or not voices_path.is_file():
        parser.error("Baixe os pesos públicos conforme docs/06-roteiro-video.md; o script não envia o roteiro pela rede.")
    ort.disable_telemetry_events()
    voice_model = Kokoro(str(model_path), str(voices_path))
    for i, segment in enumerate(segments):
        raw = OUTPUT / f"neural-raw-{i + 1}.wav"
        wav = OUTPUT / f"neural-{i + 1}.wav"
        samples, sample_rate = voice_model.create(segment["text"], voice=args.voice, speed=args.speed, lang="pt-br", sentence_pause=0.18, clause_pause=0.08)
        sf.write(str(raw), samples, sample_rate)
        subprocess.run([ffmpeg, "-y", "-loglevel", "error", "-i", str(raw), "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-ar", "48000", "-ac", "1", str(wav)], check=True)
        with wave.open(str(wav), "rb") as source:
            duration = source.getnframes() / source.getframerate()
        segment.update(audio_duration=duration, duration=round(max(32, duration + 0.8), 2), audio=str(wav), narration=f"Kokoro v1.0 / {args.voice}, voz neural brasileira sintetizada localmente, velocidade {args.speed}", audio_offset=0.25)
        print(f"Segmento {i + 1}: áudio {duration:.1f}s / vídeo {segment['duration']:.1f}s", flush=True)
    total = sum(s["duration"] for s in segments)
    if not 180 <= total <= 300:
        raise ValueError(f"Duração fora do intervalo: {total:.2f}s; ajuste --speed e gere novamente.")
    (OUTPUT / "segments.json").write_text(json.dumps(segments, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Duração total prevista: {total:.1f} segundos")


if __name__ == "__main__":
    main()
