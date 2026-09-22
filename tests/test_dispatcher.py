"""Unit tests for dispatcher module."""

import unittest

from simulator.dispatcher import assign_packages
from simulator.models import Agent, Package, Point, Warehouse


class TestDispatcher(unittest.TestCase):
    """Test package dispatching and assignment rules."""

    def setUp(self) -> None:
        self.w1 = Warehouse("W1", Point(0.0, 0.0))
        self.w2 = Warehouse("W2", Point(100.0, 100.0))

        # A1 is close to W1, A2 is close to W2, A3 is far from both
        self.a1 = Agent.create("A1", Point(2.0, 2.0))
        self.a2 = Agent.create("A2", Point(98.0, 98.0))
        self.a3 = Agent.create("A3", Point(500.0, 500.0))

    def test_nearest_agent_assignment(self) -> None:
        """Packages at W1 go to A1, packages at W2 go to A2."""
        p1 = Package("P1", "W1", Point(10.0, 10.0))
        p2 = Package("P2", "W2", Point(90.0, 90.0))

        assignments = assign_packages(
            [self.w1, self.w2],
            [self.a1, self.a2, self.a3],
            [p1, p2],
        )

        self.assertEqual(len(assignments["A1"]), 1)
        self.assertEqual(assignments["A1"][0].id, "P1")

        self.assertEqual(len(assignments["A2"]), 1)
        self.assertEqual(assignments["A2"][0].id, "P2")

        # Idle agent A3 is included with an empty list
        self.assertIn("A3", assignments)
        self.assertEqual(assignments["A3"], [])

    def test_multiple_packages_from_same_warehouse(self) -> None:
        """Multiple packages from W1 all map to A1 in order of appearance."""
        p1 = Package("P1", "W1", Point(10.0, 10.0))
        p2 = Package("P2", "W1", Point(20.0, 20.0))
        p3 = Package("P3", "W1", Point(30.0, 30.0))

        assignments = assign_packages(
            [self.w1],
            [self.a1, self.a2],
            [p1, p2, p3],
        )

        self.assertEqual([p.id for p in assignments["A1"]], ["P1", "P2", "P3"])

    def test_equidistant_tie_breaking(self) -> None:
        """Equidistant agents break ties lexicographically by ID."""
        wh = Warehouse("W_CENTER", Point(50.0, 50.0))
        # Both agents are exactly 10 units away
        agent_b = Agent.create("B_AGENT", Point(50.0, 60.0))
        agent_a = Agent.create("A_AGENT", Point(50.0, 40.0))

        pkg = Package("P_TEST", "W_CENTER", Point(0.0, 0.0))

        assignments = assign_packages(
            [wh],
            [agent_b, agent_a],
            [pkg],
        )

        # A_AGENT is chosen over B_AGENT
        self.assertEqual(len(assignments["A_AGENT"]), 1)
        self.assertEqual(len(assignments["B_AGENT"]), 0)

    def test_assignment_ignores_current_location_changes(self) -> None:
        """Package assignment strictly evaluates initial_location, ignoring current_location."""
        wh = Warehouse("W1", Point(0.0, 0.0))
        # A1 initial is (2,2), A2 initial is (10,10)
        a1 = Agent.create("A1", Point(2.0, 2.0))
        a2 = Agent.create("A2", Point(10.0, 10.0))

        # Mutate current location of A1 to be far away
        a1.current_location = Point(999.0, 999.0)

        pkg = Package("P1", "W1", Point(5.0, 5.0))
        assignments = assign_packages([wh], [a1, a2], [pkg])

        # A1 is still selected because initial_location (2,2) was closer than (10,10)
        self.assertEqual(assignments["A1"][0].id, "P1")


if __name__ == "__main__":
    unittest.main()
