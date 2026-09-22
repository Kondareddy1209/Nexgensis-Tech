"""Unit tests for reporter module."""

import json
import tempfile
import unittest
from pathlib import Path

from simulator.models import Agent, Point
from simulator.reporter import export_report, generate_report


class TestReporter(unittest.TestCase):
    """Test metric computations, top performer ranking, and report serialization."""

    def test_basic_metrics_calculation(self) -> None:
        """Correct rounding and efficiency calculation."""
        a1 = Agent.create("A1", Point(0, 0))
        a1.packages_delivered = 2
        a1.total_distance = 85.324  # should round to 85.32
        # efficiency: 85.324 / 2 = 42.662 -> 42.66

        report = generate_report([a1])
        stats = report.agents["A1"]

        self.assertEqual(stats.packages_delivered, 2)
        self.assertEqual(stats.total_distance, 85.32)
        self.assertEqual(stats.efficiency, 42.66)
        self.assertEqual(report.best_agent, "A1")

    def test_idle_agent_metrics_and_exclusion(self) -> None:
        """Idle agents have 0.0 efficiency and are excluded from best_agent candidacy."""
        idle_agent = Agent.create("A_IDLE", Point(0, 0))
        idle_agent.packages_delivered = 0
        idle_agent.total_distance = 0.0

        active_agent = Agent.create("A_ACTIVE", Point(0, 0))
        active_agent.packages_delivered = 1
        active_agent.total_distance = 50.0

        report = generate_report([idle_agent, active_agent])

        self.assertEqual(report.agents["A_IDLE"].packages_delivered, 0)
        self.assertEqual(report.agents["A_IDLE"].total_distance, 0.0)
        self.assertEqual(report.agents["A_IDLE"].efficiency, 0.0)

        # A_IDLE must NOT be chosen even though its efficiency is 0.0
        self.assertEqual(report.best_agent, "A_ACTIVE")

    def test_best_agent_selection_lowest_efficiency(self) -> None:
        """The agent with lowest efficiency is selected as best_agent."""
        a1 = Agent.create("A1", Point(0, 0))
        a1.packages_delivered = 2
        a1.total_distance = 85.32  # efficiency = 42.66

        a2 = Agent.create("A2", Point(0, 0))
        a2.packages_delivered = 2
        a2.total_distance = 120.12  # efficiency = 60.06

        a3 = Agent.create("A3", Point(0, 0))
        a3.packages_delivered = 1
        a3.total_distance = 50.00  # efficiency = 50.00

        report = generate_report([a1, a2, a3])
        self.assertEqual(report.best_agent, "A1")

    def test_efficiency_tie_breaking(self) -> None:
        """Tie-breaking prefers higher package volume, then lexicographical ID."""
        # Case 1: Same efficiency, different volume
        a1 = Agent.create("A1", Point(0, 0))
        a1.packages_delivered = 1
        a1.total_distance = 10.0  # efficiency = 10.0

        a2 = Agent.create("A2", Point(0, 0))
        a2.packages_delivered = 2
        a2.total_distance = 20.0  # efficiency = 10.0

        report = generate_report([a1, a2])
        # A2 delivered more packages, so A2 wins
        self.assertEqual(report.best_agent, "A2")

        # Case 2: Same efficiency, same volume -> lexicographical ID
        a_first = Agent.create("AGENT_A", Point(0, 0))
        a_first.packages_delivered = 1
        a_first.total_distance = 10.0

        a_second = Agent.create("AGENT_B", Point(0, 0))
        a_second.packages_delivered = 1
        a_second.total_distance = 10.0

        report2 = generate_report([a_second, a_first])
        self.assertEqual(report2.best_agent, "AGENT_A")

    def test_all_idle_agents(self) -> None:
        """When no packages were delivered by any agent, best_agent is None."""
        a1 = Agent.create("A1", Point(0, 0))
        report = generate_report([a1])
        self.assertIsNone(report.best_agent)

    def test_json_export_structure(self) -> None:
        """Export conforms to exact expected flat JSON schema."""
        a1 = Agent.create("A1", Point(0, 0))
        a1.packages_delivered = 2
        a1.total_distance = 85.32
        report = generate_report([a1])

        with tempfile.TemporaryDirectory() as tmpdir:
            out_file = Path(tmpdir) / "report.json"
            export_report(report, out_file)

            with open(out_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.assertIn("A1", data)
            self.assertIn("best_agent", data)
            self.assertEqual(data["best_agent"], "A1")
            self.assertEqual(data["A1"]["packages_delivered"], 2)
            self.assertEqual(data["A1"]["total_distance"], 85.32)
            self.assertEqual(data["A1"]["efficiency"], 42.66)


if __name__ == "__main__":
    unittest.main()
