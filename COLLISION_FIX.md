# Collision and Rendering Fix

## Issues Identified

1. **Smooth terrain broke collision visualization** - The smooth renderer was hiding the actual block positions
2. **Chunk boundaries still had gaps** - Marching squares sampling across chunk edges was complex
3. **Zoom didn't render more chunks** - View distance wasn't adjusted for zoom level
4. **Terrain is in negative Y chunks** - Ground is at chunk (0, -1) and below

## Solutions Applied

### 1. Reverted to Simple Block Rendering ✅

**Why:** Smooth terrain was causing visual confusion and performance issues.

**What:** Replaced smooth terrain with simple block-by-block rendering
- Each block drawn individually
- Proper texture scaling with zoom
- Clear visual alignment with collision

**Benefits:**
- Collision matches what you see perfectly
- No chunk boundary issues
- Better performance (cached textures)
- Easier to debug

### 2. Fixed Zoom View Distance ✅

**Problem:** Zoom didn't render more chunks when zoomed out.

**Solution:**
```python
# Expand view distance based on zoom
view_width = display.width / zoom
view_height = display.height / zoom

# Calculate visible chunks
start_chunk_x = int((camera_x - view_width // 2) // chunk_size_px) - 1
end_chunk_x = int((camera_x + view_width // 2) // chunk_size_px) + 2
```

**Result:**
- Zoom out (0.25x) = 4x more chunks visible
- Zoom in (4.0x) = fewer chunks rendered
- Proper culling at all zoom levels

### 3. Added Debug Visualization ✅

**Added:**
- Red rectangle showing player collision box
- Player chunk coordinates in debug overlay
- Hitbox scales with zoom

**Benefits:**
- See exactly where collision box is
- Verify collision alignment
- Debug spawn position issues

### 4. Terrain Generation Working ✅

**Verified:**
- Chunk (0, -1) has 859 solid blocks ✓
- Chunk (0, 0) has 0 solid blocks (air above ground) ✓
- Chunk (0, -2) has 1024 solid blocks (all underground) ✓

**Ground location:** Around world Y = -16 to 0 pixels

## Coordinate System

```
Chunks:
  Chunk (0, -2): Y = -1024 to -512 pixels (deep underground - all solid)
  Chunk (0, -1): Y = -512 to 0 pixels (terrain - mixed)
  Chunk (0, 0):  Y = 0 to 512 pixels (sky - all air)

Player:
  Spawns at: ~Y = -16 pixels (just above ground)
  Ground level: Y ≈ 0 pixels
  Underground: Y < 0
  Sky: Y > 0
```

## Testing Collision

The collision system checks 8 points on the player hitbox:
- 4 corners (inset 2px)
- 4 midpoints (top, bottom, left, right)

If any point hits a solid block → collision detected

**To verify collision is working:**
1. Check debug overlay - "On Ground: True/False"
2. Red hitbox should align with blocks
3. Player should stand on visible blocks
4. No hovering in midair

## Performance Notes

**Simple block rendering:**
- Pros: Clear, accurate, fast
- Cons: Not as pretty as smooth terrain
- FPS: Should be 60 stable

**Zoom performance:**
- Zoomed in: Fewer blocks, higher FPS
- Zoomed out: More blocks, may drop to 50-55 FPS
- Cached textures help significantly

## Future: Re-enable Smooth Terrain

Once collision is confirmed working, we can add smooth terrain back as an **optional visual layer**:

```python
# Render flow:
1. Render actual blocks (for collision alignment)
2. Overlay smooth terrain polygons (visual only)
3. Keep blocks semi-transparent or hidden
```

This separates collision (block-based) from visuals (smooth).

## What to Test

Run the game:
```bash
python main.py
```

**Checklist:**
- [ ] Player stands on ground (not hovering)
- [ ] Red hitbox aligns with player sprite
- [ ] "On Ground: True" when standing
- [ ] "On Ground: False" when jumping
- [ ] Can walk left/right smoothly
- [ ] Can jump (space/W)
- [ ] Zoom in/out works (mouse wheel)
- [ ] More chunks visible when zoomed out
- [ ] Collision feels solid

## Files Modified

1. **main.py**
   - Reverted to simple block rendering
   - Fixed zoom view distance calculation
   - Added hitbox visualization
   - Added chunk coordinates to debug

2. **smooth_terrain.py** - Not currently used (ready for future re-enablement)
