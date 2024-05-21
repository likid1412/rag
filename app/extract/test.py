"""test"""

import json


def simulate_embedding() -> list[float]:
    with open("test_embedding_vector.json", "r", encoding="utf-8") as f:
        return json.load(f)
