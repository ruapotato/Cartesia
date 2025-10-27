"""
Block definition and management system.

Defines all block types and their properties in a clean, extensible way.
"""
from dataclasses import dataclass
from typing import Dict, Optional, Tuple
from pathlib import Path
import pygame


@dataclass
class BlockDefinition:
    """Defines a single block type."""

    id: int
    name: str
    texture_path: Optional[str] = None
    solid: bool = True
    transparent: bool = False
    light_emission: int = 0  # 0-15, like Minecraft
    hardness: float = 1.0  # Time to break
    tool_required: Optional[str] = None
    drops: Optional[str] = None  # What it drops when broken

    # Rendering
    texture: Optional[pygame.Surface] = None
    color: Optional[Tuple[int, int, int]] = None

    def __post_init__(self):
        """Load texture if path is provided."""
        if self.texture_path and not self.texture:
            try:
                self.texture = pygame.image.load(self.texture_path).convert_alpha()
            except Exception as e:
                print(f"Failed to load texture for {self.name}: {e}")


class BlockRegistry:
    """
    Central registry for all block types.

    Provides easy access to block definitions and textures.
    """

    def __init__(self, assets_path: Path):
        self.assets_path = assets_path
        self.texture_path = assets_path / "img" / "pixelperfection"

        self.blocks: Dict[int, BlockDefinition] = {}
        self._loaded_textures: Dict[str, pygame.Surface] = {}
        self._scaled_texture_cache: Dict[Tuple[int, int], pygame.Surface] = {}

        # Initialize default blocks
        self._register_default_blocks()

    def _register_default_blocks(self) -> None:
        """Register all default block types."""

        # Air
        self.register(BlockDefinition(
            id=1,
            name="air",
            solid=False,
            transparent=True,
            hardness=0,
            color=(0, 175, 255)  # Sky color
        ))

        # Grass
        self.register(BlockDefinition(
            id=2,
            name="grass",
            texture_path=str(self.texture_path / "default" / "default_grass_side.png"),
            hardness=0.6,
            tool_required="shovel",
            drops="dirt"
        ))

        # Dirt
        self.register(BlockDefinition(
            id=3,
            name="dirt",
            texture_path=str(self.texture_path / "default" / "default_dirt.png"),
            hardness=0.5,
            tool_required="shovel",
            drops="dirt"
        ))

        # Stone
        self.register(BlockDefinition(
            id=4,
            name="stone",
            texture_path=str(self.texture_path / "default" / "default_stone.png"),
            hardness=1.5,
            tool_required="pickaxe",
            drops="stone"
        ))

        # Torch
        self.register(BlockDefinition(
            id=5,
            name="torch",
            texture_path=str(self.texture_path / "default" / "default_torch.png"),
            solid=False,
            transparent=True,
            light_emission=14,
            hardness=0.0,
            drops="torch"
        ))

    def register(self, block: BlockDefinition) -> None:
        """Register a new block type."""
        self.blocks[block.id] = block

        # Load texture if needed
        if block.texture_path and not block.texture:
            block.texture = self._load_texture(block.texture_path)

    def _load_texture(self, path: str) -> Optional[pygame.Surface]:
        """Load a texture with caching."""
        if path in self._loaded_textures:
            return self._loaded_textures[path]

        try:
            texture = pygame.image.load(path).convert_alpha()
            self._loaded_textures[path] = texture
            return texture
        except Exception as e:
            print(f"Failed to load texture {path}: {e}")
            return None

    def get(self, block_id: int) -> Optional[BlockDefinition]:
        """Get a block definition by ID."""
        return self.blocks.get(block_id)

    def get_texture(self, block_id: int, block_size: int = 16) -> Optional[pygame.Surface]:
        """
        Get the rendered texture for a block with caching.

        This applies lighting and scaling as needed.
        """
        # Check cache first
        cache_key = (block_id, block_size)
        if cache_key in self._scaled_texture_cache:
            return self._scaled_texture_cache[cache_key]

        block = self.get(block_id)
        if not block:
            return None

        surface = None

        # For air, return None (don't render)
        if block_id == 1:
            return None

        # For blocks with textures
        if block.texture:
            if block.texture.get_size() == (block_size, block_size):
                surface = block.texture
            else:
                surface = pygame.transform.scale(block.texture, (block_size, block_size))

        # For blocks with just a color
        elif block.color:
            surface = pygame.Surface((block_size, block_size))
            surface.fill(block.color)

        # Fallback
        else:
            surface = pygame.Surface((block_size, block_size))
            surface.fill((255, 0, 255))  # Magenta for missing texture

        # Cache the result
        if surface is not None:
            self._scaled_texture_cache[cache_key] = surface

        return surface

    def is_solid(self, block_id: int) -> bool:
        """Check if a block is solid."""
        block = self.get(block_id)
        return block.solid if block else False

    def is_transparent(self, block_id: int) -> bool:
        """Check if a block is transparent."""
        block = self.get(block_id)
        return block.transparent if block else False

    def emits_light(self, block_id: int) -> int:
        """Get the light emission level of a block."""
        block = self.get(block_id)
        return block.light_emission if block else 0


# Global block registry instance
_block_registry: Optional[BlockRegistry] = None


def get_block_registry(assets_path: Path = None) -> BlockRegistry:
    """Get the global block registry instance."""
    global _block_registry

    if _block_registry is None:
        if assets_path is None:
            from ..config import get_config
            assets_path = get_config().assets_path

        _block_registry = BlockRegistry(assets_path)

    return _block_registry
