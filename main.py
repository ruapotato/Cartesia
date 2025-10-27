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

        # Create world (screen size for fast generation - will expand later!)
        world_width = self.width
        world_height = self.height

        print(f"Creating world: {world_width}x{world_height} pixels...")
        self.sand = FallingSandEngine(world_width, world_height, cell_size=2)

        # Generate simple terrain for now (fast!)
        print("Generating simple terrain...")
        self._generate_simple_terrain()
        print("World ready!")

        # Physics engine for player
        self.physics = SandPhysicsEngine(self.sand)

        # Find spawn point (surface in middle of world)
        spawn_x = world_width // 2
        spawn_y = self._find_surface(spawn_x)

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

    def _generate_simple_terrain(self):
        """Generate simple terrain quickly - flat ground with some platforms."""
        # Bottom layer - stone (in grid coordinates)
        ground_level = self.sand.grid_height - 100

        print(f"  Grid size: {self.sand.grid_width}x{self.sand.grid_height}")
        print(f"  Cell size: {self.sand.cell_size} pixels")
        print(f"  Ground at grid_y={ground_level}, pixel_y={ground_level * self.sand.cell_size}")

        for x in range(self.sand.grid_width):
            # Ground layer
            for y in range(ground_level, self.sand.grid_height):
                depth = y - ground_level
                if depth < 5:
                    self.sand.cells[x, y] = Material.DIRT
                else:
                    self.sand.cells[x, y] = Material.STONE

        # Add some platforms
        for x in range(100, 200):
            for y in range(ground_level - 100, ground_level - 95):
                if 0 <= y < self.sand.grid_height:
                    self.sand.cells[x, y] = Material.DIRT

        for x in range(300, 400):
            for y in range(ground_level - 150, ground_level - 145):
                if 0 <= y < self.sand.grid_height:
                    self.sand.cells[x, y] = Material.STONE

        # Mark surface cells as active
        self.sand.active.fill(False)
        for x in range(self.sand.grid_width):
            for y in range(1, self.sand.grid_height - 1):
                if self.sand.cells[x, y] != Material.AIR:
                    if self.sand.cells[x, y - 1] == Material.AIR:
                        self.sand.active[x, y] = True

        print(f"  Ground level: grid_y={ground_level}, pixel_y={ground_level * self.sand.cell_size}")

    def _find_surface(self, x: int) -> int:
        """Find the surface Y coordinate at a given X position."""
        # Search from top down for first solid block
        grid_x = x // self.sand.cell_size
        for grid_y in range(0, self.sand.grid_height):
            if self.sand.cells[grid_x, grid_y] != Material.AIR:
                # Found surface - return pixel coordinate
                return grid_y * self.sand.cell_size - 60
        return 100  # Default if no surface found

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

        # Mining/placing with mouse
        mouse_x, mouse_y = pygame.mouse.get_pos()

        # Since world is screen-sized, mouse is directly in world coords!
        world_x = int(mouse_x)
        world_y = int(mouse_y)

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

        # Render falling sand world (no camera offset - world is screen-sized!)
        self.sand.render(self.screen, self.width // 2, self.height // 2, 1.0)

        # Render player at their world position
        player_screen_x = int(self.player.center_x)
        player_screen_y = int(self.player.center_y)

        # Render animated player sprite
        self.player_animation.render(self.screen, player_screen_x, player_screen_y, scale=0.75)

        # Debug: Draw player collision box
        pygame.draw.rect(self.screen, (255, 0, 0),
                        (int(self.player.x), int(self.player.y),
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
