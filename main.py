"""Main CLI entry point for FastBox Delivery Simulator."""

import argparse
import sys
from pathlib import Path
from typing import Optional

from simulator.dispatcher import assign_packages
from simulator.engine import simulate_deliveries
from simulator.models import DeliveryReport
from simulator.parser import ValidationError, parse_delivery_data
from simulator.reporter import export_report, generate_report

# ── Bonus feature imports (all optional, only used when flags are provided) ───
from simulator.delay import format_delay_report, generate_delays
from simulator.visualizer import print_visualization
from simulator.midday import (
    assign_with_midday_agent,
    build_midday_agent,
    format_midday_summary,
)
from simulator.csv_exporter import DEFAULT_CSV_PATH, export_top_performer_csv


def resolve_input_path(given_path: str) -> Path:
    """Resolve input path checking multiple candidate locations."""
    candidate = Path(given_path)
    if candidate.is_file():
        return candidate

    # Search common relative locations
    search_paths = [
        Path.cwd() / given_path,
        Path(__file__).parent / given_path,
        Path(__file__).parent / "data" / given_path,
        Path(__file__).parent / "data" / "test_cases" / given_path,
        Path(__file__).parent.parent / given_path,
        Path(__file__).parent.parent / "Python Assignment(Delivery System Test Cases)" / given_path,
    ]

    for p in search_paths:
        if p.is_file():
            return p

    raise FileNotFoundError(
        f"Could not locate input file: '{given_path}'. Please provide a valid file path."
    )


def run_simulation(
    input_path: str,
    output_path: str = "report.json",
    *,
    # ── Bonus 1: random delivery delays ──────────────────────────────────
    enable_delays: bool = False,
    delay_seed: Optional[int] = None,
    # ── Bonus 2: ASCII route visualization ───────────────────────────────
    visualize: bool = False,
    # ── Bonus 3: mid-day agent joining ───────────────────────────────────
    midday_agent_id: Optional[str] = None,
    midday_agent_x: Optional[float] = None,
    midday_agent_y: Optional[float] = None,
    midday_join_after: Optional[int] = None,
    # ── Bonus 4: CSV export of top performer ─────────────────────────────
    export_csv: bool = False,
    csv_path: str = DEFAULT_CSV_PATH,
) -> DeliveryReport:
    """Execute end-to-end simulation workflow.

    The keyword-only bonus parameters are all disabled by default, preserving
    100% backward compatibility when called without them.
    """
    resolved_input = resolve_input_path(input_path)

    # ── Core pipeline (unchanged) ─────────────────────────────────────────
    # 1. Parse and validate input data
    warehouses, agents, packages = parse_delivery_data(resolved_input)

    # 2. Assign packages to nearest agents (or run mid-day variant)
    midday_agent = None
    if (
        midday_agent_id is not None
        and midday_agent_x is not None
        and midday_agent_y is not None
    ):
        # ── Bonus 3 path ────────────────────────────────────────────────
        midday_agent = build_midday_agent(midday_agent_id, midday_agent_x, midday_agent_y)
        join_after = (
            midday_join_after
            if midday_join_after is not None
            else len(packages) // 2
        )
        assignments, all_agents = assign_with_midday_agent(
            warehouses, agents, packages, midday_agent, join_after
        )
        print(
            format_midday_summary(midday_agent, join_after, len(packages), assignments)
        )
    else:
        # ── Standard assignment path ─────────────────────────────────────
        assignments = assign_packages(warehouses, agents, packages)
        all_agents = list(agents)

    # 3. Simulate sequential physical deliveries
    simulated_agents = simulate_deliveries(all_agents, assignments, warehouses)

    # 4. Compute performance metrics and identify top courier
    report = generate_report(list(simulated_agents.values()))

    # 5. Export results to report.json
    export_report(report, output_path)

    # ── Bonus 1: delivery delays ──────────────────────────────────────────
    if enable_delays:
        delays = generate_delays(packages, seed=delay_seed)
        print(format_delay_report(assignments, delays))

    # ── Bonus 2: ASCII route visualization ────────────────────────────────
    if visualize:
        print_visualization(all_agents, assignments, warehouses, packages)

    # ── Bonus 4: CSV export ───────────────────────────────────────────────
    if export_csv:
        csv_file = export_top_performer_csv(report, csv_path)
        print(f"\n[CSV] Top performer exported to: {csv_file}\n")

    return report


def main(argv: Optional[list[str]] = None) -> int:
    """CLI runner."""
    parser = argparse.ArgumentParser(
        description="FastBox Logistics Delivery Simulator - Nexgensis Technologies Take-Home"
    )
    parser.add_argument(
        "input_file",
        nargs="?",
        default="base_case.json",
        help="Path to input JSON file (e.g., base_case.json or test_case_1.json). Default: base_case.json",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="report.json",
        help="Destination path for generated report. Default: report.json",
    )

    # ── Bonus 1 ───────────────────────────────────────────────────────────
    parser.add_argument(
        "--delays",
        action="store_true",
        default=False,
        help="[BONUS] Simulate random delivery delays.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        metavar="N",
        help="[BONUS] RNG seed for reproducible delays (requires --delays).",
    )

    # ── Bonus 2 ───────────────────────────────────────────────────────────
    parser.add_argument(
        "--visualize",
        action="store_true",
        default=False,
        help="[BONUS] Print ASCII route visualization for each agent.",
    )

    # ── Bonus 3 ───────────────────────────────────────────────────────────
    parser.add_argument(
        "--midday-agent",
        nargs=3,
        metavar=("ID", "X", "Y"),
        default=None,
        help=(
            "[BONUS] Add a mid-day agent that joins after --midday-after packages. "
            "Example: --midday-agent A_NEW 50 50"
        ),
    )
    parser.add_argument(
        "--midday-after",
        type=int,
        default=None,
        metavar="N",
        help=(
            "[BONUS] Number of packages dispatched before the mid-day agent becomes "
            "eligible (default: half the total packages)."
        ),
    )

    # ── Bonus 4 ───────────────────────────────────────────────────────────
    parser.add_argument(
        "--export-csv",
        action="store_true",
        default=False,
        help="[BONUS] Export top performer stats to reports/top_performer.csv.",
    )
    parser.add_argument(
        "--csv-path",
        default=DEFAULT_CSV_PATH,
        help=f"[BONUS] CSV output path (default: {DEFAULT_CSV_PATH}).",
    )

    args = parser.parse_args(argv)

    # Parse midday-agent spec
    midday_id: Optional[str] = None
    midday_x: Optional[float] = None
    midday_y: Optional[float] = None
    if args.midday_agent is not None:
        raw_id, raw_x, raw_y = args.midday_agent
        try:
            midday_id = raw_id
            midday_x = float(raw_x)
            midday_y = float(raw_y)
        except ValueError:
            print(
                f"\n[ERROR] --midday-agent: X and Y must be numeric. Got: {raw_x}, {raw_y}",
                file=sys.stderr,
            )
            return 1

    try:
        report = run_simulation(
            args.input_file,
            args.output,
            enable_delays=args.delays,
            delay_seed=args.seed,
            visualize=args.visualize,
            midday_agent_id=midday_id,
            midday_agent_x=midday_x,
            midday_agent_y=midday_y,
            midday_join_after=args.midday_after,
            export_csv=args.export_csv,
            csv_path=args.csv_path,
        )

        print("\n========================================================")
        print(" FASTBOX LOGISTICS SIMULATION COMPLETED SUCCESSFULLY")
        print("========================================================")
        print(f" Input File  : {args.input_file}")
        print(f" Report Saved: {args.output}")
        print(f" Best Agent  : {report.best_agent}")
        print("--------------------------------------------------------")
        print(f" {'Agent ID':<10} {'Delivered':<12} {'Distance':<12} {'Efficiency':<12}")
        print("--------------------------------------------------------")
        for aid, stats in sorted(report.agents.items()):
            print(
                f" {aid:<10} {stats.packages_delivered:<12} {stats.total_distance:<12.2f} {stats.efficiency:<12.2f}"
            )
        print("========================================================\n")
        return 0

    except (FileNotFoundError, ValidationError) as err:
        print(f"\n[ERROR] Simulation halted: {err}", file=sys.stderr)
        return 1
    except Exception as err:
        print(f"\n[UNEXPECTED ERROR] {type(err).__name__}: {err}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
