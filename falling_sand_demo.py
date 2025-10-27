#!/usr/bin/env python3
"""
Falling Sand Demo - Test the cellular automata physics!

Controls:
- Left Click: Spawn sand
- Right Click: Spawn water
- 1: Sand mode
- 2: Water mode
- 3: Dirt mode
- 4: Stone mode
- Mouse Wheel: Zoom
- WASD: Move camera
- Space: Clear screen
- ESC: Quit
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import pygame
from cartesia.engine.falling_sand import FallingSandEngine, Material


class FallingSandDemo:
    """Demo application for falling sand physics."""

    def __init__(self):
        pygame.init()
        self.width = 1200
        self.height = 800
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Falling Sand Physics - Noita Style!")
        self.clock = pygame.time.Clock()

        # Create falling sand engine (half resolution for performance)
        self.sand = FallingSandEngine(self.width, self.height, cell_size=2)

        # Camera
        self.camera_x = self.width // 2
        self.camera_y = self.height // 2
        self.zoom = 1.0

        # Current material to spawn
        self.current_material = Material.SAND

        # Spawn settings
        self.spawn_radius = 10
        self.mouse_down = False
        self.right_mouse_down = False

        # Running
        self.running = True

        # Initialize with some ground
        self._create_initial_terrain()

    def _create_initial_terrain(self):
        """Create some initial terrain."""
        # Bottom layer of stone
        for x in range(0, self.width, 2):
            for y in range(self.height - 40, self.height, 2):
                self.sand.set_cell(x, y, Material.STONE)

        # Some dirt platforms
        for x in range(200, 400, 2):
            for y in range(500, 520, 2):
                self.sand.set_cell(x, y, Material.DIRT)

        for x in range(600, 800, 2):
            for y in range(400, 420, 2):
                self.sand.set_cell(x, y, Material.DIRT)

    def run(self):
        """Main game loop - OPTIMIZED."""
        physics_updates = 0
        physics_timer = 0.0
        update_interval = 1.0 / 60.0  # 60 physics updates per second max

        while self.running:
            frame_dt = self.clock.tick(120) / 1000.0  # Uncapped FPS
            physics_timer += frame_dt

            self.handle_events()
            self.handle_mouse_spawn()
            self.handle_camera_movement(frame_dt)

            # Physics at fixed rate (but skip if too slow)
            if physics_timer >= update_interval:
                self.sand.update(update_interval)
                physics_timer = 0.0
                physics_updates += 1

            self.render()
            pygame.display.flip()

        pygame.quit()

    def handle_events(self):
        """Handle input events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_SPACE:
                    # Clear screen
                    self.sand.cells.fill(Material.AIR)
                    self.sand.active.fill(True)
                    self._create_initial_terrain()
                elif event.key == pygame.K_1:
                    self.current_material = Material.SAND
                elif event.key == pygame.K_2:
                    self.current_material = Material.WATER
                elif event.key == pygame.K_3:
                    self.current_material = Material.DIRT
                elif event.key == pygame.K_4:
                    self.current_material = Material.STONE
                elif event.key == pygame.K_5:
                    self.current_material = Material.LAVA

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
                # Zoom
                if event.y > 0:
                    self.zoom = min(self.zoom * 1.1, 4.0)
                elif event.y < 0:
                    self.zoom = max(self.zoom / 1.1, 0.25)

    def handle_mouse_spawn(self):
        """Spawn material at mouse position."""
        if self.mouse_down or self.right_mouse_down:
            mouse_x, mouse_y = pygame.mouse.get_pos()

            # Direct screen coordinates (no camera offset for now - simpler!)
            # Spawn material
            material = self.current_material if self.mouse_down else Material.WATER
            self.sand.spawn_circle(mouse_x, mouse_y, self.spawn_radius, material)

    def handle_camera_movement(self, dt: float):
        """Move camera with WASD."""
        keys = pygame.key.get_pressed()
        speed = 300.0 * dt / self.zoom  # Slower when zoomed in

        if keys[pygame.K_w]:
            self.camera_y += speed
        if keys[pygame.K_s]:
            self.camera_y -= speed
        if keys[pygame.K_a]:
            self.camera_x -= speed
        if keys[pygame.K_d]:
            self.camera_x += speed

    def render(self):
        """Render everything."""
        # Clear screen
        self.screen.fill((20, 20, 30))  # Dark blue background

        # Render falling sand
        self.sand.render(self.screen, self.camera_x, self.camera_y, self.zoom)

        # Render UI
        self.render_ui()

    def render_ui(self):
        """Render UI overlay."""
        font = pygame.font.SysFont("monospace", 16)
        y = 10

        # Material names
        material_names = {
            Material.SAND: "Sand",
            Material.WATER: "Water",
            Material.DIRT: "Dirt",
            Material.STONE: "Stone",
            Material.LAVA: "Lava",
        }

        info = [
            f"FPS: {int(self.clock.get_fps())}",
            f"Material: {material_names[self.current_material]} (Press 1-5)",
            f"Zoom: {self.zoom:.2f}x",
            f"Left Click: Spawn {material_names[self.current_material]}",
            f"Right Click: Spawn Water",
            f"Space: Clear screen",
            f"WASD: Move camera",
        ]

        for line in info:
            text = font.render(line, True, (255, 255, 255))
            shadow = font.render(line, True, (0, 0, 0))
            self.screen.blit(shadow, (11, y + 1))
            self.screen.blit(text, (10, y))
            y += 22


if __name__ == "__main__":
    demo = FallingSandDemo()
    demo.run()
