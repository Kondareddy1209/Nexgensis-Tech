"""Integration tests verifying end-to-end execution across all 11 test case datasets."""

import json
import tempfile
import unittest
from pathlib import Path

from main import run_simulation
from simulator.parser import parse_delivery_data


class TestIntegration(unittest.TestCase):
    """Run full simulation on base_case.json and all 10 test case files."""

    @classmethod
    def setUpClass(cls) -> None:
        """Locate all test case files."""
        # Candidates for root directory
        candidate_dirs = [
            Path(__file__).parent.parent / "data",
            Path(__file__).parent.parent.parent,
        ]

        cls.files_to_test: list[Path] = []

        for c_dir in candidate_dirs:
            base_case = c_dir / "base_case.json"
            if base_case.is_file() and base_case not in cls.files_to_test:
                cls.files_to_test.append(base_case)

            tc_dir = c_dir / "test_cases"
            if tc_dir.is_dir():
                for p in sorted(tc_dir.glob("*.json")):
                    if p not in cls.files_to_test:
                        cls.files_to_test.append(p)

            alt_tc_dir = c_dir / "Python Assignment(Delivery System Test Cases)"
            if alt_tc_dir.is_dir():
                for p in sorted(alt_tc_dir.glob("*.json")):
                    if p not in cls.files_to_test:
                        cls.files_to_test.append(p)

        if not cls.files_to_test:
            raise FileNotFoundError("Could not find base_case.json or test case files for integration testing.")

    def test_all_11_test_cases(self) -> None:
        """Ensure all 11 datasets run successfully and satisfy all business invariants."""
        # We expect at least base_case + 10 test cases = 11 datasets
        self.assertGreaterEqual(
            len(self.files_to_test),
            11,
            f"Expected at least 11 test case files, found {len(self.files_to_test)}.",
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            for filepath in self.files_to_test:
                with self.subTest(file=filepath.name):
                    # 1. Parse raw data to inspect input invariants
                    warehouses, agents, packages = parse_delivery_data(filepath)
                    input_agent_ids = {a.id for a in agents}
                    total_packages_input = len(packages)

                    # 2. Run end-to-end simulation
                    out_report_file = Path(tmpdir) / f"report_{filepath.stem}.json"
                    report = run_simulation(str(filepath), str(out_report_file))

                    # 3. Invariant: report.json must exist and be valid JSON
                    self.assertTrue(out_report_file.is_file())
                    with open(out_report_file, "r", encoding="utf-8") as f:
                        report_dict = json.load(f)

                    # 4. Invariant: every agent must appear in the report
                    for aid in input_agent_ids:
                        self.assertIn(aid, report_dict, f"Agent {aid} missing from report for {filepath.name}")
                        agent_entry = report_dict[aid]
                        self.assertIn("packages_delivered", agent_entry)
                        self.assertIn("total_distance", agent_entry)
                        self.assertIn("efficiency", agent_entry)

                        # Check non-negative
                        self.assertGreaterEqual(agent_entry["packages_delivered"], 0)
                        self.assertGreaterEqual(agent_entry["total_distance"], 0.0)
                        self.assertGreaterEqual(agent_entry["efficiency"], 0.0)

                        # Check precision: rounded to at most 2 decimal places
                        dist_str = str(agent_entry["total_distance"])
                        if "." in dist_str:
                            decimals = len(dist_str.split(".")[1])
                            self.assertLessEqual(decimals, 2)

                        eff_str = str(agent_entry["efficiency"])
                        if "." in eff_str:
                            decimals = len(eff_str.split(".")[1])
                            self.assertLessEqual(decimals, 2)

                    # 5. Invariant: total packages delivered matches input package count
                    total_delivered = sum(
                        report_dict[aid]["packages_delivered"] for aid in input_agent_ids
                    )
                    self.assertEqual(
                        total_delivered,
                        total_packages_input,
                        f"Package count mismatch in {filepath.name}: delivered {total_delivered} != input {total_packages_input}",
                    )

                    # 6. Invariant: best_agent must be present and non-idle
                    self.assertIn("best_agent", report_dict)
                    best_agent = report_dict["best_agent"]
                    self.assertIn(best_agent, input_agent_ids)
                    self.assertGreater(
                        report_dict[best_agent]["packages_delivered"],
                        0,
                        f"best_agent {best_agent} in {filepath.name} was idle with 0 deliveries!",
                    )

                    # 7. Invariant: best_agent has lowest efficiency among active agents
                    best_eff = report_dict[best_agent]["efficiency"]
                    for aid in input_agent_ids:
                        if report_dict[aid]["packages_delivered"] > 0:
                            self.assertLessEqual(
                                best_eff,
                                report_dict[aid]["efficiency"],
                                f"best_agent {best_agent} ({best_eff}) does not have lowest efficiency vs {aid} ({report_dict[aid]['efficiency']})",
                            )


if __name__ == "__main__":
    unittest.main()
