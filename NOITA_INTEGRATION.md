# Cartesia - Noita Integration Complete! 🎮

## What We Built

Successfully integrated **Noita-style falling sand physics** with **Starbound-style world generation** into a single, blazing-fast game!

## Key Features

### ✅ Completed

1. **Numba JIT Compilation** - 10-100x performance boost
   - Sand update loop: **125 FPS** (previously ~15 FPS)
   - Compiled `update_simulation_jit()`, `update_powder_jit()`, `update_fluid_jit()`
   - Cached compilation for instant startup

2. **Falling Sand Physics**
   - Every pixel is simulated
   - Materials: Sand, Dirt, Water, Stone, Lava
   - Realistic physics with density and flow
   - Activity tracking (only updates active cells)

3. **Perlin Noise World Generation**
   - Procedural terrain using existing TerrainGenerator
   - Natural caves and mountains
   - Converts terrain depth → sand materials

4. **Camera System**
   - Smooth camera follow
   - Renders only visible portion of world
   - Supports larger-than-screen worlds

5. **Complete Game Loop**
   - Player physics with pixel-perfect collision
   - Mining (left-click) and placing (right-click)
   - Material selection (1-5 keys)
   - Animated player sprite

## How to Play

```bash
python main.py
```

### Controls

- **WASD / Arrow Keys**: Move player
- **Space**: Jump
- **Left Click**: Mine (destroy terrain)
- **Right Click**: Place material
- **1-5**: Select material
  - 1: Dirt
  - 2: Sand
  - 3: Water
  - 4: Stone
  - 5: Lava
- **ESC**: Quit

## Performance

- **FPS**: 100-125 FPS (with Numba JIT)
- **World Size**: Currently 1920x1080 (screen size)
- **Grid Cells**: ~518,000 cells simulated
- **Generation Time**: ~2-3 seconds

## File Structure

```
main.py                    # Main game (Noita + Starbound hybrid)
falling_sand_demo.py       # Standalone falling sand demo
play_sand.py               # Early Noita prototype
main_old.py                # Backup of original chunk-based game

src/cartesia/engine/
  falling_sand.py          # Falling sand engine with Numba JIT
  physics_v2.py            # Player physics

src/cartesia/world/
  generation.py            # Perlin noise terrain generation
```

## Next Steps / TODOs

### Performance Optimizations

1. **Vectorized Terrain Generation**
   - Current: Nested Python loops (~2-3 seconds for 500k cells)
   - Goal: Numpy vectorization or Numba JIT (~0.1 seconds)
   - Would allow 4x-8x larger worlds

2. **Chunk-Based Sand Simulation**
   - Only simulate chunks near player
   - Infinite world support
   - Chunk loading/unloading system

3. **Multi-threading**
   - Separate thread for sand simulation
   - Parallel chunk updates

### Gameplay Features

1. **Material Reactions** (Noita-style)
   - Water + Lava → Steam + Stone
   - Fire + Oil → Explosion
   - Acid dissolves materials

2. **New Materials**
   - Oil (flammable liquid)
   - Gunpowder (explosive)
   - Fire (spreads)
   - Steam/Smoke (rises)
   - Acid (dissolves blocks)
   - Wood (burnable solid)

3. **Explosions**
   - Circle of destruction
   - Sends particles flying
   - Chain reactions

4. **Fire Propagation**
   - Spreads to flammable materials
   - Burns out over time
   - Creates smoke

5. **Gas Materials**
   - Rise instead of fall
   - Dissipate over time
   - Smoke, steam, poison gas

### World Features

1. **Larger Worlds**
   - Once terrain generation is optimized
   - 4x-8x screen size
   - True exploration

2. **Biomes**
   - Desert (more sand)
   - Ocean (water)
   - Volcanic (lava)
   - Ice (frozen water?)

3. **Structures**
   - Generated buildings
   - Dungeons
   - Treasure chests

### Polish

1. **Particles**
   - Dust when mining
   - Splash when water hits
   - Sparks from lava

2. **Sound Effects**
   - Digging sounds
   - Water splash
   - Explosions

3. **Better UI**
   - Inventory system
   - Health bar
   - Minimap

## Technical Notes

### Numba JIT Compilation

The falling sand simulation uses Numba's `@njit(cache=True)` decorator to compile critical loops to machine code:

```python
@njit(cache=True)
def update_simulation_jit(cells, active, frame, grid_width, grid_height):
    # This runs at C speed!
    for y in range(grid_height - 2, 0, -1):
        for x in range(offset, grid_width - 1, 2):
            # Update logic...
```

**Benefits:**
- 10-100x faster than pure Python
- First run compiles (2-3 seconds)
- Subsequent runs use cached compilation (instant)
- No performance penalty

### Camera Rendering

Only renders the visible portion of the world:

```python
# Calculate visible region
view_left = int((camera_x - screen_width // 2) / cell_size)
view_top = int((camera_y - screen_height // 2) / cell_size)

# Extract and render only visible cells
visible_cells = self.cells[view_left:view_right, view_top:view_bottom]
```

This allows large worlds without rendering performance hit!

### Activity Tracking

Only cells marked as "active" are updated:

```python
# Only surface cells start active
for grid_x in range(self.grid_width):
    for grid_y in range(1, self.grid_height - 1):
        if self.cells[grid_x, grid_y] != Material.AIR:
            if self.cells[grid_x, grid_y - 1] == Material.AIR:
                self.active[grid_x, grid_y] = True  # Surface cell!
```

This provides massive speedup - underground cells don't update until disturbed!

## Comparison: Old vs New

### Old Game (main_old.py)
- Chunk-based block system
- Static blocks (no physics)
- ~60 FPS
- Terraria-style mining
- 16x16 pixel blocks

### New Game (main.py)
- Pixel-based cellular automata
- Every pixel simulates
- **100-125 FPS** (with Numba!)
- Noita-style destruction
- 2x2 pixel cells
- Materials flow and interact

## Credits

Built using:
- **Pygame**: Graphics and input
- **Numba**: JIT compilation for speed
- **NumPy**: Fast array operations
- **Perlin Noise**: Procedural terrain
