"""Cria o ZIP de entrega; modo final exige identificação completa e vídeo."""
import argparse
import hashlib
import json
import re
import unicodedata
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def slug(value):
    plain = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "_", plain).strip("_")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--draft", action="store_true", help="Permite pendências administrativas, registradas dentro do ZIP.")
    args = parser.parse_args()
    info = json.loads((ROOT / "entrega.json").read_text(encoding="utf-8"))
    pending = []
    if not info.get("class_name"):
        pending.append("Confirmar a turma e renomear o ZIP de acordo com o padrão da atividade.")
    members = info.get("members", [])
    if info.get("submission_mode") == "individual":
        if len(members) != 1 or not members[0].get("name") or not members[0].get("rm"):
            pending.append("Informar nome e RM do único autor do trabalho individual.")
    elif not 3 <= len(members) <= 5 or any(not m.get("name") or not m.get("rm") for m in members):
        pending.append("Confirmar nomes e RMs de todos os 3 a 5 integrantes exigidos para uma entrega em equipe.")
    if len({m.get("rm") for m in members}) != len(members):
        pending.append("Corrigir RMs duplicados na equipe.")
    video = ROOT / info.get("video_file", "arquivo-inexistente")
    if not video.is_file() and not info.get("video_url"):
        pending.append("Incluir o vídeo de 3 a 5 minutos ou o seu link acessível.")
    if not info.get("video_url"):
        pending.append("Incluir o link público do vídeo de 3 a 5 minutos, exigido pelo enunciado.")
    if pending and not args.draft:
        parser.error("Pacote final bloqueado: " + " ".join(pending))
    required = ["dist/index.html", "output/pdf/agroorbit-fase6-relatorio.pdf", "docs/evidencias/01-dashboard.png", "models/risk_forest.json.gz", "data/sample/gold.csv"]
    missing = [name for name in required if not (ROOT / name).is_file()]
    if missing:
        parser.error("Artefatos ausentes: " + ", ".join(missing))
    folders = ["backend", "src", "public", "models", "data/sample", "docs", "tests", "scripts", "dist", "output/pdf", "output/video", ".github"]
    names = ["README.md", "package.json", "package-lock.json", "index.html", "vite.config.js", "requirements-model.txt", "requirements-video.txt", "entrega.json", ".gitignore", ".gitattributes"]
    files = {ROOT / name for name in names if (ROOT / name).is_file()}
    for folder in folders:
        files.update(p for p in (ROOT / folder).rglob("*") if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc")
    output = ROOT / "output" / "delivery"
    output.mkdir(parents=True, exist_ok=True)
    class_name = slug(info["class_name"]) if info.get("class_name") else "TURMA_PENDENTE"
    name = f"{slug(info['responsible_name'])}_rm{slug(info['responsible_rm'])}_{class_name}_fase6_atividade.zip"
    target = output / name
    manifest = {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)}
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=7) as archive:
        for file in sorted(files):
            archive.write(file, "agroorbit-fase6/" + file.relative_to(ROOT).as_posix())
        archive.writestr("agroorbit-fase6/MANIFEST-SHA256.json", json.dumps(manifest, indent=2))
        if pending:
            archive.writestr("agroorbit-fase6/PENDENCIAS.txt", "PACOTE DE PREPARAÇÃO - CONFERIR ANTES DO ENVIO\n\n" + "\n".join("- " + p for p in pending) + "\n\nVídeo: narração sintetizada. Revisar antes da submissão.\n")
    with zipfile.ZipFile(target) as archive:
        if archive.testzip() is not None:
            raise RuntimeError("Falha de integridade do ZIP.")
        for name, expected in manifest.items():
            actual = hashlib.sha256(archive.read("agroorbit-fase6/" + name)).hexdigest()
            if actual != expected:
                raise RuntimeError("Falha no hash de " + name)
    print(json.dumps({"path": str(target), "files": len(files), "size_bytes": target.stat().st_size, "sha256": hashlib.sha256(target.read_bytes()).hexdigest(), "draft": args.draft, "pending": pending}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
