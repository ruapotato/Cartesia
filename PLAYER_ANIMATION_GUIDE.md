# Player Animation System - Implementation Guide

## Overview

The player sprite animation system has been fully implemented! The player is now rendered as a fully animated character using the Universal LPC spritesheet format with multi-layer sprite compositing.

## What Was Implemented

### 1. Animation System (`src/cartesia/entities/player_animation.py`)

A complete animation system with the following features:

#### Animation States
- **Idle** - Standing still (first frame of walk animation)
- **Walk** - 9-frame walking cycle
- **Jump** - Ascending animation (when velocity_y < 0)
- **Fall** - Descending animation (when velocity_y > 0)

#### Direction Handling
- Left and right movement animations
- Automatic direction switching based on velocity
- Smooth transitions between states

#### Multi-Layer Sprite Support
The system composites multiple sprite layers in real-time:
1. **Body Layer** - Base character (skin tone)
2. **Clothing Layer** - Shirts, armor, accessories
3. **Hair Layer** - Hairstyles rendered on top

Default character configuration:
- Body: `body/male/light.png` (light skin tone)
- Clothing: `torso/shirts/longsleeve/male/teal_longsleeve.png` (teal shirt)
- Hair: `hair/male/bangslong2.png` (long bangs hairstyle)

### 2. Integration with Game (`play_v2.py`)

The animation system is fully integrated:
- Imports the animation system at startup
- Updates animations every frame based on physics state
- Renders animated sprites instead of red rectangle
- Scales sprites to 0.5x (32x32) to match game scale

### 3. Performance Optimizations

- **Frame Caching** - Extracted frames are cached to avoid repeated spritesheet reads
- **Efficient Compositing** - Layers are only composited when needed
- **Smart Updates** - Animation only advances when timer exceeds threshold

## How to Test

### Run the Game
```bash
source pyenv/bin/activate
python play_v2.py
```

### What to Look For

1. **Idle Animation**
   - Stand still (no keys pressed)
   - Player should display a standing pose

2. **Walking Animation**
   - Press A/D or Arrow keys to move
   - Should see smooth 9-frame walking cycle
   - Animation speed matches movement

3. **Jump Animation**
   - Press Space/W while on ground
   - Should see jump pose while ascending

4. **Fall Animation**
   - Release jump or walk off edge
   - Should see falling pose while descending

5. **Direction Changes**
   - Move left (A or Left Arrow)
   - Move right (D or Right Arrow)
   - Character should face the direction of movement

## Customization

### Change Character Appearance

Edit `play_v2.py` to customize the character:

```python
# Current (default):
self.player_animation = create_player_animation()

# Custom character:
self.player_animation = create_player_animation(
    body_sprite="path/to/body.png",
    hair_sprite="path/to/hair.png",
    clothing_sprite="path/to/clothing.png"
)
```

### Available Assets

All LPC spritesheets are located in:
`img/player/Universal-LPC-spritesheet/`

#### Body Options
- `body/male/light.png` - Light skin
- `body/male/tanned.png` - Tanned skin
- `body/male/dark.png` - Dark skin
- `body/male/darkelf.png` - Dark elf
- `body/male/orc.png` - Orc
- `body/male/skeleton.png` - Skeleton

#### Hair Options (in `hair/male/`)
- `bangslong2.png` - Long bangs
- `bangslong.png` - Medium bangs
- `bangsshort.png` - Short bangs
- Plus many more styles

#### Clothing Options (in `torso/shirts/longsleeve/male/`)
- `teal_longsleeve.png` - Teal shirt
- `brown_longsleeve.png` - Brown shirt
- `white_longsleeve.png` - White shirt
- `maroon_longsleeve.png` - Maroon shirt

### Adjust Animation Speed

Edit `src/cartesia/entities/player_animation.py`:

```python
self.animation_speed = 0.1  # seconds per frame
# Lower = faster animation
# Higher = slower animation
```

### Change Sprite Scale

Edit `play_v2.py`:

```python
self.player_animation.render(self.screen, player_screen_x, player_screen_y, scale=0.5)
# scale=0.5 → 32x32 pixels (current)
# scale=1.0 → 64x64 pixels (original size)
# scale=0.75 → 48x48 pixels
```

## Technical Details

### LPC Spritesheet Format

The Universal LPC format uses a 64x64 grid:

```
Row  0-3:  Spellcast (up, left, down, right)
Row  4-7:  Thrust (up, left, down, right)
Row  8-11: Walk (up, left, down, right)      ← Used for movement
Row 12-15: Slash (up, left, down, right)
Row 16-19: Shoot (up, left, down, right)
Row 20:    Hurt/Death
```

Currently using Row 8-11 (Walk animations) for all states.

### Animation State Logic

```python
if not on_ground:
    if velocity_y < 0:
        state = JUMP
    else:
        state = FALL
elif abs(velocity_x) > 10:
    state = WALK
else:
    state = IDLE
```

### Frame Advancement

```python
animation_timer += dt
if animation_timer >= animation_speed:
    frame_index = (frame_index + 1) % WALK_FRAMES
    animation_timer = 0.0
```

## Files Modified

1. **Created:** `src/cartesia/entities/player_animation.py`
   - Complete animation system
   - Multi-layer sprite support
   - State machine implementation

2. **Modified:** `play_v2.py`
   - Added import for player animation
   - Created animation instance
   - Update animation each frame
   - Render animated sprite instead of rectangle

3. **Updated:** `README.md`
   - Moved "Player sprite animations" to Implemented section

4. **Updated:** `WHATS_NEW.md`
   - Marked animations as complete
   - Added detailed feature description

## Next Steps

### Potential Enhancements

1. **More Animation States**
   - Add thrust/slash animations for combat
   - Add spellcast animations for magic
   - Add hurt animation when taking damage

2. **More Layers**
   - Add pants/legs layer
   - Add armor layer
   - Add accessories (hats, capes, etc.)

3. **Character Customization UI**
   - In-game character creator
   - Save/load character appearance

4. **Animated NPCs**
   - Reuse system for skeleton enemies
   - Add tree NPCs with animations
   - Create animated villagers

## Conclusion

The player animation system is fully functional and integrated! The game now has smooth, professional-looking character animations that automatically sync with the physics engine.

Try running `python play_v2.py` to see it in action!
