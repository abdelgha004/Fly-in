from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union


@dataclass
class Zone:
    """Represent a zone in the drone network."""

    name: str
    x: int
    y: int
    zone_type: str = "normal"
    color: Optional[str] = None
    max_drones: int = 1
    is_start: bool = False
    is_end: bool = False
    drones: List[int] = field(default_factory=list)

    def can_enter(self, drone: Optional[Union[int, "Drone"]] = None) -> bool:
        """Check whether another drone can enter the zone."""
        if self.is_start or self.is_end:
            return True
        return len(self.drones) < self.max_drones

    def add_drone(self, drone: Union[int, "Drone"]) -> None:
        """Add a drone to this zone."""
        drone_id = drone if isinstance(drone, int) else drone.drone_id
        if drone_id not in self.drones:
            self.drones.append(drone_id)

    def remove_drone(self, drone: Union[int, "Drone"]) -> None:
        """Remove a drone from this zone."""
        drone_id = drone if isinstance(drone, int) else drone.drone_id
        if drone_id in self.drones:
            self.drones.remove(drone_id)

    def movement_cost(self) -> int:
        """Return the movement cost for entering this zone."""
        if self.zone_type == "restricted":
            return 2
        return 1


@dataclass
class Connection:
    """Represent a bidirectional connection between two zones."""

    name: str
    zone_a: Zone
    zone_b: Zone
    max_link_capacity: int = 1
    drones: List[int] = field(default_factory=list)

    def other_zone(self, zone: Zone) -> Zone:
        """Return the zone on the other side of the connection."""
        if zone == self.zone_a:
            return self.zone_b
        if zone == self.zone_b:
            return self.zone_a
        raise ValueError(
            f"Zone '{zone.name}' is not connected to '{self.name}'"
        )

    def can_enter(
        self,
        drone: Optional[Union[int, "Drone"]] = None,
    ) -> bool:
        """Check whether another drone can use this connection."""
        return len(self.drones) < self.max_link_capacity

    def add_drone(self, drone: Union[int, "Drone"]) -> None:
        """Add a drone to the connection."""
        drone_id = drone if isinstance(drone, int) else drone.drone_id
        if drone_id not in self.drones:
            self.drones.append(drone_id)

    def remove_drone(self, drone: Union[int, "Drone"]) -> None:
        """Remove a drone from the connection."""
        drone_id = drone if isinstance(drone, int) else drone.drone_id
        if drone_id in self.drones:
            self.drones.remove(drone_id)


@dataclass
class Drone:
    """Represent a drone moving through the network."""

    drone_id: int
    current_zone: Zone
    path: List[Zone] = field(default_factory=list)
    path_index: int = 0
    delivered: bool = False
    waiting: bool = False
    in_transit: bool = False
    transit_connection: Optional[Connection] = None
    transit_destination: Optional[Zone] = None

    def next_zone(self) -> Optional[Zone]:
        """Return the next zone in the drone's path."""
        if self.path_index + 1 >= len(self.path):
            return None
        return self.path[self.path_index + 1]

    def move_to(self, zone: Zone) -> None:
        """Move the drone to a new zone."""
        self.current_zone = zone
        self.path_index += 1
        self.waiting = False

    def is_finished(self) -> bool:
        """Check whether the drone has reached the end of its path."""
        if not self.path:
            return False
        return self.path_index >= len(self.path) - 1


@dataclass
class Network:
    """Represent the complete drone network."""

    zones: Dict[str, Zone] = field(default_factory=dict)
    connections: Dict[str, Connection] = field(default_factory=dict)
    adjacency: Dict[str, List[str]] = field(default_factory=dict)
    start_zone: Optional[Zone] = None
    end_zone: Optional[Zone] = None

    def add_zone(self, zone: Zone) -> None:
        """Add a zone to the network."""
        self.zones[zone.name] = zone
        self.adjacency.setdefault(zone.name, [])
        if zone.is_start:
            self.start_zone = zone
        if zone.is_end:
            self.end_zone = zone

    def add_connection(self, connection: Connection) -> None:
        """Add a connection to the network."""
        self.connections[connection.name] = connection
        self.adjacency.setdefault(connection.zone_a.name, [])
        self.adjacency.setdefault(connection.zone_b.name, [])
        self.adjacency[connection.zone_a.name].append(
            connection.zone_b.name
        )
        self.adjacency[connection.zone_b.name].append(
            connection.zone_a.name
        )

    def get_zone(self, zone_name: str) -> Zone:
        """Return a zone by its name."""
        return self.zones[zone_name]

    def get_connection(
        self,
        zone_a: Zone,
        zone_b: Zone,
    ) -> Optional[Connection]:
        """Find the connection between two zones."""
        for connection in self.connections.values():
            if (
                connection.zone_a == zone_a
                and connection.zone_b == zone_b
            ) or (
                connection.zone_a == zone_b
                and connection.zone_b == zone_a
            ):
                return connection
        return None

    def neighbors(self, zone: Zone) -> List[Zone]:
        """Return all zones connected to the given zone."""
        neighbor_names = self.adjacency.get(zone.name, [])
        return [
            self.zones[neighbor_name]
            for neighbor_name in neighbor_names
        ]


@dataclass
class SimulationState:
    """Store the state of the simulation."""

    turn: int = 0
    drones: Dict[int, Drone] = field(default_factory=dict)
    finished: bool = False

    def all_delivered(self) -> bool:
        """Check whether all drones reached the destination."""
        return all(
            drone.is_finished()
            for drone in self.drones.values()
        )
