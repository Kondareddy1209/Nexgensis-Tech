"""Tests for all four bonus features.

These tests complement the existing 30 tests without modifying them.

Bonus 1 — Random delivery delays  (test_delay_*)
Bonus 2 — ASCII route visualization (test_visualizer_*)
Bonus 3 — Mid-day agent joining    (test_midday_*)
Bonus 4 — CSV top-performer export  (test_csv_*)

Regression — Default mode unchanged (test_regression_*)
"""

import csv
import os
import tempfile
import unittest
from pathlib import Path

from simulator.delay import format_delay_report, generate_delays
from simulator.models import Agent, Package, Point, Warehouse, AgentReport, DeliveryReport
from simulator.visualizer import format_route, print_visualization
from simulator.midday import (
    assign_with_midday_agent,
    build_midday_agent,
    format_midday_summary,
)
from simulator.csv_exporter import export_top_performer_csv
from simulator.dispatcher import assign_packages
from simulator.engine import simulate_deliveries
from simulator.reporter import generate_report


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _wh(wid: str, x: float, y: float) -> Warehouse:
    return Warehouse(id=wid, location=Point(x, y))


def _agent(aid: str, x: float, y: float) -> Agent:
    return Agent.create(aid, Point(x, y))


def _pkg(pid: str, wid: str, dx: float, dy: float) -> Package:
    return Package(id=pid, warehouse_id=wid, destination=Point(dx, dy))


# ─────────────────────────────────────────────────────────────────────────────
# Bonus 1 — Random Delivery Delays
# ─────────────────────────────────────────────────────────────────────────────

class TestDelay(unittest.TestCase):
    """Tests for simulator/delay.py."""

    def setUp(self):
        self.packages = [
            _pkg("P1", "W1", 10, 10),
            _pkg("P2", "W1", 20, 20),
            _pkg("P3", "W2", 30, 30),
        ]

    def test_delay_keys_match_package_ids(self):
        """Each package gets exactly one delay entry."""
        delays = generate_delays(self.packages)
        self.assertEqual(set(delays.keys()), {"P1", "P2", "P3"})

    def test_delay_values_in_valid_range(self):
        """All generated delays are between 1 and 30 minutes inclusive."""
        delays = generate_delays(self.packages, seed=0)
        for pid, mins in delays.items():
            self.assertGreaterEqual(mins, 1, msg=f"{pid} delay < 1")
            self.assertLessEqual(mins, 30, msg=f"{pid} delay > 30")

    def test_seeded_delay_is_deterministic(self):
        """Same seed must produce identical delays on repeated calls."""
        d1 = generate_delays(self.packages, seed=42)
        d2 = generate_delays(self.packages, seed=42)
        self.assertEqual(d1, d2)

    def test_different_seeds_produce_different_results(self):
        """Different seeds should (with overwhelming probability) differ."""
        d1 = generate_delays(self.packages, seed=1)
        d2 = generate_delays(self.packages, seed=9999)
        # Not guaranteed, but statistically certain with 3 packages
        self.assertNotEqual(d1, d2)

    def test_unseeded_is_random(self):
        """Two unseeded calls very likely differ (non-deterministic)."""
        # We simply verify the function runs and produces a dict — we cannot
        # assert randomness deterministically, but we can assert shape.
        delays = generate_delays(self.packages)
        self.assertIsInstance(delays, dict)
        self.assertEqual(len(delays), len(self.packages))

    def test_empty_package_list_returns_empty_dict(self):
        """No packages → empty delay map."""
        self.assertEqual(generate_delays([]), {})

    def test_format_delay_report_contains_agent_and_package(self):
        """Formatted report includes agent IDs and package IDs."""
        assignments = {"A1": [self.packages[0], self.packages[1]], "A2": [self.packages[2]]}
        delays = generate_delays(self.packages, seed=7)
        report = format_delay_report(assignments, delays)
        self.assertIn("A1", report)
        self.assertIn("A2", report)
        self.assertIn("P1", report)
        self.assertIn("P3", report)

    def test_format_delay_report_idle_agent(self):
        """Idle agent appears with '[idle]' and 'N/A' marker in formatted report."""
        assignments = {"A1": [], "A2": [self.packages[0]]}
        delays = generate_delays(self.packages, seed=3)
        report = format_delay_report(assignments, delays)
        self.assertIn("[idle]", report)
        self.assertIn("N/A", report)


# ─────────────────────────────────────────────────────────────────────────────
# Bonus 2 — ASCII Route Visualization
# ─────────────────────────────────────────────────────────────────────────────

class TestVisualizer(unittest.TestCase):
    """Tests for simulator/visualizer.py."""

    def setUp(self):
        self.wh1 = _wh("W1", 0, 0)
        self.wh2 = _wh("W2", 50, 50)
        self.a1 = _agent("A1", 5, 5)
        self.p1 = _pkg("P1", "W1", 30, 40)
        self.p2 = _pkg("P2", "W2", 70, 80)
        self.wh_map = {"W1": self.wh1, "W2": self.wh2}

    def test_idle_agent_shows_idle_marker(self):
        """Agents with no packages display an idle message."""
        line = format_route(self.a1, [], self.wh_map)
        self.assertIn("idle", line.lower())
        self.assertIn("A1", line)

    def test_route_contains_agent_warehouse_package(self):
        """Non-idle route includes agent ID, warehouse ID, and package ID."""
        line = format_route(self.a1, [self.p1], self.wh_map)
        self.assertIn("A1", line)
        self.assertIn("W1", line)
        self.assertIn("P1", line)

    def test_route_order_is_correct(self):
        """Steps appear in the order: agent → warehouse → package."""
        line = format_route(self.a1, [self.p1], self.wh_map)
        a1_pos = line.index("A1")
        w1_pos = line.index("W1")
        p1_pos = line.index("P1")
        self.assertLess(a1_pos, w1_pos)
        self.assertLess(w1_pos, p1_pos)

    def test_multi_package_route_order(self):
        """Multiple packages appear in assignment order."""
        a2 = _agent("A2", 55, 55)
        line = format_route(a2, [self.p2, self.p1], {"W1": self.wh1, "W2": self.wh2})
        # p2 (W2 first) must appear before p1 (W1 second)
        self.assertLess(line.index("W2"), line.index("W1"))
        self.assertLess(line.index("P2"), line.index("P1"))

    def test_visualization_uses_actual_simulation_data(self):
        """print_visualization output reflects actual warehouse/package IDs."""
        import io
        from contextlib import redirect_stdout

        agents = [self.a1]
        warehouses = [self.wh1]
        packages = [self.p1]
        assignments = {"A1": [self.p1]}

        buf = io.StringIO()
        with redirect_stdout(buf):
            print_visualization(
                agents, assignments, warehouses, packages, show_grid=False
            )
        output = buf.getvalue()
        self.assertIn("A1", output)
        self.assertIn("W1", output)
        self.assertIn("P1", output)

    def test_visualization_coordinates_present(self):
        """Route lines include coordinate annotations."""
        line = format_route(self.a1, [self.p1], self.wh_map)
        # Agent start coords
        self.assertIn("5", line)
        # Warehouse coords
        self.assertIn("0", line)


# ─────────────────────────────────────────────────────────────────────────────
# Bonus 3 — Mid-Day Agent Joining
# ─────────────────────────────────────────────────────────────────────────────

class TestMiddayAgent(unittest.TestCase):
    """Tests for simulator/midday.py."""

    def setUp(self):
        self.wh1 = _wh("W1", 0, 0)
        self.wh2 = _wh("W2", 100, 100)
        self.warehouses = [self.wh1, self.wh2]

        # A1 is close to W1; A2 is close to W2
        self.a1 = _agent("A1", 5, 5)
        self.a2 = _agent("A2", 95, 95)
        self.agents = [self.a1, self.a2]

        # 6 packages — 3 from W1, 3 from W2
        self.packages = [
            _pkg("P1", "W1", 10, 10),
            _pkg("P2", "W2", 90, 90),
            _pkg("P3", "W1", 20, 20),
            _pkg("P4", "W2", 80, 80),
            _pkg("P5", "W1", 15, 15),
            _pkg("P6", "W2", 85, 85),
        ]

        # New agent placed very close to W1 — joins after 3 packages
        self.midday = build_midday_agent("M1", 1, 1)
        self.join_after = 3

    def test_build_midday_agent_correct_id_and_position(self):
        """build_midday_agent creates agent with correct ID and coordinates."""
        agent = build_midday_agent("NEWCOMER", 12.5, 34.0)
        self.assertEqual(agent.id, "NEWCOMER")
        self.assertAlmostEqual(agent.initial_location.x, 12.5)
        self.assertAlmostEqual(agent.initial_location.y, 34.0)

    def test_midday_agent_not_in_all_agents_before_call(self):
        """Original agents list does not include mid-day agent before joining."""
        self.assertNotIn(self.midday.id, [a.id for a in self.agents])

    def test_midday_agent_appears_in_all_agents_after_call(self):
        """After assign_with_midday_agent, all_agents includes the joiner."""
        _, all_agents = assign_with_midday_agent(
            self.warehouses, self.agents, self.packages, self.midday, self.join_after
        )
        ids = [a.id for a in all_agents]
        self.assertIn("M1", ids)

    def test_midday_agent_receives_no_pre_join_packages(self):
        """The mid-day agent must not receive any of the first join_after packages."""
        assignments, _ = assign_with_midday_agent(
            self.warehouses, self.agents, self.packages, self.midday, self.join_after
        )
        pre_pkg_ids = {p.id for p in self.packages[: self.join_after]}
        midday_pkg_ids = {p.id for p in assignments.get("M1", [])}
        overlap = pre_pkg_ids & midday_pkg_ids
        self.assertEqual(
            overlap,
            set(),
            msg=f"Mid-day agent received pre-join packages: {overlap}",
        )

    def test_midday_agent_can_receive_post_join_packages(self):
        """The mid-day agent is eligible for packages after the join point."""
        # M1 at (1,1) is closer to W1 than A1 at (5,5)? No — A1(5,5) is closer
        # than M1(1,1) to W1(0,0): d(A1,W1)=7.07, d(M1,W1)=1.41 → M1 is closest.
        # So M1 should grab at least some post-join W1 packages.
        assignments, _ = assign_with_midday_agent(
            self.warehouses, self.agents, self.packages, self.midday, self.join_after
        )
        midday_pkgs = assignments.get("M1", [])
        # M1 is closer to W1 than A1, so it should win post-join W1 packages
        self.assertGreater(
            len(midday_pkgs),
            0,
            msg="Mid-day agent received 0 post-join packages despite being nearest",
        )

    def test_package_conservation_with_midday_agent(self):
        """Total packages across all agents equals total input packages."""
        assignments, all_agents = assign_with_midday_agent(
            self.warehouses, self.agents, self.packages, self.midday, self.join_after
        )
        total_assigned = sum(len(v) for v in assignments.values())
        self.assertEqual(total_assigned, len(self.packages))

    def test_join_after_zero_means_fully_eligible(self):
        """join_after=0 means mid-day agent is eligible from the first package."""
        assignments, _ = assign_with_midday_agent(
            self.warehouses, self.agents, self.packages, self.midday, join_after=0
        )
        # No restriction — M1 is nearest to W1, so it should get all W1 packages
        midday_pkgs = assignments.get("M1", [])
        self.assertGreater(len(midday_pkgs), 0)

    def test_join_after_exceeds_total_gives_no_packages_to_midday(self):
        """join_after >= len(packages) means mid-day agent gets nothing."""
        assignments, _ = assign_with_midday_agent(
            self.warehouses,
            self.agents,
            self.packages,
            self.midday,
            join_after=len(self.packages) + 10,  # beyond all packages
        )
        self.assertEqual(assignments.get("M1", []), [])

    def test_original_agents_not_affected_in_pre_join_phase(self):
        """Pre-join packages are assigned to original agents only, same as normal."""
        pre_pkgs = self.packages[: self.join_after]
        normal_assignments = assign_packages(self.warehouses, self.agents, pre_pkgs)

        midday_assignments, _ = assign_with_midday_agent(
            self.warehouses, self.agents, self.packages, self.midday, self.join_after
        )
        # Pre-join packages must match normal assignment
        for aid in [self.a1.id, self.a2.id]:
            normal_pre_ids = {p.id for p in normal_assignments[aid]}
            midday_pkgs = midday_assignments.get(aid, [])
            # Filter midday assignments to pre-join package IDs
            pre_pkg_ids = {p.id for p in pre_pkgs}
            midday_pre_ids = {p.id for p in midday_pkgs if p.id in pre_pkg_ids}
            self.assertEqual(
                normal_pre_ids,
                midday_pre_ids,
                msg=f"Pre-join packages for {aid} differ from normal assignment",
            )

    def test_format_midday_summary_contains_key_info(self):
        """Summary string includes agent ID, join point, and package counts."""
        assignments, _ = assign_with_midday_agent(
            self.warehouses, self.agents, self.packages, self.midday, self.join_after
        )
        summary = format_midday_summary(self.midday, self.join_after, len(self.packages), assignments)
        self.assertIn("M1", summary)
        self.assertIn(str(self.join_after), summary)
        self.assertIn(str(len(self.packages)), summary)


# ─────────────────────────────────────────────────────────────────────────────
# Bonus 4 — CSV Export of Top Performer
# ─────────────────────────────────────────────────────────────────────────────

class TestCsvExporter(unittest.TestCase):
    """Tests for simulator/csv_exporter.py."""

    def _make_report(self, best: str) -> DeliveryReport:
        agents = {
            "A1": AgentReport(packages_delivered=2, total_distance=100.0, efficiency=50.0),
            "A2": AgentReport(packages_delivered=3, total_distance=60.0, efficiency=20.0),
            "A3": AgentReport(packages_delivered=0, total_distance=0.0, efficiency=0.0),
        }
        return DeliveryReport(agents=agents, best_agent=best)

    def test_csv_file_is_created(self):
        """export_top_performer_csv creates the file on disk."""
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "out.csv"
            export_top_performer_csv(self._make_report("A2"), out)
            self.assertTrue(out.exists(), "CSV file not created")

    def test_csv_contains_correct_agent(self):
        """Exported row reflects the best_agent from the report."""
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "top.csv"
            export_top_performer_csv(self._make_report("A2"), out)
            with open(out, newline="", encoding="utf-8") as f:
                rows = list(csv.DictReader(f))
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["agent_id"], "A2")

    def test_csv_numeric_fields_are_correct(self):
        """packages_delivered, total_distance, efficiency are accurate."""
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "top.csv"
            export_top_performer_csv(self._make_report("A2"), out)
            with open(out, newline="", encoding="utf-8") as f:
                rows = list(csv.DictReader(f))
            row = rows[0]
            self.assertEqual(int(row["packages_delivered"]), 3)
            self.assertAlmostEqual(float(row["total_distance"]), 60.0)
            self.assertAlmostEqual(float(row["efficiency"]), 20.0)

    def test_csv_has_correct_header(self):
        """CSV headers match the required schema."""
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "top.csv"
            export_top_performer_csv(self._make_report("A1"), out)
            with open(out, newline="", encoding="utf-8") as f:
                reader = csv.reader(f)
                headers = next(reader)
            self.assertEqual(
                headers,
                ["agent_id", "packages_delivered", "total_distance", "efficiency"],
            )

    def test_csv_no_best_agent_writes_header_only(self):
        """When best_agent is None, file has header row but no data rows."""
        report = DeliveryReport(agents={}, best_agent=None)
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "empty.csv"
            export_top_performer_csv(report, out)
            with open(out, newline="", encoding="utf-8") as f:
                rows = list(csv.DictReader(f))
            self.assertEqual(rows, [])

    def test_csv_uses_existing_best_agent_selection(self):
        """best_agent in CSV matches the existing generate_report() selection."""
        warehouses = [_wh("W1", 0, 0)]
        agents = [_agent("A1", 5, 5), _agent("A2", 50, 50)]
        packages = [_pkg("P1", "W1", 10, 10)]

        assignments = assign_packages(warehouses, agents, packages)
        simulated = simulate_deliveries(agents, assignments, warehouses)
        report = generate_report(list(simulated.values()))

        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "top.csv"
            export_top_performer_csv(report, out)
            with open(out, newline="", encoding="utf-8") as f:
                rows = list(csv.DictReader(f))

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["agent_id"], report.best_agent)

    def test_csv_parent_directory_created_automatically(self):
        """Export creates missing parent directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "nested" / "subdir" / "top.csv"
            export_top_performer_csv(self._make_report("A1"), out)
            self.assertTrue(out.exists())


# ─────────────────────────────────────────────────────────────────────────────
# Regression — Default mode must remain unchanged
# ─────────────────────────────────────────────────────────────────────────────

class TestRegressionDefaultMode(unittest.TestCase):
    """Verify that bonus flags do not alter default simulation results."""

    def test_base_case_results_unchanged(self):
        """Base case results match verified baseline when no bonus flags used."""
        from main import run_simulation
        import tempfile, os

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tf:
            out = tf.name
        try:
            report = run_simulation(
                "data/base_case.json",
                out,
                # All bonus flags at their defaults (disabled)
                enable_delays=False,
                visualize=False,
                export_csv=False,
            )
        finally:
            os.unlink(out)

        self.assertEqual(report.best_agent, "A3")
        self.assertEqual(report.agents["A1"].packages_delivered, 2)
        self.assertAlmostEqual(report.agents["A1"].total_distance, 121.21, places=1)
        self.assertAlmostEqual(report.agents["A1"].efficiency, 60.61, places=1)
        self.assertEqual(report.agents["A2"].packages_delivered, 2)
        self.assertAlmostEqual(report.agents["A2"].total_distance, 79.21, places=1)
        self.assertEqual(report.agents["A3"].packages_delivered, 1)
        self.assertAlmostEqual(report.agents["A3"].total_distance, 14.14, places=1)

    def test_delays_do_not_change_distance_or_efficiency(self):
        """Enabling delays must not alter distance or efficiency values."""
        from main import run_simulation
        import tempfile, os

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tf:
            out = tf.name
        try:
            report = run_simulation(
                "data/base_case.json",
                out,
                enable_delays=True,
                delay_seed=123,
            )
        finally:
            os.unlink(out)

        # Core metrics must be unchanged
        self.assertEqual(report.best_agent, "A3")
        self.assertAlmostEqual(report.agents["A1"].total_distance, 121.21, places=1)
        self.assertAlmostEqual(report.agents["A3"].efficiency, 14.14, places=1)


if __name__ == "__main__":
    unittest.main()
