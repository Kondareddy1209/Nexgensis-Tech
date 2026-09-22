"""Report generator and JSON exporter for FastBox delivery simulation."""

import json
from pathlib import Path
from typing import Optional, Sequence, Union

from .models import Agent, AgentReport, DeliveryReport


def generate_report(agents: Sequence[Agent]) -> DeliveryReport:
    """Compute performance metrics and select top performing courier.

    Rules:
    - total_distance: rounded to 2 decimal places at final report generation.
    - efficiency: total_distance / packages_delivered, rounded to 2 decimal places.
    - Idle agents (0 packages delivered): efficiency = 0.0, excluded from best_agent selection.
    - best_agent: Candidate with LOWEST efficiency score among active agents.
    - Tie-breaking for best_agent:
        1. Higher packages_delivered
        2. Lexicographically smaller agent ID
    """
    agent_reports: dict[str, AgentReport] = {}
    active_candidates: list[tuple[float, int, str]] = []

    for agent in agents:
        delivered = agent.packages_delivered
        raw_dist = agent.total_distance
        rounded_dist = round(raw_dist, 2)

        if delivered > 0:
            raw_efficiency = raw_dist / delivered
            rounded_efficiency = round(raw_efficiency, 2)
            # Candidate tuple for min():
            # 1. lowest efficiency (rounded_efficiency)
            # 2. negative delivered (so higher delivered is preferred)
            # 3. agent ID (lexicographically smaller preferred)
            active_candidates.append((rounded_efficiency, -delivered, agent.id))
        else:
            rounded_efficiency = 0.0

        agent_reports[agent.id] = AgentReport(
            packages_delivered=delivered,
            total_distance=rounded_dist,
            efficiency=rounded_efficiency,
        )

    best_agent_id: Optional[str] = None
    if active_candidates:
        # Sort and select best agent based on the specified tie-breaking hierarchy
        best_candidate = min(active_candidates, key=lambda c: (c[0], c[1], c[2]))
        best_agent_id = best_candidate[2]

    return DeliveryReport(agents=agent_reports, best_agent=best_agent_id)


def export_report(
    report: DeliveryReport,
    output_path: Union[str, Path] = "report.json",
) -> Path:
    """Serialize the report into a JSON file with standard 2-space indentation."""
    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    report_dict = report.to_dict()

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(report_dict, f, indent=2)
        f.write("\n")

    return out_file
