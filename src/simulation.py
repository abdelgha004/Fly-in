"""Simulation engine for the Fly-in drone routing system."""

from .models import Connection, Drone, Network, Zone
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

    def run(
        self,
    ) -> tuple[list[list[str]], list[dict[int, str]]]:
        """Run the simulation until all drones reach the end.

        Returns:
            (movements per turn, position snapshot per turn).
        """
        self.scheduler.prepare_drones(self.drones)

        output: list[list[str]] = []
        states: list[dict[int, str]] = [self._snapshot()]

        while not self._all_delivered():
            self.turn += 1
            movements = self._process_turn()
            if movements:
                output.append(movements)
            states.append(self._snapshot())

        return output, states

    def _snapshot(self) -> dict[int, str]:
        """Capture the current position of every drone."""
        snap: dict[int, str] = {}
        for drone in self.drones:
            if drone.in_transit:
                origin = drone.current_zone.name
                dest = drone.transit_destination
                dest_name = dest.name if dest is not None else "?"
                snap[drone.drone_id] = f"{origin}-{dest_name}"
            else:
                snap[drone.drone_id] = drone.current_zone.name
        return snap

    def _process_turn(self) -> list[str]:
        """Process one simulation turn."""
        movements: list[str] = []
        just_arrived: set[int] = set()

        for drone in self.drones:
            if drone.in_transit:
                self._complete_transit(drone)
                just_arrived.add(drone.drone_id)
                movements.append(
                    f"D{drone.drone_id}-{drone.current_zone.name}"
                )

        occupancy: dict[str, int] = {
            name: len(zone.drones)
            for name, zone in self.network.zones.items()
        }
        reserved: dict[str, int] = {}
        leaving: dict[str, int] = {}
        arriving: dict[str, int] = {}
        link_use: dict[str, int] = {}

        planned_normal: list[tuple[Drone, Zone, Zone]] = []
        planned_restricted: list[
            tuple[Drone, Zone, Zone, Connection]
        ] = []

        for drone in self.drones:
            if drone.is_finished() or drone.in_transit:
                continue
            if drone.drone_id in just_arrived:
                continue

            current = drone.current_zone
            nxt = self.scheduler.get_next_zone(drone)
            if nxt is None:
                continue

            conn = self.network.get_connection(current, nxt)
            if conn is None:
                continue

            if (
                len(conn.drones) + link_use.get(conn.name, 0)
                >= conn.max_link_capacity
            ):
                continue

            if not nxt.is_start and not nxt.is_end:
                projected = (
                    occupancy.get(nxt.name, 0)
                    - leaving.get(nxt.name, 0)
                    + arriving.get(nxt.name, 0)
                    + reserved.get(nxt.name, 0)
                )
                if projected >= nxt.max_drones:
                    continue

            leaving[current.name] = leaving.get(current.name, 0) + 1
            link_use[conn.name] = link_use.get(conn.name, 0) + 1

            if nxt.zone_type == "restricted":
                planned_restricted.append((drone, current, nxt, conn))
                reserved[nxt.name] = reserved.get(nxt.name, 0) + 1
            else:
                planned_normal.append((drone, current, nxt))
                arriving[nxt.name] = arriving.get(nxt.name, 0) + 1

        for drone, current, nxt in planned_normal:
            current.remove_drone(drone)
            nxt.add_drone(drone)
            drone.move_to(nxt)
            if self.network.end_zone is not None:
                if nxt == self.network.end_zone:
                    drone.delivered = True
            movements.append(f"D{drone.drone_id}-{nxt.name}")

        for drone, current, nxt, conn in planned_restricted:
            current.remove_drone(drone)
            conn.add_drone(drone)
            drone.in_transit = True
            drone.transit_connection = conn
            drone.transit_destination = nxt
            movements.append(
                f"D{drone.drone_id}-{current.name}-{nxt.name}"
            )

        return movements

    def _complete_transit(self, drone: Drone) -> None:
        """Finish a restricted transit — drone arrives at destination."""
        conn = drone.transit_connection
        nxt = drone.transit_destination
        if conn is None or nxt is None:
            raise ValueError("invalid transit state")

        conn.remove_drone(drone)
        nxt.add_drone(drone)
        drone.current_zone = nxt
        drone.path_index += 1
        drone.in_transit = False
        drone.transit_connection = None
        drone.transit_destination = None

        if self.network.end_zone is not None:
            if nxt == self.network.end_zone:
                drone.delivered = True

    def _all_delivered(self) -> bool:
        """Check whether every drone reached the end."""
        for drone in self.drones:
            if not drone.is_finished():
                return False
        return True
