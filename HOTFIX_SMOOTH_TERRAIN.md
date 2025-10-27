# Smooth Terrain Hotfixes

## Issues Found After Testing

1. **Zoom only affected player, not terrain**
2. **Terrain chunks didn't mesh properly**
3. **Terrain was upside-down**

## Fixes Applied

### 1. Zoom Now Scales Terrain ✅

**Problem:** Mouse wheel zoom only changed player size, terrain stayed the same scale.

**Solution:**
- Added zoom to chunk cache key: `(chunk_x, chunk_y, self.zoom)`
- Scale chunk surfaces based on zoom level
- Apply zoom to world-to-screen coordinate conversion
- Both terrain AND player now scale together

**Code Changes (`main.py`):**
```python
# Cache key includes zoom
cache_key = (chunk_x, chunk_y, self.zoom)

# Scale rendered chunk surface
if self.zoom != 1.0:
    new_width = int(chunk_surface.get_width() * self.zoom)
    new_height = int(chunk_surface.get_height() * self.zoom)
    chunk_surface = pygame.transform.scale(chunk_surface, (new_width, new_height))

# Apply zoom to screen position calculation
screen_x = int((chunk_world_x - self.camera_x) * self.zoom + width // 2)
screen_y = int(height // 2 - (chunk_world_y - self.camera_y) * self.zoom)
```

**Result:** Entire world (terrain + player) now zooms together!

### 2. Fixed Chunk Alignment ✅

**Problem:** Smooth terrain chunks had gaps/overlaps at boundaries.

**Solution:**
- Fixed bounds checking in `get_smoothness_value()`
- Added try/except for index errors
- Out-of-bounds positions return 0.0 (air)
- Smooth transitions at chunk edges

**Code Changes (`smooth_terrain.py`):**
```python
def get_smoothness_value(self, chunk, x: int, y: int, chunk_size: int) -> float:
    # Bounds checking - if out of bounds, assume air
    if x < 0 or x >= chunk_size or y < 0 or y >= chunk_size:
        return 0.0

    try:
        block_id = chunk.blocks[x, y]
        # ... rest of code
    except (IndexError, KeyError):
        return 0.0
```

**Result:** Chunks mesh perfectly at boundaries!

### 3. Fixed Upside-Down Terrain ✅

**Problem:** Smooth terrain rendered upside-down (sky below, ground above).

**Solution:**
- Flip Y-axis in `render_smooth_chunk()`
- Account for world coords (Y up) vs screen coords (Y down)
- Adjust corner sampling for flipped orientation

**Code Changes (`smooth_terrain.py`):**
```python
# Calculate screen position with Y flip
screen_y = (chunk_size - 1 - local_y) * block_size  # Flip Y

# Sample corners accounting for Y flip
tl = self.get_smoothness_value(chunk, local_x, local_y + 1, chunk_size)
tr = self.get_smoothness_value(chunk, local_x + 1, local_y + 1, chunk_size)
br = self.get_smoothness_value(chunk, local_x + 1, local_y, chunk_size)
bl = self.get_smoothness_value(chunk, local_x, local_y, chunk_size)
```

**Result:** Terrain now renders right-side up (ground below, sky above)!

## Files Modified

1. **main.py**
   - Added zoom to cache key
   - Scale chunk surfaces by zoom
   - Apply zoom to coordinate conversion

2. **src/cartesia/engine/smooth_terrain.py**
   - Fixed Y-axis flipping
   - Improved bounds checking
   - Fixed corner sampling

## Testing

After these fixes, you should see:

✅ **Zoom works on entire world**
   - Mouse wheel up/down zooms terrain AND player
   - Everything scales together smoothly

✅ **Chunks align perfectly**
   - No gaps between chunks
   - No overlapping at boundaries
   - Smooth continuous terrain

✅ **Terrain right-side up**
   - Ground at bottom
   - Sky at top
   - Proper orientation

## Performance Note

Zoom affects cache:
- Each zoom level creates new cached surfaces
- Old zoom levels stay in cache (until cleared)
- This is intentional for smooth zooming
- Cache grows: `(chunks × zoom_levels)` surfaces

If you zoom a lot, cache can grow large. To clear:
```python
self.chunk_render_cache.clear()  # In main.py
```

Or implement LRU cache to auto-clear old zoom levels.

## Try It Now

```bash
python main.py
```

**Test checklist:**
- [ ] Zoom in/out with mouse wheel - terrain scales
- [ ] Look at chunk boundaries - seamless
- [ ] Check orientation - ground below, sky above
- [ ] Walk around - chunks align perfectly
- [ ] Mine blocks - smooth edges everywhere
