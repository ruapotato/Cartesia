"""
Procedural world generation for Cartesia.

Uses Perlin noise for realistic terrain generation.
"""
from typing import Tuple, List
import numpy as np
from perlin_noise import PerlinNoise
import random
from ..engine.falling_sand import Material


# Material type constants (using the Material enum)
# NEW ORDER: AIR=0, WATER=1, LAVA=2, SAND=3, DIRT=4, GRASS=5, STONE=6
BLOCK_AIR = Material.AIR      # 0
BLOCK_WATER = Material.WATER  # 1
BLOCK_SAND = Material.SAND    # 3
BLOCK_DIRT = Material.DIRT    # 4
BLOCK_GRASS = Material.GRASS  # 5
BLOCK_STONE = Material.STONE  # 6


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
    Generate a chunk of terrain - SUPER FAST heightmap version!

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

    # FAST: Generate heightmap for entire chunk at once (1D noise along x-axis only!)
    # This is WAY faster than per-block Perlin noise
    noise = PerlinNoise(octaves=5, seed=seed)

    # Vectorized heightmap generation
    world_x_coords = np.arange(world_x_start, world_x_start + size)
    heights = np.array([noise(x / 120.0) for x in world_x_coords])  # Simple 1D heightmap

    # Convert noise (-1 to 1) to WORLD Y coordinates (not chunk-relative!)
    # Ground level should be around a fixed world Y position
    base_ground_level = 100  # Fixed world Y coordinate for average ground level (higher for mountains)
    terrain_world_y = (base_ground_level + heights * 50).astype(np.int32)  # +/- 50 blocks variation (big mountains!)

    # Create blocks array: blocks[local_x, local_y]
    blocks = np.full((size, size), BLOCK_AIR, dtype=np.int32)
    entities = []

    # FULLY VECTORIZED terrain generation - NO LOOPS!
    # Create meshgrid of coordinates
    local_y_coords = np.arange(size)
    local_x_coords = np.arange(size)
    xx, yy = np.meshgrid(local_x_coords, local_y_coords, indexing='ij')

    # Convert local Y to world Y for comparison
    world_yy = world_y_start + yy

    # Get terrain height (in world coords) for each x column
    terrain_height_mesh = terrain_world_y[xx]

    # SUPER FAST material assignment!
    # Calculate depth below surface
    depth_below_surface = world_yy - terrain_height_mesh

    # Water only in the deepest valleys (terrain much lower than base level)
    is_deep_valley = (terrain_height_mesh < base_ground_level - 45)  # Only deepest areas

    # Determine biome types
    is_beach_area = (terrain_height_mesh < base_ground_level - 35)  # Sandy areas in low valleys

    # Material layers:
    # - Air above surface
    # - Surface (depth 0): GRASS on land, SAND in low valleys
    # - Shallow (1-2 blocks): DIRT or SAND
    # - If in deep valley floor, add small water pools
    # - Medium (2-8 blocks): DIRT
    # - Deep (8+ blocks): STONE

    # Create base terrain
    blocks = np.where(
        world_yy < terrain_height_mesh, BLOCK_AIR,  # Air above terrain
        np.where(
            depth_below_surface == 0,  # Surface layer
            np.where(is_beach_area, BLOCK_SAND, BLOCK_GRASS),  # Sand in valleys, grass on hills
            np.where(
                depth_below_surface < 2,
                np.where(is_beach_area, BLOCK_SAND, BLOCK_DIRT),  # Sand/dirt subsurface
                np.where(depth_below_surface < 8, BLOCK_DIRT, BLOCK_STONE)  # Dirt then stone
            )
        )
    )

    # Add small water pools ONLY in deepest valley floors
    # Water appears 1-3 blocks deep in valley floor
    water_pool_mask = is_deep_valley & (depth_below_surface >= 1) & (depth_below_surface <= 3)
    blocks = np.where(water_pool_mask, BLOCK_WATER, blocks)

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
