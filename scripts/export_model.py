"""Exporta o artefato próprio do agroorbit-ai e verifica paridade da inferência.

Requer o ambiente opcional requirements-model.txt. O servidor não usa pickle.
"""
import argparse
import gzip
import hashlib
import json
import random
import sys
from pathlib import Path

import joblib
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=ROOT.parent / "agroorbit-ai" / "models" / "best_model.pkl")
    args = parser.parse_args()
    bundle = joblib.load(args.source)
    pre = bundle["pipeline"].named_steps["pre"]
    classifier = bundle["pipeline"].named_steps["model"]
    cat = pre.named_transformers_["cat"]
    num = pre.named_transformers_["num"]
    trees = []
    for estimator in classifier.estimators_:
        tree = estimator.tree_
        values = tree.value[:, 0, :]
        trees.append({"left": tree.children_left.tolist(), "right": tree.children_right.tolist(), "feature": tree.feature.tolist(), "threshold": tree.threshold.tolist(), "probability": (values[:, 1] / values.sum(axis=1)).tolist()})
    artifact = {"source_repository": "https://github.com/agroorbit-org/agroorbit-ai", "source_commit": "94bdf06312fdbf12568166bb692ac24a243c3e9f", "source_sha256": hashlib.sha256(args.source.read_bytes()).hexdigest(), "categorical_features": bundle["cat_features"], "numeric_features": bundle["num_features"], "categories": [c.tolist() for c in cat.categories_], "mean": num.mean_.tolist(), "scale": num.scale_.tolist(), "classes": classifier.classes_.tolist(), "trees": trees}
    output = ROOT / "models"
    output.mkdir(exist_ok=True)
    compressed = gzip.compress(json.dumps(artifact, separators=(",", ":")).encode(), mtime=0)
    (output / "risk_forest.json.gz").write_bytes(compressed)
    from backend.model import load_model, predict
    load_model.cache_clear()
    rng = random.Random(1210)
    rows = []
    for _ in range(500):
        temp_min, temp_max = rng.uniform(8, 25), rng.uniform(26, 43)
        rain7 = rng.uniform(0, 120)
        rows.append({"estado": rng.choice(cat.categories_[0].tolist() + ["XX"]), "cultura": rng.choice(cat.categories_[1].tolist() + ["teste"]), "temp_min": temp_min, "temp_max": temp_max, "chuva_mm": rng.uniform(0, 30), "ndvi": rng.uniform(0.1, 0.9), "ndwi": rng.uniform(-0.3, 0.6), "cobertura_nuvem": rng.uniform(0, 80), "chuva_acum_7d": rain7, "chuva_acum_14d": rain7 + rng.uniform(0, 120), "temp_amplitude": temp_max - temp_min, "ndvi_tendencia_7d": rng.uniform(-0.2, 0.2), "dias_sem_chuva": rng.randrange(25), "mes": rng.randrange(1, 13)})
    expected = bundle["pipeline"].predict_proba(pd.DataFrame(rows)[bundle["features"]])[:, 1]
    errors = [abs(predict(row) - float(p)) for row, p in zip(rows, expected)]
    assert max(errors) < 1e-12, max(errors)
    report = {"source_commit": artifact["source_commit"], "source_sha256": artifact["source_sha256"], "artifact_sha256": hashlib.sha256(compressed).hexdigest(), "cases": len(rows), "trees": len(trees), "max_absolute_error": max(errors), "tolerance": 1e-12, "passed": True, "note": "Paridade de software com o modelo legado, não validação agronômica nem nova avaliação de acurácia."}
    (output / "export_validation.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (ROOT / "tests" / "model_cases.json").write_text(json.dumps([{"features": row, "probability": float(p)} for row, p in zip(rows[:12], expected[:12])], indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
