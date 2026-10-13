"""Cadastro demonstrativo e parâmetros explícitos da simulação."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
START = "2026-09-01T00:00:00+00:00"
DAYS = 14
RULE_VERSION = "water-risk.v1"
FARMS = [
    {"id": "faz-001", "plot_id": "S-12", "name": "Sítio Horizonte", "city": "Sorriso", "state": "MT", "crop": "soja", "area_ha": 1240, "lat": -12.55, "lon": -55.71, "soil": 57, "temp": 28, "ndvi": 0.74},
    {"id": "faz-002", "plot_id": "N-04", "name": "Fazenda Boa Vista", "city": "Rio Verde", "state": "GO", "crop": "milho", "area_ha": 860, "lat": -17.79, "lon": -50.92, "soil": 39, "temp": 31, "ndvi": 0.51},
    {"id": "faz-003", "plot_id": "C-02", "name": "Café Serra Clara", "city": "Patrocínio", "state": "MG", "crop": "cafe", "area_ha": 420, "lat": -18.94, "lon": -46.99, "soil": 62, "temp": 25, "ndvi": 0.67},
]
FARM_BY_ID = {f["id"]: f for f in FARMS}
SCENARIOS = {
    "baseline": "Monitoramento habitual",
    "seca": "Estresse hídrico",
    "chuva": "Recuperação após chuva",
    "falha": "Falha de sensor",
}
