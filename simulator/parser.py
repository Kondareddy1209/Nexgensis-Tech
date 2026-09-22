"""Parser and validator supporting both input JSON schema variants."""

import json
from pathlib import Path
from typing import Any, TextIO, Union

from .models import Agent, Package, Point, Warehouse


class ValidationError(ValueError):
    """Raised when the input JSON data violates schema or integrity rules."""
    pass


def _parse_coordinate(raw: Any, context: str) -> Point:
    """Validate and parse a coordinate pair into a Point."""
    if not isinstance(raw, (list, tuple)):
        raise ValidationError(f"{context}: Expected coordinate list/tuple [x, y], got {type(raw).__name__}.")
    if len(raw) != 2:
        raise ValidationError(f"{context}: Expected exactly 2 coordinates [x, y], got {len(raw)} items: {raw}.")
    x, y = raw
    if not isinstance(x, (int, float)) or isinstance(x, bool):
        raise ValidationError(f"{context}: Coordinate x must be a number, got {x!r}.")
    if not isinstance(y, (int, float)) or isinstance(y, bool):
        raise ValidationError(f"{context}: Coordinate y must be a number, got {y!r}.")
    return Point(float(x), float(y))


def _parse_warehouses(raw_warehouses: Any) -> list[Warehouse]:
    """Parse warehouses from either dictionary mapping or list of objects."""
    warehouses: list[Warehouse] = []
    seen_ids: set[str] = set()

    if isinstance(raw_warehouses, dict):
        # Schema Variant A: {"W1": [x, y], "W2": [x, y]}
        for wid, loc in raw_warehouses.items():
            if not isinstance(wid, str) or not wid.strip():
                raise ValidationError(f"Warehouse ID must be a non-empty string, got {wid!r}.")
            if wid in seen_ids:
                raise ValidationError(f"Duplicate warehouse ID encountered: {wid}.")
            seen_ids.add(wid)
            point = _parse_coordinate(loc, f"Warehouse '{wid}' location")
            warehouses.append(Warehouse(id=wid, location=point))

    elif isinstance(raw_warehouses, list):
        # Schema Variant B: [{"id": "W1", "location": [x, y]}]
        for idx, item in enumerate(raw_warehouses):
            if not isinstance(item, dict):
                raise ValidationError(f"Warehouse item at index {idx} must be a dictionary, got {type(item).__name__}.")
            if "id" not in item:
                raise ValidationError(f"Warehouse item at index {idx} is missing required 'id' field.")
            if "location" not in item:
                raise ValidationError(f"Warehouse '{item.get('id', idx)}' is missing required 'location' field.")

            wid = item["id"]
            if not isinstance(wid, str) or not wid.strip():
                raise ValidationError(f"Warehouse ID at index {idx} must be a non-empty string, got {wid!r}.")
            if wid in seen_ids:
                raise ValidationError(f"Duplicate warehouse ID encountered: {wid}.")
            seen_ids.add(wid)
            point = _parse_coordinate(item["location"], f"Warehouse '{wid}' location")
            warehouses.append(Warehouse(id=wid, location=point))
    else:
        raise ValidationError(
            f"'warehouses' must be a dictionary or list, got {type(raw_warehouses).__name__}."
        )

    if not warehouses:
        raise ValidationError("'warehouses' collection cannot be empty.")
    return warehouses


def _parse_agents(raw_agents: Any) -> list[Agent]:
    """Parse agents from either dictionary mapping or list of objects."""
    agents: list[Agent] = []
    seen_ids: set[str] = set()

    if isinstance(raw_agents, dict):
        # Schema Variant A: {"A1": [x, y], "A2": [x, y]}
        for aid, loc in raw_agents.items():
            if not isinstance(aid, str) or not aid.strip():
                raise ValidationError(f"Agent ID must be a non-empty string, got {aid!r}.")
            if aid in seen_ids:
                raise ValidationError(f"Duplicate agent ID encountered: {aid}.")
            seen_ids.add(aid)
            point = _parse_coordinate(loc, f"Agent '{aid}' location")
            agents.append(Agent.create(agent_id=aid, initial_location=point))

    elif isinstance(raw_agents, list):
        # Schema Variant B: [{"id": "A1", "location": [x, y]}]
        for idx, item in enumerate(raw_agents):
            if not isinstance(item, dict):
                raise ValidationError(f"Agent item at index {idx} must be a dictionary, got {type(item).__name__}.")
            if "id" not in item:
                raise ValidationError(f"Agent item at index {idx} is missing required 'id' field.")
            if "location" not in item:
                raise ValidationError(f"Agent '{item.get('id', idx)}' is missing required 'location' field.")

            aid = item["id"]
            if not isinstance(aid, str) or not aid.strip():
                raise ValidationError(f"Agent ID at index {idx} must be a non-empty string, got {aid!r}.")
            if aid in seen_ids:
                raise ValidationError(f"Duplicate agent ID encountered: {aid}.")
            seen_ids.add(aid)
            point = _parse_coordinate(item["location"], f"Agent '{aid}' location")
            agents.append(Agent.create(agent_id=aid, initial_location=point))
    else:
        raise ValidationError(
            f"'agents' must be a dictionary or list, got {type(raw_agents).__name__}."
        )

    if not agents:
        raise ValidationError("'agents' collection cannot be empty.")
    return agents


def _parse_packages(raw_packages: Any, valid_warehouse_ids: set[str]) -> list[Package]:
    """Parse packages and validate warehouse references."""
    if not isinstance(raw_packages, list):
        raise ValidationError(f"'packages' must be a list, got {type(raw_packages).__name__}.")

    packages: list[Package] = []
    seen_ids: set[str] = set()

    for idx, item in enumerate(raw_packages):
        if not isinstance(item, dict):
            raise ValidationError(f"Package at index {idx} must be a dictionary, got {type(item).__name__}.")
        if "id" not in item:
            raise ValidationError(f"Package at index {idx} is missing required 'id' field.")

        pid = item["id"]
        if not isinstance(pid, str) or not pid.strip():
            raise ValidationError(f"Package ID at index {idx} must be a non-empty string, got {pid!r}.")
        if pid in seen_ids:
            raise ValidationError(f"Duplicate package ID encountered: {pid}.")
        seen_ids.add(pid)

        # Support both 'warehouse' (Schema A) and 'warehouse_id' (Schema B)
        wid = item.get("warehouse") or item.get("warehouse_id")
        if not wid:
            raise ValidationError(f"Package '{pid}' missing 'warehouse' or 'warehouse_id' reference.")
        if not isinstance(wid, str) or not wid.strip():
            raise ValidationError(f"Package '{pid}' warehouse reference must be a string, got {wid!r}.")
        if wid not in valid_warehouse_ids:
            raise ValidationError(
                f"Package '{pid}' references unknown warehouse '{wid}'. Known warehouses: {sorted(valid_warehouse_ids)}."
            )

        if "destination" not in item:
            raise ValidationError(f"Package '{pid}' missing required 'destination' field.")
        dest_point = _parse_coordinate(item["destination"], f"Package '{pid}' destination")

        packages.append(Package(id=pid, warehouse_id=wid, destination=dest_point))

    return packages


def parse_delivery_data(
    source: Union[str, Path, TextIO]
) -> tuple[list[Warehouse], list[Agent], list[Package]]:
    """Parse and validate delivery configuration from a file path or readable stream.

    Supports both Schema A (dict-mapped) and Schema B (list-based) formats.
    """
    if isinstance(source, (str, Path)):
        path = Path(source)
        if not path.exists():
            raise FileNotFoundError(f"Input file not found at: {path}")
        with open(path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError as err:
                raise ValidationError(f"Malformed JSON syntax in '{path}': {err}") from err
    else:
        try:
            data = json.load(source)
        except json.JSONDecodeError as err:
            raise ValidationError(f"Malformed JSON syntax in stream: {err}") from err

    if not isinstance(data, dict):
        raise ValidationError(f"Root JSON element must be an object/dict, got {type(data).__name__}.")

    for field in ("warehouses", "agents", "packages"):
        if field not in data:
            raise ValidationError(f"Missing required top-level field '{field}'.")

    warehouses = _parse_warehouses(data["warehouses"])
    agents = _parse_agents(data["agents"])
    valid_wh_ids = {w.id for w in warehouses}
    packages = _parse_packages(data["packages"], valid_wh_ids)

    return warehouses, agents, packages
