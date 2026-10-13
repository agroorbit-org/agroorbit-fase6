"""Sensores virtuais reprodutíveis; todas as fontes são sintéticas.

Temperatura (°C), umidade relativa do solo (%), luminosidade (lux) e
precipitação (mm/h). NDVI/NDWI são contexto orbital simulado, não sensores
do circuito. A granularidade é horária, com 24 registros por dia e talhão.
"""
import copy
import hashlib
import math
import random
from datetime import datetime, timedelta

from .catalog import DAYS, FARMS, FARM_BY_ID, SCENARIOS, START


def simulate(scenario="baseline", target="faz-002", seed=42):
    if scenario not in SCENARIOS or target not in FARM_BY_ID:
        raise ValueError("Cenário ou propriedade desconhecido.")
    if isinstance(seed, bool) or not isinstance(seed, int) or not 0 <= seed <= 999999:
        raise ValueError("A semente deve ser um inteiro entre 0 e 999999.")
    batch = hashlib.sha256(f"sim.v1:{scenario}:{target}:{seed}".encode()).hexdigest()[:12]
    start = datetime.fromisoformat(START)
    events = []
    for farm in FARMS:
        rng = random.Random(f"{seed}:{farm['id']}")
        for day in range(DAYS):
            # Um sinal orbital sintético por dia, compartilhado pelas leituras horárias.
            orbital = farm["ndvi"] + (0.003 if farm["id"] != "faz-002" else -0.006) * day
            wet_day = day % (4 if farm["id"] != "faz-002" else 6) == 0
            for hour in range(24):
                timestamp = (start + timedelta(days=day, hours=hour)).isoformat().replace("+00:00", "Z")
                daylight = max(0.0, math.sin((hour - 6) * math.pi / 12))
                temp = farm["temp"] - 5 + daylight * 10 + rng.uniform(-1, 1)
                soil = farm["soil"] - day * (0.35 if farm["id"] == "faz-002" else 0.08) - daylight * 3 + rng.uniform(-1.2, 1.2)
                rain = rng.uniform(2.0, 4.0) if wet_day and hour in (5, 6, 7) else 0
                ndvi = orbital
                if farm["id"] == target and day >= 7:
                    if scenario == "seca":
                        soil = max(14, 34 - (day - 7) * 2.8) + rng.uniform(-1, 1)
                        temp += 5
                        rain = 0
                        ndvi -= (day - 6) * 0.025
                    elif scenario == "chuva":
                        soil = 53 + (day - 7) * 1.5 + rng.uniform(-1, 1)
                        temp -= 3
                        rain = rng.uniform(1.5, 3) if hour in (5, 6, 7) and day % 2 else 0
                        ndvi += (day - 6) * 0.014
                    elif scenario == "falha" and day == DAYS - 1:
                        soil = None  # As últimas 24 horas não chegam à camada Silver.
                event_id = f"{farm['id']}-{day:02d}-{hour:02d}"
                events.append({
                    "event_id": event_id, "batch_id": batch, "contract_version": "telemetry.v2",
                    "source": "agroorbit-simulator", "simulated": True, "farm_id": farm["id"],
                    "plot_id": farm["plot_id"], "captured_at": timestamp,
                    "temperature_c": round(temp, 2), "soil_moisture_pct": round(soil, 2) if soil is not None else None,
                    "luminosity_lux": round(max(0, daylight * 65000 + (rng.uniform(-500, 500) if daylight else 0)), 1),
                    "rain_mm": round(rain, 2), "ndvi": round(ndvi, 4), "ndwi": round(ndvi - 0.35, 4),
                    "cloud_cover_pct": 12.0,
                })
    # Quatro defeitos conhecidos mais uma retransmissão: qualidade visível e testável.
    events.append(copy.deepcopy(events[0]))
    for field, value, suffix in [
        ("soil_moisture_pct", 140, "range"),
        ("temperature_c", None, "missing"),
        ("captured_at", "data-invalida", "date"),
        ("farm_id", "faz-desconhecida", "farm"),
    ]:
        bad = copy.deepcopy(events[10])
        bad["event_id"] = "fault-" + suffix
        bad[field] = value
        events.append(bad)
    return events, {"batch_id": batch, "scenario": scenario, "scenario_label": SCENARIOS[scenario], "target": target, "seed": seed, "days": DAYS, "interval_minutes": 60, "simulator_version": "sim.v1"}
