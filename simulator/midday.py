"""Bonus feature: mid-day agent joining simulation.

An agent that "joins" partway through the workday becomes available
only for packages processed after its configured join point.

Since the supplied JSON has no time dimension, we define simulation-time
as the package processing order.  A "join_after" value of N means the
new agent is eligible starting from the (N+1)-th package onward.

This feature is STRICTLY ADDITIVE and does NOT affect the default
single-mode assignment path.
"""

from typing import Sequence

from .dispatcher import assign_packages
from .models import Agent, Package, Point, Warehouse


def build_midday_agent(agent_id: str, x: float, y: float) -> Agent:
    """Create an Agent instance for a mid-day joiner.

    Args:
        agent_id: Unique identifier for the new agent.
        x: Starting X coordinate.
        y: Starting Y coordinate.

    Returns:
        Freshly initialised Agent at the given position.
    """
    loc = Point(x, y)
    return Agent.create(agent_id, loc)


def assign_with_midday_agent(
    warehouses: Sequence[Warehouse],
    original_agents: Sequence[Agent],
    packages: Sequence[Package],
    midday_agent: Agent,
    join_after: int,
) -> tuple[dict[str, list[Package]], list[Agent]]:
    """Perform a two-phase package assignment incorporating a mid-day joiner.

    Phase 1 — Pre-join (packages[0 : join_after]):
        Assigned using *original_agents* only.

    Phase 2 — Post-join (packages[join_after : ]):
        Assigned using *original_agents* + *midday_agent* (all agents).

    The mid-day agent does NOT receive any package from Phase 1.
    Already-assigned packages are never retroactively moved.

    Args:
        warehouses: All warehouses.
        original_agents: Agents present at simulation start.
        packages: Full ordered package list.
        midday_agent: The agent joining partway through.
        join_after: Number of packages dispatched before the new agent
                    becomes eligible (0 = available from the very start).

    Returns:
        Tuple of (merged_assignments, all_agents) where:
          - merged_assignments maps agent_id -> list[Package]
          - all_agents includes original_agents + midday_agent
    """
    join_after = max(0, min(join_after, len(packages)))

    pre_packages: Sequence[Package] = packages[:join_after]
    post_packages: Sequence[Package] = packages[join_after:]

    all_agents: list[Agent] = list(original_agents) + [midday_agent]

    # Phase 1 — original agents only
    pre_assignments: dict[str, list[Package]] = {}
    if pre_packages:
        pre_assignments = assign_packages(warehouses, original_agents, pre_packages)
    else:
        pre_assignments = {a.id: [] for a in original_agents}

    # Phase 2 — all agents eligible
    post_assignments: dict[str, list[Package]] = {}
    if post_packages:
        post_assignments = assign_packages(warehouses, all_agents, post_packages)
    else:
        post_assignments = {a.id: [] for a in all_agents}

    # Merge: start with all agents (including midday) having empty buckets,
    # then add pre-phase results, then add post-phase results.
    merged: dict[str, list[Package]] = {a.id: [] for a in all_agents}
    for aid, pkgs in pre_assignments.items():
        merged[aid] = list(pkgs)
    for aid, pkgs in post_assignments.items():
        merged[aid] = merged.get(aid, []) + list(pkgs)

    return merged, all_agents


def format_midday_summary(
    midday_agent: Agent,
    join_after: int,
    total_packages: int,
    assignments: dict[str, list[Package]],
) -> str:
    """Format a human-readable summary of the mid-day join event.

    Args:
        midday_agent: The agent that joined.
        join_after: Package index at which the agent became available.
        total_packages: Total packages in the simulation.
        assignments: Merged assignment map (all agents).

    Returns:
        Multi-line string for CLI display.
    """
    post_count = total_packages - join_after
    received = len(assignments.get(midday_agent.id, []))
    lines = [
        "",
        "========================================================",
        " MID-DAY AGENT JOIN (BONUS)",
        "========================================================",
        f"  New agent     : {midday_agent.id}",
        f"  Joined at     : x={midday_agent.initial_location.x:.1f}, "
        f"y={midday_agent.initial_location.y:.1f}",
        f"  Join point    : after package #{join_after} of {total_packages}",
        f"  Pre-join pkgs : {join_after}  (ineligible)",
        f"  Post-join pkgs: {post_count}  (eligible)",
        f"  Pkgs received : {received}",
        "========================================================\n",
    ]
    return "\n".join(lines)
