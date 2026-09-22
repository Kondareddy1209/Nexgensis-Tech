# FastBox Logistics Delivery Simulator

**Nexgensis Technologies — Python Developer Take-Home Assignment**

---

## Overview

FastBox Logistics Delivery Simulator models a single operational day for a regional courier network. It ingests a JSON configuration describing warehouses, delivery agents, and packages; assigns each package to the nearest available agent using Euclidean distance; simulates the sequential physical delivery route for every agent; computes per-agent efficiency metrics; identifies the top-performing courier; and exports a structured JSON report.

The implementation is deterministic, uses **Python standard library only**, and requires **no external dependencies**.

---

## Features

### Core (Required)

| Feature | Module |
|---------|--------|
| Dual-schema JSON parsing and validation | `simulator/parser.py` |
| Euclidean distance calculation | `simulator/distance.py` |
| Nearest-agent package assignment with tie-breaking | `simulator/dispatcher.py` |
| Sequential delivery simulation (position tracking) | `simulator/engine.py` |
| Efficiency metrics + best-agent selection | `simulator/reporter.py` |
| JSON report export (`report.json`) | `simulator/reporter.py` |

### Bonus (Optional CLI flags)

| Feature | Flag | Module |
|---------|------|--------|
| Random delivery delays with reproducible seed | `--delays [--seed N]` | `simulator/delay.py` |
| ASCII route visualization + coordinate grid | `--visualize` | `simulator/visualizer.py` |
| Mid-day agent joining (two-phase assignment) | `--midday-agent ID X Y [--midday-after N]` | `simulator/midday.py` |
| CSV export of top performer | `--export-csv [--csv-path PATH]` | `simulator/csv_exporter.py` |

All bonus flags are **opt-in**. Omitting them preserves 100% identical default behavior.

---

## Architecture

```
nexgensis-python-assignment/
├── main.py                    # CLI entry point; orchestrates the full pipeline
│
├── simulator/
│   ├── __init__.py
│   ├── models.py              # Immutable domain types: Point, Warehouse, Agent, Package
│   ├── parser.py              # Dual-schema JSON parser + strict validation
│   ├── distance.py            # math.hypot Euclidean distance + nearest-agent finder
│   ├── dispatcher.py          # Static nearest-agent warehouse assignment (O(W·A + P))
│   ├── engine.py              # Sequential route simulation with position tracking
│   ├── reporter.py            # Efficiency metrics, best-agent ranking, JSON export
│   ├── delay.py               # [BONUS] Random delivery delay generation
│   ├── visualizer.py          # [BONUS] ASCII route visualization + coordinate grid
│   ├── midday.py              # [BONUS] Two-phase assignment for mid-day agent joining
│   └── csv_exporter.py        # [BONUS] CSV export of top performer
│
├── tests/
│   ├── test_distance.py       # 6 tests: Euclidean math and spatial functions
│   ├── test_parser.py         # 8 tests: schema variants, validation, error handling
│   ├── test_dispatcher.py     # 4 tests: assignment logic and tie-breaking
│   ├── test_engine.py         # 5 tests: route simulation and state transitions
│   ├── test_reporter.py       # 6 tests: metrics, idle agents, best-agent selection
│   ├── test_integration.py    # 1 test: end-to-end across all 11 provided datasets
│   └── test_bonus.py          # 33 tests: all four bonus features + regression guards
│
├── data/
│   ├── base_case.json         # Provided base-case dataset
│   └── test_cases/            # test_case_1.json … test_case_10.json
│
├── report.json                # Generated output for base_case.json (required)
├── requirements.txt           # Standard library only — no pip install needed
├── .gitignore
└── README.md
```

---

## Execution Flow

```
Input JSON
    │
    ▼
parser.py  ──► Validate schema, normalize both dict + list formats
    │
    ▼
dispatcher.py ──► For each package: find nearest agent (by initial location)
    │              Cache warehouse→agent mapping. Tie-break: lexicographic ID.
    ▼
engine.py  ──► For each agent, execute delivery queue sequentially:
    │            current_pos → warehouse → destination → update current_pos
    ▼
reporter.py ──► efficiency = total_distance / packages_delivered
    │           best_agent = agent with lowest efficiency (most efficient)
    ▼
report.json (+ optional CSV, delays, visualization)
```

---

## Engineering Assumptions

| # | Assumption | Rationale |
|---|-----------|-----------|
| 1 | **Euclidean distance** (`math.hypot`) | Assignment specifies straight-line distance |
| 2 | **Initial-position-based assignment** | Assignment strictly assigns by where agents *start*, not where they are mid-day |
| 3 | **Nearest eligible agent** wins each warehouse | One agent per warehouse; all packages at that warehouse go to that agent |
| 4 | **Lexicographic tie-breaking** (`"A1" < "A2"`) | Deterministic; prevents non-reproducibility |
| 5 | **FIFO package processing** | Packages delivered in input-file order |
| 6 | **Route: current_pos → warehouse → destination** | No return-to-base after final delivery |
| 7 | **Position updates after each delivery** | Agent's current position becomes the last destination |
| 8 | **No intermediate rounding** | Full IEEE 754 precision maintained; `round(v, 2)` applied only in final report |
| 9 | **Idle agents**: `efficiency = 0.0`, excluded from best-agent | Prevents division-by-zero and false minimums |
| 10 | **Best-agent ties**: higher `packages_delivered` wins, then lexicographic ID | Deterministic secondary sort |
| 11 | **Mid-day agent (bonus)**: two-phase split | Pre-join packages: original agents only. Post-join: all agents including joiner. No retroactive reassignment |
| 12 | **Delay (bonus)**: informational only | Delays do not alter distance, efficiency, or `report.json` schema |
| 13 | **Seeded randomness**: `random.Random(seed)` | Same seed → same delays, every run |

---

## Usage

### Standard Execution (Required)

```bash
# Run against the base case
python main.py data/base_case.json

# Run against a test case
python main.py data/test_cases/test_case_1.json

# Specify a custom output path
python main.py data/base_case.json -o my_report.json
```

### Bonus 1 — Delivery Delays

```bash
# Random delays (non-reproducible)
python main.py data/base_case.json --delays

# Reproducible delays with fixed seed
python main.py data/base_case.json --delays --seed 42
```

### Bonus 2 — ASCII Route Visualization

```bash
python main.py data/base_case.json --visualize
```

Output example:
```
  A1: A1(5,5) -> W1(0,0) -> P1(30,40) -> W1(0,0) -> P4(10,10)
  A2: A2(60,60) -> W2(50,75) -> P2(70,90) -> W2(50,75) -> P5(40,80)
  A3: A3(95,30) -> W3(100,25) -> P3(105,20)
```

Also prints a 60×24 ASCII coordinate grid showing `A` (agent start), `W` (warehouse), `D` (destination).

### Bonus 3 — Mid-Day Agent Joining

```bash
# Agent A5 joins at (50, 50), eligible after first 2 packages
python main.py data/base_case.json --midday-agent A5 50 50 --midday-after 2

# Default join point: half the total packages
python main.py data/base_case.json --midday-agent A5 50 50
```

### Bonus 4 — CSV Export of Top Performer

```bash
# Exports to reports/top_performer.csv (default)
python main.py data/base_case.json --export-csv

# Custom path
python main.py data/base_case.json --export-csv --csv-path results/winner.csv
```

CSV output format:
```
agent_id,packages_delivered,total_distance,efficiency
A3,1,14.14,14.14
```

### Combining Bonuses

All flags are composable:

```bash
python main.py data/base_case.json --delays --seed 42 --visualize --export-csv
```

---

## Running the Tests

```bash
python -m unittest discover -s tests -v
```

**Verified result:**

```
Ran 63 tests in ~0.2s
OK
```

| Test File | Tests | Covers |
|-----------|-------|--------|
| `test_distance.py` | 6 | Euclidean math, nearest-agent |
| `test_parser.py` | 8 | Both schema variants, validation errors |
| `test_dispatcher.py` | 4 | Assignment, tie-breaking |
| `test_engine.py` | 5 | Route simulation, state tracking |
| `test_reporter.py` | 6 | Metrics, idle agents, best-agent |
| `test_integration.py` | 1 | All 11 datasets end-to-end |
| `test_bonus.py` | 33 | All bonus features + regression |
| **Total** | **63** | **0 failures · 0 errors** |

The integration test verifies package conservation across all 11 supplied datasets (104 packages total — all assigned and delivered).

---

## Output: report.json

```json
{
  "A1": {
    "packages_delivered": 2,
    "total_distance": 121.21,
    "efficiency": 60.61
  },
  "A2": {
    "packages_delivered": 2,
    "total_distance": 79.21,
    "efficiency": 39.6
  },
  "A3": {
    "packages_delivered": 1,
    "total_distance": 14.14,
    "efficiency": 14.14
  },
  "best_agent": "A3"
}
```

### Field Definitions

| Field | Type | Description |
|-------|------|-------------|
| `packages_delivered` | `int` | Number of packages delivered by this agent |
| `total_distance` | `float` | Sum of all travel legs (rounded to 2 dp) |
| `efficiency` | `float` | `total_distance / packages_delivered` (rounded to 2 dp); `0.0` for idle agents |
| `best_agent` | `string \| null` | ID of the agent with **lowest** efficiency score; `null` if all agents are idle |

---

## Input Format

Two JSON schema variants are automatically detected and normalized:

### Format A — Dictionary-mapped (test cases 1–10)

```json
{
  "warehouses": { "W1": [0, 0], "W2": [50, 75] },
  "agents":     { "A1": [5, 5], "A2": [60, 60] },
  "packages": [
    { "id": "P1", "warehouse": "W1", "destination": [30, 40] }
  ]
}
```

### Format B — Object-list (base_case.json)

```json
{
  "warehouses": [{ "id": "W1", "location": [0, 0] }],
  "agents":     [{ "id": "A1", "location": [5, 5] }],
  "packages": [
    { "id": "P1", "warehouse_id": "W1", "destination": [30, 40] }
  ]
}
```

---

## Dependencies

| Requirement | Status |
|------------|--------|
| Python ≥ 3.8 | Required |
| External packages | **None** |
| pip install | **Not required** |

Standard library modules used: `math`, `json`, `csv`, `random`, `pathlib`, `dataclasses`, `typing`, `argparse`, `unittest`, `http.server`, `subprocess`, `tempfile`.
