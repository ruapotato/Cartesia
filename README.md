# Cartesia - 2D Voxel Adventure Game

A Starbound/Terraria-style 2D sandbox game with procedural generation,
crafting, mining, and exploration.

## Quick Start

### Run the Modern Version (Recommended):
```bash
source pyenv/bin/activate
python play_v2.py
```

### Run the Legacy Version:
```bash
source pyenv/bin/activate
./main.py
```

## Features

### Starbound-Style Physics
- Smooth acceleration and deceleration
- Variable jump height (hold jump = higher)
- Coyote time (grace period for jumping)
- Jump buffering (forgiving input timing)
- Auto-climbing (step up single blocks)
- Wall sliding
- Fast falling (release jump early)

### Core Gameplay
- **Mining** - Progressive damage with tool requirements
- **Building** - Place blocks to construct
- **Inventory** - Hotbar + main storage
- **Tools** - Durability system for pickaxes, axes, shovels
- **Crafting** - Combine items (coming soon)
- **Farming** - Plant and harvest crops (coming soon)

### Controls
- **A/D or Arrows** - Move
- **Space/W/Up** - Jump (hold for higher!)
- **Left Click** - Mine blocks
- **Right Click** - Place blocks
- **1-9** - Select hotbar slot
- **ESC** - Quit

## Documentation

- `STARBOUND_REWRITE.md` - Details on the complete physics rewrite
- `MODERNIZATION.md` - Migration guide from old to new systems
- `WHATS_NEW.md` - Complete feature comparison

## Status

### Implemented ✅
- Smooth Starbound-style movement
- Chunk loading and terrain generation
- Mining with progressive damage
- Block placement
- Inventory system with hotbar
- Tool durability
- Delta-time physics (frame-independent)
- Player sprite animations (LPC multi-layer system)

### In Progress 🚧
- Crafting system
- Farming mechanics
- NPC AI and dialogue
- Combat system
- Particle effects

### Planned 📋
- Biomes and varied terrain
- Day/night cycle
- Hunger and health systems
- Bosses and quests
- Multiplayer

## Assets

This project includes extensive assets for:
- Character customization (LPC spritesheet)
- Blocks and terrain
- Tools and weapons
- Farming and cooking
- UI elements

See `Attribution.txt` for licenses.

## License

AGPL3 by David Hamner 2023-2025

## Development

The codebase has been completely modernized with:
- Type hints throughout
- Clean separation of concerns
- Proper physics engine
- Modular systems
- Professional architecture

Built with Python 3.11+ and Pygame.
