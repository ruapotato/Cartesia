"""
Player animation system using Universal LPC spritesheets.

This module handles loading and animating LPC format character sprites,
which use a standard 64x64 grid layout with different animation rows.
"""
from enum import Enum
from typing import Optional
import pygame


class AnimationState(Enum):
    """Player animation states."""
    IDLE = "idle"
    WALK = "walk"
    JUMP = "jump"
    FALL = "fall"


class Direction(Enum):
    """Facing direction."""
    UP = 0
    LEFT = 1
    DOWN = 2
    RIGHT = 3


class PlayerAnimation:
    """
    Handles LPC spritesheet animation for the player with multiple layers.

    LPC Format (64x64 per frame):
    - Row 0-3: Spellcast (up, left, down, right)
    - Row 4-7: Thrust (up, left, down, right)
    - Row 8-11: Walk (up, left, down, right)
    - Row 12-15: Slash (up, left, down, right)
    - Row 16-19: Shoot (up, left, down, right)
    - Row 20: Hurt
    """

    # LPC spritesheet constants
    FRAME_WIDTH = 64
    FRAME_HEIGHT = 64

    # Animation row indices
    WALK_UP_ROW = 8
    WALK_LEFT_ROW = 9
    WALK_DOWN_ROW = 10
    WALK_RIGHT_ROW = 11

    # Animation frame counts
    WALK_FRAMES = 9

    def __init__(self, spritesheet_paths: list[str]):
        """
        Initialize the player animation system with multiple sprite layers.

        Args:
            spritesheet_paths: List of paths to LPC spritesheet images (body, hair, clothes, etc.)
                              These will be layered in order.
        """
        # Load all spritesheets
        self.spritesheets = []
        for path in spritesheet_paths:
            try:
                sheet = pygame.image.load(path).convert_alpha()
                self.spritesheets.append(sheet)
            except (pygame.error, FileNotFoundError) as e:
                print(f"Warning: Could not load sprite layer {path}: {e}")

        if not self.spritesheets:
            raise ValueError("No valid spritesheets loaded!")

        # Animation state
        self.current_state = AnimationState.IDLE
        self.direction = Direction.RIGHT
        self.frame_index = 0
        self.animation_timer = 0.0
        self.animation_speed = 0.1  # seconds per frame

        # Cache for extracted frames
        self.frame_cache: dict[tuple, pygame.Surface] = {}

    def update(self, dt: float, velocity_x: float, velocity_y: float, on_ground: bool):
        """
        Update animation state based on player movement.

        Args:
            dt: Delta time in seconds
            velocity_x: Horizontal velocity
            velocity_y: Vertical velocity
            on_ground: Whether player is on the ground
        """
        # Determine animation state
        if not on_ground:
            if velocity_y < 0:
                self.current_state = AnimationState.JUMP
            else:
                self.current_state = AnimationState.FALL
        elif abs(velocity_x) > 10:  # Moving threshold
            self.current_state = AnimationState.WALK
        else:
            self.current_state = AnimationState.IDLE

        # Update direction based on horizontal movement
        if velocity_x > 10:
            self.direction = Direction.RIGHT
        elif velocity_x < -10:
            self.direction = Direction.LEFT

        # Update animation timer
        self.animation_timer += dt

        # Advance frame when timer exceeds speed
        if self.animation_timer >= self.animation_speed:
            self.animation_timer = 0.0

            if self.current_state == AnimationState.WALK:
                self.frame_index = (self.frame_index + 1) % self.WALK_FRAMES
            elif self.current_state == AnimationState.IDLE:
                self.frame_index = 0  # Use first walk frame for idle
            else:
                # For jump/fall, use middle walk frame
                self.frame_index = 4

    def get_current_frame(self) -> pygame.Surface:
        """
        Get the current animation frame with all layers composited.

        Returns:
            Pygame surface containing the current frame
        """
        # Determine which row to use based on state and direction
        if self.current_state in (AnimationState.WALK, AnimationState.IDLE):
            if self.direction == Direction.LEFT:
                row = self.WALK_LEFT_ROW
            else:  # RIGHT
                row = self.WALK_RIGHT_ROW
        else:
            # Jump/fall use walk down row
            row = self.WALK_DOWN_ROW

        # Cache key (include number of layers)
        cache_key = (row, self.frame_index, len(self.spritesheets))

        # Check cache
        if cache_key not in self.frame_cache:
            # Extract frame from all spritesheets and composite them
            x = self.frame_index * self.FRAME_WIDTH
            y = row * self.FRAME_HEIGHT

            # Create transparent surface for compositing
            frame = pygame.Surface(
                (self.FRAME_WIDTH, self.FRAME_HEIGHT),
                pygame.SRCALPHA
            )
            frame.fill((0, 0, 0, 0))

            # Layer all spritesheets
            for spritesheet in self.spritesheets:
                layer = pygame.Surface(
                    (self.FRAME_WIDTH, self.FRAME_HEIGHT),
                    pygame.SRCALPHA
                )
                layer.blit(
                    spritesheet,
                    (0, 0),
                    (x, y, self.FRAME_WIDTH, self.FRAME_HEIGHT)
                )
                frame.blit(layer, (0, 0))

            self.frame_cache[cache_key] = frame

        return self.frame_cache[cache_key]

    def render(
        self,
        surface: pygame.Surface,
        x: int,
        y: int,
        scale: float = 1.0
    ):
        """
        Render the current animation frame.

        Args:
            surface: Pygame surface to draw on
            x: Center X position (in screen coordinates)
            y: Center Y position (in screen coordinates)
            scale: Scale factor for the sprite
        """
        frame = self.get_current_frame()

        # Scale if needed
        if scale != 1.0:
            new_width = int(self.FRAME_WIDTH * scale)
            new_height = int(self.FRAME_HEIGHT * scale)
            frame = pygame.transform.scale(frame, (new_width, new_height))
        else:
            new_width = self.FRAME_WIDTH
            new_height = self.FRAME_HEIGHT

        # Calculate top-left position (center the sprite)
        draw_x = x - new_width // 2
        draw_y = y - new_height // 2

        # Draw
        surface.blit(frame, (draw_x, draw_y))


def create_player_animation(
    body_sprite: Optional[str] = None,
    hair_sprite: Optional[str] = None,
    clothing_sprite: Optional[str] = None
) -> PlayerAnimation:
    """
    Create a player animation with layered sprites.

    Layers are composited in order: body, clothing, hair

    Args:
        body_sprite: Path to body spritesheet (if None, uses default)
        hair_sprite: Path to hair spritesheet (if None, uses default)
        clothing_sprite: Path to clothing spritesheet (if None, uses default)

    Returns:
        PlayerAnimation instance
    """
    from pathlib import Path

    # Find the project root
    current_file = Path(__file__)
    project_root = current_file.parent.parent.parent.parent
    sprite_base = project_root / "img" / "player" / "Universal-LPC-spritesheet"

    # Build layer list
    layers = []

    # Body layer (required)
    if body_sprite is None:
        body_sprite = str(sprite_base / "body" / "male" / "light.png")
    layers.append(body_sprite)

    # Clothing layer (optional)
    if clothing_sprite is None:
        clothing_sprite = str(sprite_base / "torso" / "shirts" / "longsleeve" / "male" / "teal_longsleeve.png")
    if clothing_sprite:
        layers.append(clothing_sprite)

    # Hair layer (optional - rendered on top)
    if hair_sprite is None:
        hair_sprite = str(sprite_base / "hair" / "male" / "bangslong2.png")
    if hair_sprite:
        layers.append(hair_sprite)

    return PlayerAnimation(layers)
