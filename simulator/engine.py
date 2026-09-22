"""Sequential delivery simulation engine for FastBox couriers."""

from typing import Mapping, Sequence

from .distance import euclidean_distance
from .models import Agent, Package, Warehouse


def simulate_deliveries(
    agents: Sequence[Agent],
    assignments: Mapping[str, Sequence[Package]],
    warehouses: Sequence[Warehouse],
) -> dict[str, Agent]:
    """Execute sequential deliveries for each agent.

    For each agent:
    - Starts at initial_location with 0 distance and 0 delivered packages.
    - For each assigned package in queue:
        1. Moves from current_location to the package origin warehouse.
        2. Moves from origin warehouse to the package destination.
        3. Updates current_location to the package destination.
        4. Increments packages_delivered.
    - No round trip back to warehouse or starting base after the final delivery.
    - Calculations maintain full floating-point precision (no intermediate rounding).

    Returns:
        Mapping of agent_id -> simulated Agent.
    """
    warehouse_by_id = {w.id: w for w in warehouses}
    simulated_agents: dict[str, Agent] = {}

    for agent in agents:
        # Reset/initialize agent mutable state for simulation run
        agent.current_location = agent.initial_location
        agent.total_distance = 0.0
        agent.packages_delivered = 0

        pkg_queue = assignments.get(agent.id, [])
        for pkg in pkg_queue:
            wh = warehouse_by_id[pkg.warehouse_id]

            # Leg 1: Current location to Warehouse
            dist_to_wh = euclidean_distance(agent.current_location, wh.location)
            agent.total_distance += dist_to_wh
            agent.current_location = wh.location

            # Leg 2: Warehouse to Package Destination
            dist_to_dest = euclidean_distance(agent.current_location, pkg.destination)
            agent.total_distance += dist_to_dest
            agent.current_location = pkg.destination

            agent.packages_delivered += 1

        simulated_agents[agent.id] = agent

    return simulated_agents
