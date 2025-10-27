"""
Falling sand physics - Noita-style cellular automata.

Every pixel is a material that follows simple rules to create emergent behavior.
"""
import numpy as np
import pygame
from enum import IntEnum
from typing import Tuple, Optional
from numba import njit


class Material(IntEnum):
    """Material types for cellular automata."""
    AIR = 0
    WATER = 1
    LAVA = 2
    SAND = 3
    DIRT = 4
    GRASS = 5
    STONE = 6


class MaterialProperties:
    """Properties for each material type."""

    def __init__(self):
        self.colors = {
            Material.AIR: (0, 0, 0, 0),  # Transparent - 0
            Material.WATER: (50, 100, 200, 200),  # Blue (semi-transparent) - 1
            Material.LAVA: (255, 100, 0, 255),  # Orange-red - 2
            Material.SAND: (194, 178, 128, 255),  # Tan - 3
            Material.DIRT: (134, 96, 67, 255),  # Brown - 4
            Material.GRASS: (88, 164, 76, 255),  # Green - 5
            Material.STONE: (100, 100, 100, 255),  # Gray - 6
        }

        # Material density (higher = sinks in lower density materials)
        self.density = {
            Material.AIR: 0,      # 0
            Material.WATER: 1,    # 1
            Material.LAVA: 1,     # 2
            Material.SAND: 2,     # 3
            Material.DIRT: 3,     # 4
            Material.GRASS: 3,    # 5 - Same as dirt
            Material.STONE: 10,   # 6
        }

        # Can material move?
        self.movable = {
            Material.AIR: False,     # 0
            Material.WATER: True,    # 1
            Material.LAVA: True,     # 2
            Material.SAND: True,     # 3
            Material.DIRT: True,     # 4 - Can fall
            Material.GRASS: False,   # 5 - Sticks like stone
            Material.STONE: False,   # 6
        }

        # How material moves
        self.fluid = {
            Material.AIR: False,     # 0
            Material.WATER: True,    # 1 - Spreads horizontally
            Material.LAVA: True,     # 2 - Spreads horizontally
            Material.SAND: False,    # 3
            Material.DIRT: False,    # 4
            Material.GRASS: False,   # 5 - Falls like dirt, not a fluid
            Material.STONE: False,   # 6
        }


@njit(cache=True)
def update_powder_jit(cells, active, x, y, frame, grid_width, grid_height):
    """JIT-compiled powder update - BLAZING FAST!"""
    material = cells[x, y]

    # Check bounds
    if y + 1 >= grid_height:
        active[x, y] = False
        return False

    below = cells[x, y + 1]

    # Material densities (hardcoded for JIT performance)
    # AIR=0, WATER=1, LAVA=1, SAND=2, DIRT=3, GRASS=3, STONE=10
    density_map = [0, 1, 1, 2, 3, 3, 10]  # Index by material ID

    material_density = density_map[material]
    below_density = density_map[below]

    # Try fall down (heavier materials sink through lighter ones)
    # Stone (density 10) never moves
    if below == 0 or (material_density > below_density and below != 6):
        cells[x, y] = below
        cells[x, y + 1] = material
        active[x, y] = True
        active[x, y + 1] = True
        return True

    # Try diagonal (alternating pattern for realistic behavior)
    if frame % 2 == 0:  # Left first
        if x > 0 and cells[x - 1, y + 1] == 0:
            cells[x, y] = 0
            cells[x - 1, y + 1] = material
            active[x, y] = True
            active[x - 1, y + 1] = True
            return True
        if x < grid_width - 1 and cells[x + 1, y + 1] == 0:
            cells[x, y] = 0
            cells[x + 1, y + 1] = material
            active[x, y] = True
            active[x + 1, y + 1] = True
            return True
    else:  # Right first
        if x < grid_width - 1 and cells[x + 1, y + 1] == 0:
            cells[x, y] = 0
            cells[x + 1, y + 1] = material
            active[x, y] = True
            active[x + 1, y + 1] = True
            return True
        if x > 0 and cells[x - 1, y + 1] == 0:
            cells[x, y] = 0
            cells[x - 1, y + 1] = material
            active[x, y] = True
            active[x - 1, y + 1] = True
            return True

    # Can't move
    active[x, y] = False
    return False


@njit(cache=True)
def update_fluid_jit(cells, active, x, y, frame, grid_width, grid_height):
    """JIT-compiled fluid update - BLAZING FAST!"""
    material = cells[x, y]

    # Try fall down (water falls through air)
    if y + 1 < grid_height:
        below = cells[x, y + 1]
        if below == 0:  # Air - just fall
            cells[x, y] = 0
            cells[x, y + 1] = material
            active[x, y] = True
            active[x, y + 1] = True
            return True

    # Try fall diagonally down if can't fall straight
    if y + 1 < grid_height:
        # Try down-left
        if x > 0 and cells[x - 1, y + 1] == 0:
            cells[x, y] = 0
            cells[x - 1, y + 1] = material
            active[x, y] = True
            active[x - 1, y + 1] = True
            return True
        # Try down-right
        if x < grid_width - 1 and cells[x + 1, y + 1] == 0:
            cells[x, y] = 0
            cells[x + 1, y + 1] = material
            active[x, y] = True
            active[x + 1, y + 1] = True
            return True

    # Try spread horizontally (alternating pattern)
    if frame % 2 == 0:
        if x > 0 and cells[x - 1, y] == 0:
            cells[x, y] = 0
            cells[x - 1, y] = material
            active[x, y] = True
            active[x - 1, y] = True
            return True
        if x < grid_width - 1 and cells[x + 1, y] == 0:
            cells[x, y] = 0
            cells[x + 1, y] = material
            active[x, y] = True
            active[x + 1, y] = True
            return True
    else:
        if x < grid_width - 1 and cells[x + 1, y] == 0:
            cells[x, y] = 0
            cells[x + 1, y] = material
            active[x, y] = True
            active[x + 1, y] = True
            return True
        if x > 0 and cells[x - 1, y] == 0:
            cells[x, y] = 0
            cells[x - 1, y] = material
            active[x, y] = True
            active[x - 1, y] = True
            return True

    # Before deactivating, check if there's air below (even not directly adjacent)
    # Keep water active if there's any air below so it will eventually spill and fall
    if y + 1 < grid_height:
        # Check directly below
        if cells[x, y + 1] == 0:
            return True  # Keep active, will fall next frame
        # Check if sitting on an edge - check diagonals for potential fall paths
        if x > 0 and cells[x - 1, y + 1] == 0:
            return True  # Can potentially fall diagonally
        if x < grid_width - 1 and cells[x + 1, y + 1] == 0:
            return True  # Can potentially fall diagonally

    active[x, y] = False
    return False


@njit(cache=True)
def update_simulation_jit_bounded(cells, active, frame, grid_width, grid_height, min_x, max_x, min_y, max_y):
    """
    JIT-compiled main simulation loop - BOUNDED for MAXIMUM PERFORMANCE!

    Only iterates the bounding box of active cells, not the entire world!
    """
    offset = frame % 2
    dirty = False

    # Scan from bottom to top OF ACTIVE REGION ONLY!
    for y in range(max_y, min_y, -1):
        # Start at correct offset within bounds
        start_x = min_x if min_x % 2 == offset else min_x + 1
        for x in range(start_x, max_x, 2):
            if not active[x, y]:
                continue

            material = cells[x, y]

            # Fast path: air
            if material == 0:
                active[x, y] = False
                continue

            # Update based on material type
            if material == 3 or material == 4:  # Sand or Dirt (not grass - it's static now)
                if update_powder_jit(cells, active, x, y, frame, grid_width, grid_height):
                    dirty = True
            elif material == 1 or material == 2:  # Water or Lava
                if update_fluid_jit(cells, active, x, y, frame, grid_width, grid_height):
                    dirty = True

    return dirty


class FallingSandEngine:
    """
    Cellular automata engine for falling sand physics.

    Uses chunk-based simulation with numpy for performance.
    """

    def __init__(self, width: int, height: int, cell_size: int = 2):
        """
        Initialize the falling sand engine.

        Args:
            width: World width in pixels
            height: World height in pixels
            cell_size: Size of each cell in pixels (2 = half resolution)
        """
        self.cell_size = cell_size
        self.grid_width = width // cell_size
        self.grid_height = height // cell_size

        # Material grid (each cell is a Material enum value)
        self.cells = np.zeros((self.grid_width, self.grid_height), dtype=np.int8)

        # Activity tracking (only update active cells)
        self.active = np.ones((self.grid_width, self.grid_height), dtype=bool)

        # Properties
        self.props = MaterialProperties()

        # Update pattern (checkerboard for stability)
        self.frame = 0

        # Rendering cache
        self.cached_surface = None
        self.dirty = True

    def set_cell(self, x: int, y: int, material: Material):
        """Set a cell to a material."""
        grid_x = x // self.cell_size
        grid_y = y // self.cell_size

        if 0 <= grid_x < self.grid_width and 0 <= grid_y < self.grid_height:
            self.cells[grid_x, grid_y] = material
            self._activate_cell(grid_x, grid_y)

    def get_cell(self, x: int, y: int) -> Material:
        """Get the material at a position."""
        grid_x = x // self.cell_size
        grid_y = y // self.cell_size

        if 0 <= grid_x < self.grid_width and 0 <= grid_y < self.grid_height:
            return Material(self.cells[grid_x, grid_y])
        return Material.AIR

    def _activate_cell(self, x: int, y: int, radius: int = 2):
        """Mark cell and neighbors as active."""
        x_min = max(0, x - radius)
        x_max = min(self.grid_width, x + radius + 1)
        y_min = max(0, y - radius)
        y_max = min(self.grid_height, y + radius + 1)

        self.active[x_min:x_max, y_min:y_max] = True

    def update(self, dt: float):
        """
        Update the cellular automata simulation - JIT-COMPILED FOR SPEED!
        """
        self.frame += 1

        # Count active cells first
        active_count = np.count_nonzero(self.active)
        if active_count == 0:
            # No active cells = no work to do!
            return

        # Debug: print when we have active cells
        if not hasattr(self, '_last_physics_print'):
            self._last_physics_print = 0
        if self.frame - self._last_physics_print > 30:  # Print every 30 physics frames
            print(f"PHYSICS running: {active_count} active cells")
            self._last_physics_print = self.frame

        # Find bounding box of active cells - MASSIVE optimization!
        active_indices = np.argwhere(self.active)

        min_y = max(1, active_indices[:, 1].min() - 2)  # Add padding for propagation
        max_y = min(self.grid_height - 1, active_indices[:, 1].max() + 2)
        min_x = max(0, active_indices[:, 0].min() - 2)
        max_x = min(self.grid_width - 1, active_indices[:, 0].max() + 2)

        # Call JIT-compiled simulation update ONLY on active region!
        dirty = update_simulation_jit_bounded(
            self.cells,
            self.active,
            self.frame,
            self.grid_width,
            self.grid_height,
            min_x,
            max_x,
            min_y,
            max_y
        )

        if dirty:
            self.dirty = True

    def _update_powder_fast(self, x: int, y: int):
        """Update powder materials - FAST version."""
        material = self.cells[x, y]
        below = self.cells[x, y + 1]

        # Try fall down
        if below == 0 or (material > below and below != 1):  # Air or less dense
            self.cells[x, y], self.cells[x, y + 1] = below, material
            self.active[x, y] = True
            self.active[x, y + 1] = True
            self.dirty = True
            return

        # Try diagonal (unrolled for speed)
        if self.frame % 2 == 0:  # Left first
            if x > 0 and (self.cells[x - 1, y + 1] == 0):
                self.cells[x, y], self.cells[x - 1, y + 1] = 0, material
                self.active[x, y] = True
                self.active[x - 1, y + 1] = True
                self.dirty = True
                return
            if x < self.grid_width - 1 and (self.cells[x + 1, y + 1] == 0):
                self.cells[x, y], self.cells[x + 1, y + 1] = 0, material
                self.active[x, y] = True
                self.active[x + 1, y + 1] = True
                self.dirty = True
                return
        else:  # Right first
            if x < self.grid_width - 1 and (self.cells[x + 1, y + 1] == 0):
                self.cells[x, y], self.cells[x + 1, y + 1] = 0, material
                self.active[x, y] = True
                self.active[x + 1, y + 1] = True
                self.dirty = True
                return
            if x > 0 and (self.cells[x - 1, y + 1] == 0):
                self.cells[x, y], self.cells[x - 1, y + 1] = 0, material
                self.active[x, y] = True
                self.active[x - 1, y + 1] = True
                self.dirty = True
                return

        # Can't move
        self.active[x, y] = False

    def _update_powder(self, x: int, y: int, material: Material):
        """Update powder materials (sand, dirt)."""
        below = self.cells[x, y + 1]

        # Try to fall straight down
        if self._can_displace(material, Material(below)):
            self._swap_cells(x, y, x, y + 1)
            return

        # Try to fall diagonally (randomize direction)
        import random
        directions = [-1, 1]
        random.shuffle(directions)

        for dx in directions:
            nx = x + dx
            if 0 <= nx < self.grid_width:
                below_diagonal = self.cells[nx, y + 1]
                if self._can_displace(material, Material(below_diagonal)):
                    self._swap_cells(x, y, nx, y + 1)
                    return

        # Can't move - deactivate
        self.active[x, y] = False

    def _update_fluid_fast(self, x: int, y: int):
        """Update fluid - FAST version."""
        material = self.cells[x, y]

        # Try fall down
        if y + 1 < self.grid_height and self.cells[x, y + 1] == 0:
            self.cells[x, y], self.cells[x, y + 1] = 0, material
            self.active[x, y] = True
            self.active[x, y + 1] = True
            self.dirty = True
            return

        # Try spread horizontally (unrolled)
        if self.frame % 2 == 0:
            if x > 0 and self.cells[x - 1, y] == 0:
                self.cells[x, y], self.cells[x - 1, y] = 0, material
                self.active[x, y] = True
                self.active[x - 1, y] = True
                self.dirty = True
                return
            if x < self.grid_width - 1 and self.cells[x + 1, y] == 0:
                self.cells[x, y], self.cells[x + 1, y] = 0, material
                self.active[x, y] = True
                self.active[x + 1, y] = True
                self.dirty = True
                return
        else:
            if x < self.grid_width - 1 and self.cells[x + 1, y] == 0:
                self.cells[x, y], self.cells[x + 1, y] = 0, material
                self.active[x, y] = True
                self.active[x + 1, y] = True
                self.dirty = True
                return
            if x > 0 and self.cells[x - 1, y] == 0:
                self.cells[x, y], self.cells[x - 1, y] = 0, material
                self.active[x, y] = True
                self.active[x - 1, y] = True
                self.dirty = True
                return

        self.active[x, y] = False

    def _update_fluid(self, x: int, y: int, material: Material):
        """Update fluid materials (water, lava)."""
        # Try to fall down
        if y + 1 < self.grid_height:
            below = self.cells[x, y + 1]
            if self._can_displace(material, Material(below)):
                self._swap_cells(x, y, x, y + 1)
                return

        # Try to spread horizontally
        import random
        directions = [-1, 1]
        random.shuffle(directions)

        for dx in directions:
            nx = x + dx
            if 0 <= nx < self.grid_width:
                side = self.cells[nx, y]
                if self._can_displace(material, Material(side)):
                    self._swap_cells(x, y, nx, y)
                    return

                # Also try diagonal down
                if y + 1 < self.grid_height:
                    below_diagonal = self.cells[nx, y + 1]
                    if self._can_displace(material, Material(below_diagonal)):
                        self._swap_cells(x, y, nx, y + 1)
                        return

        # Can't move - deactivate
        self.active[x, y] = False

    def _can_displace(self, material: Material, target: Material) -> bool:
        """Check if material can displace target."""
        # Can always move into air
        if target == Material.AIR:
            return True

        # Can't move into solid
        if not self.props.movable[target]:
            return False

        # Higher density sinks
        return self.props.density[material] > self.props.density[target]

    def _swap_cells(self, x1: int, y1: int, x2: int, y2: int):
        """Swap two cells."""
        # Swap materials
        self.cells[x1, y1], self.cells[x2, y2] = self.cells[x2, y2], self.cells[x1, y1]

        # Activate both positions
        self._activate_cell(x1, y1)
        self._activate_cell(x2, y2)
        self.dirty = True

    def render(self, surface: pygame.Surface, camera_x: float, camera_y: float, zoom: float = 1.0):
        """
        Render with camera support - shows only the visible portion!
        """
        screen_width = surface.get_width()
        screen_height = surface.get_height()

        # Calculate visible region in grid coordinates
        # Camera is at center of screen
        view_left = int((camera_x - screen_width // 2) / self.cell_size)
        view_top = int((camera_y - screen_height // 2) / self.cell_size)
        view_width = screen_width // self.cell_size
        view_height = screen_height // self.cell_size

        # Clamp to grid bounds
        view_left = max(0, min(view_left, self.grid_width - view_width))
        view_top = max(0, min(view_top, self.grid_height - view_height))
        view_right = min(self.grid_width, view_left + view_width)
        view_bottom = min(self.grid_height, view_top + view_height)

        # Extract visible portion
        visible_cells = self.cells[view_left:view_right, view_top:view_bottom]

        # Create surface for visible portion
        grid_surface = pygame.Surface((visible_cells.shape[0], visible_cells.shape[1]))
        pixels = pygame.surfarray.pixels3d(grid_surface)

        # Fast color mapping (Material enum: WATER=1, LAVA=2, SAND=3, DIRT=4, GRASS=5, STONE=6)
        pixels[visible_cells == 1] = (50, 100, 200)   # Water
        pixels[visible_cells == 2] = (255, 100, 0)    # Lava
        pixels[visible_cells == 3] = (194, 178, 128)  # Sand
        pixels[visible_cells == 4] = (134, 96, 67)    # Dirt
        pixels[visible_cells == 5] = (88, 164, 76)    # Grass
        pixels[visible_cells == 6] = (100, 100, 100)  # Stone

        del pixels

        # Scale to screen size
        scaled = pygame.transform.scale(grid_surface, (screen_width, screen_height))
        surface.blit(scaled, (0, 0))

    def spawn_circle(self, x: int, y: int, radius: int, material: Material):
        """Spawn a circle of material."""
        grid_x = x // self.cell_size
        grid_y = y // self.cell_size
        grid_radius = radius // self.cell_size

        for dy in range(-grid_radius, grid_radius + 1):
            for dx in range(-grid_radius, grid_radius + 1):
                if dx*dx + dy*dy <= grid_radius*grid_radius:
                    nx = grid_x + dx
                    ny = grid_y + dy
                    if 0 <= nx < self.grid_width and 0 <= ny < self.grid_height:
                        self.cells[nx, ny] = material
                        self._activate_cell(nx, ny)

    def is_solid_at(self, x: int, y: int) -> bool:
        """Check if position has solid material (for collision)."""
        grid_x = x // self.cell_size
        grid_y = y // self.cell_size

        if 0 <= grid_x < self.grid_width and 0 <= grid_y < self.grid_height:
            material = Material(self.cells[grid_x, grid_y])
            return material != Material.AIR and material != Material.WATER
        return False

    def generate_terrain(self, seed: int, config):
        """
        Generate terrain using Perlin noise - OPTIMIZED!

        Fills the sand engine with a Starbound-style world!
        """
        from ..world.generation import TerrainGenerator

        generator = TerrainGenerator(seed, config)

        print(f"  Generating {self.grid_width}x{self.grid_height} grid...")

        # Generate terrain row by row (faster than cell by cell)
        for grid_y in range(self.grid_height):
            if grid_y % 100 == 0:
                print(f"  Progress: {grid_y}/{self.grid_height} rows...")

            for grid_x in range(self.grid_width):
                # Convert grid coords to world coords
                world_x = grid_x * self.cell_size / config.world.block_size
                world_y = grid_y * self.cell_size / config.world.block_size

                # Get depth at this position
                depth = generator.get_solid_depth_at(world_x, world_y)

                if depth <= 0:
                    # Air
                    self.cells[grid_x, grid_y] = Material.AIR
                elif depth < 1.0:
                    # Surface - dirt/grass (we'll use dirt for sand physics)
                    self.cells[grid_x, grid_y] = Material.DIRT
                elif depth < 5.0:
                    # Shallow underground - dirt
                    self.cells[grid_x, grid_y] = Material.DIRT
                else:
                    # Deep underground - stone
                    self.cells[grid_x, grid_y] = Material.STONE

        print(f"  Terrain generation complete!")

        # Mark only surface cells as active (HUGE optimization!)
        self.active.fill(False)
        for grid_x in range(self.grid_width):
            for grid_y in range(1, self.grid_height - 1):
                # If this is solid and cell above is air, mark as active
                if self.cells[grid_x, grid_y] != Material.AIR:
                    if self.cells[grid_x, grid_y - 1] == Material.AIR:
                        self.active[grid_x, grid_y] = True
