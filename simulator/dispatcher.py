"""Package assignment engine mapping packages to the nearest agent."""

from typing import Sequence

from .distance import find_nearest_agent
from .models import Agent, Package, Warehouse


def assign_packages(
    warehouses: Sequence[Warehouse],
    agents: Sequence[Agent],
    packages: Sequence[Package],
) -> dict[str, list[Package]]:
    """Assign packages to agents based on Euclidean distance from agent starting position to warehouse.

    Key guarantees:
    - Assignments strictly use agent INITIAL location (not mutable current location).
    - Preserves package input order.
    - Deterministic tie-breaking using lexicographical agent ID.
    - Caches warehouse-to-agent mappings for efficiency.
    - All agents in the agents sequence appear in the returned dictionary, even if idle.

    Returns:
        Mapping of agent_id -> list of assigned Packages.
    """
    if not agents:
        raise ValueError("Cannot assign packages with zero agents.")

    warehouse_by_id = {w.id: w for w in warehouses}

    # Precompute / cache nearest agent for each warehouse based on initial agent locations
    wh_to_agent: dict[str, Agent] = {}
    for wid, wh in warehouse_by_id.items():
        wh_to_agent[wid] = find_nearest_agent(wh, agents)

    # Initialize assignment buckets for all agents to guarantee presence of idle agents
    assignments: dict[str, list[Package]] = {agent.id: [] for agent in agents}

    # Assign packages in original input order
    for pkg in packages:
        nearest_agent = wh_to_agent[pkg.warehouse_id]
        assignments[nearest_agent.id].append(pkg)

    return assignments
