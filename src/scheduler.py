"""Drone scheduling for the Fly-in simulation."""

from .models import Drone, Network, Zone
from .pathfinding import PathFinder


class Scheduler:
    """Schedule drone movements through the network."""

    def __init__(
        self,
        network: Network,
        pathfinder: PathFinder,
    ) -> None:
        """Initialize the scheduler."""
        self.network = network
        self.pathfinder = pathfinder

    def prepare_drones(self, drones: list[Drone]) -> None:
        """Calculate a path for every drone."""
        if self.network.start_zone is None:
            raise ValueError("network has no start zone")

        if self.network.end_zone is None:
            raise ValueError("network has no end zone")

        for drone in drones:
            path = self.pathfinder.find_path(
                self.network.start_zone,
                self.network.end_zone,
            )

            if not path:
                raise ValueError(
                    f"no path found for drone {drone.drone_id}"
                )

            drone.path = path
            drone.path_index = 0

    def get_next_zone(self, drone: Drone) -> Zone | None:
        """Return the next zone on a drone's path."""
        if drone.is_finished():
            return None

        if drone.path_index + 1 >= len(drone.path):
            return None

        return drone.path[drone.path_index + 1]

    def can_move(
        self,
        drone: Drone,
        current_zone: Zone,
        next_zone: Zone,
    ) -> bool:
        """Check whether a drone can move to the next zone."""
        if next_zone.zone_type == "blocked":
            return False

        if not next_zone.can_enter(drone):
            return False

        connection = self.pathfinder.graph.get_connection(
            current_zone,
            next_zone,
        )

        if connection is None:
            return False

        if not connection.can_enter(drone):
            return False

        return True

    def choose_move(
        self,
        drone: Drone,
    ) -> tuple[Zone, Zone] | None:
        """Return the current and next zones for a drone."""
        if drone.current_zone is None:
            return None

        next_zone = self.get_next_zone(drone)

        if next_zone is None:
            return None

        if not self.can_move(
            drone,
            drone.current_zone,
            next_zone,
        ):
            return None

        return drone.current_zone, next_zone
