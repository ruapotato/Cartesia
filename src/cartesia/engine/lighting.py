"""
Modern lighting system for Cartesia.

This module implements a sophisticated lighting system with:
- Dynamic light sources (torches, etc.)
- Ambient lighting (day/night cycle)
- Smooth light propagation
- Efficient caching and updates
"""
from typing import List, Tuple, Dict, Set
from dataclasses import dataclass
import pygame
import numpy as np
from numba import njit
from ..config import LightingConfig, get_config


@dataclass
class LightSource:
    """Represents a single light source in the world."""

    position: Tuple[float, float]  # World coordinates
    radius: float
    intensity: float
    color: Tuple[int, int, int]
    enabled: bool = True

    # Caching
    _cached_surface: pygame.Surface = None
    _cache_dirty: bool = True

    def mark_dirty(self) -> None:
        """Mark this light source as needing recalculation."""
        self._cache_dirty = True


class LightingEngine:
    """
    Modern lighting engine with smooth transitions and efficient rendering.

    Key improvements over the old system:
    1. Proper light falloff calculations
    2. Multiple blend modes
    3. Efficient caching
    4. Smooth ambient transitions
    5. Better shadow handling
    """

    def __init__(self, surface_size: Tuple[int, int], config: LightingConfig = None):
        self.config = config or get_config().lighting
        self.surface_size = surface_size

        # Light sources
        self.light_sources: Dict[str, LightSource] = {}

        # Surfaces for rendering
        self.light_layer = pygame.Surface(surface_size, pygame.SRCALPHA)
        self.shadow_layer = pygame.Surface(surface_size, pygame.SRCALPHA)
        self.final_layer = pygame.Surface(surface_size)

        # Ambient light
        self.ambient_level = 1.0  # 0.0 to 1.0
        self.target_ambient = 1.0
        self.time_of_day = 0.0  # 0.0 to 1.0 (0 = midnight, 0.5 = noon)

        # Pre-calculated light textures
        self._light_cache: Dict[Tuple[int, Tuple[int, int, int]], pygame.Surface] = {}

        # Performance tracking
        self._last_update = 0.0
        self._dirty_chunks: Set[Tuple[int, int]] = set()

    def add_light(self, name: str, x: float, y: float, radius: float = None,
                  intensity: float = 1.0, color: Tuple[int, int, int] = None) -> None:
        """Add a new light source."""
        if radius is None:
            radius = self.config.torch_radius
        if color is None:
            color = self.config.torch_color

        self.light_sources[name] = LightSource(
            position=(x, y),
            radius=radius,
            intensity=intensity,
            color=color
        )

    def remove_light(self, name: str) -> None:
        """Remove a light source."""
        if name in self.light_sources:
            del self.light_sources[name]

    def move_light(self, name: str, x: float, y: float) -> None:
        """Move an existing light source."""
        if name in self.light_sources:
            light = self.light_sources[name]
            light.position = (x, y)
            light.mark_dirty()

    def update(self, dt: float) -> None:
        """Update lighting state."""
        # Smooth ambient transitions
        if abs(self.ambient_level - self.target_ambient) > 0.001:
            transition_speed = 0.1 * dt
            if self.ambient_level < self.target_ambient:
                self.ambient_level = min(self.ambient_level + transition_speed, self.target_ambient)
            else:
                self.ambient_level = max(self.ambient_level - transition_speed, self.target_ambient)

    def set_time_of_day(self, time: float) -> None:
        """
        Set the time of day and update ambient light.

        Args:
            time: 0.0 to 1.0, where 0.0 is midnight and 0.5 is noon
        """
        self.time_of_day = time % 1.0

        # Calculate ambient level based on time
        # Uses a smooth curve for realistic day/night transitions
        if 0.25 <= self.time_of_day <= 0.75:
            # Daytime (6 AM to 6 PM)
            day_progress = (self.time_of_day - 0.25) * 2  # 0 to 1
            # Smooth curve: peaks at noon
            ambient = self.config.ambient_min + (
                self.config.ambient_max - self.config.ambient_min
            ) * (1 - np.cos(day_progress * np.pi)) / 2
        else:
            # Nighttime
            ambient = self.config.ambient_min

        self.target_ambient = ambient

    def _create_light_texture(self, radius: int, color: Tuple[int, int, int]) -> pygame.Surface:
        """Create a radial gradient light texture."""
        cache_key = (radius, color)
        if cache_key in self._light_cache:
            return self._light_cache[cache_key]

        size = radius * 2
        surface = pygame.Surface((size, size), pygame.SRCALPHA)

        center = radius

        # Create radial gradient
        for y in range(size):
            for x in range(size):
                dx = x - center
                dy = y - center
                distance = np.sqrt(dx * dx + dy * dy)

                if distance <= radius:
                    # Choose falloff function
                    if self.config.light_falloff == "linear":
                        alpha = 1.0 - (distance / radius)
                    elif self.config.light_falloff == "quadratic":
                        alpha = 1.0 - (distance / radius) ** 2
                    else:  # cubic
                        alpha = 1.0 - (distance / radius) ** 3

                    alpha = max(0, min(1, alpha))

                    # Apply color with alpha
                    pixel_color = (
                        int(color[0] * alpha),
                        int(color[1] * alpha),
                        int(color[2] * alpha),
                        int(255 * alpha)
                    )
                    surface.set_at((x, y), pixel_color)

        self._light_cache[cache_key] = surface
        return surface

    def render(self, target: pygame.Surface, camera_offset: Tuple[int, int] = (0, 0)) -> None:
        """
        Render lighting to the target surface.

        This applies the complete lighting effect including:
        - Ambient lighting
        - Dynamic light sources
        - Smooth blending
        """
        if not self.config.enabled:
            return

        # Clear light layer
        self.light_layer.fill((0, 0, 0, 0))

        # Apply ambient lighting as a base
        ambient_color = self._get_ambient_color()
        ambient_alpha = int(255 * (1.0 - self.ambient_level))

        if ambient_alpha > 0:
            ambient_surface = pygame.Surface(self.surface_size)
            ambient_surface.fill(ambient_color)
            ambient_surface.set_alpha(ambient_alpha)
            self.light_layer.blit(ambient_surface, (0, 0))

        # Render each light source
        for name, light in self.light_sources.items():
            if not light.enabled:
                continue

            # Convert world coordinates to screen coordinates
            screen_x = light.position[0] - camera_offset[0]
            screen_y = light.position[1] - camera_offset[1]

            # Cull lights outside the visible area
            if not self._is_visible(screen_x, screen_y, light.radius):
                continue

            # Get or create light texture
            light_texture = self._create_light_texture(
                int(light.radius),
                light.color
            )

            # Calculate blit position (centered on light)
            blit_x = int(screen_x - light.radius)
            blit_y = int(screen_y - light.radius)

            # Blend light onto light layer
            if self.config.light_blend_mode == "add":
                self.light_layer.blit(light_texture, (blit_x, blit_y),
                                    special_flags=pygame.BLEND_RGBA_ADD)
            elif self.config.light_blend_mode == "multiply":
                self.light_layer.blit(light_texture, (blit_x, blit_y),
                                    special_flags=pygame.BLEND_RGBA_MULT)
            else:  # screen
                # Screen blend mode: 1 - (1-a)(1-b)
                self.light_layer.blit(light_texture, (blit_x, blit_y),
                                    special_flags=pygame.BLEND_RGBA_ADD)

        # Subtract lighting from target to create darkness effect
        # (Inverted: dark layer with lights punched out)
        if self.ambient_level < 1.0 or len(self.light_sources) > 0:
            target.blit(self.light_layer, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)

    def _get_ambient_color(self) -> Tuple[int, int, int]:
        """Get the current ambient light color based on time of day."""
        if 0.25 <= self.time_of_day <= 0.75:
            # Daytime - use sunlight color
            return self.config.sunlight_color
        else:
            # Nighttime - use moonlight color
            return self.config.moonlight_color

    def _is_visible(self, x: float, y: float, radius: float) -> bool:
        """Check if a light source is visible on screen."""
        return (
            -radius <= x <= self.surface_size[0] + radius and
            -radius <= y <= self.surface_size[1] + radius
        )

    def get_light_level_at(self, x: float, y: float) -> float:
        """
        Get the total light level at a specific position.

        Returns a value from 0.0 (complete darkness) to 1.0 (full light).
        """
        # Start with ambient
        total_light = self.ambient_level

        # Add contribution from each light source
        for light in self.light_sources.values():
            if not light.enabled:
                continue

            dx = x - light.position[0]
            dy = y - light.position[1]
            distance = np.sqrt(dx * dx + dy * dy)

            if distance <= light.radius:
                # Calculate light contribution
                if self.config.light_falloff == "linear":
                    contribution = (1.0 - distance / light.radius) * light.intensity
                elif self.config.light_falloff == "quadratic":
                    contribution = (1.0 - (distance / light.radius) ** 2) * light.intensity
                else:  # cubic
                    contribution = (1.0 - (distance / light.radius) ** 3) * light.intensity

                total_light += contribution

        return min(1.0, total_light)

    def clear(self) -> None:
        """Clear all light sources."""
        self.light_sources.clear()
        self._light_cache.clear()

    def resize(self, new_size: Tuple[int, int]) -> None:
        """Resize the lighting surfaces."""
        self.surface_size = new_size
        self.light_layer = pygame.Surface(new_size, pygame.SRCALPHA)
        self.shadow_layer = pygame.Surface(new_size, pygame.SRCALPHA)
        self.final_layer = pygame.Surface(new_size)
