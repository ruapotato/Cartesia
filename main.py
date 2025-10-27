#!/usr/bin/env python3
"""
Cartesia - Noita meets Starbound!

A complete sandbox game where:
- The entire world is made of falling sand physics (Noita-style)
- Infinite procedural world generation with Perlin noise (Starbound-style)
- Fast performance with Numba JIT compilation

Run with: python main.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import pygame
import numpy as np
from cartesia.config import get_config
from cartesia.engine.falling_sand import FallingSandEngine, Material
from cartesia.engine.physics_v2 import PhysicsBody, PhysicsConfig
from cartesia.entities.player_animation import create_player_animation


class SandPhysicsEngine:
    """Physics engine that collides with falling sand pixels."""

    def __init__(self, sand_engine: FallingSandEngine):
        self.sand = sand_engine

    def update(self, body: PhysicsBody, dt: float) -> None:
        """Update physics with pixel-perfect collision."""
        # Update timers
        if not body.on_ground:
            body.coyote_timer -= dt
        else:
            body.coyote_timer = body.config.coyote_time

        if body.jump_buffer_timer > 0:
            body.jump_buffer_timer -= dt

        # Handle jump input
        if body.jump_pressed:
            body.jump_buffer_timer = body.config.jump_buffer_time
            body.jump_pressed = False

        # Apply horizontal movement
        self._apply_horizontal_movement(body, dt)

        # Apply gravity and jumping
        self._apply_gravity_and_jump(body, dt)

        # Move and handle collision
        self._move_with_collision(body, dt)

        # Update facing direction
        if body.move_input < 0:
            body.facing = -1
        elif body.move_input > 0:
            body.facing = 1

    def _apply_horizontal_movement(self, body: PhysicsBody, dt: float) -> None:
        """Apply horizontal acceleration and friction."""
        if body.on_ground:
            acceleration = body.config.ground_acceleration
            friction = body.config.ground_friction
        else:
            acceleration = body.config.air_acceleration
            friction = body.config.air_friction

        # Apply input acceleration
        if body.move_input != 0:
            body.vx += body.move_input * acceleration * dt
        else:
            # Apply friction
            import math
            if abs(body.vx) > friction * dt * 60:
                body.vx -= math.copysign(friction * dt * 60, body.vx)
            else:
                body.vx = 0

        # Clamp to max speed
        body.vx = max(-body.config.max_run_speed, min(body.config.max_run_speed, body.vx))

    def _apply_gravity_and_jump(self, body: PhysicsBody, dt: float) -> None:
        """Apply gravity and handle jumping."""
        # Check if we should execute a buffered jump
        if body.jump_buffer_timer > 0 and body.can_jump():
            body.vy = -body.config.jump_speed  # Negative = up in screen coords
            body.jump_buffer_timer = 0
            body.coyote_timer = 0
            body.on_ground = False

        # Apply gravity (positive = down in screen coords)
        if body.vy < 0 and body.jump_held:
            # Holding jump = lower gravity (higher jump)
            gravity = body.config.jump_hold_gravity
        else:
            # Not holding jump or falling = higher gravity (fast fall)
            gravity = body.config.jump_release_gravity

        body.vy += gravity * dt

        # Jump cut (release jump to fall faster)
        if not body.jump_held and body.vy < -body.config.jump_cut_speed:
            body.vy = -body.config.jump_cut_speed

        # Clamp fall speed
        body.vy = min(body.config.max_fall_speed, body.vy)

    def _move_with_collision(self, body: PhysicsBody, dt: float) -> None:
        """Move body and handle pixel-perfect collision."""
        # Move X
        dx = body.vx * dt
        new_x = body.x + dx

        # Check X collision
        if self._check_collision_at(new_x, body.y, body.width, body.height):
            body.vx = 0
        else:
            body.x = new_x

        # Move Y
        dy = body.vy * dt
        new_y = body.y + dy

        # Check Y collision
        if self._check_collision_at(body.x, new_y, body.width, body.height):
            if dy > 0:
                # Moving down - hit ground
                body.vy = 0
                body.on_ground = True
            else:
                # Moving up - hit ceiling
                body.vy = 0
        else:
            body.y = new_y
            # Check if still on ground
            if body.on_ground:
                if not self._check_collision_at(body.x, body.y + 2, body.width, body.height):
                    body.on_ground = False

    def _check_collision_at(self, x: float, y: float, width: float, height: float) -> bool:
        """Check collision with sand pixels."""
        # Check corners and edges
        check_points = [
            (x + 2, y + 2),  # Top-left
            (x + width - 2, y + 2),  # Top-right
            (x + 2, y + height - 2),  # Bottom-left
            (x + width - 2, y + height - 2),  # Bottom-right
            (x + width/2, y + height - 2),  # Bottom-middle (for ground)
        ]

        for px, py in check_points:
            if self.sand.is_solid_at(int(px), int(py)):
                return True

        return False


class CartesiaGame:
    """
    Cartesia - The ultimate sandbox game!

    Combines:
    - Noita-style falling sand physics
    - Starbound-style world generation and movement
    - 120+ FPS performance with Numba
    """

    def __init__(self):
        # Config
        self.config = get_config()

        # Initialize pygame
        pygame.init()
        self.width = self.config.display.width
        self.height = self.config.display.height
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Cartesia - Noita meets Starbound!")
        self.clock = pygame.time.Clock()

        # Create large world for exploration (Starbound-style!)
        world_width = self.width * 4
        world_height = self.height * 2

        print(f"Creating world: {world_width}x{world_height} pixels...")
        self.sand = FallingSandEngine(world_width, world_height, cell_size=2)

        # Physics engine for player
        self.physics = SandPhysicsEngine(self.sand)

        # Start player in center of world, middle height
        spawn_x = world_width // 2
        spawn_y = world_height // 2  # Start in middle, will fall to ground

        # Setup terrain generator for on-demand generation
        from cartesia.world.generation import TerrainGenerator
        self.terrain_generator = TerrainGenerator(self.config.world.seed, self.config)

        # Track which chunks are generated
        self.generated_chunks = set()
        self.chunk_size = 150  # Larger chunks = fewer generations

        # Terrain generation timer (don't generate every frame!)
        self.terrain_gen_timer = 0.0

        # Generate initial area around player (fast!)
        print("Generating starting area...")
        self._generate_chunks_around(spawn_x, spawn_y, radius=2)
        print("World ready - terrain will generate as you explore!")

        # Player
        self.player = self._create_player_body(spawn_x, spawn_y)
        self.player_animation = create_player_animation()

        # Camera (follows player)
        self.camera_x = spawn_x
        self.camera_y = spawn_y

        # Current material to place
        self.current_material = Material.DIRT
        self.brush_size = 10

        # Input state
        self.mouse_down = False
        self.right_mouse_down = False

        # Running
        self.running = True

    def _generate_chunks_around(self, center_x: int, center_y: int, radius: int = 2):
        """Generate terrain chunks around a position."""
        # Convert pixel coords to chunk coords
        center_chunk_x = center_x // (self.chunk_size * self.sand.cell_size)
        center_chunk_y = center_y // (self.chunk_size * self.sand.cell_size)

        # Generate chunks in a radius
        for chunk_y in range(center_chunk_y - radius, center_chunk_y + radius + 1):
            for chunk_x in range(center_chunk_x - radius, center_chunk_x + radius + 1):
                chunk_key = (chunk_x, chunk_y)

                # Skip if already generated
                if chunk_key in self.generated_chunks:
                    continue

                # Generate this chunk
                self._generate_chunk(chunk_x, chunk_y)
                self.generated_chunks.add(chunk_key)

    def _generate_chunk(self, chunk_x: int, chunk_y: int):
        """Generate a single chunk of terrain."""
        # Calculate grid coordinates for this chunk
        start_grid_x = chunk_x * self.chunk_size
        start_grid_y = chunk_y * self.chunk_size
        end_grid_x = min(start_grid_x + self.chunk_size, self.sand.grid_width)
        end_grid_y = min(start_grid_y + self.chunk_size, self.sand.grid_height)

        # Skip if out of bounds
        if start_grid_x >= self.sand.grid_width or start_grid_y >= self.sand.grid_height:
            return
        if start_grid_x < 0 or start_grid_y < 0:
            return

        # Generate terrain for this chunk
        for grid_x in range(start_grid_x, end_grid_x):
            for grid_y in range(start_grid_y, end_grid_y):
                # Convert grid coords to world coords
                world_x = grid_x * self.sand.cell_size / self.config.world.block_size

                # FLIP Y AXIS! Screen Y increases downward, but world Y increases upward
                # Map grid_y so that bottom of screen = high Y values in world space
                world_y = (self.sand.grid_height - grid_y) * self.sand.cell_size / self.config.world.block_size

                # Get depth from Perlin noise
                depth = self.terrain_generator.get_solid_depth_at(world_x, world_y)

                if depth <= 0:
                    self.sand.cells[grid_x, grid_y] = Material.AIR
                elif depth < 0.5:
                    self.sand.cells[grid_x, grid_y] = Material.DIRT
                elif depth < 3.0:
                    self.sand.cells[grid_x, grid_y] = Material.DIRT
                else:
                    self.sand.cells[grid_x, grid_y] = Material.STONE

        # Mark surface cells as active in this chunk
        for grid_x in range(start_grid_x, end_grid_x):
            for grid_y in range(start_grid_y + 1, end_grid_y):
                if self.sand.cells[grid_x, grid_y] != Material.AIR:
                    if grid_y > 0 and self.sand.cells[grid_x, grid_y - 1] == Material.AIR:
                        self.sand.active[grid_x, grid_y] = True

    def _create_player_body(self, x: float, y: float) -> PhysicsBody:
        """Create player physics body."""
        config = PhysicsConfig(
            ground_acceleration=1200.0,
            air_acceleration=800.0,
            ground_friction=20.0,
            max_run_speed=180.0,
            jump_speed=340.0,
            coyote_time=0.15,
            jump_buffer_time=0.1,
        )

        return PhysicsBody(x, y, width=24, height=48, config=config)

    def run(self):
        """Main game loop - FAST!"""
        while self.running:
            dt = self.clock.tick(120) / 1000.0
            dt = min(dt, 0.016)  # Cap at 60 FPS physics

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

                # Material selection
                elif event.key == pygame.K_1:
                    self.current_material = Material.DIRT
                elif event.key == pygame.K_2:
                    self.current_material = Material.SAND
                elif event.key == pygame.K_3:
                    self.current_material = Material.WATER
                elif event.key == pygame.K_4:
                    self.current_material = Material.STONE
                elif event.key == pygame.K_5:
                    self.current_material = Material.LAVA

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click - mine
                    self.mouse_down = True
                elif event.button == 3:  # Right click - place
                    self.right_mouse_down = True

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    self.mouse_down = False
                elif event.button == 3:
                    self.right_mouse_down = False

    def update(self, dt: float):
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

        # Update camera (smooth follow)
        target_camera_x = self.player.center_x
        target_camera_y = self.player.center_y

        self.camera_x += (target_camera_x - self.camera_x) * 0.1
        self.camera_y += (target_camera_y - self.camera_y) * 0.1

        # Generate terrain around player as they explore (but not every frame!)
        self.terrain_gen_timer += dt
        if self.terrain_gen_timer >= 0.2:  # Generate every 0.2 seconds (5 times per second)
            self._generate_chunks_around(int(self.player.center_x), int(self.player.center_y), radius=2)
            self.terrain_gen_timer = 0.0

        # Mining/placing with mouse
        mouse_x, mouse_y = pygame.mouse.get_pos()

        # Convert screen coords to world coords (accounting for camera)
        world_x = int(mouse_x - self.width // 2 + self.camera_x)
        world_y = int(mouse_y - self.height // 2 + self.camera_y)

        if self.mouse_down:
            # Mine (destroy sand)
            self.sand.spawn_circle(world_x, world_y, self.brush_size, Material.AIR)
            self.sand.dirty = True
        elif self.right_mouse_down:
            # Place
            self.sand.spawn_circle(world_x, world_y, self.brush_size, self.current_material)
            self.sand.dirty = True

        # Update falling sand simulation at 60 FPS (half rendering rate for performance!)
        if not hasattr(self, '_sand_timer'):
            self._sand_timer = 0.0

        self._sand_timer += dt
        if self._sand_timer >= 1.0 / 60.0:  # 60 physics updates per second
            self.sand.update(self._sand_timer)
            self._sand_timer = 0.0

    def render(self):
        """Render everything."""
        # Clear
        self.screen.fill((135, 206, 235))  # Sky blue

        # Render falling sand world with camera following player
        self.sand.render(self.screen, self.camera_x, self.camera_y, 1.0)

        # Render player at center of screen (camera follows)
        player_screen_x = int(self.player.center_x - self.camera_x + self.width // 2)
        player_screen_y = int(self.player.center_y - self.camera_y + self.height // 2)

        # Render animated player sprite
        self.player_animation.render(self.screen, player_screen_x, player_screen_y, scale=0.75)

        # Debug: Draw player collision box
        hitbox_x = int(self.player.x - self.camera_x + self.width // 2)
        hitbox_y = int(self.player.y - self.camera_y + self.height // 2)
        pygame.draw.rect(self.screen, (255, 0, 0),
                        (hitbox_x, hitbox_y,
                         int(self.player.width), int(self.player.height)), 2)

        # Render UI
        self.render_ui()

    def render_ui(self):
        """Render UI overlay."""
        font = pygame.font.SysFont("monospace", 14)
        y = 10

        material_names = {
            Material.DIRT: "Dirt",
            Material.SAND: "Sand",
            Material.WATER: "Water",
            Material.STONE: "Stone",
            Material.LAVA: "Lava",
        }

        info = [
            f"FPS: {int(self.clock.get_fps())}",
            f"Position: ({int(self.player.x)}, {int(self.player.y)})",
            f"Material: {material_names[self.current_material]} (1-5)",
            f"On Ground: {self.player.on_ground}",
            "",
            "WASD/Arrows: Move",
            "Space: Jump",
            "Left Click: Mine",
            "Right Click: Place",
        ]

        for line in info:
            text = font.render(line, True, (255, 255, 255))
            shadow = font.render(line, True, (0, 0, 0))
            self.screen.blit(shadow, (11, y + 1))
            self.screen.blit(text, (10, y))
            y += 20


if __name__ == "__main__":
    print("=" * 60)
    print("CARTESIA - Noita meets Starbound!")
    print("=" * 60)
    print("Loading...")

    game = CartesiaGame()

    print("Game loaded! Starting...")
    print("=" * 60)

    game.run()
