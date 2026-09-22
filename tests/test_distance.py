"""Unit tests for distance module."""

import unittest

from simulator.distance import euclidean_distance, find_nearest_agent
from simulator.models import Agent, Point, Warehouse


class TestDistance(unittest.TestCase):
    """Test distance calculation and nearest-agent logic."""

    def test_pythagorean_triple(self) -> None:
        """(0,0) -> (3,4) = 5.0"""
        p1 = Point(0.0, 0.0)
        p2 = Point(3.0, 4.0)
        self.assertAlmostEqual(euclidean_distance(p1, p2), 5.0, places=9)

    def test_same_point(self) -> None:
        """Distance between identical points must be 0.0."""
        p1 = Point(42.5, 17.8)
        p2 = Point(42.5, 17.8)
        self.assertEqual(euclidean_distance(p1, p2), 0.0)

    def test_decimal_coordinates(self) -> None:
        """Accurate calculation with arbitrary float coordinates."""
        p1 = Point(1.5, 2.5)
        p2 = Point(4.5, 6.5)
        # dx = 3, dy = 4 -> 5.0
        self.assertAlmostEqual(euclidean_distance(p1, p2), 5.0, places=9)

    def test_find_nearest_agent_basic(self) -> None:
        """Finds closest agent correctly."""
        wh = Warehouse(id="W1", location=Point(0.0, 0.0))
        a1 = Agent.create("A1", Point(10.0, 10.0))
        a2 = Agent.create("A2", Point(1.0, 1.0))
        a3 = Agent.create("A3", Point(50.0, 50.0))

        nearest = find_nearest_agent(wh, [a1, a2, a3])
        self.assertEqual(nearest.id, "A2")

    def test_find_nearest_agent_tie_breaking(self) -> None:
        """Deterministic tie-breaking picks lexicographically smaller agent ID."""
        wh = Warehouse(id="W1", location=Point(0.0, 0.0))
        # Both A2 and A1 are exactly 5.0 units away
        a2 = Agent.create("A2", Point(3.0, 4.0))
        a1 = Agent.create("A1", Point(4.0, 3.0))

        nearest = find_nearest_agent(wh, [a2, a1])
        self.assertEqual(nearest.id, "A1")

    def test_empty_agents_raises_value_error(self) -> None:
        """Searching in an empty list of agents raises ValueError."""
        wh = Warehouse(id="W1", location=Point(0.0, 0.0))
        with self.assertRaises(ValueError):
            find_nearest_agent(wh, [])


if __name__ == "__main__":
    unittest.main()
