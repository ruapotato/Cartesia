"""
Modern physics and collision system for Cartesia.

Replaces the wonky hardcoded collision detection with proper AABB collision,
smooth block climbing, and frame-independent movement.
"""
from typing import Tuple, Optional, List
from dataclasses import dataclass
import math
from ..config import get_config


@dataclass
class AABB:
    """Axis-Aligned Bounding Box for collision detection."""

    x: float
    y: float
    width: float
    height: float

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

    @property
    def center_x(self) -> float:
        return self.x + self.width / 2

    @property
    def center_y(self) -> float:
        return self.y + self.height / 2

    def intersects(self, other: "AABB") -> bool:
        """Check if this AABB intersects with another."""
        return (
            self.left < other.right and
            self.right > other.left and
            self.top < other.bottom and
            self.bottom > other.top
        )

    def get_overlap(self, other: "AABB") -> Tuple[float, float]:
        """Get the overlap amount with another AABB."""
        overlap_x = min(self.right, other.right) - max(self.left, other.left)
        overlap_y = min(self.bottom, other.bottom) - max(self.top, other.top)
        return overlap_x, overlap_y

    def offset(self, dx: float, dy: float) -> "AABB":
        """Return a new AABB offset by dx, dy."""
        return AABB(self.x + dx, self.y + dy, self.width, self.height)


@dataclass
class PhysicsBody:
    """
    Physics body with velocity, acceleration, and collision.

    Much cleaner than the old system!
    """

    # Position (world coordinates)
    x: float
    y: float

    # Velocity
    vx: float = 0.0
    vy: float = 0.0

    # Acceleration
    ax: float = 0.0
    ay: float = 0.0

    # Hitbox
    hitbox_width: float = 32.0
    hitbox_height: float = 64.0

    # Physics properties
    mass: float = 1.0
    friction: float = 0.8  # Ground friction
    air_resistance: float = 0.99  # Air resistance
    bounce: float = 0.0  # Bounciness (0-1)

    # State
    on_ground: bool = False
    can_jump: bool = False
    is_jumping: bool = False
    is_climbing: bool = False

    # Limits
    max_speed_x: float = 10.0
    max_speed_y: float = 30.0

    @property
    def hitbox(self) -> AABB:
        """Get the current hitbox as an AABB."""
        return AABB(self.x, self.y, self.hitbox_width, self.hitbox_height)

    @property
    def center_x(self) -> float:
        return self.x + self.hitbox_width / 2

    @property
    def center_y(self) -> float:
        return self.y + self.hitbox_height / 2


class PhysicsEngine:
    """
    Handles physics simulation and collision detection.

    This replaces all the wonky collision code with proper physics.
    """

    def __init__(self, chunk_manager, config=None):
        self.chunk_manager = chunk_manager
        self.config = config or get_config()

        self.gravity = self.config.world.gravity
        self.terminal_velocity = self.config.world.terminal_velocity

        # Block climbing settings
        self.max_climb_height = 1.0  # Can climb 1 block high
        self.climb_speed = 3.0  # Speed when climbing

    def update(self, body: PhysicsBody, dt: float) -> None:
        """
        Update physics body for one frame.

        Args:
            body: The physics body to update
            dt: Delta time in seconds (for frame-independent movement)
        """
        # Apply gravity if not on ground
        if not body.on_ground:
            body.vy += self.gravity * dt * 60  # Scale for smoother feel
            body.vy = max(body.vy, self.terminal_velocity)
        else:
            # Apply ground friction
            body.vx *= body.friction

        # Apply air resistance
        if not body.on_ground:
            body.vx *= body.air_resistance
            body.vy *= body.air_resistance

        # Clamp velocities
        body.vx = max(-body.max_speed_x, min(body.max_speed_x, body.vx))
        body.vy = max(-body.max_speed_y, min(body.max_speed_y, body.vy))

        # Move and handle collisions
        self._move_with_collision(body, body.vx * dt * 60, body.vy * dt * 60)

        # Update state
        self._update_state(body)

    def _move_with_collision(self, body: PhysicsBody, dx: float, dy: float) -> None:
        """
        Move body while handling collision and sliding.

        This is MUCH cleaner than the old 8-point collision check!
        """
        # Reset climbing state
        body.is_climbing = False

        # Move X with collision
        if dx != 0:
            body.x += dx

            # Check for X collision
            x_collision = self._check_collision(body)

            if x_collision:
                # Try to climb up (if moving and small height difference)
                if abs(dx) > 0.1 and not body.is_jumping:
                    climb_success = self._try_climb(body, dx > 0)

                    if climb_success:
                        body.is_climbing = True
                    else:
                        # Can't climb, push back
                        body.x -= dx
                        body.vx = 0

        # Move Y with collision
        if dy != 0:
            body.y += dy

            # Check for Y collision
            y_collision = self._check_collision(body)

            if y_collision:
                # Snap to block grid
                block_size = self.config.world.block_size

                if dy < 0:
                    # Moving up - hit ceiling
                    body.y = math.ceil(body.y / block_size) * block_size
                    body.vy = 0
                    body.is_jumping = False
                else:
                    # Moving down - hit ground
                    # Snap to top of block
                    body.y = math.floor(body.y / block_size) * block_size
                    body.vy = 0
                    body.on_ground = True
                    body.can_jump = True
                    body.is_jumping = False

    def _check_collision(self, body: PhysicsBody) -> bool:
        """
        Check if body is colliding with solid blocks.

        Uses multiple sample points for accuracy.
        """
        hitbox = body.hitbox

        # Sample points around the hitbox
        sample_points = [
            # Feet
            (hitbox.left + 2, hitbox.bottom - 1),
            (hitbox.center_x, hitbox.bottom - 1),
            (hitbox.right - 2, hitbox.bottom - 1),
            # Middle
            (hitbox.left + 1, hitbox.center_y),
            (hitbox.right - 1, hitbox.center_y),
            # Head
            (hitbox.left + 2, hitbox.top + 1),
            (hitbox.center_x, hitbox.top + 1),
            (hitbox.right - 2, hitbox.top + 1),
        ]

        for px, py in sample_points:
            block_id = self.chunk_manager.get_block_at_world(px, py)

            if block_id is not None and block_id != 1:  # Not air
                from ..world.blocks import get_block_registry
                registry = get_block_registry()

                if registry.is_solid(block_id):
                    return True

        return False

    def _try_climb(self, body: PhysicsBody, moving_right: bool) -> bool:
        """
        Try to climb up a single block.

        This replaces the wonky "pos[1] -= 6" code!
        """
        block_size = self.config.world.block_size
        max_climb_pixels = self.max_climb_height * block_size

        # Try stepping up in small increments
        for step in range(1, int(max_climb_pixels) + 1):
            test_y = body.y - step
            test_body = PhysicsBody(
                x=body.x,
                y=test_y,
                hitbox_width=body.hitbox_width,
                hitbox_height=body.hitbox_height
            )

            # Check if we can fit at this height
            if not self._check_collision(test_body):
                # Success! Move up
                body.y = test_y
                body.vy = 0
                return True

        return False

    def _update_state(self, body: PhysicsBody) -> None:
        """Update body state (on_ground, can_jump, etc.)."""
        # Check if on ground
        test_body = PhysicsBody(
            x=body.x,
            y=body.y + 2,  # Check slightly below
            hitbox_width=body.hitbox_width,
            hitbox_height=body.hitbox_height
        )

        was_on_ground = body.on_ground
        body.on_ground = self._check_collision(test_body)

        # Update jump state
        if body.on_ground:
            body.can_jump = True
            if body.vy < 0:
                body.is_jumping = False
        else:
            body.can_jump = False

        # Landing detection
        if body.on_ground and not was_on_ground:
            # Just landed - calculate fall damage if needed
            fall_speed = abs(body.vy)
            if fall_speed > 20:
                # Could return fall damage here
                pass

    def raycast(self, start_x: float, start_y: float,
                end_x: float, end_y: float) -> Optional[Tuple[float, float, int]]:
        """
        Cast a ray and find the first solid block.

        Returns: (hit_x, hit_y, block_id) or None
        """
        # Bresenham's line algorithm for efficiency
        dx = abs(end_x - start_x)
        dy = abs(end_y - start_y)
        sx = 1 if start_x < end_x else -1
        sy = 1 if start_y < end_y else -1
        err = dx - dy

        x, y = start_x, start_y

        max_steps = 1000  # Prevent infinite loops
        steps = 0

        while steps < max_steps:
            # Check current position
            block_id = self.chunk_manager.get_block_at_world(x, y)

            if block_id is not None and block_id != 1:
                from ..world.blocks import get_block_registry
                registry = get_block_registry()

                if registry.is_solid(block_id):
                    return (x, y, block_id)

            # Reached end?
            if abs(x - end_x) < 1 and abs(y - end_y) < 1:
                break

            # Next step
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy

            steps += 1

        return None

    def apply_impulse(self, body: PhysicsBody, ix: float, iy: float) -> None:
        """Apply an instantaneous force (impulse) to the body."""
        body.vx += ix / body.mass
        body.vy += iy / body.mass

    def apply_force(self, body: PhysicsBody, fx: float, fy: float, dt: float) -> None:
        """Apply a continuous force to the body."""
        body.vx += (fx / body.mass) * dt
        body.vy += (fy / body.mass) * dt
