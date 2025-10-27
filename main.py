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
from numba import njit
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
        # Check if player is in water
        in_water = self._check_in_water(body)

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
        self._apply_horizontal_movement(body, dt, in_water)

        # Apply gravity and jumping
        self._apply_gravity_and_jump(body, dt, in_water)

        # Move and handle collision
        self._move_with_collision(body, dt)

        # Update facing direction
        if body.move_input < 0:
            body.facing = -1
        elif body.move_input > 0:
            body.facing = 1

    def _apply_horizontal_movement(self, body: PhysicsBody, dt: float, in_water: bool = False) -> None:
        """Apply horizontal acceleration and friction."""
        if in_water:
            # Swimming - slower movement with high friction
            acceleration = body.config.air_acceleration * 0.7
            friction = body.config.ground_friction * 1.5
        elif body.on_ground:
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
        max_speed = body.config.max_run_speed * 0.6 if in_water else body.config.max_run_speed
        body.vx = max(-max_speed, min(max_speed, body.vx))

    def _apply_gravity_and_jump(self, body: PhysicsBody, dt: float, in_water: bool = False) -> None:
        """Apply gravity and handle jumping."""
        if in_water:
            # Swimming mechanics
            if body.jump_buffer_timer > 0:
                # Swim up
                body.vy = -body.config.jump_speed * 0.5  # Slower swim up
                body.jump_buffer_timer = 0

            # Reduced gravity in water (buoyancy)
            gravity = body.config.jump_hold_gravity * 0.2
            body.vy += gravity * dt

            # Clamp swim speed (slower than falling)
            body.vy = max(-body.config.jump_speed * 0.5, min(body.config.max_fall_speed * 0.3, body.vy))

        else:
            # Normal land/air physics
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
        """Check collision with sand pixels - MORE ROBUST for slopes!"""
        # Clamp coordinates to world bounds to prevent drift issues
        max_x = (self.sand.grid_width * self.sand.cell_size) - 1
        max_y = (self.sand.grid_height * self.sand.cell_size) - 1

        # Check MORE points for better slope handling
        check_points = [
            # Top edge
            (max(0, min(x + 2, max_x)), max(0, min(y + 2, max_y))),
            (max(0, min(x + width/2, max_x)), max(0, min(y + 2, max_y))),
            (max(0, min(x + width - 2, max_x)), max(0, min(y + 2, max_y))),

            # Bottom edge (MORE POINTS for ground detection!)
            (max(0, min(x + 2, max_x)), max(0, min(y + height - 1, max_y))),
            (max(0, min(x + width/4, max_x)), max(0, min(y + height - 1, max_y))),
            (max(0, min(x + width/2, max_x)), max(0, min(y + height - 1, max_y))),
            (max(0, min(x + width*3/4, max_x)), max(0, min(y + height - 1, max_y))),
            (max(0, min(x + width - 2, max_x)), max(0, min(y + height - 1, max_y))),

            # Sides
            (max(0, min(x + 2, max_x)), max(0, min(y + height/2, max_y))),
            (max(0, min(x + width - 2, max_x)), max(0, min(y + height/2, max_y))),
        ]

        for px, py in check_points:
            if self.sand.is_solid_at(int(px), int(py)):
                return True

        return False

    def _check_in_water(self, body: PhysicsBody) -> bool:
        """Check if player is submerged in water."""
        # Sample center of player hitbox
        center_x = int(body.center_x)
        center_y = int(body.center_y)

        # Convert to grid coordinates
        grid_x = center_x // self.sand.cell_size
        grid_y = center_y // self.sand.cell_size

        # Check bounds
        if grid_x < 0 or grid_x >= self.sand.grid_width:
            return False
        if grid_y < 0 or grid_y >= self.sand.grid_height:
            return False

        # Check if current cell is water
        return self.sand.cells[grid_x, grid_y] == Material.WATER


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

        # Performance profiling
        import time
        self.perf_timers = {}
        self.time_module = time

        # Create large world for exploration (Starbound-style!)
        # Wide for horizontal exploration, tall enough for deep digging AND high mountains
        world_width = self.width * 4
        world_height = self.height * 8  # 8x screen height for mountains and caves!

        print(f"Creating world: {world_width}x{world_height} pixels...")
        self.sand = FallingSandEngine(world_width, world_height, cell_size=6)  # Bigger cells = faster rendering!

        # Physics engine for player
        self.physics = SandPhysicsEngine(self.sand)

        # Start player in center of world, above ground level
        spawn_x = world_width // 2
        # Ground is at world Y=100 (see generation.py), spawn above it
        spawn_y = int(70 * self.sand.cell_size)  # Spawn above surface, will fall down

        # Setup terrain generator for on-demand generation
        from cartesia.world.generation import TerrainGenerator, generate_chunk as generate_terrain_chunk
        self.terrain_generator = TerrainGenerator(self.config.world.seed, self.config)

        # Track which chunks are generated
        self.generated_chunks = set()
        self.chunk_size = 32  # Larger chunks work better with vectorization!
        self.chunk_generation_radius = 12  # Generate further out

        # Physics simulation only runs near player for MASSIVE performance boost!
        self.physics_simulation_radius = 6  # Only simulate 6 chunks around player

        # Track chunks with all neighbors loaded (safe for physics)
        self.chunks_with_neighbors = set()

        # Chunk activity system - track last movement per chunk
        self.active_chunks = {}  # chunk_key -> frames since last movement
        self.chunk_settle_threshold = 60  # Deactivate after 60 frames (2 seconds) of no movement

        # Generate multiple chunks per frame (catch up fast!)
        self.chunk_queue = []
        self.chunks_per_frame = 50  # Generate 50 chunks per frame (flat world = BLAZING fast!)

        # Generate initial area around player (generate immediately for instant play!)
        print("Generating starting area...")
        self._queue_chunks_around(spawn_x, spawn_y)

        # Generate first wave immediately (no waiting!)
        print(f"  Generating {len(self.chunk_queue)} initial chunks...")
        chunks_to_generate = min(200, len(self.chunk_queue))  # Generate 200 chunks immediately (flat world = instant!)
        for i in range(chunks_to_generate):
            if self.chunk_queue:
                chunk_x, chunk_y = self.chunk_queue.pop(0)
                if i % 50 == 0:
                    print(f"    Generated {i}/{chunks_to_generate}...")
                self._generate_chunk(chunk_x, chunk_y)
                self.generated_chunks.add((chunk_x, chunk_y))

        print(f"World ready - {chunks_to_generate} chunks loaded, rest will stream in!")

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

        # Rain system
        import random
        self.raining = False
        self.rain_timer = 0.0
        self.rain_spawn_timer = 0.0
        self.rain_toggle_timer = random.uniform(10, 30)  # Random rain intervals
        self.random = random

        # Running
        self.running = True

    def _has_all_neighbors(self, chunk_x: int, chunk_y: int) -> bool:
        """Check if a chunk has all 8 neighbors loaded."""
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue  # Skip self
                neighbor = (chunk_x + dx, chunk_y + dy)
                if neighbor not in self.generated_chunks:
                    return False
        return True

    def _activate_chunk_if_safe(self, chunk_x: int, chunk_y: int):
        """Mark chunk as safe for physics if it has all neighbors loaded (but don't activate yet)."""
        if not self._has_all_neighbors(chunk_x, chunk_y):
            return

        # Mark as having neighbors (safe for physics, but not necessarily active)
        self.chunks_with_neighbors.add((chunk_x, chunk_y))

    def _reactivate_chunk_at_position(self, world_x: int, world_y: int):
        """Mark chunk and neighbors as active when player interacts."""
        # Convert world position to chunk coordinates
        grid_x = world_x // self.sand.cell_size
        grid_y = world_y // self.sand.cell_size
        chunk_x = grid_x // self.chunk_size
        chunk_y = grid_y // self.chunk_size

        # Mark this chunk and all 8 neighbors as active (reset movement timer)
        activated = 0
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                neighbor_chunk = (chunk_x + dx, chunk_y + dy)
                # Activate ANY generated chunk (don't require neighbors)
                if neighbor_chunk in self.generated_chunks:
                    self.active_chunks[neighbor_chunk] = 0  # Reset: just had movement
                    activated += 1

        if activated == 0:
            print(f"WARNING: No chunks activated at chunk ({chunk_x}, {chunk_y})! Generated: {len(self.generated_chunks)}")

    def _update_physics_simulation_area(self, player_chunk_x: int, player_chunk_y: int):
        """Activate physics on ALL active chunks (including rain!)"""
        # Deactivate ALL chunks
        self.sand.active.fill(False)

        # Track which chunks we're checking this frame
        chunks_to_simulate = []

        # Activate ALL chunks in active_chunks (not just near player!)
        # This ensures rain falls even if it spawns far from player
        for chunk_key in list(self.active_chunks.keys()):
            chunk_x, chunk_y = chunk_key

            # Skip if chunk wasn't generated
            if chunk_key not in self.generated_chunks:
                continue

            # Calculate grid coordinates
            start_grid_x = chunk_x * self.chunk_size
            start_grid_y = chunk_y * self.chunk_size
            end_grid_x = min(start_grid_x + self.chunk_size, self.sand.grid_width)
            end_grid_y = min(start_grid_y + self.chunk_size, self.sand.grid_height)

            # Skip if out of bounds
            if start_grid_x >= self.sand.grid_width or start_grid_y >= self.sand.grid_height:
                continue
            if end_grid_x <= 0 or end_grid_y <= 0:
                continue

            # Activate entire chunk for physics simulation
            self.sand.active[start_grid_x:end_grid_x, start_grid_y:end_grid_y] = True
            chunks_to_simulate.append(chunk_key)

        return chunks_to_simulate

    def _queue_chunks_around(self, center_x: int, center_y: int):
        """Queue chunks PRIORITIZING direction of movement - prevents falling into ungenerated areas!"""
        # Don't queue if we already have lots queued (prevents slowdown)
        if len(self.chunk_queue) > 50:
            return

        # Convert pixel coords to chunk coords
        center_chunk_x = center_x // (self.chunk_size * self.sand.cell_size)
        center_chunk_y = center_y // (self.chunk_size * self.sand.cell_size)

        # Determine movement direction for prioritization (only if player exists)
        if hasattr(self, 'player'):
            falling = self.player.vy > 100  # Falling fast
            moving_right = self.player.vx > 50
            moving_left = self.player.vx < -50
        else:
            # Initial generation - prioritize below
            falling = True
            moving_right = False
            moving_left = False

        # Priority chunks (in direction of movement)
        priority_chunks = []
        normal_chunks = []

        # Generate in expanding RINGS (spiral outward, ALL chunks!)
        radius = self.chunk_generation_radius
        for dist in range(radius + 1):
            for chunk_y in range(center_chunk_y - dist, center_chunk_y + dist + 1):
                for chunk_x in range(center_chunk_x - dist, center_chunk_x + dist + 1):
                    # Skip if not on current ring (except center)
                    if dist > 0 and abs(chunk_x - center_chunk_x) != dist and abs(chunk_y - center_chunk_y) != dist:
                        continue

                    chunk_key = (chunk_x, chunk_y)

                    # Skip if already generated or queued
                    if chunk_key in self.generated_chunks:
                        continue
                    if chunk_key in self.chunk_queue:
                        continue

                    # Prioritize chunks in direction of movement
                    is_priority = False
                    if falling and chunk_y > center_chunk_y:  # Below player
                        is_priority = True
                    elif moving_right and chunk_x > center_chunk_x:  # To the right
                        is_priority = True
                    elif moving_left and chunk_x < center_chunk_x:  # To the left
                        is_priority = True

                    if is_priority:
                        priority_chunks.append(chunk_key)
                    else:
                        normal_chunks.append(chunk_key)

        # Add priority chunks first, then normal chunks
        self.chunk_queue.extend(priority_chunks)
        self.chunk_queue.extend(normal_chunks)

    def _generate_chunk(self, chunk_x: int, chunk_y: int):
        """Generate a single chunk of terrain using Perlin noise!"""
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

        # Use Perlin noise generation for interesting terrain!
        from cartesia.world.generation import generate_chunk as generate_terrain_chunk
        blocks, entities = generate_terrain_chunk(chunk_x, chunk_y, self.config.world.seed, self.config)

        # Assign blocks to sand grid (blocks are already in correct Material enum values)
        actual_width = end_grid_x - start_grid_x
        actual_height = end_grid_y - start_grid_y
        self.sand.cells[start_grid_x:end_grid_x, start_grid_y:end_grid_y] = blocks[:actual_width, :actual_height]

        # DON'T activate immediately - only activate if all neighbors are loaded
        # This prevents materials from falling into ungenerated chunks!
        # Mark as inactive initially
        self.sand.active[start_grid_x:end_grid_x, start_grid_y:end_grid_y] = False

        # Try to activate this chunk (if neighbors are loaded)
        self._activate_chunk_if_safe(chunk_x, chunk_y)

        # Perlin terrain needs to settle, so mark as active if it has surface blocks
        # (This will be handled by player interaction)

        # Also check all neighbors - they might now have all their neighbors!
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue  # Skip self (already checked)
                neighbor_chunk = (chunk_x + dx, chunk_y + dy)
                if neighbor_chunk in self.generated_chunks:
                    # Try to activate this neighbor if it now has all neighbors
                    self._activate_chunk_if_safe(neighbor_chunk[0], neighbor_chunk[1])

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
        import time
        frame_count = 0
        frame_times = []

        while self.running:
            frame_start = time.perf_counter()

            dt = self.clock.tick(120) / 1000.0
            dt = min(dt, 0.016)  # Cap at 60 FPS physics

            self.handle_events()

            t1 = time.perf_counter()
            self.update(dt)
            t2 = time.perf_counter()

            self.render()
            t3 = time.perf_counter()

            pygame.display.flip()

            frame_end = time.perf_counter()
            frame_time = (frame_end - frame_start) * 1000
            frame_times.append(frame_time)
            frame_count += 1

            # Print stats every 30 frames
            if frame_count % 30 == 0:
                avg_frame = sum(frame_times[-30:]) / min(30, len(frame_times))
                update_time = (t2 - t1) * 1000
                render_time = (t3 - t2) * 1000
                print(f"Frame: {avg_frame:.1f}ms ({1000/avg_frame:.0f} FPS) | Update: {update_time:.1f}ms | Render: {render_time:.1f}ms", flush=True)

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

        # Clamp player position to world bounds (prevents collision issues at edges)
        world_max_x = (self.sand.grid_width * self.sand.cell_size) - self.player.width
        world_max_y = (self.sand.grid_height * self.sand.cell_size) - self.player.height
        self.player.x = max(0, min(self.player.x, world_max_x))
        self.player.y = max(0, min(self.player.y, world_max_y))

        # Update player animation
        self.player_animation.update(dt, self.player.vx, self.player.vy, self.player.on_ground)

        # Update camera (smooth follow)
        target_camera_x = self.player.center_x
        target_camera_y = self.player.center_y

        self.camera_x += (target_camera_x - self.camera_x) * 0.1
        self.camera_y += (target_camera_y - self.camera_y) * 0.1

        # CRITICAL: Clamp camera to world bounds to match sand rendering!
        # Camera is at center of screen, so it can't go too close to edges
        # or the sand rendering will clamp the view and cause coordinate mismatch
        world_width_pixels = self.sand.grid_width * self.sand.cell_size
        world_height_pixels = self.sand.grid_height * self.sand.cell_size

        camera_min_x = self.width // 2
        camera_max_x = world_width_pixels - self.width // 2
        camera_min_y = self.height // 2
        camera_max_y = world_height_pixels - self.height // 2

        self.camera_x = max(camera_min_x, min(self.camera_x, camera_max_x))
        self.camera_y = max(camera_min_y, min(self.camera_y, camera_max_y))

        # Queue new chunks around player (Bastion-style terrain building!)
        self._queue_chunks_around(int(self.player.center_x), int(self.player.center_y))

        # Generate multiple chunks per frame (fast catch-up!)
        for _ in range(self.chunks_per_frame):
            if self.chunk_queue:
                chunk_x, chunk_y = self.chunk_queue.pop(0)
                self._generate_chunk(chunk_x, chunk_y)
                self.generated_chunks.add((chunk_x, chunk_y))

        # Update physics simulation area - only simulate active chunks!
        player_chunk_x = int(self.player.center_x) // (self.chunk_size * self.sand.cell_size)
        player_chunk_y = int(self.player.center_y) // (self.chunk_size * self.sand.cell_size)
        chunks_to_simulate = self._update_physics_simulation_area(player_chunk_x, player_chunk_y)

        # Mining/placing with mouse
        mouse_x, mouse_y = pygame.mouse.get_pos()

        # Convert screen coords to world coords (accounting for camera)
        # X is straightforward
        world_x = int(mouse_x - self.width // 2 + self.camera_x)

        # Y needs careful handling - mouse_y increases downward, but we rendered with flipped Y
        # World coordinates: Y increases upward from bottom
        # Screen coordinates: Y increases downward from top
        # The sand is rendered with camera, so just offset by camera position
        world_y = int(mouse_y - self.height // 2 + self.camera_y)

        if self.mouse_down:
            # Mine (destroy sand)
            self.sand.spawn_circle(world_x, world_y, self.brush_size, Material.AIR)
            self.sand.dirty = True
            # Reactivate affected chunks
            self._reactivate_chunk_at_position(world_x, world_y)
            if not hasattr(self, '_last_mine_frame'):
                self._last_mine_frame = 0
            if self.clock.get_fps() > 0 and pygame.time.get_ticks() - self._last_mine_frame > 500:
                print(f"MINED at ({world_x},{world_y}), active chunks: {len(self.active_chunks)}")
                self._last_mine_frame = pygame.time.get_ticks()
        elif self.right_mouse_down:
            # Place
            self.sand.spawn_circle(world_x, world_y, self.brush_size, self.current_material)
            self.sand.dirty = True
            # Reactivate affected chunks
            self._reactivate_chunk_at_position(world_x, world_y)
            if not hasattr(self, '_last_place_frame'):
                self._last_place_frame = 0
            if self.clock.get_fps() > 0 and pygame.time.get_ticks() - self._last_place_frame > 500:
                print(f"PLACED {self.current_material} at ({world_x},{world_y}), active chunks: {len(self.active_chunks)}")
                self._last_place_frame = pygame.time.get_ticks()

        # Update rain system
        self.rain_timer += dt
        if self.rain_timer >= self.rain_toggle_timer:
            # Toggle rain on/off
            self.raining = not self.raining
            self.rain_timer = 0.0
            if self.raining:
                self.rain_toggle_timer = self.random.uniform(15, 45)  # Rain for 15-45 seconds
            else:
                self.rain_toggle_timer = self.random.uniform(30, 90)  # No rain for 30-90 seconds

        # Spawn rain droplets
        if self.raining:
            self.rain_spawn_timer += dt
            if self.rain_spawn_timer >= 0.2:  # Spawn every 0.2 seconds (5 drops/sec)
                self.rain_spawn_timer = 0.0
                # Spawn water near top of visible area
                camera_top_y = int(self.camera_y - self.height // 2)
                spawn_y = max(0, camera_top_y - 50)
                # Random X position across screen width
                camera_left_x = int(self.camera_x - self.width // 2)
                camera_right_x = int(self.camera_x + self.width // 2)
                for _ in range(1):  # Spawn 1 drop at a time
                    spawn_x = self.random.randint(max(0, camera_left_x),
                                                   min(self.sand.grid_width * self.sand.cell_size - 1, camera_right_x))
                    grid_x = spawn_x // self.sand.cell_size
                    grid_y = spawn_y // self.sand.cell_size
                    if 0 <= grid_x < self.sand.grid_width and 0 <= grid_y < self.sand.grid_height:
                        if self.sand.cells[grid_x, grid_y] == Material.AIR:
                            self.sand.cells[grid_x, grid_y] = Material.WATER
                            self.sand.active[grid_x, grid_y] = True

                            # Activate the chunk where rain spawns so it falls!
                            chunk_x = grid_x // self.chunk_size
                            chunk_y = grid_y // self.chunk_size
                            chunk_key = (chunk_x, chunk_y)
                            if chunk_key in self.generated_chunks:
                                self.active_chunks[chunk_key] = 0

        # Update falling sand simulation at 30 FPS (performance boost!)
        if not hasattr(self, '_sand_timer'):
            self._sand_timer = 0.0

        self._sand_timer += dt
        if self._sand_timer >= 1.0 / 30.0:  # 30 physics updates per second
            # Store cell state before physics to detect movement
            cells_before = self.sand.cells.copy() if len(chunks_to_simulate) > 0 else None

            # Run physics simulation
            self.sand.update(self._sand_timer)
            self._sand_timer = 0.0

            # Check which chunks had movement and update settling timers
            if cells_before is not None:
                for chunk_key in chunks_to_simulate:
                    chunk_x, chunk_y = chunk_key

                    # Calculate grid coordinates
                    start_grid_x = chunk_x * self.chunk_size
                    start_grid_y = chunk_y * self.chunk_size
                    end_grid_x = min(start_grid_x + self.chunk_size, self.sand.grid_width)
                    end_grid_y = min(start_grid_y + self.chunk_size, self.sand.grid_height)

                    # Check if any cells in this chunk changed
                    chunk_before = cells_before[start_grid_x:end_grid_x, start_grid_y:end_grid_y]
                    chunk_after = self.sand.cells[start_grid_x:end_grid_x, start_grid_y:end_grid_y]
                    had_movement = not np.array_equal(chunk_before, chunk_after)

                    if had_movement:
                        # Reset timer - chunk is still moving
                        self.active_chunks[chunk_key] = 0
                    else:
                        # Increment timer - no movement this frame
                        self.active_chunks[chunk_key] += 1

                # Remove settled chunks (no movement for threshold frames)
                settled_chunks = [k for k, v in self.active_chunks.items() if v >= self.chunk_settle_threshold]
                for chunk_key in settled_chunks:
                    del self.active_chunks[chunk_key]

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

        # Draw cursor indicator (helps debug mouse alignment!)
        mouse_x, mouse_y = pygame.mouse.get_pos()
        pygame.draw.circle(self.screen, (255, 255, 0), (mouse_x, mouse_y), 5, 2)
        pygame.draw.line(self.screen, (255, 255, 0), (mouse_x - 10, mouse_y), (mouse_x + 10, mouse_y), 2)
        pygame.draw.line(self.screen, (255, 255, 0), (mouse_x, mouse_y - 10), (mouse_x, mouse_y + 10), 2)

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
            Material.GRASS: "Grass",
        }

        # Count active cells for performance monitoring
        active_cells = np.count_nonzero(self.sand.active)
        active_chunk_count = len(self.active_chunks)

        # Calculate what SHOULD be simulated
        player_chunk_x = int(self.player.center_x) // (self.chunk_size * self.sand.cell_size)
        player_chunk_y = int(self.player.center_y) // (self.chunk_size * self.sand.cell_size)
        chunks_in_radius = 0
        for cy in range(player_chunk_y - self.physics_simulation_radius, player_chunk_y + self.physics_simulation_radius + 1):
            for cx in range(player_chunk_x - self.physics_simulation_radius, player_chunk_x + self.physics_simulation_radius + 1):
                if (cx, cy) in self.chunks_with_neighbors:
                    chunks_in_radius += 1

        info = [
            f"FPS: {int(self.clock.get_fps())}",
            f"Weather: {'RAINING' if self.raining else 'Clear'}",
            f"Position: ({int(self.player.x)}, {int(self.player.y)})",
            f"Player Chunk: ({player_chunk_x}, {player_chunk_y})",
            f"Material: {material_names[self.current_material]} (1-5)",
            f"On Ground: {self.player.on_ground}",
            "",
            f"Chunks Generated: {len(self.generated_chunks)}",
            f"Chunks w/ Neighbors: {len(self.chunks_with_neighbors)}",
            f"Chunks in Radius: {chunks_in_radius}",
            f"Active Chunks: {active_chunk_count}",
            f"Active Cells: {active_cells}",
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
