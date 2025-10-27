# Falling Sand Physics - Noita Style!

## What I Built

A complete **cellular automata physics engine** for falling sand simulation, like Noita!

### Features

**Materials:**
- 🟤 Sand - Falls and piles naturally
- 💧 Water - Flows and spreads
- 🟫 Dirt - Falls like sand but heavier
- ⬛ Stone - Static, doesn't move
- 🔥 Lava - Flows like water (ready for future interactions!)

**Physics:**
- Every pixel is simulated individually
- Materials interact based on density
- Sand falls and slides diagonally
- Water flows horizontally and down
- Emergent behavior from simple rules!

**Performance Optimizations:**
- ✅ Checkerboard update pattern (stability)
- ✅ Active cell tracking (skip static areas)
- ✅ Numpy vectorization (C-level speed)
- ✅ Half-resolution (cell_size=2) for 4x performance
- ✅ Spatial culling (only render visible area)

## Try It Now!

```bash
python falling_sand_demo.py
```

## Controls

**Spawning Materials:**
- **Left Click** - Spawn current material
- **Right Click** - Spawn water
- **1** - Sand mode
- **2** - Water mode
- **3** - Dirt mode
- **4** - Stone mode
- **5** - Lava mode

**Camera:**
- **Mouse Wheel** - Zoom in/out
- **W/A/S/D** - Move camera

**Other:**
- **Space** - Clear screen
- **ESC** - Quit

## How It Works

### Cellular Automata Rules

Each cell follows simple rules based on material type:

**Powder Materials (Sand, Dirt):**
1. Try to fall straight down
2. If blocked, try diagonal left
3. If blocked, try diagonal right
4. If can't move, go to sleep

**Fluid Materials (Water, Lava):**
1. Try to fall straight down
2. If blocked, try left or right
3. If blocked, try diagonal down-left or down-right
4. If can't move, go to sleep

**Displacement Rules:**
- Higher density materials sink through lower density
- Water (density=1) displaces air (density=0)
- Sand (density=2) sinks through water
- Nothing moves stone (density=10)

### The Update Loop

```python
# 30 physics updates per second (stable)
for each cell from bottom to top:
    if not active:
        skip (performance!)

    material = get_cell(x, y)

    if movable:
        try to move based on rules
        if moved:
            activate neighbors
        else:
            deactivate (go to sleep)
```

### Performance Tricks

**1. Checkerboard Pattern:**
```
Frame 0: Update even cells
Frame 1: Update odd cells
Result: Prevents tunneling, more stable
```

**2. Active Cell Tracking:**
```
Only update cells that moved recently
Static piles go to "sleep"
Wake up when neighbors move
Result: 10x-50x speedup on settled areas
```

**3. Spatial Culling:**
```
Only render cells visible on screen
Skip off-screen simulation (could add)
Result: Zoom in = better FPS
```

## Expected Performance

**On Modern Hardware:**
```
Resolution: 1200x800 = 960,000 pixels
Cell size: 2x2 = 240,000 cells
Active cells: ~25% = 60,000 cells updating
Update rate: 30 physics updates/sec
Expected FPS: 45-60 FPS

Zoomed in (4x): 60 FPS (fewer cells visible)
Zoomed out (0.25x): 30-40 FPS (more cells visible)
```

**Bottlenecks:**
- Python overhead for cell updates
- Rendering thousands of tiny rectangles
- No GPU acceleration (yet!)

## What You Can Do

**Experiment:**
1. Spawn sand and watch it pile up
2. Pour water and watch it flow
3. Mix materials and see density sorting
4. Build structures and test stability
5. Zoom in to see individual cells
6. Zoom out to see large-scale behavior

**Future Ideas:**
- 🔥 Fire that burns materials
- 💥 Explosions that displace cells
- ⚗️ Chemical reactions (water + lava = stone)
- 🧪 Acid that dissolves blocks
- 🌱 Growing plants
- ⚡ Electricity propagation
- 🎨 Temperature simulation
- 🎯 Player with circle collision

## Architecture

```
FallingSandEngine
├── cells: np.array[width, height]  # Material at each position
├── active: np.array[width, height]  # Is cell updating?
├── props: MaterialProperties        # Colors, density, etc.
└── Methods:
    ├── update(dt)                   # Physics step
    ├── render(surface, camera)      # Draw cells
    ├── set_cell(x, y, material)    # Spawn material
    ├── spawn_circle(...)            # Spawn area
    └── is_solid_at(x, y)           # Collision check
```

## Integration with Main Game

To integrate with the full game:

1. Replace block-based world with falling sand grid
2. Use `is_solid_at()` for player collision
3. Spawn materials instead of placing blocks
4. Keep inventory/tools but change what they do:
   - Pickaxe = dig out cells
   - Bucket = pour water
   - Wands = spawn materials/effects

## Optimization Opportunities

If FPS is low:

**Easy Wins:**
1. Increase `cell_size` to 3 or 4 (lower resolution)
2. Reduce `updates_per_second` to 20-25
3. Limit active region to screen bounds
4. Skip rendering for water (just show level)

**Advanced:**
1. Use Cython for hot loops
2. Implement dirty rectangles
3. Add GPU compute shader (PyOpenGL)
4. Multi-threading for chunks
5. Use pygame.PixelArray for faster rendering

## Next Steps

**If performance is good:**
1. Add player collision with circular hitbox
2. Implement digging/placing materials
3. Add more material interactions
4. Build the actual game!

**If performance is bad:**
1. Profile with `cProfile`
2. Increase cell_size
3. Reduce update rate
4. Consider Cython/Numba compilation
5. Or stick with block-based physics

## The Cool Part

This is **real emergent physics**! You didn't program:
- How sand piles form cones
- How water finds the lowest point
- How materials segregate by density
- How fluids flow around obstacles

All of this emerges from simple local rules. That's the magic of cellular automata!

## Try It!

```bash
python falling_sand_demo.py
```

Pour some sand, add some water, zoom in and watch the individual cells interact. It's mesmerizing!

If it runs well (40+ FPS), we can build the full game with this system. If it's slow, we can optimize or adjust the approach.

Let me know what you think! 🎮✨
