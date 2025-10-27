"""
Modern chunk management system for Cartesia.

Improvements over the old system:
- Better memory management
- Async chunk generation
- Proper caching
- Thread-safe operations
"""
from typing import Dict, Tuple, Optional, List, Set
from dataclasses import dataclass, field
from pathlib import Path
import numpy as np
import pygame
import yaml
from threading import Lock
from ..config import get_config


@dataclass
class Chunk:
    """Represents a single chunk of the world."""

    position: Tuple[int, int]  # Chunk coordinates (not world coordinates)
    blocks: np.ndarray  # 2D array of block IDs
    surface: Optional[pygame.Surface] = None
    entities: List[dict] = field(default_factory=list)
    dirty: bool = True  # Needs re-rendering
    loaded: bool = False

    def __post_init__(self):
        config = get_config().world
        if self.blocks is None:
            size = config.chunk_size
            self.blocks = np.zeros((size, size), dtype=np.int32)

    def get_block(self, x: int, y: int) -> int:
        """Get block at local chunk coordinates."""
        return self.blocks[x, y]

    def set_block(self, x: int, y: int, block_id: int) -> None:
        """Set block at local chunk coordinates."""
        self.blocks[x, y] = block_id
        self.dirty = True

    def to_world_coords(self) -> Tuple[int, int]:
        """Convert chunk position to world coordinates (top-left corner)."""
        config = get_config().world
        chunk_size = config.chunk_size * config.block_size
        return (
            self.position[0] * chunk_size,
            self.position[1] * chunk_size
        )


class ChunkManager:
    """
    Manages chunk loading, unloading, and caching.

    Features:
    - LRU cache for chunks
    - Async chunk generation
    - Thread-safe operations
    - Efficient disk I/O
    """

    def __init__(self, world_seed: int, save_path: Path = None):
        self.config = get_config()
        self.world_seed = world_seed

        if save_path is None:
            self.save_path = self.config.save_path / "worlds" / str(world_seed)
        else:
            self.save_path = Path(save_path)

        self.save_path.mkdir(parents=True, exist_ok=True)

        # Chunk storage
        self.chunks: Dict[Tuple[int, int], Chunk] = {}
        self.chunk_lock = Lock()

        # Caching
        self.max_cached_chunks = self.config.display.chunk_cache_size
        self.chunk_access_order: List[Tuple[int, int]] = []

        # Generation queue (for async generation)
        self.generation_queue: Set[Tuple[int, int]] = set()

    def get_chunk(self, x: int, y: int, generate: bool = True) -> Optional[Chunk]:
        """
        Get a chunk at the given chunk coordinates.

        Args:
            x, y: Chunk coordinates
            generate: Whether to generate the chunk if it doesn't exist

        Returns:
            The chunk, or None if it doesn't exist and generate=False
        """
        chunk_pos = (x, y)

        with self.chunk_lock:
            # Check if chunk is already loaded
            if chunk_pos in self.chunks:
                self._update_access_order(chunk_pos)
                return self.chunks[chunk_pos]

            # Try to load from disk
            chunk = self._load_chunk_from_disk(x, y)

            if chunk is None and generate:
                # Generate new chunk
                chunk = self._generate_chunk(x, y)

            if chunk is not None:
                self.chunks[chunk_pos] = chunk
                self._update_access_order(chunk_pos)
                self._enforce_cache_limit()

            return chunk

    def unload_chunk(self, x: int, y: int, save: bool = True) -> None:
        """Unload a chunk from memory, optionally saving it first."""
        chunk_pos = (x, y)

        with self.chunk_lock:
            if chunk_pos in self.chunks:
                chunk = self.chunks[chunk_pos]

                if save:
                    self._save_chunk_to_disk(chunk)

                del self.chunks[chunk_pos]

                if chunk_pos in self.chunk_access_order:
                    self.chunk_access_order.remove(chunk_pos)

    def save_all_chunks(self) -> None:
        """Save all loaded chunks to disk."""
        with self.chunk_lock:
            for chunk in self.chunks.values():
                self._save_chunk_to_disk(chunk)

    def get_chunks_in_range(self, center_x: int, center_y: int,
                           radius: int) -> List[Chunk]:
        """
        Get all chunks within a certain radius of a center chunk.

        Args:
            center_x, center_y: Center chunk coordinates
            radius: Number of chunks in each direction

        Returns:
            List of chunks
        """
        chunks = []

        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                chunk_x = center_x + dx
                chunk_y = center_y + dy
                chunk = self.get_chunk(chunk_x, chunk_y)

                if chunk is not None:
                    chunks.append(chunk)

        return chunks

    def world_to_chunk_coords(self, world_x: float, world_y: float) -> Tuple[int, int, int, int]:
        """
        Convert world coordinates to chunk coordinates and local block coordinates.

        Returns:
            (chunk_x, chunk_y, local_x, local_y)
        """
        chunk_pixel_size = self.config.world.chunk_size * self.config.world.block_size

        chunk_x = int(world_x // chunk_pixel_size)
        chunk_y = int(world_y // chunk_pixel_size)

        local_x = int((world_x % chunk_pixel_size) // self.config.world.block_size)
        local_y = int((world_y % chunk_pixel_size) // self.config.world.block_size)

        return chunk_x, chunk_y, local_x, local_y

    def get_block_at_world(self, world_x: float, world_y: float) -> Optional[int]:
        """Get the block ID at world coordinates."""
        chunk_x, chunk_y, local_x, local_y = self.world_to_chunk_coords(world_x, world_y)

        chunk = self.get_chunk(chunk_x, chunk_y, generate=False)
        if chunk is None:
            return None

        try:
            return chunk.get_block(local_x, local_y)
        except IndexError:
            return None

    def set_block_at_world(self, world_x: float, world_y: float, block_id: int) -> bool:
        """Set a block at world coordinates."""
        chunk_x, chunk_y, local_x, local_y = self.world_to_chunk_coords(world_x, world_y)

        chunk = self.get_chunk(chunk_x, chunk_y)
        if chunk is None:
            return False

        try:
            chunk.set_block(local_x, local_y, block_id)
            return True
        except IndexError:
            return False

    def _generate_chunk(self, x: int, y: int) -> Chunk:
        """Generate a new chunk using the world generator."""
        # Import here to avoid circular dependency
        from .generation import generate_chunk

        blocks, entities = generate_chunk(x, y, self.world_seed, self.config)

        chunk = Chunk(
            position=(x, y),
            blocks=blocks,
            entities=entities,
            loaded=True
        )

        return chunk

    def _load_chunk_from_disk(self, x: int, y: int) -> Optional[Chunk]:
        """Load a chunk from disk."""
        chunk_dir = self.save_path / f"{x}_{y}"
        block_file = chunk_dir / "blocks.txt"

        if not block_file.exists():
            return None

        try:
            blocks = np.loadtxt(block_file, dtype=np.int32)

            # Load entities
            entities = []
            entity_files = chunk_dir.glob("init_*.yml")

            for entity_file in entity_files:
                with open(entity_file) as f:
                    entity_data = yaml.safe_load(f)
                    entities.append(entity_data)

            chunk = Chunk(
                position=(x, y),
                blocks=blocks,
                entities=entities,
                loaded=True
            )

            return chunk

        except Exception as e:
            print(f"Error loading chunk ({x}, {y}): {e}")
            return None

    def _save_chunk_to_disk(self, chunk: Chunk) -> None:
        """Save a chunk to disk."""
        x, y = chunk.position
        chunk_dir = self.save_path / f"{x}_{y}"
        chunk_dir.mkdir(parents=True, exist_ok=True)

        # Save blocks
        block_file = chunk_dir / "blocks.txt"
        np.savetxt(block_file, chunk.blocks, fmt='%d')

        # Save entities
        for i, entity in enumerate(chunk.entities):
            entity_file = chunk_dir / f"entity_{i}.yml"
            with open(entity_file, 'w') as f:
                yaml.dump(entity, f, default_flow_style=False)

    def _update_access_order(self, chunk_pos: Tuple[int, int]) -> None:
        """Update the LRU cache access order."""
        if chunk_pos in self.chunk_access_order:
            self.chunk_access_order.remove(chunk_pos)

        self.chunk_access_order.append(chunk_pos)

    def _enforce_cache_limit(self) -> None:
        """Enforce the maximum number of cached chunks."""
        while len(self.chunks) > self.max_cached_chunks:
            # Remove least recently used chunk
            if self.chunk_access_order:
                oldest_chunk = self.chunk_access_order.pop(0)
                self.unload_chunk(*oldest_chunk, save=True)
