*This project has been created as part of the 42 curriculum by aakourya.*

# Fly-in

## Description

**Fly-in** is a drone routing and simulation project developed as part of the 42 curriculum.

The goal of the project is to design a system capable of routing multiple drones through a network of connected zones while respecting movement constraints and minimizing the number of simulation turns.

The map is represented as a graph:

* **Zones** are the nodes of the graph.
* **Connections** are the edges between zones.
* **Drones** move from a start zone to an end zone.
* Zones may have different types, capacities, and movement costs.
* Connections may have limited capacities.
* Several drones may need to share the same routes while avoiding conflicts.

The project is implemented in Python and follows an object-oriented design. It is divided into several components responsible for parsing maps, representing the network, finding paths, scheduling drones, running the simulation, and displaying the results.

### Main goals

The implementation focuses on:

* Parsing and validating map files.
* Representing the map as a custom graph.
* Finding efficient paths between the start and end zones.
* Assigning paths to multiple drones.
* Respecting zone capacity constraints.
* Respecting connection capacity constraints.
* Handling restricted zones with additional movement cost.
* Resolving conflicts between drones.
* Simulating the movement of all drones turn by turn.
* Producing the required output format.
* Providing an optional terminal visualization.

---

## Project Structure

```text
src/
├── __init__.py
├── __main__.py
├── models.py
├── parser.py
├── graph.py
├── pathfinding.py
├── scheduler.py
├── simulation.py
└── visualization.py
```

### `models.py`

Contains the main data structures:

* `Zone`
* `Connection`
* `Drone`
* `Network`
* `SimulationState`

These classes represent the state of the map and the drones during the simulation.

### `parser.py`

Responsible for reading map files and validating their contents.

It handles:

* Number of drones.
* Start and end zones.
* Zone definitions.
* Connections.
* Zone metadata.
* Connection capacity metadata.
* Invalid input and malformed maps.

### `graph.py`

Provides graph-related operations such as:

* Finding neighboring zones.
* Checking whether two zones are connected.
* Finding connections.
* Checking whether a zone can be entered.
* Calculating movement costs.

The project uses its own graph representation rather than an external graph library.

### `pathfinding.py`

Responsible for finding routes between the start and end zones.

The pathfinding system takes movement costs and blocked zones into account and can generate several candidate paths.

### `scheduler.py`

Assigns paths to drones and determines the next zone each drone should attempt to enter.

Several candidate paths can be distributed between drones to reduce conflicts and improve overall throughput.

### `simulation.py`

Runs the actual turn-by-turn simulation.

It handles:

* Drone movement.
* Zone occupancy.
* Connection capacity.
* Restricted-zone movement.
* Conflict resolution.
* Transit between zones.
* Delivery detection.
* Simulation termination.

### `visualization.py`

Produces the terminal output required by the project and also provides an optional visual mode with colored zones and turn-by-turn movement information.

---

# Instructions

## Requirements

The project requires:

* Python 3.10+
* `uv`

## Installation

Clone the repository and enter the project directory:

```bash
git clone <repository-url>
cd fly-in
```

Install the project dependencies:

```bash
make install
```

or:

```bash
uv sync
```

## Running the program

The program expects one map file:

```bash
uv run python -m src <map_file>
```

For example:

```bash
uv run python -m src maps/easy/01_linear_path.txt
```

The Makefile also provides a convenient default command:

```bash
make run
```

The default map can be changed with:

```bash
make run FILE=maps/medium/01_dead_end_trap.txt
```

## Debugging

The project provides a debugging command:

```bash
make debug FILE=maps/easy/01_linear_path.txt
```

## Visual mode

An optional terminal visualization can be enabled with:

```bash
uv run python -m src maps/easy/01_linear_path.txt --visual
```

or:

```bash
make visual FILE=maps/easy/01_linear_path.txt
```

## Code quality

The project can be checked with:

```bash
make lint
```

This runs:

* `flake8`
* `mypy`

A stricter check is also available:

```bash
make lint-strict
```

## Cleaning generated files

To remove Python cache and type-checking files:

```bash
make clean
```

---

# Algorithm and Implementation Strategy

## 1. Map representation

The map is represented as a graph.

Each zone is stored as a `Zone` object and each connection is represented by a `Connection` object.

The `Network` class maintains:

* A dictionary of zones.
* A dictionary of connections.
* An adjacency structure for efficient neighbor lookup.
* References to the start and end zones.

Connections are bidirectional, so a drone can theoretically move in either direction along a connection.

---

## 2. Pathfinding

The pathfinding system searches for routes from the start zone to the end zone.

Movement is not always equally expensive. For example, restricted zones have a higher movement cost than normal zones.

The pathfinding algorithm therefore uses weighted graph traversal rather than treating every zone as identical.

The main rules are:

* Blocked zones cannot be used.
* Normal zones have a movement cost of `1`.
* Restricted zones have a movement cost of `2`.
* The algorithm keeps track of the best known cost for reaching each zone.
* Candidate paths are generated so that multiple drones can use different routes when possible.

This allows the scheduler to distribute drones across several possible routes instead of forcing every drone onto the exact same path.

---

## 3. Multiple candidate paths

The scheduler requests several candidate paths from the pathfinder.

The number of requested paths is limited according to the number of drones:

```python
k = max(1, min(4, len(drones)))
```

This means that the implementation considers up to four candidate routes.

The scheduler then distributes these paths between drones.

For example, if four paths are available:

```text
Drone 1 -> Path 1
Drone 2 -> Path 2
Drone 3 -> Path 3
Drone 4 -> Path 4
Drone 5 -> Path 1
...
```

This helps reduce congestion on maps where several routes are available.

---

## 4. Zone capacity

Zones can have a maximum number of drones that may occupy them.

Before a drone enters a zone, the simulation checks its current and projected occupancy.

The simulation considers:

* Drones currently inside the zone.
* Drones leaving the zone during the current turn.
* Drones arriving during the current turn.
* Drones already reserved for the zone.

This prevents several drones from incorrectly entering a zone whose capacity has already been reached.

Start and end zones are treated specially and are not restricted by normal zone capacity rules.

---

## 5. Connection capacity

Connections can also have a maximum capacity.

Before a drone uses a connection, the simulation checks:

```text
current connection usage
+
planned usage during the current turn
```

If the connection is already full, the drone waits and tries again during a later turn.

This prevents multiple drones from exceeding the capacity of a connection.

---

## 6. Restricted zones

Restricted zones have a higher movement cost and require special handling during the simulation.

Instead of treating their movement exactly like a normal zone transition, the implementation models the movement as a transit.

When a drone starts a restricted transition:

```text
D1-zone_a-zone_b
```

the drone enters a transit state.

The transition is completed on the following turn:

```text
D1-zone_b
```

This allows restricted movement to take an additional simulation turn while keeping track of the connection being used.

---

## 7. Turn-based simulation

The simulation is performed one turn at a time.

For every turn, the simulation:

1. Completes restricted transits from the previous turn.
2. Calculates current zone occupancy.
3. Checks which drones are ready to move.
4. Determines each drone's next zone.
5. Checks connection capacity.
6. Checks destination-zone capacity.
7. Reserves valid movements.
8. Executes normal movements.
9. Starts restricted movements.
10. Continues until every drone reaches the destination.

Planning movements before executing them is important because it allows the simulation to reason about several drones during the same turn.

For example, if one drone leaves a zone during a turn, another drone may be able to enter that zone during the same turn if the capacity rules allow it.

---

## 8. Conflict resolution

When several drones want to use the same resource, the simulation checks the resource's capacity before allowing the movement.

For zones:

```text
current occupancy
- leaving drones
+ arriving drones
+ reserved drones
```

is used to calculate the projected occupancy.

For connections, current usage and planned usage are checked against the connection capacity.

If a movement cannot be performed safely, that drone simply waits for a later turn.

This prevents invalid states such as:

* More drones than a zone can contain.
* More drones than a connection can support.
* A drone occupying two zones simultaneously.
* A connection being used beyond its capacity.

---

## 9. Simulation termination

The simulation stops when every drone has reached the end of its assigned path.

Each drone keeps track of its current position in its path using `path_index`.

A drone is considered finished when:

```text
path_index >= len(path) - 1
```

The simulation repeatedly checks all drones and terminates only when all of them are finished.

---

# Visual Representation

The project provides an optional terminal visualization using:

```bash
uv run python -m src <map_file> --visual
```

The visualization displays the simulation turn by turn.

Example:

```text
Turn 1:
  D1-waypoint1
  D2-waypoint1

Turn 2:
  D1-waypoint2
  D2-waypoint2

Final positions:
  D1 -> goal
  D2 -> goal
```

When zone colors are defined in the map, the visualizer uses ANSI terminal colors to display destinations using their configured colors.

The visualization helps the user:

* Follow the movement of each drone.
* Understand how many turns the simulation requires.
* See where drones finish.
* Quickly identify different zones.
* Better understand the behavior of the routing algorithm.

The normal output remains available separately so that the visualization does not interfere with the required project output.

---

# Example

## Input

Example map:

```text
2
##start
start 0 0
waypoint1 1 0
waypoint2 2 0
##end
goal 3 0
start-waypoint1
waypoint1-waypoint2
waypoint2-goal
```

This map contains:

* 2 drones.
* One start zone.
* Two intermediate zones.
* One destination zone.
* A linear route from start to goal.

## Command

```bash
uv run python -m src maps/easy/01_linear_path.txt
```

## Expected output

```text
D1-waypoint1
D1-waypoint2 D2-waypoint1
D1-goal D2-waypoint2
D2-goal
```

Each line represents one simulation turn.

For example:

```text
D1-waypoint1
```

means that Drone 1 moved to `waypoint1` during that turn.

---

# Performance

The implementation was tested against the provided easy, medium, and hard benchmark maps.

The following results were obtained:

| Category   | Map                | Turns |
| ---------- | ------------------ | ----: |
| Easy       | Linear path        |     4 |
| Easy       | Simple fork        |     4 |
| Easy       | Basic capacity     |     4 |
| Medium     | Dead end trap      |     8 |
| Medium     | Circular loop      |    17 |
| Medium     | Priority puzzle    |     6 |
| Hard       | Maze nightmare     |    14 |
| Hard       | Capacity hell      |    16 |
| Hard       | Ultimate challenge |    25 |
| Challenger | Impossible Dream   |    45 |

The implementation successfully handles the provided benchmark maps and remains within the mandatory performance requirements.

---

# Technical Choices

## Python and Object-Oriented Design

The project uses Python classes to separate responsibilities.

The main objects are:

```text
Network
 ├── Zone
 └── Connection

Drone
 └── path / current state

Graph
 └── graph operations

PathFinder
 └── route calculation

Scheduler
 └── path assignment

Simulation
 └── turn execution

Visualizer
 └── output
```

This separation makes the implementation easier to test, understand, and maintain.

## Custom Graph Implementation

No external graph library is used.

The project implements its own graph representation using dictionaries and adjacency lists.

This keeps the implementation lightweight and gives direct control over:

* Neighbor lookup.
* Connections.
* Movement costs.
* Capacity rules.
* Pathfinding behavior.

---

# Resources

The following resources were used to understand the concepts required by the project:

* Python documentation — classes, dataclasses, type hints, collections, and standard library functionality.
* Python `heapq` documentation — priority queues used by the pathfinding implementation.
* Python `dataclasses` documentation — used to model zones, connections, drones, and network state.
* Graph theory and shortest-path algorithm references — used to understand weighted graphs and shortest-path search.
* Dijkstra's algorithm references — used to understand weighted shortest-path traversal.
* 42 project subject and correction guidelines — used to understand the required map format, simulation rules, and expected behavior.

## AI Usage

AI tools were used as a learning and development assistant during the project.

AI was used for:

* Understanding the project subject and breaking the requirements into smaller tasks.
* Explaining graph concepts and pathfinding algorithms.
* Understanding Python type hints and dataclasses.
* Reviewing code structure and identifying potential bugs.
* Helping analyze simulation behavior and benchmark results.
* Suggesting debugging approaches and test cases.
* Improving code readability and organization.
* Reviewing the README structure against the project requirements.

The final implementation, testing, debugging, and integration were performed by the project author.

AI was not used as a replacement for understanding the project. Its role was primarily to explain concepts, help investigate problems, and provide development feedback.

---

# Testing

The project was tested using:

* Easy maps.
* Medium maps.
* Hard maps.
* Edge cases.
* Invalid input cases.
* Capacity constraints.
* Restricted zones.
* Multiple drones.
* Multiple candidate paths.
* Performance benchmarks.

Static analysis was also performed with:

```bash
make lint
```

including:

```bash
flake8
mypy
```

The project passes the type-checking stage with no reported mypy errors.

---

# Author

**aakourya**

42 Network — Rabat
