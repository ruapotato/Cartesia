"""
Modern rendering system for Cartesia.

Handles world rendering, sprite batching, and camera management
with proper layering and optimization.
"""
from typing import Tuple, List, Optional
import pygame
from ..config import get_config
from ..world.blocks import get_block_registry
from ..world.chunk import ChunkManager
from .lighting import LightingEngine
from ..entities.entity import Entity, SpriteComponent, TransformComponent


class Camera:
    """
    Game camera with smooth following and screen shake.

    Much better than just using world_xy!
    """

    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height

        # Camera position (center of view)
        self.x = 0.0
        self.y = 0.0

        # Target to follow
        self.target_x = 0.0
        self.target_y = 0.0

        # Camera settings
        self.follow_speed = 0.1  # 0-1, higher = faster following
        self.zoom = 1.0

        # Screen shake
        self.shake_amount = 0.0
        self.shake_decay = 0.9

    def follow(self, x: float, y: float, immediate: bool = False) -> None:
        """Set camera to follow a target position."""
        self.target_x = x
        self.target_y = y

        if immediate:
            self.x = x
            self.y = y

    def update(self, dt: float) -> None:
        """Update camera (smooth following, shake, etc.)."""
        # Smooth following
        dx = self.target_x - self.x
        dy = self.target_y - self.y

        self.x += dx * self.follow_speed
        self.y += dy * self.follow_speed

        # Update screen shake
        if self.shake_amount > 0.1:
            self.shake_amount *= self.shake_decay
        else:
            self.shake_amount = 0

    def shake(self, amount: float) -> None:
        """Trigger screen shake."""
        self.shake_amount = max(self.shake_amount, amount)

    def world_to_screen(self, world_x: float, world_y: float) -> Tuple[int, int]:
        """Convert world coordinates to screen coordinates."""
        screen_x = (world_x - self.x) * self.zoom + self.width // 2
        screen_y = (world_y - self.y) * self.zoom + self.height // 2

        # Apply screen shake
        if self.shake_amount > 0:
            import random
            screen_x += random.uniform(-self.shake_amount, self.shake_amount)
            screen_y += random.uniform(-self.shake_amount, self.shake_amount)

        return int(screen_x), int(screen_y)

    def screen_to_world(self, screen_x: int, screen_y: int) -> Tuple[float, float]:
        """Convert screen coordinates to world coordinates."""
        world_x = (screen_x - self.width // 2) / self.zoom + self.x
        world_y = (screen_y - self.height // 2) / self.zoom + self.y
        return world_x, world_y

    def get_visible_bounds(self) -> Tuple[float, float, float, float]:
        """Get the visible world bounds (left, top, right, bottom)."""
        half_width = (self.width / 2) / self.zoom
        half_height = (self.height / 2) / self.zoom

        return (
            self.x - half_width,
            self.y - half_height,
            self.x + half_width,
            self.y + half_height
        )


class Renderer:
    """
    Main rendering system.

    Handles:
    - Chunk rendering
    - Sprite rendering
    - Lighting integration
    - Layer management
    """

    def __init__(
        self,
        screen: pygame.Surface,
        chunk_manager: ChunkManager,
        lighting_engine: LightingEngine
    ):
        self.screen = screen
        self.chunk_manager = chunk_manager
        self.lighting = lighting_engine
        self.config = get_config()

        # Screen dimensions
        self.width = screen.get_width()
        self.height = screen.get_height()

        # Camera
        self.camera = Camera(self.width, self.height)

        # Block registry
        self.block_registry = get_block_registry()

        # Rendering layers
        self.background_layer = pygame.Surface((self.width, self.height))
        self.world_layer = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.entity_layer = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.ui_layer = pygame.Surface((self.width, self.height), pygame.SRCALPHA)

        # Performance tracking
        self.chunks_rendered = 0
        self.sprites_rendered = 0

        # Chunk rendering cache
        self._chunk_surfaces = {}

    def update(self, dt: float) -> None:
        """Update renderer state."""
        self.camera.update(dt)

    def render_world(self) -> None:
        """
        Render the game world (chunks and blocks).

        This is MUCH cleaner than the old draw_world function!
        """
        self.world_layer.fill((0, 0, 0, 0))
        self.chunks_rendered = 0

        # Get visible chunk range
        left, top, right, bottom = self.camera.get_visible_bounds()

        chunk_size_pixels = (
            self.config.world.chunk_size * self.config.world.block_size
        )

        chunk_left = int(left // chunk_size_pixels) - 1
        chunk_right = int(right // chunk_size_pixels) + 1
        chunk_top = int(top // chunk_size_pixels) - 1
        chunk_bottom = int(bottom // chunk_size_pixels) + 1

        # Render visible chunks
        for chunk_y in range(chunk_top, chunk_bottom + 1):
            for chunk_x in range(chunk_left, chunk_right + 1):
                self._render_chunk(chunk_x, chunk_y)

    def _render_chunk(self, chunk_x: int, chunk_y: int) -> None:
        """Render a single chunk."""
        chunk = self.chunk_manager.get_chunk(chunk_x, chunk_y, generate=True)
        if not chunk:
            return

        # Check if chunk needs re-rendering
        chunk_key = (chunk_x, chunk_y)

        if chunk.dirty or chunk_key not in self._chunk_surfaces:
            # Render chunk to surface
            chunk_surface = self._render_chunk_to_surface(chunk)
            self._chunk_surfaces[chunk_key] = chunk_surface
            chunk.dirty = False
        else:
            chunk_surface = self._chunk_surfaces[chunk_key]

        # Calculate screen position
        world_x, world_y = chunk.to_world_coords()
        screen_x, screen_y = self.camera.world_to_screen(world_x, world_y)

        # Blit to world layer
        self.world_layer.blit(chunk_surface, (screen_x, screen_y))
        self.chunks_rendered += 1

    def _render_chunk_to_surface(self, chunk) -> pygame.Surface:
        """Render a chunk to a surface for caching."""
        config = self.config.world
        chunk_pixel_size = config.chunk_size * config.block_size

        surface = pygame.Surface(
            (chunk_pixel_size, chunk_pixel_size),
            pygame.SRCALPHA
        )

        # Render each block
        for y in range(config.chunk_size):
            for x in range(config.chunk_size):
                block_id = chunk.blocks[x, y]

                # Skip air blocks
                if block_id == 1:
                    continue

                # Get block texture
                texture = self.block_registry.get_texture(block_id, config.block_size)

                if texture:
                    surface.blit(
                        texture,
                        (x * config.block_size, y * config.block_size)
                    )

        return surface

    def render_entities(self, entities: List[Entity]) -> None:
        """Render all entities with sprite components."""
        self.entity_layer.fill((0, 0, 0, 0))
        self.sprites_rendered = 0

        # Get visible bounds for culling
        left, top, right, bottom = self.camera.get_visible_bounds()

        for entity in entities:
            if not entity.active:
                continue

            # Check if entity has required components
            if not entity.has_component(TransformComponent):
                continue
            if not entity.has_component(SpriteComponent):
                continue

            transform = entity.get_component(TransformComponent)
            sprite_comp = entity.get_component(SpriteComponent)

            # Cull off-screen entities
            if not (left <= transform.x <= right and top <= transform.y <= bottom):
                continue

            # Get sprite
            sprite = sprite_comp.get_current_sprite()
            if not sprite:
                continue

            # Convert to screen coordinates
            screen_x, screen_y = self.camera.world_to_screen(transform.x, transform.y)

            # Center sprite
            screen_x -= sprite.get_width() // 2
            screen_y -= sprite.get_height() // 2

            # Blit sprite
            self.entity_layer.blit(sprite, (screen_x, screen_y))
            self.sprites_rendered += 1

    def render_ui(self, ui_elements: List) -> None:
        """Render UI elements (health bars, inventory, etc.)."""
        self.ui_layer.fill((0, 0, 0, 0))

        # UI rendering will be handled by UI system
        # This is just a placeholder
        pass

    def composite_and_present(self) -> None:
        """
        Composite all layers and present to screen.

        Layering order:
        1. Background (sky)
        2. World (blocks)
        3. Lighting
        4. Entities
        5. UI
        """
        # Clear screen
        self.screen.fill(self._get_sky_color())

        # Blit world layer
        self.screen.blit(self.world_layer, (0, 0))

        # Apply lighting
        self.lighting.render(self.screen, camera_offset=(self.camera.x, self.camera.y))

        # Blit entity layer
        self.screen.blit(self.entity_layer, (0, 0))

        # Blit UI layer
        self.screen.blit(self.ui_layer, (0, 0))

        # Debug info
        if self.config.debug_mode and self.config.show_fps:
            self._draw_debug_info()

    def _get_sky_color(self) -> Tuple[int, int, int]:
        """Get the current sky color based on time of day."""
        # TODO: Sync with lighting time of day
        return (135, 206, 235)  # Sky blue

    def _draw_debug_info(self) -> None:
        """Draw debug information."""
        font = pygame.font.SysFont("monospace", 14)

        debug_lines = [
            f"Camera: ({self.camera.x:.1f}, {self.camera.y:.1f})",
            f"Chunks: {self.chunks_rendered}",
            f"Sprites: {self.sprites_rendered}",
        ]

        y_offset = 10
        for line in debug_lines:
            text = font.render(line, True, (255, 255, 255))
            # Draw shadow
            self.screen.blit(text, (11, y_offset + 1))
            # Draw text
            text = font.render(line, True, (0, 255, 0))
            self.screen.blit(text, (10, y_offset))
            y_offset += 20

    def clear_chunk_cache(self) -> None:
        """Clear the chunk rendering cache."""
        self._chunk_surfaces.clear()

    def resize(self, width: int, height: int) -> None:
        """Handle screen resize."""
        self.width = width
        self.height = height

        self.camera.width = width
        self.camera.height = height

        # Recreate layers
        self.background_layer = pygame.Surface((width, height))
        self.world_layer = pygame.Surface((width, height), pygame.SRCALPHA)
        self.entity_layer = pygame.Surface((width, height), pygame.SRCALPHA)
        self.ui_layer = pygame.Surface((width, height), pygame.SRCALPHA)

        # Resize lighting
        self.lighting.resize((width, height))
