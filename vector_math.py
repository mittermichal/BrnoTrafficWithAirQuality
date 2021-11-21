import math
from typing import Tuple, Callable

Vector = Tuple[float, float]


def dot(a: Vector, b: Vector):
    return a[0] * b[0] + a[1] * b[1]


def sub(a: Vector, b: Vector):
    return a[0] - b[0], a[1] - b[1]


def add(a: Vector, b: Vector):
    return a[0] + b[0], a[1] + b[1]


def mul(a: Vector, k: float):
    return k * a[0], k * a[1]


def PointToLineSegmentSquaredDistance(point, segment1, segment2) -> float:
    direction = segment2 - segment1
    segmentLengthSqrd = dot(direction, direction)
    if segmentLengthSqrd == 0.0:
        delta = segment1 - point
        return dot(delta, delta)

    t = dot(point - segment1, direction) / segmentLengthSqrd
    t = max(0.0, min(1.0, t))
    closest = add(segment1, mul(direction, t))
    delta = sub(closest, point)
    return dot(delta, delta)


def weighted_distance_sum(
        point: Vector,
        segment1: Vector,
        segment2: Vector,
        weight: Callable[[float], float]):
    """
    Integrates weighted distance from point to line segment
    :param point:
    :param segment1:
    :param segment2:
    :param weight:
    :return:
    """
    s = 0
    t = 0
    direction = sub(segment2, segment1)
    segment_size = math.sqrt(dot(direction, direction))
    dt = 1 / segment_size
    # dt = min(dt * k, 1)  # for changing precision
    while t < 1:
        segment_point = add(segment1, mul(direction, t))
        point_to_segment = sub(point, segment_point)
        dist = math.sqrt(dot(point_to_segment, point_to_segment))
        s += weight(dist) * dt
        t = t + dt
    return s
