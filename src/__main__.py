"""Entry point for the Fly-in application."""

import sys

from .graph import Graph
from .models import Drone, Zone
from .parser import MapParser
from .pathfinding import PathFinder
from .scheduler import Scheduler
from .simulation import Simulation
from .visualization import Visualizer


def main() -> None:
    """Run the Fly-in application."""
    args = [a for a in sys.argv[1:] if a != "--visual"]
    visual = "--visual" in sys.argv

    if len(args) != 1:
        print("Usage: python -m src <map_file> [--visual]")
        return

    filename = args[0]

    try:
        parser = MapParser()
        network = parser.parse(filename)

        start_zone = network.start_zone
        if start_zone is None:
            raise ValueError("missing start zone")

        graph = Graph(network)
        pathfinder = PathFinder(graph)
        scheduler = Scheduler(network, pathfinder)

        drones = _create_drones(parser.nb_drones, start_zone)

        simulation = Simulation(network, drones, scheduler)
        visualizer = Visualizer(network)

        results = simulation.run()

        if visual:
            visualizer.emit_visual_output(results, drones)
        else:
            visualizer.emit_required_output(results)

    except (OSError, ValueError) as error:
        print(f"Error: {error}")


def _create_drones(
    number_of_drones: int,
    start_zone: Zone,
) -> list[Drone]:
    """Create all drones at the start zone."""
    drones: list[Drone] = []

    for drone_id in range(1, number_of_drones + 1):
        drone = Drone(drone_id=drone_id, current_zone=start_zone)
        start_zone.add_drone(drone)
        drones.append(drone)

    return drones


if __name__ == "__main__":
    main()
