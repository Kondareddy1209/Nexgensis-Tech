"""Unit tests for parser module."""

import io
import json
import unittest

from simulator.models import Point
from simulator.parser import ValidationError, parse_delivery_data


class TestParser(unittest.TestCase):
    """Test JSON parsing, schema variant support, and input validation."""

    def test_schema_a_dict_format(self) -> None:
        """Parse Schema Variant A (warehouses and agents as dicts, packages have 'warehouse')."""
        payload = {
            "warehouses": {
                "W1": [0, 0],
                "W2": [50, 75],
            },
            "agents": {
                "A1": [5, 5],
                "A2": [60, 60],
            },
            "packages": [
                {"id": "P1", "warehouse": "W1", "destination": [30, 40]},
                {"id": "P2", "warehouse": "W2", "destination": [70, 90]},
            ],
        }
        stream = io.StringIO(json.dumps(payload))
        warehouses, agents, packages = parse_delivery_data(stream)

        self.assertEqual(len(warehouses), 2)
        self.assertEqual(len(agents), 2)
        self.assertEqual(len(packages), 2)

        self.assertEqual(warehouses[0].id, "W1")
        self.assertEqual(warehouses[0].location, Point(0.0, 0.0))
        self.assertEqual(packages[0].warehouse_id, "W1")
        self.assertEqual(packages[0].destination, Point(30.0, 40.0))

    def test_schema_b_list_format(self) -> None:
        """Parse Schema Variant B (warehouses and agents as lists, packages have 'warehouse_id')."""
        payload = {
            "warehouses": [
                {"id": "W1", "location": [0, 0]},
                {"id": "W2", "location": [50, 75]},
            ],
            "agents": [
                {"id": "A1", "location": [5, 5]},
                {"id": "A2", "location": [60, 60]},
            ],
            "packages": [
                {"id": "P1", "warehouse_id": "W1", "destination": [30, 40]},
                {"id": "P2", "warehouse_id": "W2", "destination": [70, 90]},
            ],
        }
        stream = io.StringIO(json.dumps(payload))
        warehouses, agents, packages = parse_delivery_data(stream)

        self.assertEqual(len(warehouses), 2)
        self.assertEqual(len(agents), 2)
        self.assertEqual(len(packages), 2)

        self.assertEqual(warehouses[1].id, "W2")
        self.assertEqual(warehouses[1].location, Point(50.0, 75.0))
        self.assertEqual(packages[1].warehouse_id, "W2")
        self.assertEqual(packages[1].destination, Point(70.0, 90.0))

    def test_missing_top_level_field(self) -> None:
        """Fails when top-level keys like 'agents' are missing."""
        payload = {
            "warehouses": {"W1": [0, 0]},
            "packages": [],
        }
        stream = io.StringIO(json.dumps(payload))
        with self.assertRaises(ValidationError) as ctx:
            parse_delivery_data(stream)
        self.assertIn("Missing required top-level field 'agents'", str(ctx.exception))

    def test_invalid_coordinates_length(self) -> None:
        """Fails when coordinate has fewer or more than 2 components."""
        payload = {
            "warehouses": {"W1": [0, 0, 0]},
            "agents": {"A1": [1, 1]},
            "packages": [],
        }
        stream = io.StringIO(json.dumps(payload))
        with self.assertRaises(ValidationError) as ctx:
            parse_delivery_data(stream)
        self.assertIn("Expected exactly 2 coordinates", str(ctx.exception))

    def test_invalid_coordinates_non_numeric(self) -> None:
        """Fails when coordinate component is not a number."""
        payload = {
            "warehouses": {"W1": [0, "invalid"]},
            "agents": {"A1": [1, 1]},
            "packages": [],
        }
        stream = io.StringIO(json.dumps(payload))
        with self.assertRaises(ValidationError) as ctx:
            parse_delivery_data(stream)
        self.assertIn("must be a number", str(ctx.exception))

    def test_missing_warehouse_reference(self) -> None:
        """Fails when a package references a warehouse that does not exist."""
        payload = {
            "warehouses": {"W1": [0, 0]},
            "agents": {"A1": [1, 1]},
            "packages": [
                {"id": "P1", "warehouse": "W_NONEXISTENT", "destination": [10, 10]}
            ],
        }
        stream = io.StringIO(json.dumps(payload))
        with self.assertRaises(ValidationError) as ctx:
            parse_delivery_data(stream)
        self.assertIn("references unknown warehouse", str(ctx.exception))

    def test_duplicate_package_id(self) -> None:
        """Fails when package IDs are duplicated."""
        payload = {
            "warehouses": {"W1": [0, 0]},
            "agents": {"A1": [1, 1]},
            "packages": [
                {"id": "P1", "warehouse": "W1", "destination": [10, 10]},
                {"id": "P1", "warehouse": "W1", "destination": [20, 20]},
            ],
        }
        stream = io.StringIO(json.dumps(payload))
        with self.assertRaises(ValidationError) as ctx:
            parse_delivery_data(stream)
        self.assertIn("Duplicate package ID", str(ctx.exception))

    def test_malformed_json_syntax(self) -> None:
        """Fails with ValidationError when JSON syntax is corrupted."""
        stream = io.StringIO("{ invalid json ...")
        with self.assertRaises(ValidationError) as ctx:
            parse_delivery_data(stream)
        self.assertIn("Malformed JSON syntax", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
