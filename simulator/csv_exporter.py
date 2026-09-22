"""Bonus feature: CSV export of the top-performing agent.

Uses the existing reporter module's best_agent field — no separate
best-agent logic is implemented here.
"""

import csv
from pathlib import Path
from typing import Union

from .models import DeliveryReport

# Default export path (relative to cwd; created if absent)
DEFAULT_CSV_PATH: str = "reports/top_performer.csv"

# Fixed column order for the exported CSV
_FIELDNAMES: list[str] = [
    "agent_id",
    "packages_delivered",
    "total_distance",
    "efficiency",
]


def export_top_performer_csv(
    report: DeliveryReport,
    output_path: Union[str, Path] = DEFAULT_CSV_PATH,
) -> Path:
    """Write the best-performing agent's stats to a CSV file.

    Best-agent selection is taken directly from `report.best_agent`,
    which is produced by the existing `generate_report()` function.
    No selection logic is duplicated here.

    If no agent delivered any package (`best_agent` is None), the file
    is written with headers only.

    Args:
        report: Completed DeliveryReport from the standard pipeline.
        output_path: Destination CSV file path.

    Returns:
        Resolved Path of the written CSV file.
    """
    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)

    with open(out_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=_FIELDNAMES)
        writer.writeheader()

        if report.best_agent is not None:
            stats = report.agents[report.best_agent]
            writer.writerow(
                {
                    "agent_id": report.best_agent,
                    "packages_delivered": stats.packages_delivered,
                    "total_distance": stats.total_distance,
                    "efficiency": stats.efficiency,
                }
            )

    return out_file
