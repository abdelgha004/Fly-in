"""Pygame visualization for the Fly-in simulation."""

from typing import Any

from .models import Network


class Visualizer:
    """Display the drone simulation in a pygame window."""

    WIDTH = 1400
    HEIGHT = 850
    MARGIN = 80
    HEADER = 50
    ZONE_RADIUS = 26
    DRONE_RADIUS = 10

    BG = (28, 30, 40)
    EDGE = (90, 95, 115)
    TEXT = (235, 235, 240)
    TEXT_DIM = (150, 155, 170)
    DRONE_FILL = (30, 30, 40)
    DRONE_RING = (255, 210, 90)

    def __init__(self, network: Network) -> None:
        """Initialize the visualizer."""
        self.network = network

    def emit_required_output(
        self,
        results: list[list[str]],
    ) -> None:
        """Print simulation in the exact format required by subject."""
        for movements in results:
            print(" ".join(movements))

    def run_pygame(
        self,
        states: list[dict[int, str]],
    ) -> None:
        """Open a pygame window; SPACE advances one turn."""
        try:
            import pygame
        except ImportError:
            print("pygame not installed — skipping visualization")
            return

        pygame.init()
        try:
            screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        except pygame.error as exc:
            print(f"cannot open window: {exc} — skipping")
            pygame.quit()
            return

        pygame.display.set_caption("Fly-in Drone Simulation")
        clock = pygame.time.Clock()
        font_zone = pygame.font.SysFont("consolas", 13, True)
        font_id = pygame.font.SysFont("consolas", 11, True)
        font_hud = pygame.font.SysFont("consolas", 20, True)
        font_hint = pygame.font.SysFont("consolas", 14)

        positions = self._compute_positions()
        colors = self._zone_colors()

        turn = 0
        total = len(states) - 1

        running = True
        while running:
            clock.tick(60)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_SPACE:
                        if turn < total:
                            turn += 1

            screen.fill(self.BG)
            self._draw_edges(screen, positions, pygame)
            self._draw_zones(
                screen, positions, colors, pygame, font_zone
            )
            self._draw_drones(
                screen, states[turn], positions, pygame, font_id
            )
            self._draw_hud(
                screen, turn, total, states[turn],
                pygame, font_hud, font_hint,
            )
            pygame.display.flip()

        pygame.quit()

    def _compute_positions(self) -> dict[str, tuple[int, int]]:
        zones = list(self.network.zones.values())
        xs = [z.x for z in zones]
        ys = [z.y for z in zones]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        rng_x = max_x - min_x or 1
        rng_y = max_y - min_y or 1
        w = self.WIDTH - 2 * self.MARGIN
        h = self.HEIGHT - self.HEADER - 2 * self.MARGIN
        pos: dict[str, tuple[int, int]] = {}
        for z in zones:
            px = int(self.MARGIN + (z.x - min_x) / rng_x * w)
            py = int(
                self.HEADER + self.MARGIN
                + (z.y - min_y) / rng_y * h
            )
            pos[z.name] = (px, py)
        return pos

    def _zone_colors(self) -> dict[str, tuple[int, int, int]]:
        palette = {
            "red": (235, 90, 100),
            "green": (110, 210, 130),
            "blue": (90, 160, 245),
            "yellow": (245, 215, 95),
            "orange": (245, 160, 80),
            "purple": (180, 130, 230),
            "cyan": (90, 220, 230),
            "magenta": (230, 110, 210),
            "gray": (150, 150, 155),
            "grey": (150, 150, 155),
            "gold": (235, 200, 100),
            "crimson": (220, 80, 110),
            "maroon": (170, 70, 90),
            "white": (230, 230, 235),
            "black": (90, 90, 95),
        }
        colors: dict[str, tuple[int, int, int]] = {}
        for name, zone in self.network.zones.items():
            key = (zone.color or "").lower()
            colors[name] = palette.get(key, (170, 170, 180))
        return colors

    def _draw_edges(
        self,
        screen: Any,
        positions: dict[str, tuple[int, int]],
        pygame: Any,
    ) -> None:
        for conn in self.network.connections.values():
            a = positions.get(conn.zone_a.name)
            b = positions.get(conn.zone_b.name)
            if a is not None and b is not None:
                pygame.draw.line(screen, self.EDGE, a, b, 3)

    def _draw_zones(
        self,
        screen: Any,
        positions: dict[str, tuple[int, int]],
        colors: dict[str, tuple[int, int, int]],
        pygame: Any,
        font_zone: Any,
    ) -> None:
        for i, (name, pos) in enumerate(positions.items()):
            color = colors.get(name, (170, 170, 180))
            pygame.draw.circle(screen, color, pos, self.ZONE_RADIUS)
            pygame.draw.circle(
                screen, self.TEXT, pos, self.ZONE_RADIUS, 2
            )

            zone = self.network.zones[name]
            if zone.is_start:
                tag_text = "START"
            elif zone.is_end:
                tag_text = "END"
            else:
                tag_text = str(zone.max_drones)

            if i % 2 == 0:
                name_y = pos[1] - self.ZONE_RADIUS - 14
                tag_y = pos[1] + self.ZONE_RADIUS + 14
            else:
                name_y = pos[1] + self.ZONE_RADIUS + 14
                tag_y = pos[1] - self.ZONE_RADIUS - 14

            label = font_zone.render(name, True, self.TEXT)
            screen.blit(
                label,
                label.get_rect(center=(pos[0], name_y)),
            )
            tag = font_zone.render(tag_text, True, self.TEXT_DIM)
            screen.blit(
                tag,
                tag.get_rect(center=(pos[0], tag_y)),
            )

    def _draw_drones(
        self,
        screen: Any,
        snapshot: dict[int, str],
        positions: dict[str, tuple[int, int]],
        pygame: Any,
        font_id: Any,
    ) -> None:
        by_loc: dict[str, list[int]] = {}
        for drone_id, loc in snapshot.items():
            by_loc.setdefault(loc, []).append(drone_id)

        for loc, ids in by_loc.items():
            in_transit = "-" in loc

            if in_transit:
                a, _, b = loc.partition("-")
                if a not in positions or b not in positions:
                    continue
                ax, ay = positions[a]
                cx, cy = positions[b]
                bx = (ax + cx) // 2
                by = (ay + cy) // 2
            elif loc in positions:
                bx, by = positions[loc]
            else:
                continue

            for idx, did in enumerate(ids):
                col = idx % 3
                row = idx // 3
                px = bx + col * 14 - 14
                py = by + row * 14 - 14

                if in_transit:
                    pygame.draw.circle(
                        screen, self.DRONE_RING, (px, py),
                        self.DRONE_RADIUS, 2,
                    )
                else:
                    pygame.draw.circle(
                        screen, self.DRONE_FILL, (px, py),
                        self.DRONE_RADIUS,
                    )
                    pygame.draw.circle(
                        screen, self.DRONE_RING, (px, py),
                        self.DRONE_RADIUS, 2,
                    )

                lbl = font_id.render(
                    str(did), True, self.DRONE_RING
                )
                screen.blit(
                    lbl,
                    (
                        px - lbl.get_width() // 2,
                        py - lbl.get_height() // 2,
                    ),
                )

    def _draw_hud(
        self,
        screen: Any,
        turn: int,
        total: int,
        snapshot: dict[int, str],
        pygame: Any,
        font_hud: Any,
        font_hint: Any,
    ) -> None:
        end_name = (
            self.network.end_zone.name
            if self.network.end_zone else None
        )
        delivered = 0
        if end_name is not None:
            delivered = sum(
                1 for loc in snapshot.values() if loc == end_name
            )
        total_drones = len(snapshot)

        pygame.draw.rect(
            screen, (18, 20, 30),
            (0, 0, self.WIDTH, self.HEADER),
        )
        pygame.draw.line(
            screen, (60, 66, 90),
            (0, self.HEADER), (self.WIDTH, self.HEADER), 1,
        )

        line = (
            f"Turn {turn} / {total}"
            f"     Delivered {delivered} / {total_drones}"
        )
        label = font_hud.render(line, True, self.TEXT)
        screen.blit(label, (20, 12))

        hint = font_hint.render(
            "SPACE: next turn     ESC: quit",
            True, self.TEXT_DIM,
        )
        screen.blit(hint, (20, self.HEIGHT - 28))
