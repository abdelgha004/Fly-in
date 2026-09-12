"""Terminal visualization for the Fly-in simulation."""

from .models import Drone, Network


class Visualizer:
    """Display the drone simulation in the terminal."""

    RESET = "\033[0m"
    BOLD = "\033[1m"

    def __init__(self, network: Network) -> None:
        """Initialize the visualizer."""
        self.network = network

    def emit_required_output(
        self,
        results: list[list[str]],
    ) -> None:
        """Print simulation in the exact format required by the subject."""
        for movements in results:
            print(" ".join(movements))

    def emit_visual_output(
        self,
        results: list[list[str]],
        drones: list[Drone],
    ) -> None:
        """Print a colored turn-by-turn visualization."""
        for turn, movements in enumerate(results, start=1):
            print(f"\n{self.BOLD}Turn {turn}:{self.RESET}")
            if not movements:
                print("  (no movement)")
            else:
                for movement in movements:
                    print(f"  {self._colorize_movement(movement)}")

        print(f"\n{self.BOLD}Final positions:{self.RESET}")
        for drone in drones:
            zone = drone.current_zone
            print(
                f"  D{drone.drone_id} -> "
                f"{self._colorize(zone.name, zone.color)}"
            )

    def _colorize_movement(self, movement: str) -> str:
        """Color a movement string according to its destination zone."""
        parts = movement.split("-")

        if len(parts) == 2:
            drone_id, zone_name = parts
            zone = self.network.zones.get(zone_name)
            if zone is None:
                return movement
            return (
                f"{drone_id}-"
                f"{self._colorize(zone_name, zone.color)}"
            )

        if len(parts) == 3:
            drone_id, origin_name, dest_name = parts
            dest = self.network.zones.get(dest_name)
            color = dest.color if dest is not None else None
            return (
                f"{drone_id}-{origin_name}-"
                f"{self._colorize(dest_name, color)}"
            )

        return movement

    def _colorize(
        self,
        text: str,
        color_name: str | None,
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
            "gray": "\033[90m",
            "grey": "\033[90m",
            "orange": "\033[38;5;208m",
            "purple": "\033[38;5;93m",
            "gold": "\033[38;5;220m",
            "crimson": "\033[38;5;161m",
            "maroon": "\033[38;5;88m",
        }

        if color_name is None:
            return text

        code = color_codes.get(color_name.lower(), "\033[37m")
        return f"{code}{text}{self.RESET}"
