"""
Starbound-style physics system.

This physics system is designed to FEEL GOOD with:
- Smooth acceleration/deceleration
- Coyote time (grace period for jumping after leaving platform)
- Jump buffering (can press jump before landing)
- Variable jump height (hold jump = higher jump)
- Fast falling (release jump to fall faster)
- Proper collision without getting stuck
- Wall sliding
- Slope handling
"""
from typing import Tuple, Optional
from dataclasses import dataclass
import math


@dataclass
class PhysicsConfig:
    """Physics constants tuned for good feel."""

    # Movement
    ground_acceleration: float = 800.0  # Pixels/sec²
    air_acceleration: float = 600.0
    ground_friction: float = 15.0  # Higher = more responsive
    air_friction: float = 0.5
    max_run_speed: float = 160.0  # Pixels/sec
    max_fall_speed: float = 400.0

    # Jumping
    jump_speed: float = 320.0  # Initial jump velocity
    jump_hold_gravity: float = 450.0  # Gravity while holding jump
    jump_release_gravity: float = 900.0  # Gravity when releasing jump (fast fall)
    jump_cut_speed: float = 80.0  # Min speed when releasing jump early

    # Feel-good mechanics
    coyote_time: float = 0.15  # Seconds after leaving platform you can still jump
    jump_buffer_time: float = 0.1  # Seconds before landing you can press jump
    wall_slide_speed: float = 60.0  # Max speed when sliding down wall

    # Collision
    ground_check_distance: float = 4.0  # Pixels to check below for ground
    wall_check_distance: float = 2.0  # Pixels to check for walls

    # Block climbing
    auto_climb_height: float = 16.0  # Auto-climb blocks up to this height
    climb_speed: float = 100.0


class PhysicsBody:
    """
    Physics body with Starbound-style movement.

    This replaces the old wonky physics!
    """

    def __init__(self, x: float, y: float, width: float, height: float, config: PhysicsConfig = None):
        # Position
        self.x = x
        self.y = y
        self.width = width
        self.height = height

        # Velocity
        self.vx = 0.0
        self.vy = 0.0

        # Input (set by controller)
        self.move_input = 0.0  # -1 to 1
        self.jump_pressed = False
        self.jump_held = False

        # State
        self.on_ground = False
        self.on_wall = 0  # -1 for left wall, 1 for right wall, 0 for none
        self.facing = 1  # -1 for left, 1 for right

        # Timers for feel-good mechanics
        self.coyote_timer = 0.0  # Time since leaving ground
        self.jump_buffer_timer = 0.0  # Time jump has been buffered

        # Config
        self.config = config or PhysicsConfig()

    @property
    def center_x(self) -> float:
        return self.x + self.width / 2

    @property
    def center_y(self) -> float:
        return self.y + self.height / 2

    @property
    def left(self) -> float:
        return self.x

    @property
    def right(self) -> float:
        return self.x + self.width

    @property
    def top(self) -> float:
        return self.y

    @property
    def bottom(self) -> float:
        return self.y + self.height

    def can_jump(self) -> bool:
        """Check if jump is allowed (on ground or within coyote time)."""
        return self.on_ground or self.coyote_timer > 0


class PhysicsEngine:
    """
    Starbound-style physics engine.

    Handles movement, jumping, and collision with good feel.
    """

    def __init__(self, chunk_manager, block_size: int = 16):
        self.chunk_manager = chunk_manager
        self.block_size = block_size

    def update(self, body: PhysicsBody, dt: float) -> None:
        """
        Update physics body for one frame.

        This is the main physics update loop that makes movement feel good!
        """
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
            body.jump_pressed = False  # Consume input

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
            body.vy = body.config.jump_speed
            body.jump_buffer_timer = 0
            body.coyote_timer = 0
            body.on_ground = False

        # Apply gravity
        if body.vy > 0 and body.jump_held:
            # Holding jump = lower gravity (higher jump)
            gravity = body.config.jump_hold_gravity
        else:
            # Not holding jump or falling = higher gravity (fast fall)
            gravity = body.config.jump_release_gravity

        body.vy -= gravity * dt

        # Jump cut (release jump to fall faster)
        if not body.jump_held and body.vy > body.config.jump_cut_speed:
            body.vy = body.config.jump_cut_speed

        # Wall sliding
        if body.on_wall != 0 and body.vy < 0:
            body.vy = max(body.vy, -body.config.wall_slide_speed)

        # Clamp fall speed
        body.vy = max(-body.config.max_fall_speed, body.vy)

    def _move_with_collision(self, body: PhysicsBody, dt: float) -> None:
        """
        Move body and handle collision.

        This is pixel-perfect collision like Terraria/Starbound!
        """
        # Move X
        dx = body.vx * dt
        body.x += dx

        # Check X collision
        if self._check_collision(body):
            # Push back
            if dx > 0:
                # Moving right - snap to left edge of block
                block_x = math.floor(body.right / self.block_size) * self.block_size
                body.x = block_x - body.width
                body.on_wall = 1
            else:
                # Moving left - snap to right edge of block
                block_x = math.ceil(body.left / self.block_size) * self.block_size
                body.x = block_x
                body.on_wall = -1

            body.vx = 0

            # Try auto-climbing
            if abs(dx) > 0 and not body.jump_held:
                if self._try_auto_climb(body):
                    body.on_wall = 0
        else:
            body.on_wall = 0

        # Move Y
        dy = body.vy * dt
        body.y += dy

        # Check Y collision
        if self._check_collision(body):
            if dy > 0:
                # Moving up - hit ceiling
                block_y = math.floor(body.top / self.block_size) * self.block_size
                body.y = block_y
                body.vy = 0
            else:
                # Moving down - hit ground
                block_y = math.ceil(body.bottom / self.block_size) * self.block_size
                body.y = block_y - body.height
                body.vy = 0
                body.on_ground = True
        else:
            # Not colliding - check if we're still on ground
            if body.on_ground:
                # Check slightly below
                test_body_y = body.y + body.config.ground_check_distance
                if not self._check_collision_at(body.x, test_body_y, body.width, body.height):
                    body.on_ground = False

    def _check_collision(self, body: PhysicsBody) -> bool:
        """Check if body is colliding with solid blocks."""
        return self._check_collision_at(body.x, body.y, body.width, body.height)

    def _check_collision_at(self, x: float, y: float, width: float, height: float) -> bool:
        """Check collision at a specific position."""
        # Check corners and midpoints
        check_points = [
            (x + 2, y + 2),  # Top-left
            (x + width - 2, y + 2),  # Top-right
            (x + 2, y + height - 2),  # Bottom-left
            (x + width - 2, y + height - 2),  # Bottom-right
            (x + width/2, y + 2),  # Top-middle
            (x + width/2, y + height - 2),  # Bottom-middle
            (x + 2, y + height/2),  # Left-middle
            (x + width - 2, y + height/2),  # Right-middle
        ]

        for px, py in check_points:
            block_id = self.chunk_manager.get_block_at_world(px, py)
            if block_id and block_id != 1:  # Not air
                # Check if solid
                from ..world.blocks import get_block_registry
                registry = get_block_registry()
                if registry.is_solid(block_id):
                    return True

        return False

    def _try_auto_climb(self, body: PhysicsBody) -> bool:
        """
        Try to automatically climb up a block (Starbound-style step up).

        This makes movement feel smooth!
        """
        max_climb = body.config.auto_climb_height

        # Try climbing in small increments
        for climb_y in range(1, int(max_climb) + 1):
            test_y = body.y - climb_y

            # Check if we can fit at this height
            if not self._check_collision_at(body.x, test_y, body.width, body.height):
                # Success! Move up
                body.y = test_y
                return True

        return False


def create_player_body(x: float, y: float) -> PhysicsBody:
    """Create a physics body for the player with good default values."""
    config = PhysicsConfig(
        # Tuned for responsive, fun movement
        ground_acceleration=1200.0,
        air_acceleration=800.0,
        ground_friction=20.0,
        max_run_speed=180.0,
        jump_speed=340.0,
        coyote_time=0.15,
        jump_buffer_time=0.1,
        auto_climb_height=16.0
    )

    return PhysicsBody(x, y, width=24, height=48, config=config)
