cat > ~/Desktop/Fly-in/README.md << 'ENDOFREADME'
*This project has been created as part of the 42 curriculum by aakourya.*

# Fly-in

## Description

Fly-in is a drone routing simulation. Given a network of connected zones,
a fleet of drones and a set of movement constraints, the program computes
a set of routes that moves every drone from the start hub to the end hub
in the fewest possible simulation turns.

The simulation runs in discrete turns. At each turn every drone may move
to an adjacent zone, start a two-turn flight toward a restricted zone, or
wait. Zone capacities (`max_drones`) and connection capacities
(`max_link_capacity`) are respected at every turn, including the rule that
drones leaving a zone free its space for the same turn.

## Instructions

Requirements:
- Python 3.10 or later
- `uv` (https://docs.astral.sh/uv/)

Install dependencies:

    make install

Run the simulation on a map:

    make run FILE=maps/easy/01_linear_path.txt
    uv run python -m src maps/easy/01_linear_path.txt

Run with the colored visualization:

    make visual FILE=maps/easy/02_simple_fork.txt
    uv run python -m src maps/easy/02_simple_fork.txt --visual

Debug:

    make debug FILE=maps/easy/01_linear_path.txt

Lint:

    make lint

Clean caches:

    make clean

## Algorithm

1. Parsing — the map file is read line by line. Zones, metadata,
   connections and capacities are validated. Any error stops the program
   with a message that includes the offending line number.

2. Pathfinding — a bounded k-shortest-paths search runs from the start
   hub to the end hub. The cost of entering a zone is 1 for normal or
   priority zones and 2 for restricted zones. Blocked zones are skipped.
   Priority zones are preferred when path costs tie. The search returns up
   to k = min(4, number_of_drones) simple paths.

3. Distribution — the scheduler assigns drones to paths in round-robin
   order so multiple routes are used simultaneously.

4. Simulation — at each turn the engine plans moves with a per-turn
   occupancy ledger. For every candidate move it checks:
   - link capacity (drones_on_link + planned_uses < max_link_capacity);
   - destination zone capacity
     (occupancy - leaving + arriving + reserved < max_drones),
     skipped for start and end hubs.

   Accepted moves are executed simultaneously. Drones entering a restricted
   zone start a two-turn transit: on the first turn they occupy the
   connection and appear in the output as D1-A-B; on the next turn they
   arrive and appear as D1-B. A drone cannot wait on a connection.

5. Output — one line per turn, space-separated, in the exact format
   required by the subject.

Complexity: the k-shortest-paths search is O(k * (V + E) * log V). Each
simulation turn is O(D * E) where D is the number of drones. Paths are
computed once before the simulation and cached for the whole run.

## Visual representation

Running with --visual prints every turn as a numbered block. Zone names
are colored using the color metadata declared in the map file, so a user
can immediately see which zone each drone is heading to. Restricted-zone
transits are shown as origin-destination to make the two-turn movement
visible. A final panel lists the last position of every drone.

## Example

Input (maps/easy/01_linear_path.txt):

    nb_drones: 2

    start_hub: start 0 0 [color=green]
    hub: waypoint1 1 0 [color=blue]
    hub: waypoint2 2 0 [color=blue]
    end_hub: goal 3 0 [color=red]

    connection: start-waypoint1
    connection: waypoint1-waypoint2
    connection: waypoint2-goal

Expected output:

    D1-waypoint1
    D1-waypoint2 D2-waypoint1
    D1-goal D2-waypoint2
    D2-goal

## Resources

- Subject: Fly-in v1.6
- PEP 257 docstring conventions: https://peps.python.org/pep-0257/
- Python heapq documentation: https://docs.python.org/3/library/heapq.html
- Dijkstra and k-shortest-paths background:
  https://en.wikipedia.org/wiki/K_shortest_path_routing
- uv documentation: https://docs.astral.sh/uv/

AI usage: AI was used to review the parser design, to suggest the
per-turn occupancy accounting and to help structure this README. All code
was written, tested and validated against the maps provided in the subject.
ENDOFREADME