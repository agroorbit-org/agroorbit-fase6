"""Inferência do Random Forest legado exportado em JSON.

Reproduz OneHotEncoder + StandardScaler + árvores, sem desserializar pickle
no servidor. A exportação e a paridade são verificadas por export_model.py.
"""
import gzip
import json
import math
import struct
from functools import lru_cache

from .catalog import ROOT


@lru_cache(maxsize=1)
def load_model():
    with gzip.open(ROOT / "models" / "risk_forest.json.gz", "rt", encoding="utf-8") as stream:
        return json.load(stream)


def predict(features):
    model = load_model()
    vector = []
    for field, categories in zip(model["categorical_features"], model["categories"]):
        vector.extend(float(features[field] == value) for value in categories)
    for field, mean, scale in zip(model["numeric_features"], model["mean"], model["scale"]):
        value = float(features[field])
        if not math.isfinite(value):
            raise ValueError(f"Feature não finita: {field}")
        vector.append((value - mean) / scale)
    # O sklearn converte a entrada das árvores para float32.
    vector = [struct.unpack("f", struct.pack("f", v))[0] for v in vector]
    probabilities = []
    for tree in model["trees"]:
        node = 0
        while tree["left"][node] != -1:
            node = tree["left"][node] if vector[tree["feature"][node]] <= tree["threshold"][node] else tree["right"][node]
        probabilities.append(tree["probability"][node])
    return sum(probabilities) / len(probabilities)
