"""Terminal visualization for the Fly-in simulation."""

from .models import Drone, Network


class Visualizer:
    """Display the drone simulation in the terminal."""

    RESET = "\033[0m"

    def __init__(self, network: Network) -> None:
        """Initialize the visualizer."""
        self.network = network

    def display_turn(
        self,
        turn: int,
        movements: list[str],
    ) -> None:
        """Display the movements made during one turn."""
        print(f"\nTurn {turn}:")

        if not movements:
            print("  No movement")
            return

        for movement in movements:
            print(f"  {self._colorize_movement(movement)}")

    def display_drones(
        self,
        drones: list[Drone],
    ) -> None:
        """Display the final position of all drones."""
        print("\nFinal positions:")

        for drone in drones:
            if drone.current_zone is None:
                continue

            zone_name = drone.current_zone.name
            color = drone.current_zone.color

            print(
                f"  D{drone.drone_id} -> "
                f"{self._colorize(zone_name, color)}"
            )

    def _colorize_movement(self, movement: str) -> str:
        """Color a movement according to its destination zone."""
        parts = movement.split("-", 1)

        if len(parts) != 2:
            return movement

        zone_name = parts[1]
        zone = self.network.zones.get(zone_name)

        if zone is None:
            return movement

        return (
            f"D{parts[0][1:]}-"
            f"{self._colorize(zone_name, zone.color)}"
        )

    def _colorize(
        self,
        text: str,
        color_name: str,
    ) -> str:
        """Return text with an ANSI terminal color."""
        color_codes = {
            "black": "\033[30m",
            "red": "\033[31m",
            "green": "\033[32m",
            "yellow": "\033[33m",
            "blue": "\033[34m",
            "magenta": "\033[35m",
            "cyan": "\033[36m",
            "white": "\033[37m",
        }

        code = color_codes.get(
            color_name.lower(),
            "\033[37m",
        )

        return f"{code}{text}{self.RESET}"
