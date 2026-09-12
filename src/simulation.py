"""Simulation engine for the Fly-in drone routing system."""

from .models import Drone, Network
from .scheduler import Scheduler


class Simulation:
    """Run the drone simulation turn by turn."""

    def __init__(
        self,
        network: Network,
        drones: list[Drone],
        scheduler: Scheduler,
    ) -> None:
        """Initialize the simulation."""
        self.network = network
        self.drones = drones
        self.scheduler = scheduler
        self.turn = 0

    def run(self) -> list[list[str]]:
        """Run the simulation until all drones reach the end."""
        self.scheduler.prepare_drones(self.drones)

        output: list[list[str]] = []

        while not self._all_delivered():
            self.turn += 1

            movements = self._process_turn()

            if movements:
                output.append(movements)

        return output

    def _process_turn(self) -> list[str]:
        """Process one simulation turn."""
        movements: list[str] = []
        planned: list[tuple[Drone, object, object]] = []

        for drone in self.drones:
            if drone.is_finished():
                continue

            move = self.scheduler.choose_move(drone)

            if move is None:
                continue

            current_zone, next_zone = move

            if self._already_planned_for_zone(
                planned,
                next_zone,
            ):
                continue

            planned.append(
                (
                    drone,
                    current_zone,
                    next_zone,
                )
            )

        for drone, current_zone, next_zone in planned:
            if not self._can_execute_move(
                drone,
                current_zone,
                next_zone,
            ):
                continue

            self._move_drone(
                drone,
                current_zone,
                next_zone,
            )

            movements.append(
                f"D{drone.drone_id}-{next_zone.name}"
            )

        return movements

    def _can_execute_move(
        self,
        drone: Drone,
        current_zone: object,
        next_zone: object,
    ) -> bool:
        """Check whether a planned movement can be executed."""
        if not next_zone.can_enter(drone):
            return False

        connection = self.scheduler.pathfinder.graph.get_connection(
            current_zone,
            next_zone,
        )

        if connection is None:
            return False

        if not connection.can_enter(drone):
            return False

        return True

    def _move_drone(
        self,
        drone: Drone,
        current_zone: object,
        next_zone: object,
    ) -> None:
        """Move a drone from one zone to another."""
        current_zone.remove_drone(drone)
        next_zone.add_drone(drone)

        drone.move_to(next_zone)

        if drone.is_finished():
            drone.delivered = True

    def _already_planned_for_zone(
        self,
        planned: list[tuple[Drone, object, object]],
        next_zone: object,
    ) -> bool:
        """Check whether another drone targets the same zone."""
        for _, _, target_zone in planned:
            if target_zone == next_zone:
                return True

        return False

    def _all_delivered(self) -> bool:
        """Check whether every drone reached the end."""
        for drone in self.drones:
            if not drone.is_finished():
                return False

        return True
