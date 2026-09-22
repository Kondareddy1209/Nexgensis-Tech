"""Bonus feature: ASCII route visualization.

Generates a text-based route summary from actual simulation state.
No GUI, no web framework — strictly CLI output.
"""

from typing import Mapping, Sequence

from .models import Agent, Package, Warehouse

# Grid dimensions for the optional coordinate-grid display
_GRID_WIDTH: int = 60
_GRID_HEIGHT: int = 24


def format_route(
    agent: Agent,
    packages: Sequence[Package],
    warehouse_by_id: Mapping[str, Warehouse],
) -> str:
    """Format one agent's delivery route as a hop-by-hop text chain.

    Example output:
        A1: A1(5,5) → W1(0,0) → P1(30,40) → W1(0,0) → P4(10,10)

    Args:
        agent: The agent whose route is being rendered.
        packages: Ordered list of packages assigned to this agent.
        warehouse_by_id: Lookup map of warehouse_id -> Warehouse.

    Returns:
        Single-line route string.
    """
    if not packages:
        return (
            f"  {agent.id}: [{agent.id}({agent.initial_location.x:.0f},"
            f"{agent.initial_location.y:.0f})] -> [idle - no packages assigned]"
        )

    steps: list[str] = [
        f"{agent.id}({agent.initial_location.x:.0f},{agent.initial_location.y:.0f})"
    ]
    for pkg in packages:
        wh = warehouse_by_id[pkg.warehouse_id]
        steps.append(
            f"{wh.id}({wh.location.x:.0f},{wh.location.y:.0f})"
        )
        steps.append(
            f"{pkg.id}({pkg.destination.x:.0f},{pkg.destination.y:.0f})"
        )

    return f"  {agent.id}: " + " -> ".join(steps)


def _scale(value: float, v_min: float, v_max: float, target: int) -> int:
    """Map a coordinate value to a grid cell index (0-indexed)."""
    span = v_max - v_min
    if span == 0:
        return target // 2
    return int((value - v_min) / span * (target - 1))


def _build_coordinate_grid(
    agents: Sequence[Agent],
    warehouses: Sequence[Warehouse],
    packages: Sequence[Package],
) -> list[str]:
    """Build a simple ASCII coordinate grid showing all entities.

    Symbols:
        A  — agent starting position
        W  — warehouse
        D  — package destination
    """
    # Collect all coordinates for scaling
    all_x: list[float] = []
    all_y: list[float] = []
    for a in agents:
        all_x.append(a.initial_location.x)
        all_y.append(a.initial_location.y)
    for w in warehouses:
        all_x.append(w.location.x)
        all_y.append(w.location.y)
    for p in packages:
        all_x.append(p.destination.x)
        all_y.append(p.destination.y)

    x_min, x_max = min(all_x), max(all_x)
    y_min, y_max = min(all_y), max(all_y)

    grid: list[list[str]] = [
        ["."] * _GRID_WIDTH for _ in range(_GRID_HEIGHT)
    ]

    def place(x: float, y: float, symbol: str) -> None:
        gx = _scale(x, x_min, x_max, _GRID_WIDTH)
        # Invert Y so larger coordinates appear higher on screen
        gy = _GRID_HEIGHT - 1 - _scale(y, y_min, y_max, _GRID_HEIGHT)
        grid[gy][gx] = symbol

    for pkg in packages:
        place(pkg.destination.x, pkg.destination.y, "D")
    for w in warehouses:
        place(w.location.x, w.location.y, "W")
    for a in agents:
        place(a.initial_location.x, a.initial_location.y, "A")

    border = "+" + "-" * _GRID_WIDTH + "+"
    rows = [border]
    for row in grid:
        rows.append("|" + "".join(row) + "|")
    rows.append(border)
    rows.append(f"  Legend: A=Agent start  W=Warehouse  D=Destination")
    rows.append(
        f"  X range: [{x_min:.0f}, {x_max:.0f}]   "
        f"Y range: [{y_min:.0f}, {y_max:.0f}]"
    )
    return rows


def print_visualization(
    agents: Sequence[Agent],
    assignments: Mapping[str, Sequence[Package]],
    warehouses: Sequence[Warehouse],
    packages: Sequence[Package],
    *,
    show_grid: bool = True,
) -> None:
    """Print the full ASCII route visualization to stdout.

    Args:
        agents: All agents (including idle ones).
        assignments: agent_id -> ordered list of assigned packages.
        warehouses: All warehouses.
        packages: All packages (used for the coordinate grid).
        show_grid: Whether to render the coordinate-grid overview.
    """
    wh_map: dict[str, Warehouse] = {w.id: w for w in warehouses}

    print("\n========================================================")
    print(" ROUTE VISUALIZATION (BONUS)")
    print("========================================================")

    for agent in sorted(agents, key=lambda a: a.id):
        pkgs = list(assignments.get(agent.id, []))
        print(format_route(agent, pkgs, wh_map))

    print("--------------------------------------------------------")
    print(" Format: AgentID(x,y) -> WarehouseID(x,y) -> PkgID(x,y)")
    print("========================================================\n")

    if show_grid and agents and warehouses:
        print("  Coordinate Overview:")
        for line in _build_coordinate_grid(agents, warehouses, packages):
            print(line)
        print()
