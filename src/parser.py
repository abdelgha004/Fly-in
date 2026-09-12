"""Parser for Fly-in map files."""

import re
from pathlib import Path

from .models import Connection, Network, Zone


class MapParser:
    """Parse and validate a Fly-in map file."""

    def __init__(self) -> None:
        """Initialize the parser."""
        self.network = Network()
        self.nb_drones = 0

    def parse(self, filename: str) -> Network:
        """Parse a map file and return the resulting network."""
        try:
            lines = Path(filename).read_text(
                encoding="utf-8"
            ).splitlines()
        except OSError as error:
            raise ValueError(
                f"cannot read map file: {error}"
            ) from error

        for line_number, line in enumerate(lines, start=1):
            self._parse_line(line, line_number)

        self._validate_map()
        return self.network

    def _parse_line(self, line: str, line_number: int) -> None:
        """Parse one line of the map."""
        line = line.strip()

        if not line or line.startswith("#"):
            return

        if line.startswith("nb_drones:"):
            self._parse_nb_drones(line, line_number)
            return

        if line.startswith("start_hub:"):
            self._parse_zone(line, line_number, "start")
            return

        if line.startswith("end_hub:"):
            self._parse_zone(line, line_number, "end")
            return

        if line.startswith("hub:"):
            self._parse_zone(line, line_number, "normal")
            return

        if "-" in line:
            self._parse_connection(line, line_number)
            return

        self._error(line_number, "unknown line format")

    def _parse_nb_drones(
        self,
        line: str,
        line_number: int,
    ) -> None:
        """Parse the number of drones."""
        if self.nb_drones != 0:
            self._error(
                line_number,
                "nb_drones is defined more than once",
            )

        value = line[len("nb_drones:"):].strip()

        if not value.isdigit() or int(value) <= 0:
            self._error(
                line_number,
                "nb_drones must be a positive integer",
            )

        self.nb_drones = int(value)

    def _parse_zone(
        self,
        line: str,
        line_number: int,
        zone_kind: str,
    ) -> None:
        """Parse a start, end, or normal hub."""
        prefix = self._get_zone_prefix(line)
        content = line[len(prefix):].strip()
        parts = content.split()

        if len(parts) < 3:
            self._error(
                line_number,
                "zone must contain name, x and y",
            )

        name = parts[0]
        self._validate_zone_name(name, line_number)

        try:
            x = int(parts[1])
            y = int(parts[2])
        except ValueError:
            self._error(
                line_number,
                "zone coordinates must be integers",
            )

        if name in self.network.zones:
            self._error(
                line_number,
                f"duplicate zone name '{name}'",
            )

        metadata = self._parse_zone_metadata(
            parts[3:],
            line_number,
        )

        is_start = zone_kind == "start"
        is_end = zone_kind == "end"

        if is_start and self.network.start_zone is not None:
            self._error(
                line_number,
                "more than one start hub",
            )

        if is_end and self.network.end_zone is not None:
            self._error(
                line_number,
                "more than one end hub",
            )

        zone = Zone(
            name=name,
            x=x,
            y=y,
            zone_type=metadata["zone"],
            color=metadata["color"],
            max_drones=metadata["max_drones"],
            is_start=is_start,
            is_end=is_end,
        )

        self.network.add_zone(zone)

    def _parse_connection(
        self,
        line: str,
        line_number: int,
    ) -> None:
        """Parse a connection between two zones."""
        parts = line.split()

        connection_names = parts[0]

        if connection_names.count("-") != 1:
            self._error(
                line_number,
                "connection must have exactly two zone names",
            )

        first_name, second_name = connection_names.split("-", 1)

        if not first_name or not second_name:
            self._error(
                line_number,
                "connection contains an empty zone name",
            )

        if first_name not in self.network.zones:
            self._error(
                line_number,
                f"unknown zone '{first_name}' in connection",
            )

        if second_name not in self.network.zones:
            self._error(
                line_number,
                f"unknown zone '{second_name}' in connection",
            )

        if first_name == second_name:
            self._error(
                line_number,
                "a zone cannot connect to itself",
            )

        zone_a = self.network.zones[first_name]
        zone_b = self.network.zones[second_name]

        if self._connection_exists(zone_a, zone_b):
            self._error(
                line_number,
                "duplicate connection",
            )

        metadata = self._parse_connection_metadata(
            parts[1:],
            line_number,
        )

        connection = Connection(
            name=f"{first_name}-{second_name}",
            zone_a=zone_a,
            zone_b=zone_b,
            max_link_capacity=metadata["max_link_capacity"],
        )

        self.network.add_connection(connection)

    def _parse_zone_metadata(
        self,
        metadata: list[str],
        line_number: int,
    ) -> dict[str, object]:
        """Parse optional zone metadata."""
        values: dict[str, object] = {
            "zone": "normal",
            "color": "white",
            "max_drones": 1,
        }

        seen: set[str] = set()

        for item in metadata:
            if "=" not in item:
                self._error(
                    line_number,
                    f"invalid zone metadata '{item}'",
                )

            key, value = item.split("=", 1)

            if key in seen:
                self._error(
                    line_number,
                    f"duplicate metadata '{key}'",
                )

            seen.add(key)

            if key == "zone":
                if value not in {
                    "normal",
                    "blocked",
                    "restricted",
                    "priority",
                }:
                    self._error(
                        line_number,
                        f"invalid zone type '{value}'",
                    )

                values["zone"] = value

            elif key == "color":
                if not value or " " in value:
                    self._error(
                        line_number,
                        "color must be one word",
                    )

                values["color"] = value

            elif key == "max_drones":
                if not value.isdigit() or int(value) <= 0:
                    self._error(
                        line_number,
                        "max_drones must be a positive integer",
                    )

                values["max_drones"] = int(value)

            else:
                self._error(
                    line_number,
                    f"unknown zone metadata '{key}'",
                )

        return values

    def _parse_connection_metadata(
        self,
        metadata: list[str],
        line_number: int,
    ) -> dict[str, int]:
        """Parse optional connection metadata."""
        values = {
            "max_link_capacity": 1,
        }

        seen: set[str] = set()

        for item in metadata:
            if "=" not in item:
                self._error(
                    line_number,
                    f"invalid connection metadata '{item}'",
                )

            key, value = item.split("=", 1)

            if key in seen:
                self._error(
                    line_number,
                    f"duplicate metadata '{key}'",
                )

            seen.add(key)

            if key == "max_link_capacity":
                if not value.isdigit() or int(value) <= 0:
                    self._error(
                        line_number,
                        "max_link_capacity must be a positive integer",
                    )

                values["max_link_capacity"] = int(value)

            else:
                self._error(
                    line_number,
                    f"unknown connection metadata '{key}'",
                )

        return values

    def _validate_zone_name(
        self,
        name: str,
        line_number: int,
    ) -> None:
        """Validate a zone name."""
        if not name:
            self._error(
                line_number,
                "zone name cannot be empty",
            )

        if " " in name:
            self._error(
                line_number,
                "zone name cannot contain spaces",
            )

        if "-" in name:
            self._error(
                line_number,
                "zone name cannot contain '-'",
            )

        if not re.fullmatch(r"[A-Za-z0-9_]+", name):
            self._error(
                line_number,
                "zone name contains invalid characters",
            )

    def _connection_exists(
        self,
        zone_a: Zone,
        zone_b: Zone,
    ) -> bool:
        """Check whether an undirected connection already exists."""
        for connection in self.network.connections.values():
            same_direction = (
                connection.zone_a == zone_a
                and connection.zone_b == zone_b
            )

            opposite_direction = (
                connection.zone_a == zone_b
                and connection.zone_b == zone_a
            )

            if same_direction or opposite_direction:
                return True

        return False

    def _get_zone_prefix(self, line: str) -> str:
        """Return the prefix used by a zone line."""
        if line.startswith("start_hub:"):
            return "start_hub:"

        if line.startswith("end_hub:"):
            return "end_hub:"

        return "hub:"

    def _validate_map(self) -> None:
        """Validate the complete map after parsing."""
        if self.nb_drones <= 0:
            raise ValueError(
                "map error: missing or invalid nb_drones"
            )

        if self.network.start_zone is None:
            raise ValueError(
                "map error: missing start_hub"
            )

        if self.network.end_zone is None:
            raise ValueError(
                "map error: missing end_hub"
            )

        if self.network.start_zone == self.network.end_zone:
            raise ValueError(
                "map error: start_hub and end_hub must be different"
            )

    def _error(
        self,
        line_number: int,
        message: str,
    ) -> None:
        """Raise a parsing error with the line number."""
        raise ValueError(
            f"line {line_number}: {message}"
        )
