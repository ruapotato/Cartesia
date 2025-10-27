"""
Main game engine for Cartesia.

This replaces the messy 1500-line gui.py with a clean, maintainable game loop.
"""
from typing import Optional
import pygame
from pathlib import Path

from ..config import get_config, GameConfig
from ..world.chunk import ChunkManager
from ..world.blocks import get_block_registry
from .lighting import LightingEngine
from .renderer import Renderer
from .physics import PhysicsEngine, PhysicsBody
from ..entities.entity import (
    EntityManager,
    Entity,
    TransformComponent,
    PhysicsComponent,
    SpriteComponent,
    AnimationComponent,
    HealthComponent,
    Animation
)


class InputManager:
    """
    Handles input state and makes it easier to query.

    No more scattered pygame.key.get_pressed() calls!
    """

    def __init__(self):
        self.keys_down = set()
        self.keys_pressed = set()  # This frame only
        self.keys_released = set()  # This frame only

        self.mouse_pos = (0, 0)
        self.mouse_down = set()
        self.mouse_pressed = set()
        self.mouse_released = set()

    def update(self) -> None:
        """Update input state (call at start of frame)."""
        self.keys_pressed.clear()
        self.keys_released.clear()
        self.mouse_pressed.clear()
        self.mouse_released.clear()

    def handle_event(self, event: pygame.event.Event) -> None:
        """Process a pygame event."""
        if event.type == pygame.KEYDOWN:
            self.keys_down.add(event.key)
            self.keys_pressed.add(event.key)

        elif event.type == pygame.KEYUP:
            self.keys_down.discard(event.key)
            self.keys_released.add(event.key)

        elif event.type == pygame.MOUSEBUTTONDOWN:
            self.mouse_down.add(event.button)
            self.mouse_pressed.add(event.button)

        elif event.type == pygame.MOUSEBUTTONUP:
            self.mouse_down.discard(event.button)
            self.mouse_released.add(event.button)

        elif event.type == pygame.MOUSEMOTION:
            self.mouse_pos = event.pos

    def is_key_down(self, key: int) -> bool:
        """Check if key is currently held down."""
        return key in self.keys_down

    def is_key_pressed(self, key: int) -> bool:
        """Check if key was pressed this frame."""
        return key in self.keys_pressed

    def is_key_released(self, key: int) -> bool:
        """Check if key was released this frame."""
        return key in self.keys_released

    def is_mouse_down(self, button: int = 1) -> bool:
        """Check if mouse button is down."""
        return button in self.mouse_down


class GameEngine:
    """
    Main game engine.

    Coordinates all systems and runs the game loop.
    """

    def __init__(self, config: Optional[GameConfig] = None):
        # Load config
        if config is None:
            config = get_config()
        self.config = config

        # Initialize pygame
        pygame.init()
        pygame.font.init()
        pygame.mixer.init()

        # Create window
        if self.config.display.fullscreen:
            self.screen = pygame.display.set_mode(
                (self.config.display.width, self.config.display.height),
                pygame.FULLSCREEN
            )
        else:
            self.screen = pygame.display.set_mode(
                (self.config.display.width, self.config.display.height)
            )

        pygame.display.set_caption("Cartesia")

        # Clock for frame timing
        self.clock = pygame.time.Clock()
        self.running = False

        # Input
        self.input = InputManager()

        # Core systems
        self.chunk_manager = ChunkManager(self.config.world.seed)
        self.lighting = LightingEngine(
            (self.config.display.width, self.config.display.height),
            self.config.lighting
        )
        self.renderer = Renderer(self.screen, self.chunk_manager, self.lighting)
        self.physics = PhysicsEngine(self.chunk_manager, self.config)
        self.entity_manager = EntityManager()

        # Player
        self.player: Optional[Entity] = None

        # Game state
        self.game_time = 0.0  # Total game time in seconds
        self.paused = False

    def initialize(self) -> None:
        """Initialize the game (load assets, create player, etc.)."""
        # Ensure assets are loaded
        get_block_registry()

        # Create player
        self.player = self._create_player()

        # Load music
        if self.config.audio.music_enabled:
            try:
                music_path = self.config.assets_path.parent / "music" / "Komiku - Hélice's Theme.mp3"
                if music_path.exists():
                    pygame.mixer.music.load(str(music_path))
                    pygame.mixer.music.set_volume(self.config.audio.music_volume)
                    pygame.mixer.music.play(-1)
            except Exception as e:
                print(f"Failed to load music: {e}")

        # Set initial camera position
        if self.player:
            transform = self.player.get_component(TransformComponent)
            self.renderer.camera.follow(transform.x, transform.y, immediate=True)

    def _create_player(self) -> Entity:
        """Create the player entity."""
        # Create entity
        player = self.entity_manager.create_entity("Player")
        player.add_tag("player")

        # Add transform
        transform = TransformComponent(player, x=0, y=0)
        player.add_component(transform)

        # Add physics
        physics_body = PhysicsBody(
            x=0,
            y=-100,  # Start above ground
            hitbox_width=self.config.player.hitbox_width,
            hitbox_height=self.config.player.hitbox_height,
            max_speed_x=self.config.player.walk_speed,
            max_speed_y=30.0
        )
        physics_comp = PhysicsComponent(player, physics_body)
        player.add_component(physics_comp)

        # Add health
        health = HealthComponent(player, self.config.player.max_health)
        player.add_component(health)

        # TODO: Add sprite and animation components when we have the assets loaded

        return player

    def run(self) -> None:
        """Run the main game loop."""
        self.running = True
        self.initialize()

        while self.running:
            # Calculate delta time
            dt = self.clock.tick(self.config.display.fps_target) / 1000.0
            dt = min(dt, 0.1)  # Cap to prevent huge jumps

            # Handle events
            self._handle_events()

            # Update
            if not self.paused:
                self._update(dt)

            # Render
            self._render()

            # Update display
            pygame.display.flip()

        # Cleanup
        self._cleanup()

    def _handle_events(self) -> None:
        """Handle pygame events."""
        self.input.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            # Pass to input manager
            self.input.handle_event(event)

        # Handle pause
        if self.input.is_key_pressed(pygame.K_ESCAPE):
            self.paused = not self.paused

    def _update(self, dt: float) -> None:
        """Update game logic."""
        self.game_time += dt

        # Update player input
        self._update_player_input(dt)

        # Update physics
        if self.player:
            physics_comp = self.player.get_component(PhysicsComponent)
            if physics_comp:
                self.physics.update(physics_comp.body, dt)

        # Update entities
        self.entity_manager.update(dt)

        # Update camera
        if self.player:
            transform = self.player.get_component(TransformComponent)
            self.renderer.camera.follow(transform.x, transform.y)

        # Update lighting
        # Sync time of day (0-1 based on game time)
        day_length = self.config.lighting.day_length_minutes * 60
        time_of_day = (self.game_time % day_length) / day_length
        self.lighting.set_time_of_day(time_of_day)
        self.lighting.update(dt)

        # Update renderer
        self.renderer.update(dt)

    def _update_player_input(self, dt: float) -> None:
        """Handle player input."""
        if not self.player:
            return

        physics_comp = self.player.get_component(PhysicsComponent)
        if not physics_comp:
            return

        body = physics_comp.body

        # Movement
        move_x = 0
        if self.input.is_key_down(pygame.K_a) or self.input.is_key_down(pygame.K_LEFT):
            move_x -= 1
        if self.input.is_key_down(pygame.K_d) or self.input.is_key_down(pygame.K_RIGHT):
            move_x += 1

        # Apply movement
        if move_x != 0:
            target_vx = move_x * self.config.player.walk_speed
            # Smooth acceleration
            body.vx += (target_vx - body.vx) * 0.2
        else:
            # Deceleration when not moving
            body.vx *= 0.8

        # Jumping
        if (self.input.is_key_pressed(pygame.K_w) or
            self.input.is_key_pressed(pygame.K_UP) or
            self.input.is_key_pressed(pygame.K_SPACE)):

            if body.can_jump:
                body.vy = self.config.player.jump_speed
                body.is_jumping = True
                body.can_jump = False

        # Block breaking (left click)
        if self.input.is_mouse_down(1):
            self._handle_block_interaction(True)

        # Block placing (right click)
        if self.input.is_mouse_down(3):
            self._handle_block_interaction(False)

    def _handle_block_interaction(self, is_breaking: bool) -> None:
        """Handle block breaking/placing."""
        # Convert mouse pos to world coords
        mouse_x, mouse_y = self.input.mouse_pos
        world_x, world_y = self.renderer.camera.screen_to_world(mouse_x, mouse_y)

        # Get block at position
        block_id = self.chunk_manager.get_block_at_world(world_x, world_y)

        if is_breaking:
            # Break block
            if block_id and block_id != 1:  # Not air
                self.chunk_manager.set_block_at_world(world_x, world_y, 1)  # Set to air
                # Clear chunk cache to force re-render
                self.renderer.clear_chunk_cache()
        else:
            # Place block
            if block_id == 1:  # Only place in air
                self.chunk_manager.set_block_at_world(world_x, world_y, 3)  # Place dirt
                self.renderer.clear_chunk_cache()

    def _render(self) -> None:
        """Render the game."""
        # Render world
        self.renderer.render_world()

        # Render entities
        self.renderer.render_entities(self.entity_manager.entities)

        # Composite and present
        self.renderer.composite_and_present()

        # Show FPS
        if self.config.show_fps:
            font = pygame.font.SysFont("monospace", 16)
            fps_text = font.render(f"FPS: {int(self.clock.get_fps())}", True, (0, 255, 0))
            self.screen.blit(fps_text, (10, self.config.display.height - 30))

    def _cleanup(self) -> None:
        """Cleanup resources."""
        # Save all chunks
        self.chunk_manager.save_all_chunks()

        # Quit pygame
        pygame.quit()


def main():
    """Entry point for the game."""
    game = GameEngine()
    game.run()


if __name__ == "__main__":
    main()
