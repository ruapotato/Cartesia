"""
Mining and block interaction system.

Starbound/Terraria-style mining with:
- Progressive damage indicators
- Tool requirements
- Different block hardness
- Drop items when broken
- Block placement
"""
from typing import Optional, Tuple, Dict
from dataclasses import dataclass
import pygame
import time


@dataclass
class BlockDamage:
    """Tracks damage to a block being mined."""

    world_x: int
    world_y: int
    damage: float = 0.0
    last_hit_time: float = 0.0


class MiningSystem:
    """
    Handles block breaking and placement.

    This makes mining feel satisfying with visual feedback!
    """

    def __init__(self, chunk_manager, block_registry):
        self.chunk_manager = chunk_manager
        self.block_registry = block_registry

        # Currently damaged blocks
        self.damaged_blocks: Dict[Tuple[int, int], BlockDamage] = {}

        # Damage decay time (blocks heal if you stop mining)
        self.damage_decay_time = 1.0  # seconds

        # Mining range
        self.max_mining_distance = 80  # pixels

    def update(self, dt: float):
        """Update mining system (decay old damage)."""
        current_time = time.time()

        # Decay damage on blocks not being hit
        to_remove = []
        for coords, damage in self.damaged_blocks.items():
            if current_time - damage.last_hit_time > self.damage_decay_time:
                to_remove.append(coords)

        for coords in to_remove:
            del self.damaged_blocks[coords]

    def mine_block(
        self,
        world_x: float,
        world_y: float,
        player_x: float,
        player_y: float,
        tool_type: Optional[str],
        tool_power: int,
        dt: float
    ) -> Optional[Tuple[str, int]]:
        """
        Mine a block.

        Args:
            world_x, world_y: Block world coordinates
            player_x, player_y: Player position (for range check)
            tool_type: Type of tool being used
            tool_power: Power of the tool (1-5)
            dt: Delta time

        Returns:
            (item_id, quantity) if block was broken, else None
        """
        # Check range
        dx = world_x - player_x
        dy = world_y - player_y
        distance = (dx * dx + dy * dy) ** 0.5

        if distance > self.max_mining_distance:
            return None

        # Get block
        block_id = self.chunk_manager.get_block_at_world(world_x, world_y)
        if not block_id or block_id == 1:  # Air
            return None

        block_def = self.block_registry.get(block_id)
        if not block_def:
            return None

        # Check tool requirement
        if block_def.tool_required and tool_type != block_def.tool_required:
            # Wrong tool - mine very slowly
            mining_speed = 0.5
        else:
            # Right tool
            mining_speed = tool_power * 2.0

        # Calculate damage per hit
        damage_per_second = mining_speed / block_def.hardness
        damage = damage_per_second * dt

        # Get or create damage tracker
        coords = (int(world_x), int(world_y))
        if coords not in self.damaged_blocks:
            self.damaged_blocks[coords] = BlockDamage(int(world_x), int(world_y))

        block_damage = self.damaged_blocks[coords]
        block_damage.damage += damage
        block_damage.last_hit_time = time.time()

        # Check if block is broken
        if block_damage.damage >= 1.0:
            # Block broken!
            del self.damaged_blocks[coords]

            # Remove block
            self.chunk_manager.set_block_at_world(world_x, world_y, 1)  # Air

            # Return dropped item
            if block_def.drops:
                return (block_def.drops, 1)
            else:
                # Drop the block itself
                return (block_def.name.lower().replace(" ", "_"), 1)

        return None

    def place_block(
        self,
        world_x: float,
        world_y: float,
        player_x: float,
        player_y: float,
        block_id: int
    ) -> bool:
        """
        Place a block.

        Returns True if successful.
        """
        # Check range
        dx = world_x - player_x
        dy = world_y - player_y
        distance = (dx * dx + dy * dy) ** 0.5

        if distance > self.max_mining_distance:
            return False

        # Check if space is empty
        existing_block = self.chunk_manager.get_block_at_world(world_x, world_y)
        if existing_block != 1:  # Not air
            return False

        # Place block
        return self.chunk_manager.set_block_at_world(world_x, world_y, block_id)

    def get_block_damage(self, world_x: int, world_y: int) -> float:
        """Get damage progress for a block (0.0 to 1.0)."""
        coords = (world_x, world_y)
        if coords in self.damaged_blocks:
            return min(1.0, self.damaged_blocks[coords].damage)
        return 0.0

    def render_damage_indicators(self, surface: pygame.Surface, camera_offset: Tuple[float, float], block_size: int):
        """Render crack overlays on damaged blocks."""
        # TODO: Load crack textures
        # For now, just draw a transparent overlay
        for coords, damage in self.damaged_blocks.items():
            world_x, world_y = coords

            # Convert to screen coords
            screen_x = world_x - camera_offset[0]
            screen_y = world_y - camera_offset[1]

            # Calculate alpha based on damage
            alpha = int(255 * damage.damage)

            # Draw damage overlay
            overlay = pygame.Surface((block_size, block_size))
            overlay.set_alpha(alpha)
            overlay.fill((255, 255, 255))

            surface.blit(overlay, (screen_x, screen_y))
