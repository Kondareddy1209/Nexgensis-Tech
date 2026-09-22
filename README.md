# 🚚 FastBox Logistics Delivery Simulator

> **Nexgensis Technologies — Python Developer Take-Home Assignment**

---

## 🤔 What Does This Project Do?

Imagine you work at a **delivery company**. Every morning you have:

- 🏭 **Warehouses** — places where packages are stored
- 🧑 **Delivery Agents** — people who deliver the packages
- 📦 **Packages** — things that need to be delivered to customers

This program **figures out the smartest way** to assign packages to agents and then **simulates the delivery day** — tracking how far each agent travels and who does the best job.

At the end, it produces a **report** telling you:
- How many packages each agent delivered
- How far each agent traveled
- Who was the most **efficient** (did the most work with the least travel)

---

## 🗂️ Project Structure — What's Inside?

```
nexgensis-python-assignment/
│
├── 📄 main.py                  ← START HERE — the main program you run
│
├── 📁 simulator/               ← The engine that powers everything
│   ├── models.py               ← Defines what a Warehouse, Agent, Package looks like
│   ├── parser.py               ← Reads and checks the input JSON file
│   ├── distance.py             ← Calculates how far apart two places are
│   ├── dispatcher.py           ← Assigns each package to the nearest agent
│   ├── engine.py               ← Simulates the actual delivery journey
│   ├── reporter.py             ← Calculates scores and picks the best agent
│   │
│   ├── delay.py                ← ✨ BONUS: Adds random delivery delays
│   ├── visualizer.py           ← ✨ BONUS: Draws the routes as ASCII art
│   ├── midday.py               ← ✨ BONUS: Lets a new agent join halfway through
│   └── csv_exporter.py         ← ✨ BONUS: Saves the top agent to a CSV file
│
├── 📁 data/                    ← Input files (the delivery day data)
│   ├── base_case.json          ← The main test file
│   └── test_cases/             ← 10 more test files (test_case_1 to test_case_10)
│
├── 📁 tests/                   ← Automated checks to make sure everything works
│
├── 📄 report.json              ← The OUTPUT — results of the base case run
├── 📄 README.md                ← This file!
└── 📄 requirements.json        ← No extra libraries needed — just plain Python!
```

---

## 🔄 How It Works — Step by Step

Think of it like a **recipe**:

```
📂 Read the JSON file
        ↓
🔍 Check it for mistakes (wrong format? missing data?)
        ↓
📏 Measure distance from each agent to each warehouse
        ↓
🎯 Assign each package to the NEAREST agent
        ↓
🚶 Simulate the journey: Agent → Warehouse → Customer's door
        ↓
📊 Calculate: how far did each agent travel? how efficient were they?
        ↓
🏆 Pick the BEST agent (lowest distance per package)
        ↓
💾 Save results to report.json
```

---

## 📐 The Math — Kept Simple

### How is distance calculated?

We use **straight-line distance** (like a crow flies), also called **Euclidean distance**:

```
distance = √( (x2-x1)² + (y2-y1)² )
```

Same as the Pythagorean theorem you learned in school! 📐

### What is "efficiency"?

```
efficiency = total distance traveled ÷ number of packages delivered
```

**Lower efficiency = BETTER** (less distance per package = smarter routing)

So the agent with the **lowest efficiency score** is the **best agent**. 🏆

### Who gets which package?

Every package sits at a warehouse. We find which agent's **starting location** is **closest** to that warehouse — that agent gets all packages at that warehouse.

If two agents are equally close → we pick the one whose ID comes first alphabetically (`A1` beats `A2`).

---

## 🗃️ Input Format — What Does the JSON Look Like?

The program handles **two slightly different styles** of JSON automatically:

### Style 1 (used in test cases 1–10):
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

### Style 2 (used in base_case.json):
```json
{
  "warehouses": [{ "id": "W1", "location": [0, 0] }],
  "agents":     [{ "id": "A1", "location": [5, 5] }],
  "packages": [
    { "id": "P1", "warehouse_id": "W1", "destination": [30, 40] }
  ]
}
```

Both styles produce the same result. The program figures out which one you're using automatically.

---

## 📤 Output — What Does report.json Look Like?

After running the program, `report.json` is created/updated:

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

| Field | Meaning |
|-------|---------|
| `packages_delivered` | How many packages this agent delivered |
| `total_distance` | Total km/units traveled (rounded to 2 decimal places) |
| `efficiency` | Distance ÷ Packages (lower = better!) |
| `best_agent` | The winner 🏆 — agent with the lowest efficiency score |

---

## 🚀 How to Run It

### Step 1 — Make sure you have Python 3.8+
```bash
python --version
```

### Step 2 — No installation needed!
```bash
# No pip install required — this uses only Python's built-in libraries
```

### Step 3 — Run the simulator
```bash
# Run on the base case
python main.py data/base_case.json

# Run on any test case
python main.py data/test_cases/test_case_1.json

# Save the report to a custom file
python main.py data/base_case.json -o my_report.json
```

### What you'll see:
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

## ✨ Bonus Features

All bonus features are **optional extras** — the program works exactly the same without them.

---

### 🎲 Bonus 1 — Random Delivery Delays

Simulates real-world traffic delays for each package (1–30 minutes).
Delays are **just for show** — they don't change distances or scores.

```bash
# Random delays
python main.py data/base_case.json --delays

# Same delays every time (use a seed number)
python main.py data/base_case.json --delays --seed 42
```

Example output:
```
 Agent    Package     Delay (min)
 A1       P1                   21
 A1       P4                   24
 A2       P2                    4
 A3       P3                    1
```

---

### 🗺️ Bonus 2 — ASCII Route Map

Draws each agent's delivery route as a text diagram — AND shows a map!

```bash
python main.py data/base_case.json --visualize
```

Example output:
```
  A1: A1(5,5) -> W1(0,0) -> P1(30,40) -> W1(0,0) -> P4(10,10)
  A2: A2(60,60) -> W2(50,75) -> P2(70,90) -> W2(50,75) -> P5(40,80)
  A3: A3(95,30) -> W3(100,25) -> P3(105,20)
```

Plus a coordinate grid showing where everything is:
```
+------------------------------------------------------------+
|..A..........................................................|
|W............................................................|
+------------------------------------------------------------+
  Legend: A=Agent start  W=Warehouse  D=Destination
```

---

### 🧑‍🤝‍🧑 Bonus 3 — Mid-Day Agent Joining

A new delivery agent joins the team **partway through the day**.

- Packages already assigned **stay with their original agents** — no changes
- The new agent **only gets packages** that haven't been assigned yet

```bash
# Agent A5 starts at position (50, 50) and joins after 2 packages are dispatched
python main.py data/base_case.json --midday-agent A5 50 50 --midday-after 2

# Default: agent joins after half the packages are dispatched
python main.py data/base_case.json --midday-agent A5 50 50
```

---

### 📋 Bonus 4 — Export Top Performer to CSV

Saves the best agent's stats to a spreadsheet-friendly CSV file.

```bash
python main.py data/base_case.json --export-csv
```

Creates `reports/top_performer.csv`:
```
agent_id,packages_delivered,total_distance,efficiency
A3,1,14.14,14.14
```

Custom save location:
```bash
python main.py data/base_case.json --export-csv --csv-path results/winner.csv
```

---

### 🔀 Mix and Match Bonuses

All bonus flags work together:

```bash
python main.py data/base_case.json --delays --seed 42 --visualize --export-csv
```

---

## 🧪 Running the Tests

```bash
python -m unittest discover -s tests -v
```

Expected result:
```
Ran 63 tests in ~0.2s
OK
```

### What is tested?

| Test File | # Tests | What It Checks |
|-----------|---------|----------------|
| `test_distance.py` | 6 | Distance math is correct |
| `test_parser.py` | 8 | JSON files are read correctly |
| `test_dispatcher.py` | 4 | Packages go to the right agent |
| `test_engine.py` | 5 | Delivery routes are simulated correctly |
| `test_reporter.py` | 6 | Scores and best-agent are calculated correctly |
| `test_integration.py` | 1 | All 11 test datasets work end-to-end |
| `test_bonus.py` | 33 | All 4 bonus features work correctly |
| **Total** | **63** | **0 failures · 0 errors** |

The integration test also verifies **all 104 packages** across all 11 datasets are correctly assigned and delivered — not a single one is lost or duplicated.

---

## 🤝 Key Rules the Program Follows

| Rule | Why |
|------|-----|
| Distance uses initial agent position (not current) | Ensures consistent, fair assignment |
| Packages at the same warehouse always go to the same agent | Keeps routes simple |
| No return trips home after the last delivery | Matches real-world courier behavior |
| Tie in distance → pick agent with earlier ID (`A1` before `A2`) | Makes results deterministic |
| Idle agents (0 packages) score `0.0` and can't win | Prevents division-by-zero errors |
| Rounding only happens in the final report | Keeps math precise throughout |

---

## 🛡️ No API Keys. No Internet. No Setup.

| Requirement | Status |
|------------|--------|
| Python 3.8+ | ✅ Required |
| `pip install` anything | ❌ Not needed |
| Internet connection | ❌ Not needed |
| API keys or accounts | ❌ Not needed |
| Database | ❌ Not needed |

Everything uses Python's **built-in standard library**: `math`, `json`, `csv`, `random`, `pathlib`, `dataclasses`, `argparse`, `unittest`.

---

## 📬 Assignment Info

**Company:** Nexgensis Technologies
**Role:** Python Developer Intern
**Candidate:** Ambavaram Tirumala Konda Reddy
