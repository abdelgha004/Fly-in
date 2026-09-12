"""Entry point for the Fly-in application."""

import sys

from .graph import Graph
from .parser import MapParser
from .pathfinding import PathFinder
from .models import Drone
from .scheduler import Scheduler
from .simulation import Simulation
from .visualization import Visualizer


def main() -> None:
    """Run the Fly-in application."""
    if len(sys.argv) != 2:
        print("Usage: python -m src <map_file>")
        return

    filename = sys.argv[1]

    try:
        parser = MapParser()
        network = parser.parse(filename)

        if network.start_zone is None:
            raise ValueError("missing start zone")

        graph = Graph(network)
        pathfinder = PathFinder(graph)
        scheduler = Scheduler(network, pathfinder)

        drones = _create_drones(
            parser.nb_drones,
            network.start_zone,
        )

        simulation = Simulation(
            network,
            drones,
            scheduler,
        )

        visualizer = Visualizer(network)

        results = simulation.run()

        for turn, movements in enumerate(results, start=1):
            visualizer.display_turn(
                turn,
                movements,
            )

        visualizer.display_drones(drones)

    except (OSError, ValueError) as error:
        print(f"Error: {error}")


def _create_drones(
    number_of_drones: int,
    start_zone: object,
) -> list[Drone]:
    """Create all drones at the start zone."""
    drones: list[Drone] = []

    for drone_id in range(1, number_of_drones + 1):
        drone = Drone(
            drone_id=drone_id,
            current_zone=start_zone,
        )
        start_zone.add_drone(drone)
        drones.append(drone)

    return drones


if __name__ == "__main__":
    main()
