import copy
import json
import tempfile
import unittest
from pathlib import Path

from backend.catalog import ROOT
from backend.model import predict
from backend.pipeline import aggregate, persist, run_pipeline, validate
from backend.rules import decide
from backend.simulator import simulate


class PipelineTests(unittest.TestCase):
    def test_reproducible_simulation(self):
        self.assertEqual(simulate("seca", "faz-002", 42), simulate("seca", "faz-002", 42))
        self.assertNotEqual(simulate(seed=42)[0], simulate(seed=43)[0])

    def test_quality_reconciliation_and_quarantine(self):
        events, meta = simulate()
        snapshot, silver, gold = run_pipeline(events, meta)
        self.assertEqual(len(events), 1013)
        self.assertEqual(len(silver), 1008)
        self.assertEqual(len(gold), 42)
        self.assertEqual(snapshot["quality"]["quarantined"], 4)
        self.assertEqual(snapshot["quality"]["duplicates"], 1)
        self.assertEqual(sum(snapshot["quality"][k] for k in ("accepted", "quarantined", "duplicates")), len(events))

    def test_reject_nonfinite_boolean_missing_and_bad_timestamp(self):
        original = simulate()[0][0]
        for field, value in [("temperature_c", float("nan")), ("rain_mm", float("inf")), ("ndvi", True), ("soil_moisture_pct", -1), ("captured_at", "2026-09-01T00:00:00"), ("captured_at", "2026-09-01T00:30:00Z")]:
            row = {**original, field: value}
            with self.subTest(field=field, value=value):
                valid, rejected, duplicates = validate([row])
                self.assertFalse(valid)
                self.assertEqual(len(rejected), 1)
                self.assertFalse(duplicates)

    def test_duplicate_conflict_is_not_silently_accepted(self):
        row = simulate()[0][0]
        valid, rejected, duplicates = validate([row, {**row, "temperature_c": row["temperature_c"] + 1}])
        self.assertEqual((len(valid), len(rejected), len(duplicates)), (1, 1, 0))

    def test_daily_rain_is_sum_not_average(self):
        events, _ = simulate()
        silver = validate(events)[0]
        gold = aggregate(silver)
        rows = [r for r in silver if r["farm_id"] == "faz-001" and r["captured_at"].startswith("2026-09-01")]
        result = next(r for r in gold if r["farm_id"] == "faz-001" and r["date"] == "2026-09-01")
        self.assertAlmostEqual(result["chuva_mm"], sum(r["rain_mm"] for r in rows), 2)
        self.assertEqual(result["readings"], 24)

    def test_warmup_and_isolation_between_farms(self):
        events, meta = simulate("seca", "faz-002")
        snapshot, _, gold = run_pipeline(events, meta)
        for row in gold:
            self.assertEqual(row["ml_ready"], row["date"] == "2026-09-14")
            if not row["ml_ready"]:
                self.assertIsNone(row["risk_probability"])
        normal_events, normal_meta = simulate()
        baseline = run_pipeline(normal_events, normal_meta)[0]
        # Aleatoriedade das outras fazendas não depende do cenário do talhão-alvo.
        for farm_id in ("faz-001", "faz-003"):
            a = next(f for f in snapshot["farms"] if f["id"] == farm_id)
            b = next(f for f in baseline["farms"] if f["id"] == farm_id)
            self.assertEqual(a["latest"], b["latest"])

    def test_scenario_changes_risk_and_data(self):
        dry = run_pipeline(*simulate("seca", "faz-002"))[0]["farms"][1]
        wet = run_pipeline(*simulate("chuva", "faz-002"))[0]["farms"][1]
        self.assertEqual(dry["decision"]["level"], "alto")
        self.assertLess(dry["latest"]["soil_moisture_pct"], wet["latest"]["soil_moisture_pct"])
        self.assertGreater(dry["latest"]["risk_probability"], wet["latest"]["risk_probability"])

    def test_sensor_failure_never_looks_current(self):
        snapshot, _, _ = run_pipeline(*simulate("falha", "faz-002"))
        farm = snapshot["farms"][1]
        self.assertFalse(farm["available"])
        self.assertEqual(farm["decision"]["level"], "indisponivel")
        self.assertEqual(farm["latest"]["date"], "2026-09-13")
        self.assertEqual(snapshot["quality"]["quarantined"], 28)
        alert = next(a for a in snapshot["alerts"] if a["farm_id"] == farm["id"])
        self.assertFalse(alert["evidence_event_ids"])

    def test_rule_boundaries(self):
        row = {"soil_moisture_pct": 25, "temp_max": 34.9, "chuva_acum_7d": 10, "ndvi_tendencia_7d": -0.04}
        self.assertEqual(decide(row, 0.499)["level"], "atencao")
        self.assertEqual(decide({**row, "soil_moisture_pct": 40}, 0.499)["level"], "baixo")
        self.assertEqual(decide({**row, "soil_moisture_pct": 40}, 0.5)["level"], "atencao")
        self.assertEqual(decide({**row, "soil_moisture_pct": 40}, 0.7)["level"], "alto")
        self.assertEqual(decide({**row, "soil_moisture_pct": 24.99}, None)["level"], "alto")

    def test_replay_produces_identical_artifacts(self):
        events, metadata = simulate()
        with tempfile.TemporaryDirectory() as temp:
            first, second = Path(temp) / "first", Path(temp) / "second"
            persist(events, metadata, first)
            replay = [json.loads(r) for r in (first / "bronze.jsonl").read_text().splitlines()]
            persist(replay, metadata, second)
            self.assertEqual((first / "checksums.json").read_bytes(), (second / "checksums.json").read_bytes())

    def test_exported_forest_matches_original_reference_cases(self):
        cases = json.loads((ROOT / "tests" / "model_cases.json").read_text())
        for case in cases:
            self.assertAlmostEqual(predict(case["features"]), case["probability"], 12)


if __name__ == "__main__":
    unittest.main()
