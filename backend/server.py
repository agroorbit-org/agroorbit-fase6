"""Servidor local da plataforma. Python 3.9+, sem dependências externas."""
import argparse
import json
import mimetypes
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from .catalog import ROOT
from .pipeline import persist
from .simulator import simulate

ALLOWED_DOWNLOADS = {"bronze.jsonl", "silver.csv", "gold.csv", "alerts.json", "quality.json", "quarantine.json", "checksums.json"}


class Platform:
    def __init__(self, run_root):
        self.lock = threading.RLock()
        self.run_root = Path(run_root)
        self.snapshot = None
        self.output = None
        self.simulate("baseline", "faz-002", 42)

    def simulate(self, scenario, target, seed):
        events, metadata = simulate(scenario, target, seed)
        with self.lock:
            output = self.run_root / metadata["batch_id"]
            snapshot = persist(events, metadata, output)
            self.output, self.snapshot = output, snapshot
            return snapshot


def handler_for(platform, static_root):
    class Handler(BaseHTTPRequestHandler):
        def send(self, status, body, content_type="application/json; charset=utf-8", filename=None):
            data = body if isinstance(body, bytes) else json.dumps(body, ensure_ascii=False, allow_nan=False).encode()
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store" if content_type.startswith("application/json") else "no-cache")
            self.send_header("X-Content-Type-Options", "nosniff")
            if filename:
                self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            path = urlparse(self.path).path
            if path == "/api/health":
                self.send(200, {"status": "ok", "version": "1.0.0", "simulated": True})
            elif path == "/api/dashboard":
                with platform.lock:
                    self.send(200, platform.snapshot)
            elif path.startswith("/api/download/"):
                filename = path.rsplit("/", 1)[-1]
                if filename not in ALLOWED_DOWNLOADS:
                    self.send(404, {"error": "Arquivo não disponível."})
                    return
                with platform.lock:
                    data = (platform.output / filename).read_bytes()
                self.send(200, data, "text/csv; charset=utf-8" if filename.endswith("csv") else "application/json; charset=utf-8" if filename.endswith("json") else "application/x-ndjson", filename)
            elif path.startswith("/api/"):
                self.send(404, {"error": "Endpoint não encontrado."})
            else:
                file_path = (static_root / path.lstrip("/")).resolve() if path != "/" else static_root / "index.html"
                if not file_path.is_relative_to(static_root) or not file_path.is_file():
                    self.send(404, {"error": "Arquivo não encontrado. Execute npm run build antes de iniciar."})
                    return
                self.send(200, file_path.read_bytes(), mimetypes.guess_type(str(file_path))[0] or "application/octet-stream")

        def do_POST(self):
            if urlparse(self.path).path != "/api/simulate":
                self.send(404, {"error": "Endpoint não encontrado."})
                return
            origin = self.headers.get("Origin")
            if origin and origin not in {f"http://127.0.0.1:{self.server.server_port}", f"http://localhost:{self.server.server_port}", "http://127.0.0.1:5173", "http://localhost:5173"}:
                self.send(403, {"error": "Origem não autorizada para o servidor local."})
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= 4096 or not self.headers.get("Content-Type", "").startswith("application/json"):
                    raise ValueError("Envie um objeto JSON com até 4096 bytes.")
                payload = json.loads(self.rfile.read(length))
                if not isinstance(payload, dict) or set(payload) - {"scenario", "target", "seed"}:
                    raise ValueError("Campos permitidos: scenario, target, seed.")
                snapshot = platform.simulate(payload.get("scenario", "baseline"), payload.get("target", "faz-002"), payload.get("seed", 42))
                self.send(200, snapshot)
            except (ValueError, TypeError) as error:
                self.send(400, {"error": str(error)})

    return Handler


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8766)
    parser.add_argument("--run-dir", type=Path, default=ROOT / "data" / "runs")
    args = parser.parse_args()
    if not (ROOT / "dist" / "index.html").is_file():
        parser.error("Build ausente. Execute npm install && npm run build.")
    platform = Platform(args.run_dir)
    server = ThreadingHTTPServer(("127.0.0.1", args.port), handler_for(platform, (ROOT / "dist").resolve()))
    print(f"AgroOrbit Horizon disponível em http://127.0.0.1:{args.port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()


if __name__ == "__main__":
    main()
