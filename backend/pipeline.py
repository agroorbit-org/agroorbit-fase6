"""Bronze → Silver → Gold → modelo → regras → dashboard.

Uso: python3 -m backend.pipeline --scenario seca --target faz-002
Replay: python3 -m backend.pipeline --input data/sample/bronze.jsonl
"""
import argparse
import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .catalog import DAYS, FARMS, FARM_BY_ID, ROOT, START
from .model import predict
from .rules import LEVELS, decide
from .simulator import simulate

RANGES = {"temperature_c": (-20, 60), "soil_moisture_pct": (0, 100), "luminosity_lux": (0, 150000), "rain_mm": (0, 300), "ndvi": (-1, 1), "ndwi": (-1, 1), "cloud_cover_pct": (0, 100)}


def validate(events):
    valid, rejected, duplicates = [], [], []
    seen = {}
    slots = set()
    start = datetime.fromisoformat(START)
    for index, original in enumerate(events):
        row = dict(original)
        reasons = []
        for field in ("event_id", "batch_id", "source", "farm_id", "plot_id"):
            if not isinstance(row.get(field), str) or not row[field].strip():
                reasons.append(f"{field}: campo obrigatório")
        if row.get("contract_version") != "telemetry.v2" or row.get("simulated") is not True:
            reasons.append("contrato: este pipeline aceita somente telemetry.v2 simulado")
        farm = FARM_BY_ID.get(row.get("farm_id"))
        if farm is None or row.get("plot_id") != farm["plot_id"]:
            reasons.append("farm_id/plot_id: propriedade ou talhão desconhecido")
        try:
            timestamp = datetime.fromisoformat(str(row.get("captured_at", "")).replace("Z", "+00:00"))
            if timestamp.tzinfo is None or not start <= timestamp < start + timedelta(days=DAYS):
                raise ValueError()
            if timestamp.minute or timestamp.second or timestamp.microsecond:
                raise ValueError()
            row["captured_at"] = timestamp.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
        except (ValueError, TypeError):
            reasons.append("captured_at: timestamp horário inválido ou fora da janela de demonstração")
        for field, (low, high) in RANGES.items():
            value = row.get(field)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not low <= value <= high:
                reasons.append(f"{field}: esperado número finito entre {low} e {high}")
        key = (row.get("source"), row.get("event_id"))
        slot = (row.get("farm_id"), row.get("plot_id"), row.get("captured_at"))
        if reasons:
            rejected.append({"row_number": index + 1, "event": original, "reasons": reasons})
        elif key in seen:
            if row == seen[key]:
                duplicates.append({"event_id": row["event_id"], "source": row["source"], "row_number": index + 1})
            else:
                rejected.append({"row_number": index + 1, "event": original, "reasons": ["event_id: conteúdo conflitante"]})
        elif slot in slots:
            rejected.append({"row_number": index + 1, "event": original, "reasons": ["captured_at: mais de uma leitura do talhão na mesma hora"]})
        else:
            seen[key] = row
            slots.add(slot)
            valid.append(row)
    valid.sort(key=lambda e: (e["farm_id"], e["captured_at"]))
    return valid, rejected, duplicates


def aggregate(silver):
    grouped = defaultdict(list)
    for row in silver:
        grouped[(row["farm_id"], row["captured_at"][:10])].append(row)
    output = []
    for farm in FARMS:
        history, dry_days = [], 0
        for day_index in range(DAYS):
            date = (datetime.fromisoformat(START) + timedelta(days=day_index)).date().isoformat()
            readings = grouped.get((farm["id"], date), [])
            if not readings:
                dry_days = None
                continue
            full = len(readings) == 24
            rain = sum(e["rain_mm"] for e in readings)
            dry_days = (0 if rain >= 1 else dry_days + 1 if dry_days is not None else None) if full else None
            row = {
                "farm_id": farm["id"], "plot_id": farm["plot_id"], "date": date,
                "estado": farm["state"], "cultura": farm["crop"], "readings": len(readings),
                "soil_moisture_pct": round(sum(e["soil_moisture_pct"] for e in readings) / len(readings), 2),
                "temperature_c": round(sum(e["temperature_c"] for e in readings) / len(readings), 2),
                "luminosity_lux": round(sum(e["luminosity_lux"] for e in readings) / len(readings)),
                "temp_min": min(e["temperature_c"] for e in readings), "temp_max": max(e["temperature_c"] for e in readings),
                "chuva_mm": round(rain, 2), "ndvi": readings[-1]["ndvi"], "ndwi": readings[-1]["ndwi"],
                "cobertura_nuvem": readings[-1]["cloud_cover_pct"], "dias_sem_chuva": dry_days,
                "mes": int(date[5:7]), "event_ids": [e["event_id"] for e in readings],
            }
            history.append(row)
            for window in (7, 14):
                earliest = (datetime.fromisoformat(date) - timedelta(days=window - 1)).date().isoformat()
                rows = [r for r in history if r["date"] >= earliest]
                row[f"chuva_acum_{window}d"] = round(sum(r["chuva_mm"] for r in rows), 2)
            prior_date = (datetime.fromisoformat(date) - timedelta(days=7)).date().isoformat()
            lag = next((r for r in history if r["date"] == prior_date), None)
            row["ndvi_tendencia_7d"] = round(row["ndvi"] - lag["ndvi"], 4) if lag else None
            row["temp_amplitude"] = round(row["temp_max"] - row["temp_min"], 2)
            # Nunca preencher uma janela incompleta como se fosse observação real.
            window_dates = {(datetime.fromisoformat(date) - timedelta(days=i)).date().isoformat() for i in range(14)}
            complete_history = sum(r["readings"] == 24 and r["date"] in window_dates for r in history) == 14
            row["ml_ready"] = full and complete_history and lag is not None and dry_days is not None
            row["risk_probability"] = round(predict(row), 6) if row["ml_ready"] else None
            rules_input = {**row, "ndvi_tendencia_7d": row["ndvi_tendencia_7d"] or 0}
            row["decision"] = decide(rules_input, row["risk_probability"], available=full)
            output.append(row)
    return output


def run_pipeline(events, metadata):
    silver, quarantine, duplicates = validate(events)
    gold = aggregate(silver)
    final_date = (datetime.fromisoformat(START) + timedelta(days=DAYS - 1)).date().isoformat()
    farms, alerts = [], []
    for farm in FARMS:
        history = [r for r in gold if r["farm_id"] == farm["id"]]
        latest = history[-1] if history else None
        available = latest is not None and latest["date"] == final_date and latest["readings"] == 24
        decision = latest["decision"] if available else decide({}, None, available=False)
        rejected_count = sum(q["event"].get("farm_id") == farm["id"] for q in quarantine)
        farms.append({**farm, "history": history, "latest": latest, "available": available, "decision": decision,
                      "invalid_readings": rejected_count, "readings": [r for r in silver if r["farm_id"] == farm["id"]][-24:]})
        if decision["level"] != "baixo":
            alerts.append({"id": f"{metadata['batch_id']}:{farm['id']}", "farm_id": farm["id"], "farm_name": farm["name"], "plot_id": farm["plot_id"], "date": final_date,
                           **decision, "batch_id": metadata["batch_id"], "evidence_event_ids": latest["event_ids"] if available else []})
    alerts.sort(key=lambda a: LEVELS[a["level"]], reverse=True)
    quality = {"received": len(events), "accepted": len(silver), "quarantined": len(quarantine), "duplicates": len(duplicates),
               "acceptance_pct": round(len(silver) / len(events) * 100, 2) if events else 0,
               "expected_unique": len(FARMS) * DAYS * 24, "reasons": dict(Counter(reason.split(":")[0] for q in quarantine for reason in q["reasons"]))}
    snapshot = {"version": "dashboard.v1", "simulated": True, "metadata": metadata, "period": {"start": START[:10], "end": final_date, "timezone": "UTC"},
                "quality": quality, "farms": farms, "alerts": alerts,
                "model": {"name": "Random Forest · AgroOrbit AI", "source_commit": "94bdf06312fdbf12568166bb692ac24a243c3e9f", "trees": 300,
                          "scope": "Modelo legado treinado em dados e rótulos sintéticos; saída experimental, não validada em campo.",
                          "explanation": "Motivos exibidos são regras rastreáveis. Não são valores SHAP.", "warmup_days": 14},
                "quarantine": quarantine, "duplicates": duplicates}
    return snapshot, silver, gold


def write_csv(path, rows):
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        for row in rows:
            writer.writerow({k: json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v for k, v in row.items()})


def persist(events, metadata, output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    snapshot, silver, gold = run_pipeline(events, metadata)
    (output / "bronze.jsonl").write_text("\n".join(json.dumps(e, ensure_ascii=False, allow_nan=False) for e in events) + "\n", encoding="utf-8")
    write_csv(output / "silver.csv", silver)
    write_csv(output / "gold.csv", gold)
    for filename, data in [("dashboard.json", snapshot), ("quality.json", snapshot["quality"]), ("quarantine.json", snapshot["quarantine"]), ("alerts.json", snapshot["alerts"]), ("metadata.json", metadata)]:
        (output / filename).write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    files = ["bronze.jsonl", "silver.csv", "gold.csv", "dashboard.json", "quality.json", "quarantine.json", "alerts.json"]
    manifest = {name: hashlib.sha256((output / name).read_bytes()).hexdigest() for name in files}
    (output / "checksums.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return snapshot


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", choices=["baseline", "seca", "chuva", "falha"], default="baseline")
    parser.add_argument("--target", choices=list(FARM_BY_ID), default="faz-002")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=Path, default=ROOT / "data" / "sample")
    parser.add_argument("--input", type=Path, help="Bronze JSONL; o arquivo metadata.json deve estar na mesma pasta.")
    args = parser.parse_args()
    if args.input:
        events = [json.loads(line) for line in args.input.read_text(encoding="utf-8").splitlines() if line.strip()]
        metadata = json.loads((args.input.parent / "metadata.json").read_text(encoding="utf-8"))
    else:
        events, metadata = simulate(args.scenario, args.target, args.seed)
    snapshot = persist(events, metadata, args.output)
    if args.output.resolve() == (ROOT / "data" / "sample").resolve():
        destination = ROOT / "public" / "data"
        destination.mkdir(parents=True, exist_ok=True)
        (destination / "dashboard.json").write_text(json.dumps(snapshot, ensure_ascii=False, allow_nan=False), encoding="utf-8")
    print(json.dumps({"output": str(args.output), "quality": snapshot["quality"], "decisions": {f["name"]: f["decision"]["label"] for f in snapshot["farms"]}}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
