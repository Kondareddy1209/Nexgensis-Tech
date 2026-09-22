"""Unit tests for simulation engine."""

import math
import unittest

from simulator.engine import simulate_deliveries
from simulator.models import Agent, Package, Point, Warehouse


class TestEngine(unittest.TestCase):
    """Test sequential physical delivery simulation."""

    def test_single_package_delivery(self) -> None:
        """Single package: Agent start -> Warehouse -> Destination."""
        w1 = Warehouse("W1", Point(0.0, 0.0))
        agent = Agent.create("A1", Point(3.0, 4.0))  # dist to W1 = 5.0
        pkg = Package("P1", "W1", Point(6.0, 8.0))   # dist from W1 = 10.0

        simulated = simulate_deliveries([agent], {"A1": [pkg]}, [w1])
        a = simulated["A1"]

        self.assertEqual(a.packages_delivered, 1)
        self.assertAlmostEqual(a.total_distance, 5.0 + 10.0, places=9)
        self.assertEqual(a.current_location, Point(6.0, 8.0))

    def test_multiple_packages_same_warehouse(self) -> None:
        """Sequential route: Agent -> W1 -> Dest1 -> W1 -> Dest2."""
        w1 = Warehouse("W1", Point(0.0, 0.0))
        agent = Agent.create("A1", Point(0.0, 0.0))  # start at warehouse

        pkg1 = Package("P1", "W1", Point(3.0, 4.0))   # W1 -> (3,4) = 5.0
        pkg2 = Package("P2", "W1", Point(0.0, 10.0))  # (3,4) -> W1 = 5.0, W1 -> (0,10) = 10.0

        simulated = simulate_deliveries([agent], {"A1": [pkg1, pkg2]}, [w1])
        a = simulated["A1"]

        self.assertEqual(a.packages_delivered, 2)
        # 0.0 (start to W1) + 5.0 (W1 to Dest1) + 5.0 (Dest1 to W1) + 10.0 (W1 to Dest2) = 20.0
        self.assertAlmostEqual(a.total_distance, 20.0, places=9)
        self.assertEqual(a.current_location, Point(0.0, 10.0))

    def test_multiple_warehouses_single_agent(self) -> None:
        """Agent handles packages from multiple distinct warehouses."""
        w1 = Warehouse("W1", Point(0.0, 0.0))
        w2 = Warehouse("W2", Point(10.0, 0.0))

        agent = Agent.create("A1", Point(0.0, 0.0))

        # P1 at W1, dest at (0, 5)
        pkg1 = Package("P1", "W1", Point(0.0, 5.0))
        # P2 at W2, dest at (10, 5)
        pkg2 = Package("P2", "W2", Point(10.0, 5.0))

        simulated = simulate_deliveries([agent], {"A1": [pkg1, pkg2]}, [w1, w2])
        a = simulated["A1"]

        # Leg 1: (0,0) to W1(0,0) = 0.0
        # Leg 2: W1(0,0) to Dest1(0,5) = 5.0
        # Leg 3: Dest1(0,5) to W2(10,0) = sqrt(10^2 + (-5)^2) = sqrt(125) ≈ 11.180339887
        # Leg 4: W2(10,0) to Dest2(10,5) = 5.0
        expected = 0.0 + 5.0 + math.hypot(10.0 - 0.0, 0.0 - 5.0) + 5.0
        self.assertEqual(a.packages_delivered, 2)
        self.assertAlmostEqual(a.total_distance, expected, places=9)
        self.assertEqual(a.current_location, Point(10.0, 5.0))

    def test_zero_distance_legs(self) -> None:
        """Destination collocated with warehouse or agent starting point."""
        w1 = Warehouse("W1", Point(0.0, 0.0))
        agent = Agent.create("A1", Point(0.0, 0.0))
        pkg = Package("P1", "W1", Point(0.0, 0.0))

        simulated = simulate_deliveries([agent], {"A1": [pkg]}, [w1])
        a = simulated["A1"]

        self.assertEqual(a.packages_delivered, 1)
        self.assertEqual(a.total_distance, 0.0)

    def test_idle_agent_remains_at_start(self) -> None:
        """Agent with no packages has 0 distance and stays at initial position."""
        w1 = Warehouse("W1", Point(0.0, 0.0))
        agent = Agent.create("A_IDLE", Point(25.0, 30.0))

        simulated = simulate_deliveries([agent], {"A_IDLE": []}, [w1])
        a = simulated["A_IDLE"]

        self.assertEqual(a.packages_delivered, 0)
        self.assertEqual(a.total_distance, 0.0)
        self.assertEqual(a.current_location, Point(25.0, 30.0))


if __name__ == "__main__":
    unittest.main()
