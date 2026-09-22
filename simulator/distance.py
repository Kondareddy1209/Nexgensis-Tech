"""Euclidean distance and nearest-neighbor calculations."""

import math
from typing import Sequence

from .models import Agent, Point, Warehouse


def euclidean_distance(point_a: Point, point_b: Point) -> float:
    """Calculate exact Euclidean distance between two 2D points using math.hypot.

    Does not round results to prevent precision drift during intermediate simulation steps.
    """
    dx = point_a.x - point_b.x
    dy = point_a.y - point_b.y
    return math.hypot(dx, dy)


def find_nearest_agent(warehouse: Warehouse, agents: Sequence[Agent]) -> Agent:
    """Find the closest agent to a warehouse based on agent INITIAL location.

    When distances are equal, deterministic tie-breaking selects the
    lexicographically smaller agent ID.

    Raises:
        ValueError: If the agents sequence is empty.
    """
    if not agents:
        raise ValueError("Cannot find nearest agent from an empty agents sequence.")

    def sort_key(agent: Agent) -> tuple[float, str]:
        distance = euclidean_distance(agent.initial_location, warehouse.location)
        return (distance, agent.id)

    return min(agents, key=sort_key)
