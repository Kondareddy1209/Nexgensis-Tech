"""Domain models for FastBox Delivery Simulator."""

from dataclasses import dataclass
from typing import Any, Optional


@dataclass(frozen=True)
class Point:
    """Represents a 2D Cartesian coordinate point (x, y)."""
    x: float
    y: float

    def __post_init__(self) -> None:
        # Enforce float conversion for robust calculations
        object.__setattr__(self, "x", float(self.x))
        object.__setattr__(self, "y", float(self.y))


@dataclass(frozen=True)
class Warehouse:
    """Represents a warehouse storage facility with an identifier and location."""
    id: str
    location: Point


@dataclass(frozen=True)
class Package:
    """Represents a package originating from a warehouse heading to a destination."""
    id: str
    warehouse_id: str
    destination: Point


@dataclass
class Agent:
    """Represents a delivery courier agent whose position and statistics update during simulation."""
    id: str
    initial_location: Point
    current_location: Point
    packages_delivered: int = 0
    total_distance: float = 0.0

    @classmethod
    def create(cls, agent_id: str, initial_location: Point) -> "Agent":
        """Factory method to initialize an agent with starting coordinates."""
        return cls(
            id=agent_id,
            initial_location=initial_location,
            current_location=initial_location,
            packages_delivered=0,
            total_distance=0.0,
        )


@dataclass(frozen=True)
class AgentReport:
    """Per-agent final performance metrics."""
    packages_delivered: int
    total_distance: float
    efficiency: float

    def to_dict(self) -> dict[str, Any]:
        """Convert agent statistics into JSON-serializable dictionary."""
        return {
            "packages_delivered": self.packages_delivered,
            "total_distance": self.total_distance,
            "efficiency": self.efficiency,
        }


@dataclass
class DeliveryReport:
    """Overall simulation report containing per-agent metrics and top performer."""
    agents: dict[str, AgentReport]
    best_agent: Optional[str]

    def to_dict(self) -> dict[str, Any]:
        """Serialize report to flat dictionary format required by assignment specification."""
        result: dict[str, Any] = {
            agent_id: stats.to_dict()
            for agent_id, stats in sorted(self.agents.items())
        }
        result["best_agent"] = self.best_agent
        return result
