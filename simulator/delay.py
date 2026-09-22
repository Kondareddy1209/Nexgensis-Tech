"""Bonus feature: optional random delivery delay simulation.

Delays are purely informational and do NOT affect distance calculations,
package assignment, efficiency scores, or the required report schema.
"""

import random
from typing import Optional, Sequence

from .models import Package

# Delay range in minutes — realistic last-mile delivery variance
_MIN_DELAY_MINUTES: int = 1
_MAX_DELAY_MINUTES: int = 30


def generate_delays(
    packages: Sequence[Package],
    seed: Optional[int] = None,
) -> dict[str, int]:
    """Generate a random delay (in minutes) for each package delivery.

    Args:
        packages: Ordered sequence of packages to generate delays for.
        seed: Optional RNG seed for reproducible results.
              When supplied, repeated calls with the same seed produce
              identical delay values.

    Returns:
        Mapping of package_id -> delay in minutes.
    """
    rng = random.Random(seed)
    return {
        pkg.id: rng.randint(_MIN_DELAY_MINUTES, _MAX_DELAY_MINUTES)
        for pkg in packages
    }


def format_delay_report(
    assignments: dict[str, list[Package]],
    delays: dict[str, int],
) -> str:
    """Format delay information for CLI display.

    Args:
        assignments: Mapping of agent_id -> list of assigned packages.
        delays: Mapping of package_id -> delay in minutes.

    Returns:
        Multi-line string ready for printing.
    """
    lines: list[str] = [
        "",
        "========================================================",
        " DELIVERY DELAY SIMULATION (BONUS)",
        "========================================================",
        f" {'Agent':<8} {'Package':<10} {'Delay (min)':>12}",
        "--------------------------------------------------------",
    ]
    for agent_id in sorted(assignments):
        pkgs = assignments[agent_id]
        if not pkgs:
            lines.append(f" {agent_id:<8} {'[idle]':<10} {'N/A':>12}")
        else:
            for pkg in pkgs:
                delay = delays.get(pkg.id, 0)
                lines.append(f" {agent_id:<8} {pkg.id:<10} {delay:>12}")
    lines.append("========================================================\n")
    return "\n".join(lines)
