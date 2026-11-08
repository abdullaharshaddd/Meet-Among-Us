import math


def normalise(vector: list[float]) -> list[float]:
    length = math.sqrt(sum(value * value for value in vector))

    if length == 0:
        return list(vector)

    return [value / length for value in vector]


def cosine_similarity(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(normalise(a), normalise(b)))
