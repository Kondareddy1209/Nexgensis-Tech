# FastBox Logistics Delivery Simulator

## Candidate

Ambavaram Tirumala Konda Reddy

Python Developer Take-Home Assignment  
Nexgensis Technologies

---

## 1. What This Project Does

FastBox Logistics Delivery Simulator is a discrete-event logistics routing and simulation engine written in pure Python.

Consider a real-world courier operation:
- Warehouses hold packages ready for dispatch.
- Delivery agents start at specific locations across a city.
- Packages have known pickup warehouses and customer drop-off destinations.

The simulator models this workflow end-to-end:
1. It assigns each package to the most suitable delivery agent based on proximity to the pickup warehouse.
2. It simulates the physical transit of each courier moving from their starting location to the warehouse, picking up items, and dropping them off at customer destinations.
3. It aggregates distance traveled and calculates efficiency metrics for every agent.
4. It identifies the top-performing courier and exports the results to a structured `report.json` file.

---

## 2. Core Requirements

The core assignment defines seven mandatory functional capabilities:

1. **Read JSON Input**: Load operational data specifying warehouses, delivery agents, and packages.
2. **Schema Validation & Parsing**: Extract coordinate pairs and entity identifiers reliably across schema variants.
3. **Distance Calculation**: Compute Euclidean distances between coordinate points on a 2D plane.
4. **Package Assignment**: Assign packages to eligible couriers based on proximity to the source warehouse.
5. **Delivery Simulation**: Track multi-leg courier movements sequentially, updating courier positions after each drop-off.
6. **Metrics Calculation**: Compute total packages delivered, cumulative distance traveled, and efficiency ratio per agent.
7. **Report Generation**: Export metrics and identify the best-performing agent in `report.json`.

---

## 3. How the Program Works

The execution pipeline follows a clear, unidirectional flow:

```
+-----------------------------------------------------------+
|                        JSON Input                         |
+-----------------------------------------------------------+
                              |
                              v
+-----------------------------------------------------------+
|                   Parse & Validate Data                   |
|       (Normalize entities and validate coordinates)       |
+-----------------------------------------------------------+
                              |
                              v
+-----------------------------------------------------------+
|                Find Nearest Eligible Agent                |
|      (Measure distance from agent start to warehouse)     |
+-----------------------------------------------------------+
                              |
                              v
+-----------------------------------------------------------+
|                      Assign Packages                      |
|         (Deterministic assignment & tie-breaking)         |
+-----------------------------------------------------------+
                              |
                              v
+-----------------------------------------------------------+
|                 Simulate Delivery Routes                  |
|     (Leg 1: Agent -> Warehouse; Leg 2: Warehouse -> Dest) |
|      (Subsequent legs start from previous destination)    |
+-----------------------------------------------------------+
                              |
                              v
+-----------------------------------------------------------+
|                     Calculate Metrics                     |
|           (Distance, package count, efficiency)           |
+-----------------------------------------------------------+
                              |
                              v
+-----------------------------------------------------------+
|                   Generate report.json                    |
|             (Select best agent & export JSON)             |
+-----------------------------------------------------------+
```

### Execution Steps:
1. **Parse Input**: Loads JSON data and validates coordinate structures, IDs, and referential integrity (ensuring referenced warehouses exist).
2. **Dispatch Packages**: For each package, identifies which agent starts closest to the package's pickup warehouse.
3. **Simulate Transit**: Each agent begins at their initial coordinate, drives to the warehouse to collect the package, travels to the drop-off coordinate, and remains there for subsequent deliveries.
4. **Calculate Scores**: Computes total distance per courier and evaluates efficiency.
5. **Output**: Writes the required `report.json` file and displays an execution summary in the terminal.

---

## 4. Important Engineering Decision: Assignment vs Delivery Simulation

A central architectural decision in this simulator is the separation between **Package Assignment** and **Delivery Simulation**.

```
PACKAGE ASSIGNMENT PHASE (Dispatch Time)
========================================
Agent Initial Position --------> Warehouse
                                     |
               Determines nearest eligible agent

DELIVERY SIMULATION PHASE (Execution Time)
==========================================
Agent Current Position --------> Warehouse --------> Package Destination
                                                           |
                                      Agent Current Position is updated!
```

### Why These Are Separate Concepts

1. **Package Assignment (Planning)**:
   - Evaluates who is responsible for each package before operations begin.
   - Assignment proximity is calculated from the **agent's initial starting location** to the warehouse.
   - This prevents race conditions, order-dependent dispatch bias, and unpredictable reassignment cascades during dispatch planning.

2. **Delivery Simulation (Execution)**:
   - Models the physical reality of a courier on the road.
   - For the first delivery, the courier travels: `Initial Location -> Warehouse -> Destination`.
   - After completing that delivery, the courier is physically located at `Destination`.
   - For any subsequent delivery assigned to that courier, the route begins from their **current location** (the previous drop-off destination): `Previous Destination -> Warehouse -> Next Destination`.
   - Couriers remain at their final destination at the end of the shift; they do not make an uncompensated return trip to the warehouse or starting position.

### Concrete Example:

- Agent `A1` starts at `(5, 5)`. Warehouse `W1` is at `(0, 0)`.
- Packages `P1` (dest: `[30, 40]`) and `P4` (dest: `[10, 10]`) are assigned to `A1`.
- **First Delivery (`P1`)**:
  - Leg 1: `(5, 5)` to `W1 (0, 0)` = 7.07 units
  - Leg 2: `W1 (0, 0)` to `P1 (30, 40)` = 50.00 units
  - `A1` is now at `(30, 40)`.
- **Second Delivery (`P4`)**:
  - Leg 1: `(30, 40)` to `W1 (0, 0)` = 50.00 units
  - Leg 2: `W1 (0, 0)` to `P4 (10, 10)` = 14.14 units
  - `A1` ends at `(10, 10)`.
- Total distance for `A1`: `7.07 + 50.00 + 50.00 + 14.14 = 121.21` units.

---

## 5. Distance Calculation

All spatial measurements are calculated using Euclidean distance on a two-dimensional Cartesian plane:

$$\text{distance} = \sqrt{(x_2 - x_1)^2 + (y_2 - y_1)^2}$$

This formula represents straight-line distance, analogous to applying the Pythagorean theorem to calculate the hypotenuse between two coordinates.

### Implementation Detail
The project implements this via Python's standard library function `math.hypot(dx, dy)` in `simulator/distance.py`:

```python
def calculate_distance(p1: tuple[float, float], p2: tuple[float, float]) -> float:
    return math.hypot(p2[0] - p1[0], p2[1] - p1[1])
```

`math.hypot` is selected because it is fast, numerically stable, and prevents intermediate floating-point overflow or underflow. Rounding is deferred until final metric presentation to prevent cumulative precision loss.

---

## 6. Package Assignment

Package assignment is handled by `simulator/dispatcher.py`:

1. **Nearest Warehouse Proximity**: For each package, the dispatcher calculates the Euclidean distance between every eligible agent's starting position and the package's pickup warehouse.
2. **Deterministic Tie-Breaking**: If two or more agents are equidistant to a warehouse, ties are broken lexicographically by agent identifier (`A1` precedes `A2`).
3. **Preservation of Package Order**: Packages are processed in the exact order in which they appear in the input file.
4. **Eligibility**: By default, all parsed agents are eligible for assignment from the start of the schedule.

---

## 7. Delivery Simulation

The delivery simulation lifecycle is executed by `simulator/engine.py`:

- **Route Execution**:
  - Leg A: Transit from agent's current position to the pickup warehouse.
  - Leg B: Transit from the pickup warehouse to the customer destination coordinate.
- **Position Tracking**: Upon arrival at the customer destination, the agent's internal state updates: `agent.current_location = destination`.
- **Sequential Multi-Package Delivery**: If an agent has multiple deliveries, subsequent deliveries depart from the drop-off coordinate of the previous delivery.
- **Shift Termination**: The agent stays at the destination of their final package. No return trip is logged.
- **Idle Agents**: Agents with zero assigned packages remain at their starting coordinates, logging 0.0 units traveled.

---

## 8. Report

Simulation results are written to `report.json` via `simulator/reporter.py`.

### Schema and Fields

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

### Field Definitions:
- `packages_delivered` (`int`): Count of packages successfully delivered by the agent.
- `total_distance` (`float`): Total Euclidean units traveled across all delivery legs, rounded to 2 decimal places.
- `efficiency` (`float`): Ratio of distance per package delivered:
  $$\text{efficiency} = \frac{\text{total\_distance}}{\text{packages\_delivered}}$$
  **Lower efficiency values indicate superior performance** (less distance traveled per package delivered).
- `best_agent` (`str`): The agent identifier with the lowest efficiency score among active agents.

### Edge Case Handling:
- **Idle Agents**: If an agent delivers 0 packages, their efficiency is recorded as `0.0`. They are strictly excluded from `best_agent` selection to prevent unearned wins or division-by-zero errors.
- **Efficiency Ties**: If two active agents share the exact same efficiency score, ties are broken by highest package count, then lexicographically by agent ID.
- **All Idle**: If no packages are delivered across the entire simulation, `best_agent` evaluates to `null`.

---

## 9. Project Structure

The repository is modularized into cohesive, single-responsibility files:

```
nexgensis-python-assignment/
├── main.py                     # CLI entry point and orchestration
├── requirements.txt            # Environment documentation (Python standard library only)
├── report.json                 # Verified simulation output for base_case.json
├── .gitignore                  # Git hygiene and exclusion rules
├── README.md                   # Technical system documentation
│
├── simulator/                  # Core simulation and bonus packages
│   ├── __init__.py             # Package marker and version info
│   ├── models.py               # Domain models: Warehouse, Agent, Package, DeliveryResult
│   ├── parser.py               # JSON input parsing and multi-schema validation
│   ├── distance.py             # Euclidean distance math using math.hypot
│   ├── dispatcher.py           # Nearest-agent package assignment and tie-breaking
│   ├── engine.py               # Discrete-event multi-leg route simulation engine
│   ├── reporter.py             # Performance metric aggregation and JSON export
│   │
│   ├── delay.py                # [Bonus 1] Stochastic traffic delay modeling
│   ├── visualizer.py           # [Bonus 2] ASCII route diagrams and 2D grid visualizer
│   ├── midday.py               # [Bonus 3] Mid-day agent dynamic onboarding
│   └── csv_exporter.py         # [Bonus 4] Top-performer CSV export utility
│
├── data/                       # Input test datasets
│   ├── base_case.json          # Standard assignment baseline dataset
│   └── test_cases/             # 10 comprehensive edge-case datasets (test_case_1 to 10)
│
└── tests/                      # Automated test suite (63 unit and integration tests)
    ├── __init__.py             # Test package marker
    ├── test_parser.py          # Schema parsing and validation test suite
    ├── test_distance.py        # Distance calculations and edge case validation
    ├── test_dispatcher.py      # Dispatching and tie-breaking rules
    ├── test_engine.py          # Movement simulation and position state updates
    ├── test_reporter.py        # Efficiency calculation and best-agent determination
    ├── test_integration.py     # End-to-end multi-dataset verification (all 11 files)
    └── test_bonus.py           # Unit tests for all 4 optional bonus features
```

---

## 10. Input Data

The parser (`simulator/parser.py`) natively supports two JSON schema variants without requiring manual configuration:

### Schema Variant A (Used in `test_case_1.json` through `test_case_10.json`)
Entities are stored as dictionaries keyed by identifier, and packages use the `"warehouse"` attribute:

```json
{
  "warehouses": {
    "W1": [0, 0],
    "W2": [50, 75]
  },
  "agents": {
    "A1": [5, 5],
    "A2": [60, 60]
  },
  "packages": [
    { "id": "P1", "warehouse": "W1", "destination": [30, 40] }
  ]
}
```

### Schema Variant B (Used in `base_case.json`)
Entities are stored as lists of objects with `"id"` and `"location"` attributes, and packages use `"warehouse_id"`:

```json
{
  "warehouses": [
    { "id": "W1", "location": [0, 0] }
  ],
  "agents": [
    { "id": "A1", "location": [5, 5] }
  ],
  "packages": [
    { "id": "P1", "warehouse_id": "W1", "destination": [30, 40] }
  ]
}
```

Both schemas are parsed into standardized domain models (`Warehouse`, `Agent`, `Package`) defined in `simulator/models.py`.

---

## 11. Running the Project

### Basic Execution
Execute the simulation against the base case:

```bash
python main.py data/base_case.json
```

Or omit the argument to run `data/base_case.json` by default:

```bash
python main.py
```

### Running Test Case Datasets
Execute against any provided dataset:

```bash
python main.py data/test_cases/test_case_1.json
python main.py data/test_cases/test_case_5.json
```

### Custom Output Path
Specify a custom destination for the generated report using `-o` or `--output`:

```bash
python main.py data/base_case.json -o custom_report.json
```

### Sample Console Output

```
========================================================
 FASTBOX LOGISTICS SIMULATION COMPLETED SUCCESSFULLY
========================================================
 Input File  : data/base_case.json
 Report Saved: report.json
 Best Agent  : A3
--------------------------------------------------------
 Agent ID   Delivered    Distance     Efficiency
--------------------------------------------------------
 A1         2            121.21       60.61
 A2         2            79.21        39.60
 A3         1            14.14        14.14
========================================================
```

---

## 12. Optional Bonus Features

The core requirements are implemented independently of the optional bonus features. Bonus flags are opt-in and do not change default core metrics or baseline outputs.

### Random Delivery Delays

- **Flag**: `--delays`
- **Seed Flag**: `--seed N` (optional integer for reproducible pseudorandom values)
- **Description**: Models stochastic traffic delays (between 1 and 30 minutes) per package delivery.
- **Behavior**: Delays are displayed in a formatted breakdown table. Crucially, delays do not alter Euclidean distance or efficiency calculations.

```bash
python main.py data/base_case.json --delays --seed 42
```

### ASCII Route Visualization

- **Flag**: `--visualize`
- **Description**: Renders two complementary visual outputs:
  1. A text-based route sequence showing hops: `Agent(x, y) -> Warehouse(x, y) -> Package(x, y)`.
  2. A 2D ASCII grid coordinate map plotting relative positions of agents (`A`), warehouses (`W`), and customer destinations (`D`).

```bash
python main.py data/base_case.json --visualize
```

### Mid-Day Agent Joining

- **Flags**:
  - `--midday-agent ID X Y`: Specifies the identifier and initial coordinate of an agent onboarding mid-shift.
  - `--midday-after N`: Specifies the number of packages dispatched before the new agent becomes eligible (defaults to $\lfloor\text{total packages} / 2\rfloor$).
- **Description**: Models dynamic courier onboarding.
- **Behavior**: Packages dispatched before threshold $N$ remain assigned to original agents. Only packages dispatched at or after package index $N$ consider the mid-day agent as an eligible candidate.

```bash
python main.py data/base_case.json --midday-agent A_NEW 50 50 --midday-after 2
```

### CSV Top Performer Export

- **Flag**: `--export-csv`
- **Path Flag**: `--csv-path CSV_PATH` (defaults to `reports/top_performer.csv`)
- **Description**: Exports the metrics of the best-performing agent into standard tabular CSV format.

```bash
python main.py data/base_case.json --export-csv --csv-path reports/top_performer.csv
```

### Composing Bonus Features

All bonus options can be composed together cleanly:

```bash
python main.py data/base_case.json --delays --seed 42 --visualize --export-csv
```

---

## 13. Engineering Assumptions

Every architectural choice aligns with the assignment specification and predictable behavior:

| Decision | Implementation | Rationale |
|---|---|---|
| **Distance Formula** | Euclidean distance via `math.hypot` | Direct straight-line distance on 2D coordinate grid |
| **Package Assignment** | Nearest eligible agent from starting position to warehouse | Establishes deterministic package ownership |
| **Tie-Breaking** | Lexicographical order by ID (`A1` < `A2`) | Guarantees deterministic, reproducible assignment across environments |
| **Package Ordering** | Preserves input file sequential order | Respects intake ordering without unrequested re-sorting |
| **Delivery Route** | `Current Position -> Warehouse -> Destination` | Models sequential physical legs of package pickup and drop-off |
| **Position Updates** | Agent coordinate updates to drop-off point after each delivery | Subsequent legs originate from courier's real physical location |
| **Depot Return** | No return trip after final delivery | Matches standard gig-economy/courier shift termination at last stop |
| **Efficiency Metric** | $\text{Distance} / \text{Delivered}$ | Measures unit travel required per completed delivery (lower = better) |
| **Idle Couriers** | Logged with 0.0 distance, 0.0 efficiency, excluded from `best_agent` | Prevents division-by-zero; idle couriers cannot win best agent |
| **Precision** | Floating-point throughout, rounded to 2 decimals on report export | Eliminates cumulative rounding errors during route legs |
| **Mid-Day Eligibility** | Agent joins only for package index $\ge N$ | Existing assignments remain immutable; only pending deliveries re-evaluate |
| **Delay Impact** | Reported independently; does not alter route distance | Preserves core metric integrity while demonstrating bonus simulation |

---

## 14. Testing

The project includes an automated test suite executed via Python's standard `unittest` framework:

```bash
python -m unittest discover -s tests -v
```

### Verified Test Suite Results:
- **Total Tests**: **63 passed**
- **Failures**: **0**
- **Errors**: **0**
- **Execution Time**: ~0.20 seconds

### Test File Breakdown:

| Test File | Count | Scope |
|---|:---:|---|
| `tests/test_distance.py` | 6 | Pythagorean triples, identical coordinates, float precision, empty inputs |
| `tests/test_parser.py` | 8 | Schema Variant A & B parsing, malformed JSON, missing keys, invalid coords |
| `tests/test_dispatcher.py` | 4 | Proximity selection, multi-package mapping, tie-breaking, position independence |
| `tests/test_engine.py` | 5 | Single/multi-package routes, multi-warehouse routing, idle agents, collocated points |
| `tests/test_reporter.py` | 6 | Efficiency calculation, best-agent selection, tie-breaking, idle agent exclusion, JSON structure |
| `tests/test_integration.py` | 1 | End-to-end verification across **all 11 datasets** (104 packages verified without loss) |
| `tests/test_bonus.py` | 33 | Unit tests for delay simulation, ASCII route/map visualizer, mid-day agent logic, and regression invariants |
| **Total** | **63** | **100% Pass Rate** |

---

## 15. Regression Safety

The bonus features are strictly opt-in. Running the application without bonus flags preserves the required baseline behavior.

### Baseline Verification (`data/base_case.json`):
- `A1`: 2 packages delivered, total distance 121.21, efficiency 60.61
- `A2`: 2 packages delivered, total distance 79.21, efficiency 39.60
- `A3`: 1 package delivered, total distance 14.14, efficiency 14.14
- **Best Agent**: `A3` (efficiency: 14.14)

Automated tests in `tests/test_bonus.py` (`TestRegressionDefaultMode`) continuously assert that enabling bonus features like delays does not mutate total distance, package counts, or efficiency scores.

---

## 16. Dependencies

**No third-party Python packages are required.**

The application is written entirely using the Python Standard Library:
- `math`: Coordinate geometry and distance computation (`math.hypot`).
- `json`: Data parsing and formatted report generation.
- `csv`: Top performer tabular data export.
- `random`: Reproducible stochastic delay modeling.
- `argparse`: Command-line interface argument parsing.
- `dataclasses`: Strongly-typed internal data modeling.
- `pathlib`: Operating-system agnostic filesystem operations.
- `unittest`: Automated unit and integration testing suite.

### Requirements File
The repository includes a `requirements.txt` file documenting Python 3.8+ compatibility and verifying that no third-party packages need to be installed.

---

## 17. Output

The primary artifact generated is `report.json` in the project root:

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

When `--export-csv` is passed, the simulator additionally writes `reports/top_performer.csv`:

```csv
agent_id,packages_delivered,total_distance,efficiency
A3,1,14.14,14.14
```

---

## 18. Quick Start

Get up and running in five steps:

1. **Verify Python Installation**:
   ```bash
   python --version
   # Requires Python 3.8 or higher
   ```

2. **Navigate to the Repository**:
   ```bash
   cd nexgensis-python-assignment
   ```

3. **Run the Simulation**:
   ```bash
   python main.py data/base_case.json
   ```

4. **Review the Generated Report**:
   ```bash
   # Linux / macOS
   cat report.json

   # Windows PowerShell
   Get-Content report.json
   ```

5. **Run the Automated Test Suite**:
   ```bash
   python -m unittest discover -s tests -v
   ```
