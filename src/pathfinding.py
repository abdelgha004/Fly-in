"""Pathfinding algorithms for the Fly-in drone routing system."""

import heapq

from .graph import Graph
from .models import Zone


class PathFinder:
    """Find valid paths through the drone network."""

    def __init__(self, graph: Graph) -> None:
        """Initialize the pathfinder."""
        self.graph = graph

    def find_k_paths(
        self,
        start: Zone,
        end: Zone,
        k: int = 4,
    ) -> list[list[Zone]]:
        """Find up to k lowest-cost simple paths."""
        if k <= 0:
            return []

        paths: list[list[Zone]] = []
        heap: list[tuple[int, int, int, tuple[str, ...]]] = []
        counter = 0

        heapq.heappush(
            heap,
            (0, 0, counter, (start.name,)),
        )

        best_cost: int | None = None
        cost_margin = 1

        while heap and len(paths) < k:
            cost, _, _, path_names = heapq.heappop(heap)

            if best_cost is not None and cost > best_cost + cost_margin:
                break

            last_name = path_names[-1]

            if last_name == end.name:
                if best_cost is None:
                    best_cost = cost
                paths.append(
                    [self.graph.network.get_zone(n) for n in path_names]
                )
                continue

            current_zone = self.graph.network.get_zone(last_name)

            for neighbor in self.graph.get_neighbors(current_zone):
                if not self.graph.can_enter(neighbor):
                    continue
                if neighbor.name in path_names:
                    continue

                new_cost = cost + self.graph.get_cost(neighbor)
                counter += 1
                heapq.heappush(
                    heap,
                    (
                        new_cost,
                        0,
                        counter,
                        path_names + (neighbor.name,),
                    ),
                )

        if not paths:
            single = self.find_path(start, end)
            if single:
                paths.append(single)

        return paths

    def find_path(
        self,
        start: Zone,
        end: Zone,
    ) -> list[Zone]:
        """Find the lowest-cost path between two zones."""
        distances: dict[str, int] = {start.name: 0}
        previous: dict[str, Zone | None] = {start.name: None}

        queue: list[tuple[int, int, str]] = []
        counter = 0

        heapq.heappush(queue, (0, counter, start.name))

        while queue:
            current_cost, _, current_name = heapq.heappop(queue)

            if current_name == end.name:
                return self._build_path(previous, end)

            if current_cost > distances.get(current_name, 10**18):
                continue

            current_zone = self.graph.network.get_zone(current_name)

            for neighbor in self.graph.get_neighbors(current_zone):
                if not self.graph.can_enter(neighbor):
                    continue

                new_cost = current_cost + self.graph.get_cost(neighbor)

                if self._is_better_path(neighbor, new_cost, distances):
                    distances[neighbor.name] = new_cost
                    previous[neighbor.name] = current_zone
                    counter += 1
                    heapq.heappush(
                        queue,
                        (new_cost, counter, neighbor.name),
                    )

        return []

    def _is_better_path(
        self,
        zone: Zone,
        new_cost: int,
        distances: dict[str, int],
    ) -> bool:
        """Check whether a new path is better."""
        old_cost = distances.get(zone.name)
        if old_cost is None:
            return True
        if new_cost < old_cost:
            return True
        if new_cost == old_cost and zone.zone_type == "priority":
            return True
        return False

    def _build_path(
        self,
        previous: dict[str, Zone | None],
        end: Zone,
    ) -> list[Zone]:
        """Build the path from the previous-zone information."""
        path: list[Zone] = []
        current: Zone | None = end
        while current is not None:
            path.append(current)
            current = previous.get(current.name)
        path.reverse()
        return path
