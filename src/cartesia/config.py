"""
Configuration management for Cartesia.

This module provides a centralized configuration system with sane defaults
and easy customization through YAML files.
"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Tuple
import os
import yaml


@dataclass
class DisplayConfig:
    """Display and rendering configuration."""

    width: int = 1920
    height: int = 1080
    fullscreen: bool = False
    vsync: bool = True
    fps_target: int = 60
    scale: float = 1.0

    # Performance
    max_chunk_render_distance: int = 7  # chunks
    chunk_cache_size: int = 100


@dataclass
class LightingConfig:
    """Modern lighting system configuration.

    This is designed to be highly tweakable to achieve good-looking lighting.
    """

    # Enable/disable systems
    enabled: bool = True
    dynamic_shadows: bool = True
    ambient_occlusion: bool = True
    smooth_lighting: bool = True

    # Ambient light (day/night cycle)
    ambient_min: float = 0.15  # Minimum ambient light (night)
    ambient_max: float = 1.0   # Maximum ambient light (day)
    day_length_minutes: float = 7.0

    # Light sources
    torch_radius: int = 200  # pixels
    torch_intensity: float = 1.0
    torch_color: Tuple[int, int, int] = (255, 230, 180)  # Warm torch light

    sunlight_color: Tuple[int, int, int] = (255, 250, 230)
    moonlight_color: Tuple[int, int, int] = (100, 120, 180)

    # Light propagation
    light_falloff: str = "quadratic"  # "linear", "quadratic", "cubic"
    light_blend_mode: str = "add"  # "add", "multiply", "screen"

    # Performance
    light_update_interval: float = 0.1  # seconds
    max_light_sources: int = 50

    # Shadow quality
    shadow_softness: float = 0.5  # 0.0-1.0
    shadow_opacity: float = 0.7   # 0.0-1.0


@dataclass
class WorldConfig:
    """World generation and physics configuration."""

    # Terrain generation
    seed: int = 1564654
    chunk_size: int = 32  # blocks per chunk
    block_size: int = 16  # pixels per block

    # Perlin noise parameters for terrain
    terrain_octaves: int = 3
    terrain_scale: float = 100.0
    terrain_crazyness_octaves: int = 8
    terrain_crazyness_scale: float = 1000.0
    terrain_height_multiplier: float = 100.0

    # Physics
    gravity: float = -1.5
    terminal_velocity: float = -30.0

    # World boundaries
    max_depth: int = 1000  # blocks
    max_height: int = 500  # blocks


@dataclass
class PlayerConfig:
    """Player character configuration."""

    # Movement
    walk_speed: float = 5.0
    run_speed: float = 8.0
    jump_speed: float = 15.0
    climb_speed: float = 3.0

    # Stats
    max_health: int = 100
    max_magic: int = 100
    max_stamina: int = 100

    # Regeneration
    health_regen: float = 0.1
    magic_regen: float = 0.2
    stamina_regen: float = 0.5

    # Inventory
    inventory_width: int = 9
    inventory_height: int = 6

    # Display
    hitbox_width: int = 32
    hitbox_height: int = 64
    sprite_size: int = 64


@dataclass
class AudioConfig:
    """Audio configuration."""

    master_volume: float = 0.7
    music_volume: float = 0.5
    sfx_volume: float = 0.8

    enabled: bool = True
    music_enabled: bool = True
    sfx_enabled: bool = True


@dataclass
class GameConfig:
    """Main game configuration container."""

    display: DisplayConfig = field(default_factory=DisplayConfig)
    lighting: LightingConfig = field(default_factory=LightingConfig)
    world: WorldConfig = field(default_factory=WorldConfig)
    player: PlayerConfig = field(default_factory=PlayerConfig)
    audio: AudioConfig = field(default_factory=AudioConfig)

    # Paths
    save_path: Path = field(default_factory=lambda: Path.home() / ".cartesia")
    assets_path: Path = field(default_factory=lambda: Path(__file__).parent.parent.parent)

    # Debug
    debug_mode: bool = True
    show_fps: bool = True
    show_chunk_borders: bool = False
    show_hitboxes: bool = False

    @classmethod
    def load_from_file(cls, path: Optional[Path] = None) -> "GameConfig":
        """Load configuration from YAML file."""
        if path is None:
            path = Path.home() / ".cartesia" / "config.yaml"

        if not path.exists():
            return cls()

        with open(path) as f:
            data = yaml.safe_load(f)

        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: dict) -> "GameConfig":
        """Create configuration from dictionary."""
        config = cls()

        if "display" in data:
            for key, value in data["display"].items():
                setattr(config.display, key, value)

        if "lighting" in data:
            for key, value in data["lighting"].items():
                setattr(config.lighting, key, value)

        if "world" in data:
            for key, value in data["world"].items():
                setattr(config.world, key, value)

        if "player" in data:
            for key, value in data["player"].items():
                setattr(config.player, key, value)

        if "audio" in data:
            for key, value in data["audio"].items():
                setattr(config.audio, key, value)

        return config

    def save_to_file(self, path: Optional[Path] = None) -> None:
        """Save configuration to YAML file."""
        if path is None:
            path = Path.home() / ".cartesia" / "config.yaml"

        path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "display": vars(self.display),
            "lighting": vars(self.lighting),
            "world": vars(self.world),
            "player": vars(self.player),
            "audio": vars(self.audio),
        }

        with open(path, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    def ensure_paths(self) -> None:
        """Ensure all required directories exist."""
        self.save_path.mkdir(parents=True, exist_ok=True)
        (self.save_path / "worlds").mkdir(exist_ok=True)
        (self.save_path / "screenshots").mkdir(exist_ok=True)


# Global configuration instance
_config: Optional[GameConfig] = None


def get_config() -> GameConfig:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = GameConfig.load_from_file()
        _config.ensure_paths()
    return _config


def reload_config() -> GameConfig:
    """Reload configuration from file."""
    global _config
    _config = GameConfig.load_from_file()
    _config.ensure_paths()
    return _config
