#!/usr/bin/env python3
"""
Starbound-style Cartesia - Complete rewrite.

Run with: python play_v2.py

This uses the new physics, inventory, and mining systems!
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import pygame
from cartesia.config import get_config
from cartesia.world.chunk import ChunkManager
from cartesia.world.blocks import get_block_registry
from cartesia.engine.lighting import LightingEngine
from cartesia.engine.physics_v2 import PhysicsEngine, create_player_body
from cartesia.systems.inventory import Inventory
from cartesia.systems.mining import MiningSystem
from cartesia.entities.player_animation import create_player_animation
from cartesia.engine.smooth_terrain import get_smooth_renderer


class Game:
    """Complete Starbound-style game."""

    def __init__(self):
        # Config
        self.config = get_config()

        # Initialize pygame
        pygame.init()
        self.screen = pygame.display.set_mode(
            (self.config.display.width, self.config.display.height)
        )
        pygame.display.set_caption("Cartesia - Starbound Style")
        self.clock = pygame.time.Clock()

        # Core systems
        self.chunk_manager = ChunkManager(self.config.world.seed)
        self.block_registry = get_block_registry()
        self.physics = PhysicsEngine(self.chunk_manager, self.config.world.block_size)
        self.lighting = LightingEngine(
            (self.config.display.width, self.config.display.height),
            self.config.lighting
        )
        self.mining = MiningSystem(self.chunk_manager, self.block_registry)
        self.smooth_renderer = get_smooth_renderer()

        # Chunk render cache
        self.chunk_render_cache = {}  # (chunk_x, chunk_y) -> pygame.Surface

        # Player - spawn on ground
        spawn_x = 0
        spawn_y = self._find_spawn_y(spawn_x)
        self.player = create_player_body(spawn_x, spawn_y)
        self.inventory = Inventory()
        self.player_animation = create_player_animation()

        # Give player starting items
        self.inventory.add_item("pickaxe_wood", 1)
        self.inventory.add_item("dirt", 99)
        self.inventory.add_item("torch", 20)

        # Camera
        self.camera_x = 0
        self.camera_y = 0
        self.zoom = 1.0  # Zoom level (1.0 = normal, 2.0 = 2x zoomed in)

        # Input state
        self.mouse_down = False
        self.right_mouse_down = False

        # Running
        self.running = True

    def _find_spawn_y(self, spawn_x: float) -> float:
        """Find the Y coordinate to spawn the player on the ground."""
        from cartesia.world.generation import TerrainGenerator

        # Initialize terrain generator
        generator = TerrainGenerator(self.config.world.seed, self.config)

        # Search upward from y=-100 to find the surface (where depth becomes 0)
        for world_y in range(-100, 100):
            depth = generator.get_solid_depth_at(spawn_x, world_y)
            if depth == 0 or depth < 0.1:
                # Found the surface - spawn player just above it
                return (world_y - 1) * self.config.world.block_size

        # If no ground found, use default
        return -200

    def run(self):
        """Main game loop."""
        while self.running:
            dt = self.clock.tick(60) / 1000.0
            dt = min(dt, 0.1)

            self.handle_events()
            self.update(dt)
            self.render()

            pygame.display.flip()

        pygame.quit()

    def handle_events(self):
        """Handle input."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False

                # Hotbar selection
                if pygame.K_1 <= event.key <= pygame.K_9:
                    self.inventory.selected_slot = event.key - pygame.K_1

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    self.mouse_down = True
                elif event.button == 3:  # Right click
                    self.right_mouse_down = True

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    self.mouse_down = False
                elif event.button == 3:
                    self.right_mouse_down = False

            elif event.type == pygame.MOUSEWHEEL:
                # Zoom in/out with mouse wheel
                if event.y > 0:  # Scroll up
                    self.zoom = min(self.zoom * 1.1, 4.0)
                elif event.y < 0:  # Scroll down
                    self.zoom = max(self.zoom / 1.1, 0.25)

    def update(self, dt):
        """Update game state."""
        # Player input
        keys = pygame.key.get_pressed()

        # Movement
        self.player.move_input = 0
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            self.player.move_input -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            self.player.move_input += 1

        # Jumping
        if keys[pygame.K_SPACE] or keys[pygame.K_w] or keys[pygame.K_UP]:
            if not self.player.jump_held:
                self.player.jump_pressed = True
            self.player.jump_held = True
        else:
            self.player.jump_held = False

        # Update physics
        self.physics.update(self.player, dt)

        # Update player animation
        self.player_animation.update(dt, self.player.vx, self.player.vy, self.player.on_ground)

        # Update camera (smooth following)
        target_camera_x = self.player.center_x
        target_camera_y = self.player.center_y

        self.camera_x += (target_camera_x - self.camera_x) * 0.1
        self.camera_y += (target_camera_y - self.camera_y) * 0.1

        # Mining/placing
        mouse_x, mouse_y = pygame.mouse.get_pos()
        # Convert screen coords to world coords (Y-axis is inverted)
        world_x = mouse_x + self.camera_x - self.config.display.width // 2
        world_y = (self.config.display.height // 2 - mouse_y) + self.camera_y

        # Snap to block grid
        block_x = int(world_x // self.config.world.block_size) * self.config.world.block_size
        block_y = int(world_y // self.config.world.block_size) * self.config.world.block_size

        if self.mouse_down:
            # Mining
            item_def = self.inventory.get_selected_item_def()

            if item_def and item_def.tool_type:
                tool_type = item_def.tool_type.value
                tool_power = item_def.tool_power
            else:
                tool_type = None
                tool_power = 1

            dropped_item = self.mining.mine_block(
                block_x, block_y,
                self.player.center_x, self.player.center_y,
                tool_type, tool_power, dt
            )

            if dropped_item:
                item_id, quantity = dropped_item
                self.inventory.add_item(item_id, quantity)
                # Damage tool
                if item_def and item_def.tool_type:
                    self.inventory.damage_selected_tool()

        elif self.right_mouse_down:
            # Placing
            selected = self.inventory.get_selected_item()
            item_def = self.inventory.get_selected_item_def()

            if selected and item_def and item_def.placeable_block_id:
                success = self.mining.place_block(
                    block_x, block_y,
                    self.player.center_x, self.player.center_y,
                    item_def.placeable_block_id
                )

                if success:
                    self.inventory.remove_item(item_def.id, 1)

        # Update mining system
        self.mining.update(dt)

        # Update lighting
        self.lighting.set_time_of_day(0.5)  # Noon for now
        self.lighting.update(dt)

    def render(self):
        """Render everything."""
        # Clear
        self.screen.fill((135, 206, 235))  # Sky blue

        # Calculate visible chunks (adjusted for zoom)
        chunk_size_px = self.config.world.chunk_size * self.config.world.block_size

        # Expand view distance based on zoom
        view_width = self.config.display.width / self.zoom
        view_height = self.config.display.height / self.zoom

        # Render chunks
        start_chunk_x = int((self.camera_x - view_width // 2) // chunk_size_px) - 1
        end_chunk_x = int((self.camera_x + view_width // 2) // chunk_size_px) + 2
        start_chunk_y = int((self.camera_y - view_height // 2) // chunk_size_px) - 1
        end_chunk_y = int((self.camera_y + view_height // 2) // chunk_size_px) + 2

        for chunk_y in range(start_chunk_y, end_chunk_y + 1):
            for chunk_x in range(start_chunk_x, end_chunk_x + 1):
                self.render_chunk(chunk_x, chunk_y)

        # Render player
        # Convert world coords to screen coords (Y-axis is inverted) with zoom
        player_screen_x = int((self.player.center_x - self.camera_x) * self.zoom + self.config.display.width // 2)
        player_screen_y = int(self.config.display.height // 2 - (self.player.center_y - self.camera_y) * self.zoom)

        # Render animated player sprite (scale based on zoom)
        player_sprite_scale = 0.75 * self.zoom  # Make player bigger
        self.player_animation.render(self.screen, player_screen_x, player_screen_y, scale=player_sprite_scale)

        # Debug: Draw player collision box
        hitbox_screen_x = int((self.player.x - self.camera_x) * self.zoom + self.config.display.width // 2)
        hitbox_screen_y = int(self.config.display.height // 2 - (self.player.y - self.camera_y) * self.zoom)
        hitbox_w = int(self.player.width * self.zoom)
        hitbox_h = int(self.player.height * self.zoom)
        pygame.draw.rect(self.screen, (255, 0, 0), (hitbox_screen_x, hitbox_screen_y, hitbox_w, hitbox_h), 2)

        # Render UI
        self.render_ui()

        # Debug info
        self.render_debug()

    def render_chunk(self, chunk_x: int, chunk_y: int):
        """Render a single chunk - simple block rendering for now."""
        chunk = self.chunk_manager.get_chunk(chunk_x, chunk_y)
        if not chunk:
            return

        chunk_world_x = chunk_x * self.config.world.chunk_size * self.config.world.block_size
        chunk_world_y = chunk_y * self.config.world.chunk_size * self.config.world.block_size

        block_size = self.config.world.block_size

        for local_y in range(self.config.world.chunk_size):
            for local_x in range(self.config.world.chunk_size):
                block_id = chunk.blocks[local_x, local_y]

                # Skip air blocks
                texture = self.block_registry.get_texture(block_id, block_size)
                if not texture:
                    continue

                block_world_x = chunk_world_x + local_x * block_size
                block_world_y = chunk_world_y + local_y * block_size

                # Convert world coords to screen coords with zoom
                screen_x = int((block_world_x - self.camera_x) * self.zoom + self.config.display.width // 2)
                screen_y = int(self.config.display.height // 2 - (block_world_y - self.camera_y) * self.zoom)

                # Scale block based on zoom
                if abs(self.zoom - 1.0) > 0.01:
                    scaled_size = int(block_size * self.zoom)
                    texture = pygame.transform.scale(texture, (scaled_size, scaled_size))

                # Render block
                self.screen.blit(texture, (screen_x, screen_y))

    def render_ui(self):
        """Render UI overlay."""
        # Hotbar
        hotbar_x = self.config.display.width // 2 - (self.inventory.hotbar_size * 40) // 2
        hotbar_y = self.config.display.height - 60

        for i in range(self.inventory.hotbar_size):
            # Slot background
            color = (100, 100, 100) if i != self.inventory.selected_slot else (200, 200, 200)
            pygame.draw.rect(self.screen, color, (
                hotbar_x + i * 40,
                hotbar_y,
                36,
                36
            ))

            # Item in slot
            item = self.inventory.hotbar[i]
            if item:
                item_def = self.inventory.registry.get(item.item_id)
                if item_def and item_def.icon:
                    icon = pygame.transform.scale(item_def.icon, (32, 32))
                    self.screen.blit(icon, (hotbar_x + i * 40 + 2, hotbar_y + 2))

                # Quantity
                if item.quantity > 1:
                    font = pygame.font.SysFont("monospace", 14)
                    text = font.render(str(item.quantity), True, (255, 255, 255))
                    self.screen.blit(text, (hotbar_x + i * 40 + 20, hotbar_y + 20))

            # Slot number
            font = pygame.font.SysFont("monospace", 12)
            text = font.render(str(i + 1), True, (255, 255, 255))
            self.screen.blit(text, (hotbar_x + i * 40 + 2, hotbar_y - 15))

    def render_debug(self):
        """Render debug info."""
        font = pygame.font.SysFont("monospace", 14)
        y = 10

        # Calculate player's chunk
        chunk_size_px = self.config.world.chunk_size * self.config.world.block_size
        player_chunk_x = int(self.player.center_x // chunk_size_px)
        player_chunk_y = int(self.player.center_y // chunk_size_px)

        debug_info = [
            f"FPS: {int(self.clock.get_fps())}",
            f"Player: ({self.player.x:.1f}, {self.player.y:.1f})",
            f"Player Chunk: ({player_chunk_x}, {player_chunk_y})",
            f"Velocity: ({self.player.vx:.1f}, {self.player.vy:.1f})",
            f"On Ground: {self.player.on_ground}",
            f"Zoom: {self.zoom:.2f}x",
        ]

        for line in debug_info:
            text = font.render(line, True, (255, 255, 255))
            # Shadow
            self.screen.blit(text, (11, y + 1))
            # Text
            text = font.render(line, True, (0, 255, 0))
            self.screen.blit(text, (10, y))
            y += 20


if __name__ == "__main__":
    game = Game()
    game.run()
