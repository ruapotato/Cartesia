"""
Smooth terrain rendering using marching squares algorithm.

This creates Terraria-style smooth terrain instead of blocky pixels.
"""
import pygame
import numpy as np
from typing import List, Tuple, Optional


class SmoothTerrainRenderer:
    """
    Renders terrain with smooth edges using marching squares.

    Instead of drawing square blocks, this creates smooth polygons
    that follow the terrain contours.
    """

    def __init__(self):
        self.surface_cache = {}  # Cache for rendered chunk surfaces

    def get_smoothness_value(self, chunk, x: int, y: int, chunk_size: int) -> float:
        """
        Get smoothness value for a position (0 = air, 1 = solid).

        We use values between 0 and 1 to create smooth transitions.
        """
        # Bounds checking - if out of bounds, assume air
        if x < 0 or x >= chunk_size or y < 0 or y >= chunk_size:
            return 0.0

        try:
            block_id = chunk.blocks[x, y]
            # Air = 0, Solid = 1
            if block_id == 1:  # Air
                return 0.0
            else:
                return 1.0
        except (IndexError, KeyError):
            return 0.0

    def get_marching_square_case(self, tl: float, tr: float, br: float, bl: float) -> int:
        """
        Get marching squares case number (0-15) based on corner values.

        Case is determined by which corners are solid (>= 0.5):
        - Top-left: +1
        - Top-right: +2
        - Bottom-right: +4
        - Bottom-left: +8
        """
        case = 0
        if tl >= 0.5:
            case += 1
        if tr >= 0.5:
            case += 2
        if br >= 0.5:
            case += 4
        if bl >= 0.5:
            case += 8
        return case

    def render_smooth_chunk(
        self,
        chunk,
        chunk_size: int,
        block_size: int,
        block_registry
    ) -> pygame.Surface:
        """
        Render a chunk with smooth terrain.

        Returns a surface with the smoothly rendered terrain.
        """
        # Create surface for this chunk
        surface_width = chunk_size * block_size
        surface_height = chunk_size * block_size
        surface = pygame.Surface((surface_width, surface_height), pygame.SRCALPHA)
        surface.fill((0, 0, 0, 0))  # Transparent

        # Draw smooth terrain
        # Y increases upward in world coords, but downward in screen coords
        for local_y in range(chunk_size):
            for local_x in range(chunk_size):
                block_id = chunk.blocks[local_x, local_y]

                # Skip air
                if block_id == 1:
                    continue

                # Calculate screen position
                # Screen Y is flipped from world Y
                screen_x = local_x * block_size
                screen_y = (chunk_size - 1 - local_y) * block_size  # Flip Y

                # Get corner smoothness values
                # Sample neighbors accounting for Y flip
                tl = self.get_smoothness_value(chunk, local_x, local_y + 1, chunk_size)
                tr = self.get_smoothness_value(chunk, local_x + 1, local_y + 1, chunk_size)
                br = self.get_smoothness_value(chunk, local_x + 1, local_y, chunk_size)
                bl = self.get_smoothness_value(chunk, local_x, local_y, chunk_size)

                # Draw the block with smooth edges
                self._draw_smooth_block(
                    surface,
                    screen_x,
                    screen_y,
                    block_size,
                    block_id,
                    block_registry,
                    tl, tr, br, bl
                )

        return surface

    def _draw_smooth_block(
        self,
        surface: pygame.Surface,
        x: int,
        y: int,
        size: int,
        block_id: int,
        block_registry,
        tl: float,
        tr: float,
        br: float,
        bl: float
    ):
        """
        Draw a single block with smooth edges based on neighbor values.
        """
        # Get block color/texture
        block_def = block_registry.get(block_id)
        if not block_def:
            return

        # Determine color
        if block_def.color:
            color = block_def.color
        else:
            # Sample texture color (take average color)
            if block_def.texture:
                # Simple: use a base color for the block type
                if block_id == 2:  # Grass
                    color = (95, 159, 53)
                elif block_id == 3:  # Dirt
                    color = (134, 96, 67)
                elif block_id == 4:  # Stone
                    color = (128, 128, 128)
                else:
                    color = (200, 200, 200)
            else:
                color = (200, 200, 200)

        # Simple approach: draw full block with rounded corners
        # For proper smooth terrain, we'd use marching squares polygons

        # Check if this block has any air neighbors
        has_air_neighbor = (tl < 1.0 or tr < 1.0 or br < 1.0 or bl < 1.0)

        if not has_air_neighbor:
            # Full block (no smoothing needed)
            pygame.draw.rect(surface, color, (x, y, size, size))
        else:
            # Draw with smooth edges
            # Create a polygon based on the marching squares case
            points = self._get_smooth_polygon(x, y, size, tl, tr, br, bl)
            if len(points) >= 3:
                pygame.draw.polygon(surface, color, points)

    def _get_smooth_polygon(
        self,
        x: int,
        y: int,
        size: int,
        tl: float,
        tr: float,
        br: float,
        bl: float
    ) -> List[Tuple[float, float]]:
        """
        Get polygon points for smooth rendering using marching squares.
        """
        # Threshold for solid/air
        threshold = 0.5

        # Corner positions
        corners = [
            (x, y),              # Top-left
            (x + size, y),       # Top-right
            (x + size, y + size),  # Bottom-right
            (x, y + size)        # Bottom-left
        ]

        # Edge midpoints
        top_mid = (x + size / 2, y)
        right_mid = (x + size, y + size / 2)
        bottom_mid = (x + size / 2, y + size)
        left_mid = (x, y + size / 2)
        center = (x + size / 2, y + size / 2)

        # Get marching square case
        case = self.get_marching_square_case(tl, tr, br, bl)

        # Return polygon points based on case
        # Cases 0 and 15 are special (all air or all solid)
        if case == 0:
            return []  # All air
        elif case == 15:
            return corners  # All solid - full square

        # For other cases, create smooth polygons
        # This is a simplified version - full implementation would interpolate edge positions
        points = []

        # Simplified marching squares - just use corners and midpoints
        if case == 1:  # Only TL
            points = [corners[0], top_mid, left_mid]
        elif case == 2:  # Only TR
            points = [top_mid, corners[1], right_mid]
        elif case == 3:  # TL and TR
            points = [corners[0], corners[1], right_mid, left_mid]
        elif case == 4:  # Only BR
            points = [right_mid, corners[2], bottom_mid]
        elif case == 5:  # TL and BR (diagonal)
            points = [corners[0], top_mid, right_mid, corners[2], bottom_mid, left_mid]
        elif case == 6:  # TR and BR
            points = [top_mid, corners[1], corners[2], bottom_mid]
        elif case == 7:  # TL, TR, BR
            points = [corners[0], corners[1], corners[2], bottom_mid, left_mid]
        elif case == 8:  # Only BL
            points = [left_mid, bottom_mid, corners[3]]
        elif case == 9:  # TL and BL
            points = [corners[0], top_mid, bottom_mid, corners[3]]
        elif case == 10:  # TR and BL (diagonal)
            points = [top_mid, corners[1], right_mid, bottom_mid, corners[3], left_mid]
        elif case == 11:  # TL, TR, BL
            points = [corners[0], corners[1], right_mid, bottom_mid, corners[3]]
        elif case == 12:  # BR and BL
            points = [left_mid, right_mid, corners[2], corners[3]]
        elif case == 13:  # TL, BR, BL
            points = [corners[0], top_mid, right_mid, corners[2], corners[3]]
        elif case == 14:  # TR, BR, BL
            points = [top_mid, corners[1], corners[2], corners[3], left_mid]

        return points


# Global instance
_smooth_renderer: Optional[SmoothTerrainRenderer] = None


def get_smooth_renderer() -> SmoothTerrainRenderer:
    """Get the global smooth terrain renderer."""
    global _smooth_renderer
    if _smooth_renderer is None:
        _smooth_renderer = SmoothTerrainRenderer()
    return _smooth_renderer
