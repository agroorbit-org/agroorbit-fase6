import json
import tempfile
import threading
import unittest
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
from pathlib import Path

from backend.server import Platform, handler_for


class ServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temp.name)
        (cls.root / "index.html").write_text("<title>AgroOrbit</title>")
        cls.platform = Platform(cls.root / "runs")
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), handler_for(cls.platform, cls.root))
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()
        cls.temp.cleanup()

    def request(self, method, path, payload=None, headers=None):
        conn = HTTPConnection("127.0.0.1", self.server.server_port, timeout=10)
        body = json.dumps(payload).encode() if payload is not None else None
        conn.request(method, path, body=body, headers=headers or {"Content-Type": "application/json"})
        response = conn.getresponse()
        data = response.read()
        status = response.status
        conn.close()
        return status, data

    def test_health_and_frontend(self):
        self.assertEqual(json.loads(self.request("GET", "/api/health")[1])["status"], "ok")
        self.assertIn(b"AgroOrbit", self.request("GET", "/")[1])

    def test_scenario_and_download_have_same_batch(self):
        status, body = self.request("POST", "/api/simulate", {"scenario": "seca", "target": "faz-002", "seed": 42})
        self.assertEqual(status, 200)
        snapshot = json.loads(body)
        self.assertEqual(snapshot["farms"][1]["decision"]["level"], "alto")
        status, csv = self.request("GET", "/api/download/silver.csv")
        self.assertEqual(status, 200)
        self.assertIn(snapshot["metadata"]["batch_id"].encode(), csv)
        self.assertEqual(len(csv.decode().splitlines()), 1009)

    def test_invalid_request_does_not_change_current_batch(self):
        before = self.platform.snapshot["metadata"]["batch_id"]
        for payload in ({"scenario": "inexistente"}, {"seed": -1}, {"seed": True}, {"unexpected": 1}, [], {"target": "outra"}):
            self.assertEqual(self.request("POST", "/api/simulate", payload)[0], 400)
        self.assertEqual(before, self.platform.snapshot["metadata"]["batch_id"])

    def test_foreign_origin_is_rejected(self):
        self.assertEqual(self.request("POST", "/api/simulate", {"scenario": "seca"}, {"Content-Type": "application/json", "Origin": "https://example.invalid"})[0], 403)

    def test_download_allowlist_and_path_traversal(self):
        self.assertEqual(self.request("GET", "/api/download/server.py")[0], 404)
        self.assertEqual(self.request("GET", "/../server.py")[0], 404)
        self.assertEqual(self.request("GET", "/api/unknown")[0], 404)


if __name__ == "__main__":
    unittest.main()
