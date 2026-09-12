"""Graph operations for the Fly-in drone routing system."""

from .models import Connection, Network, Zone


class Graph:
    """Represent the map as a graph of zones and connections."""

    def __init__(self, network: Network) -> None:
        """Initialize the graph from a network."""
        self.network = network

    def get_neighbors(self, zone: Zone) -> list[Zone]:
        """Return all zones directly connected to a zone."""
        return self.network.neighbors(zone)

    def get_connection(
        self,
        first_zone: Zone,
        second_zone: Zone,
    ) -> Connection | None:
        """Return the connection between two zones, if it exists."""
        for connection in self.network.connections.values():
            if self._connects(
                connection,
                first_zone,
                second_zone,
            ):
                return connection

        return None

    def is_connected(
        self,
        first_zone: Zone,
        second_zone: Zone,
    ) -> bool:
        """Check whether two zones are directly connected."""
        return self.get_connection(
            first_zone,
            second_zone,
        ) is not None

    def can_enter(self, zone: Zone) -> bool:
        """Check whether a zone can be used by drones."""
        return zone.zone_type != "blocked"

    def get_cost(self, zone: Zone) -> int:
        """Return the movement cost of entering a zone."""
        if zone.zone_type == "restricted":
            return 2

        return 1

    def _connects(
        self,
        connection: Connection,
        first_zone: Zone,
        second_zone: Zone,
    ) -> bool:
        """Check whether a connection links two zones."""
        direct = (
            connection.zone_a == first_zone
            and connection.zone_b == second_zone
        )

        reverse = (
            connection.zone_a == second_zone
            and connection.zone_b == first_zone
        )

        return direct or reverse
