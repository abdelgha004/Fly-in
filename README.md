*This project has been created as part of the 42 curriculum by aakourya.*

# Fly-in

## Description

Fly-in is a drone routing and scheduling simulator. The goal is to model a network of connected zones, assign a fleet of drones to valid routes, and simulate their movement while respecting the constraints of the map.

The program reads a map file describing zones, links, capacities, and drone count. It then computes candidate paths from the start hub to the end hub, schedules the drones, and simulates their movements turn by turn. Every movement must respect zone capacity, connection capacity, and the special two-turn behavior used for restricted zones.

This project is designed to solve a classic graph-routing problem with a strong emphasis on real-time constraints and deterministic simulation. It is particularly suited to problems involving:

- multi-drone coordination,
- constrained graph traversal,
- path planning under capacity limits,
- turn-based simulation with simultaneous moves,
- graphical visualization for debugging and presentation.

## Project structure

- `src/__main__.py` — command-line entry point
- `src/parser.py` — parses and validates map files
- `src/models.py` — data structures for zones, connections, drones, and network state
- `src/graph.py` — graph topology and movement rules
- `src/pathfinding.py` — path generation and search logic
- `src/scheduler.py` — assignment of routes to drones
- `src/simulation.py` — turn-based simulation engine
- `src/visualization.py` — real-time pygame map view
- `maps/` — sample challenge maps

## Instructions

### Requirements

- Python 3.10 or newer
- `uv` for dependency management

### Installation

From the project root:

```bash
make install
```

This installs the project dependencies using `uv sync`.

### Running the simulator

Run the project on a map file:

```bash
make run FILE=maps/easy/01_linear_path.txt
```

Or directly with Python:

```bash
uv run python -m src maps/easy/01_linear_path.txt
```

### Visual mode

To open an interactive pygame window showing the map and drones turn by turn:

```bash
make visual FILE=maps/easy/02_simple_fork.txt
```

Or:

```bash
uv run python -m src maps/easy/02_simple_fork.txt --visual
```

Press `SPACE` to advance one turn, `ESC` to quit.

### Debugging and quality checks

```bash
make debug FILE=maps/easy/01_linear_path.txt
make lint
make clean
```

## Implementation strategy and algorithm choices

The implementation is organized around four major stages: parsing, path search, scheduling, and simulation.

### 1. Parsing and validation

The map parser reads the input file line by line and supports the required syntax:

- `nb_drones:`
- `start_hub:`
- `end_hub:`
- `hub:`
- `connection:`

Each zone definition may include optional metadata such as color and capacity. The parser validates:

- duplicate zone names,
- invalid coordinates,
- duplicate or malformed connections,
- missing start and end hubs,
- invalid `nb_drones` values,
- malformed metadata blocks.

This ensures that the simulation only runs on consistent maps.

### 2. Graph model and pathfinding

The network is represented as a graph where zones are nodes and links are edges. Each node can have a specific type:

- normal hub,
- start hub,
- end hub,
- restricted zone,
- blocked/invalid zone depending on the project rules.

The pathfinder uses a cost-aware search strategy to generate valid paths from the starting point to the destination. In this project, the cost of entering a zone depends on its type:

- normal zones cost 1,
- restricted zones cost 2.

The algorithm looks for a bounded set of low-cost simple paths, up to a fixed number of candidates, which is useful when several drones must be coordinated without all following the same route. This is a lightweight form of k-shortest-path planning and keeps the search practical even when multiple drones share a network.

### 3. Scheduler

Once paths are computed, the scheduler assigns each drone a path. The assignment is round-robin based to distribute traffic and avoid overloading one route. This means the fleet is not simply sent one after another; instead, all drones are coordinated to make use of multiple valid routes when available.

The scheduler also handles the fact that a drone must eventually arrive at the end hub while respecting the dynamic state of the environment.

### 4. Simulation engine

The simulation runs turn by turn. At each turn, the engine:

- completes any restricted-zone transit started in the previous turn,
- evaluates candidate moves for all drones that are ready to move,
- verifies current occupancy and connection capacity,
- reserves destination capacity for restricted-zone entries,
- executes legal moves simultaneously.

This logic is crucial because the system must respect all constraints at once, not sequentially. A move is only accepted if:

- the connection between current and next zone has free capacity,
- the destination zone has enough remaining capacity,
- the drone is not already in a transit state,
- the move is part of its planned path.

For restricted zones, the drone enters the connection first and remains in transit for one additional turn before arriving at the destination zone. This is handled explicitly in the simulation loop.

## Algorithm explanation

Pathfinding uses **Dijkstra's algorithm** (`PathFinder.find_path`), where
entering a normal zone costs `1` and a restricted zone costs `2`; blocked
zones are never expanded. To spread the fleet across multiple routes instead
of funneling every drone through one path, `find_k_paths` runs a bounded
best-first search that keeps popping cheapest partial paths off a heap until
it collects up to `k` complete simple paths within a small margin of the
optimal cost.

The **scheduler** assigns these k paths to drones round-robin
(`drone[i] → paths[i % k]`), so traffic is distributed rather than
serialized on a single link.

The **simulation** resolves each turn in two phases so moves happen
simultaneously rather than sequentially: first, drones that entered a
restricted-zone transit last turn complete their arrival; then, remaining
drones are evaluated against speculative occupancy/capacity counters before
any real state is mutated, so two drones can't over-book the same zone or
connection in one turn. Restricted-zone entries are deferred one extra turn
to model their higher cost.

## Visual representation features

The program includes a graphical visualizer, built with `pygame`, that can be activated with `--visual`.

### What the visualizer does

- lays out every zone on screen using the coordinates declared in the map file, and connects them with lines matching the map's topology,
- colors each zone according to its metadata, and labels it with its name plus a tag showing `START`, `END`, or its maximum drone capacity,
- draws each drone as a small circle labeled with its ID: a filled circle marks a drone that has landed at a zone, while a hollow ring marks a drone currently in transit along a connection (drawn at the connection's midpoint),
- shows a header bar with the current turn out of the total, and a live count of drones delivered to the end hub versus the total fleet size,
- advances one turn at a time on `SPACE`, so each step can be inspected before moving on.

### Why it improves the user experience

This mode is valuable both for debugging and for demonstration. A user can immediately see:

- which drones are landed versus mid-flight at any given turn,
- how close each zone is to its declared capacity,
- how many drones have reached the end hub so far,
- how traffic spreads (or bottlenecks) across the available routes,
- how the final state compares to the expected outcome.

Because the map file can declare colors for zones, the visualization becomes intuitive and helps the reader track flows visually, even in complex maps.

## Map format and example

The input map format is simple and structured. Example:

```text
nb_drones: 2

start_hub: start 0 0 [color=green]
hub: waypoint1 1 0 [color=blue]
hub: waypoint2 2 0 [color=blue]
end_hub: goal 3 0 [color=red]

connection: start-waypoint1
connection: waypoint1-waypoint2
connection: waypoint2-goal
```

### Example output

```text
D1-waypoint1
D1-waypoint2 D2-waypoint1
D1-goal D2-waypoint2
D2-goal
```

This example demonstrates that drones move simultaneously each turn and that the output format is composed of one line per round, with space-separated movements.

## Resources

### References

- Dijkstra's algorithm: https://en.wikipedia.org/wiki/Dijkstra%27s_algorithm
- K-shortest paths: https://en.wikipedia.org/wiki/K_shortest_path_routing

### AI usage

AI was used to support the project in several ways:

- reviewing the parser and validation strategy,
- helping structure the capacity-checking logic for simultaneous moves,
- suggesting ways to organize the scheduling and path assignment logic,
- improving the clarity and completeness of this README,
- helping debug edge cases in the simulation logic and output formatting.