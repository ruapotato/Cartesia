"""
Procedural world generation for Cartesia.

Uses Perlin noise for realistic terrain generation.
"""
from typing import Tuple, List
import numpy as np
from perlin_noise import PerlinNoise
import random


# Block type constants
BLOCK_AIR = 1
BLOCK_GRASS = 2
BLOCK_DIRT = 3
BLOCK_STONE = 4
BLOCK_TORCH = 5


class TerrainGenerator:
    """Generates terrain using Perlin noise."""

    def __init__(self, seed: int, config):
        self.seed = seed
        self.config = config

        # Initialize Perlin noise generators
        self.ground_noise = PerlinNoise(
            octaves=config.world.terrain_octaves,
            seed=seed
        )

        self.crazyness_noise = PerlinNoise(
            octaves=config.world.terrain_crazyness_octaves,
            seed=seed
        )

    def get_crazyness_at(self, x: float, y: float) -> float:
        """Get terrain 'crazyness' (variation) at a position."""
        crazyness = self.ground_noise([
            x / self.config.world.terrain_crazyness_scale,
            y / self.config.world.terrain_crazyness_scale
        ])
        return crazyness + crazyness  # Double for more variation

    def get_solid_depth_at(self, x: float, y: float) -> float:
        """
        Get the depth of solid ground at a position.

        Returns:
            Depth value (positive means solid, 0 or negative means air)
        """
        ground_level = 0

        # Get terrain variation
        crazyness = self.get_crazyness_at(x, y)
        hills = crazyness * self.config.world.terrain_height_multiplier

        # Get base altitude
        ground_alt = (
            self.ground_noise([
                x / self.config.world.terrain_scale,
                y / self.config.world.terrain_scale
            ]) * 100
        ) - 10

        ground_alt *= crazyness

        # Calculate final altitude
        final_altitude = ground_level + ground_alt + hills

        # Return depth (how far below surface)
        if y < final_altitude:
            return final_altitude - y
        else:
            return 0


def generate_chunk(chunk_x: int, chunk_y: int, seed: int, config) -> Tuple[np.ndarray, List[dict]]:
    """
    Generate a chunk of terrain.

    Args:
        chunk_x, chunk_y: Chunk coordinates
        seed: World seed
        config: Game configuration

    Returns:
        Tuple of (blocks array, entities list) where blocks[x, y] is the block at local coords (x, y)
    """
    size = config.world.chunk_size

    # Calculate world coordinates for this chunk (top-left corner)
    world_x_start = chunk_x * size
    world_y_start = chunk_y * size

    # Initialize generator
    generator = TerrainGenerator(seed, config)

    # Create blocks array: blocks[local_x, local_y]
    blocks = np.zeros((size, size), dtype=np.int32)
    entities = []

    tree_plant_rate = 5.0

    # First pass: generate all blocks
    depth_map = {}
    for local_y in range(size):
        for local_x in range(size):
            world_x = world_x_start + local_x
            world_y = world_y_start + local_y
            depth = generator.get_solid_depth_at(world_x, world_y)
            depth_map[(local_x, local_y)] = depth

    # Second pass: determine block types with proper layering
    for local_y in range(size):
        for local_x in range(size):
            world_x = world_x_start + local_x
            world_y = world_y_start + local_y

            depth = depth_map[(local_x, local_y)]
            crazyness = generator.get_crazyness_at(world_x, world_y)

            # Check if block above is air (for grass placement)
            depth_above = depth_map.get((local_x, local_y - 1), 0)
            is_surface = depth > 0 and depth_above == 0

            # Determine block type based on depth
            if depth <= 0:
                # Air
                blocks[local_x, local_y] = BLOCK_AIR

            elif is_surface and 0 < depth < 3:
                # Grass (surface block with air above)
                blocks[local_x, local_y] = BLOCK_GRASS

                # Plant trees on flat areas
                if crazyness < 10:
                    tree_chance = random.randint(0, 1000000) / 10000
                    if tree_chance <= tree_plant_rate:
                        entities.append({
                            "init_tree": [local_x, local_y]
                        })
                        blocks[local_x, local_y] = BLOCK_DIRT

            elif 0 < depth < 3:
                # Dirt (shallow underground)
                blocks[local_x, local_y] = BLOCK_DIRT

            else:
                # Stone (deep underground)
                blocks[local_x, local_y] = BLOCK_STONE

    return blocks, entities


def get_block_at_position(x: float, y: float, seed: int, config) -> int:
    """
    Get the block type at a specific world position without loading chunks.

    Useful for quick lookups and preview generation.
    """
    generator = TerrainGenerator(seed, config)
    depth = generator.get_solid_depth_at(x, y)

    if not depth:
        return BLOCK_AIR
    elif 0 < depth < 0.7:
        return BLOCK_GRASS
    elif 0.7 <= depth < 3:
        return BLOCK_DIRT
    else:
        return BLOCK_STONE
