extends CharacterBody2D

# Movement constants
const SPEED = 300.0
const JUMP_VELOCITY = -400.0
const ACCELERATION = 1500.0
const AIR_ACCELERATION = 750.0
const FRICTION = 1000.0
const AIR_RESISTANCE = 200.0
const GRAVITY = 980.0

# Mining constants
const MINING_RANGE = 5 * 16  # 5 tiles
const MINING_TIME = 0.5  # seconds to mine a block

# Equipment paths
const SWORD_PATH = "res://godot/equipment/wooden_sword.tscn"
const SHIELD_PATH = "res://godot/equipment/wooden_shield.tscn"

# Animation states
enum AnimState {
	IDLE,
	WALK,
	JUMP,
	FALL,
	MINE,
	SLASH,
	BLOCK,
	HURT,
	DEATH
}

# Equipment slots
enum EquipSlot {
	MAIN_HAND,
	OFF_HAND,
	HEAD,
	BODY,
	LEGS,
	FEET
}

# Inventory
const MAX_STACK = 999
const HOTBAR_SIZE = 10

# Node references
@onready var sprite = $Sprite2D
@onready var anim_player = $AnimationPlayer
@onready var mining_ray = $MiningRayCast2D
@onready var world = get_parent()
@onready var equipment_mount = $EquipmentMount

# State variables
var current_anim := AnimState.IDLE
var facing_right := true
var mining_timer := 0.0
var mining_target := Vector2i.ZERO
var mining_block_type := ""
var is_mining := false

# Inventory system
var inventory := {}  # Dictionary of item_name: quantity
var hotbar := []  # Array of selected items
var selected_slot := 0
var equipped_items := {}  # Dictionary of EquipSlot: Equipment

func _ready() -> void:
	# Initialize hotbar
	hotbar.resize(HOTBAR_SIZE)
	
	# Setup mining raycast
	mining_ray.enabled = true
	mining_ray.collision_mask = 1  # Match tilemap collision layer
	
	# Create equipment mount if it doesn't exist
	if not equipment_mount:
		equipment_mount = Node2D.new()
		equipment_mount.name = "EquipmentMount"
		add_child(equipment_mount)
	
	# Initialize animations
	setup_animations()
	
	# Load test equipment
	load_test_equipment()

func load_test_equipment() -> void:
	# Load and equip sword
	var sword_scene = load(SWORD_PATH)
	if sword_scene:
		var sword = sword_scene.instantiate()
		equip_item(sword, EquipSlot.MAIN_HAND)
	
	# Load and equip shield
	var shield_scene = load(SHIELD_PATH)
	if shield_scene:
		var shield = shield_scene.instantiate()
		equip_item(shield, EquipSlot.OFF_HAND)

func _physics_process(delta: float) -> void:
	handle_movement(delta)
	handle_actions(delta)
	handle_animation()
	handle_equipment_direction()
	move_and_slide()

func handle_movement(delta: float) -> void:
	# Apply gravity
	if not is_on_floor():
		velocity.y += GRAVITY * delta

	# Handle jump
	if Input.is_action_just_pressed("jump") and is_on_floor() and can_move():
		velocity.y = JUMP_VELOCITY
		current_anim = AnimState.JUMP

	# Get movement input
	var direction := Input.get_axis("move_left", "move_right")
	
	# Apply movement only if not blocked by equipment
	if can_move():
		if direction != 0:
			var accel = ACCELERATION if is_on_floor() else AIR_ACCELERATION
			velocity.x = move_toward(velocity.x, direction * SPEED, accel * delta)
			facing_right = direction > 0
		else:
			var friction = FRICTION if is_on_floor() else AIR_RESISTANCE
			velocity.x = move_toward(velocity.x, 0, friction * delta)

func handle_equipment_direction() -> void:
	# Update equipment facing direction
	if equipment_mount:
		equipment_mount.scale.x = 1 if facing_right else -1

func can_move() -> bool:
	# Check if any equipment is restricting movement
	var shield = equipped_items.get(EquipSlot.OFF_HAND)
	return not (shield and shield is Shield and shield.block_area.monitoring)

func handle_actions(delta: float) -> void:
	# Handle mining
	if Input.is_action_pressed("mine") and not is_blocking():
		handle_mining(delta)
	else:
		is_mining = false
		mining_timer = 0.0

	# Handle block placement
	if Input.is_action_just_pressed("place") and not is_blocking():
		handle_block_placement()

	# Handle equipment use
	handle_equipment()

	# Handle hotbar selection
	for i in range(HOTBAR_SIZE):
		if Input.is_action_just_pressed("hotbar_" + str(i + 1)):
			selected_slot = i

func is_blocking() -> bool:
	var shield = equipped_items.get(EquipSlot.OFF_HAND)
	return shield and shield is Shield and shield.block_area.monitoring

func handle_equipment() -> void:
	# Handle main hand equipment (usually weapons)
	var main_hand = equipped_items.get(EquipSlot.MAIN_HAND)
	if main_hand and Input.is_action_just_pressed("attack") and not is_blocking():
		main_hand.use()

	# Handle off hand equipment (usually shields)
	var off_hand = equipped_items.get(EquipSlot.OFF_HAND)
	if off_hand:
		if Input.is_action_just_pressed("block"):
			off_hand.use()
		elif Input.is_action_just_released("block"):
			off_hand.stop_use()

func handle_mining(delta: float) -> void:
	mining_ray.target_position = get_local_mouse_position().normalized() * MINING_RANGE
	
	if mining_ray.is_colliding():
		var collision_point = mining_ray.get_collision_point()
		var tile_pos = world.tile_map.local_to_map(collision_point)
		
		# Check if we're in range
		if collision_point.distance_to(global_position) <= MINING_RANGE:
			if not is_mining or tile_pos != mining_target:
				# Start mining new block
				is_mining = true
				mining_target = tile_pos
				mining_timer = 0.0
				mining_block_type = get_block_type(tile_pos)
			else:
				# Continue mining current block
				mining_timer += delta
				if mining_timer >= MINING_TIME:
					mine_block(tile_pos)
					mining_timer = 0.0

func handle_block_placement() -> void:
	var mouse_pos = get_global_mouse_position()
	var tile_pos = world.tile_map.local_to_map(mouse_pos)
	
	# Check if selected hotbar slot has blocks
	var selected_item = hotbar[selected_slot]
	if selected_item and selected_item.begins_with("BLOCK_"):
		if remove_from_inventory(selected_item, 1):
			world.modify_block(tile_pos, selected_item.trim_prefix("BLOCK_"))

func equip_item(item: Equipment, slot: EquipSlot) -> void:
	# Unequip current item in slot if it exists
	if equipped_items.has(slot):
		var current_item = equipped_items[slot]
		current_item.unequip()
		equipment_mount.remove_child(current_item)
	
	# Equip new item
	equipped_items[slot] = item
	equipment_mount.add_child(item)
	item.equip()
	
	# Connect signals
	if item is MeleeWeapon:
		item.connect("on_use", _on_weapon_use)
	elif item is Shield:
		item.connect("on_use", _on_shield_use)
		item.connect("on_stop_use", _on_shield_stop_use)

func unequip_item(slot: EquipSlot) -> void:
	if equipped_items.has(slot):
		var item = equipped_items[slot]
		item.unequip()
		equipment_mount.remove_child(item)
		equipped_items.erase(slot)

func _on_weapon_use() -> void:
	current_anim = AnimState.SLASH

func _on_shield_use() -> void:
	current_anim = AnimState.BLOCK

func _on_shield_stop_use() -> void:
	current_anim = AnimState.IDLE

func get_block_type(pos: Vector2i) -> String:
	# Get block type from world
	# This should be implemented based on your world's tile system
	if world.has_method("get_block_type"):
		return world.get_block_type(pos)
	return ""

func mine_block(pos: Vector2i) -> void:
	var block_type = get_block_type(pos)
	if block_type and block_type != "AIR":
		world.modify_block(pos, "AIR")
		add_to_inventory("BLOCK_" + block_type, 1)

func add_to_inventory(item: String, amount: int) -> bool:
	if item in inventory:
		if inventory[item] + amount <= MAX_STACK:
			inventory[item] += amount
			return true
	else:
		inventory[item] = amount
		return true
	return false

func remove_from_inventory(item: String, amount: int) -> bool:
	if item in inventory and inventory[item] >= amount:
		inventory[item] -= amount
		if inventory[item] <= 0:
			inventory.erase(item)
		return true
	return false

func setup_animations() -> void:
	# Setup frame ranges for each animation state
	var animations = {
		AnimState.IDLE: {"start": 0, "end": 4, "row": 0, "loop": true},
		AnimState.WALK: {"start": 0, "end": 8, "row": 11, "loop": true},
		AnimState.JUMP: {"start": 0, "end": 3, "row": 2, "loop": false},
		AnimState.FALL: {"start": 2, "end": 3, "row": 20, "loop": false},
		AnimState.MINE: {"start": 0, "end": 5, "row": 3, "loop": true},
		AnimState.SLASH: {"start": 0, "end": 5, "row": 4, "loop": false},
		AnimState.BLOCK: {"start": 0, "end": 2, "row": 5, "loop": false},
		AnimState.HURT: {"start": 0, "end": 3, "row": 6, "loop": false},
		AnimState.DEATH: {"start": 0, "end": 5, "row": 7, "loop": false}
	}
	
	# Create animation library
	var library = AnimationLibrary.new()
	
	# Create animations
	for anim_name in animations:
		var anim = Animation.new()
		var track_index = anim.add_track(Animation.TYPE_VALUE)
		anim.track_set_path(track_index, "Sprite2D:frame")
		
		var data = animations[anim_name]
		var frame_count = data.end - data.start + 1
		var frame_time = 0.1  # Adjust animation speed here
		
		for i in range(frame_count):
			var frame = data.start + i
			var time = i * frame_time
			anim.track_insert_key(track_index, time, frame + (data.row * 13))
		
		anim.length = frame_count * frame_time
		anim.loop_mode = Animation.LOOP_LINEAR if data.loop else Animation.LOOP_NONE
		
		# Add animation to library
		library.add_animation(str(anim_name), anim)
	
	# Add library to animation player
	anim_player.add_animation_library("", library)  # Empty string means default library

func handle_animation() -> void:
	var new_anim := AnimState.IDLE
	
	# Determine animation state
	if is_blocking():
		new_anim = AnimState.BLOCK
	elif current_anim == AnimState.SLASH:
		# Let slash animation finish
		return
	elif is_mining:
		new_anim = AnimState.MINE
	elif not is_on_floor():
		new_anim = AnimState.JUMP if velocity.y < 0 else AnimState.FALL
	elif abs(velocity.x) > 10:
		new_anim = AnimState.WALK
	
	# Update sprite if animation state changed
	if new_anim != current_anim:
		current_anim = new_anim
		play_animation(current_anim)
	
	# Update sprite direction
	sprite.flip_h = not facing_right

func play_animation(anim_state: AnimState) -> void:
	anim_player.play(str(anim_state))
