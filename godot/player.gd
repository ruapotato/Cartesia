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
const SWORD_PATH = "res://godot/equipment/wooden_sword.tscn"
const SHIELD_PATH = "res://godot/equipment/wooden_shield.tscn"


# Node references
@onready var mining_ray = $MiningRayCast2D
@onready var world = get_parent()
@onready var equipment_mount = $EquipmentMount
@onready var lpc_sprite = $LPCAnimatedSprite2D

# State variables
var facing_direction = LPCEnum.LPCAnimation.WALK_DOWN  # Using walk animation as base for direction
var mining_timer := 0.0
var mining_target := Vector2i.ZERO
var mining_block_type := ""
var is_mining := false
var is_attacking := false
var is_blocking := false

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
	
	# Load test equipment
	load_test_equipment()

func _physics_process(delta: float) -> void:
	handle_movement(delta)
	handle_actions(delta)
	handle_animation()
	handle_equipment_direction()
	move_and_slide()

func handle_movement(delta: float) -> void:
	# Apply gravity if not on floor
	if not is_on_floor():
		velocity.y += GRAVITY * delta

	# Handle jump
	if Input.is_action_just_pressed("jump") and is_on_floor() and can_move():
		velocity.y = JUMP_VELOCITY
		
	# Get movement input
	var direction = Vector2.ZERO
	direction.x = Input.get_axis("move_left", "move_right")
	direction.y = Input.get_axis("move_up", "move_down")
	direction = direction.normalized()
	
	# Don't allow movement while blocking
	if is_blocking:
		direction = Vector2.ZERO
	
	# Apply movement only if not blocked by equipment
	if can_move():
		if direction != Vector2.ZERO:
			var accel = ACCELERATION if is_on_floor() else AIR_ACCELERATION
			velocity.x = move_toward(velocity.x, direction.x * SPEED, accel * delta)
			velocity.y = move_toward(velocity.y, direction.y * SPEED, accel * delta)
			update_facing_direction(direction)
			
			# Update equipment animations for movement
			if equipped_items.has(EquipSlot.MAIN_HAND):
				equipped_items[EquipSlot.MAIN_HAND].update_animation(facing_direction)
			if equipped_items.has(EquipSlot.OFF_HAND):
				equipped_items[EquipSlot.OFF_HAND].update_animation(facing_direction)
		else:
			var friction = FRICTION if is_on_floor() else AIR_RESISTANCE
			velocity.x = move_toward(velocity.x, 0, friction * delta)
			velocity.y = move_toward(velocity.y, 0, friction * delta)
			
			# Update equipment animations for idle
			if equipped_items.has(EquipSlot.MAIN_HAND):
				equipped_items[EquipSlot.MAIN_HAND].update_animation(facing_direction)
			if equipped_items.has(EquipSlot.OFF_HAND):
				equipped_items[EquipSlot.OFF_HAND].update_animation(facing_direction)

func update_facing_direction(direction: Vector2) -> void:
	if abs(direction.x) > abs(direction.y):
		# Horizontal movement dominates
		facing_direction = LPCEnum.LPCAnimation.WALK_RIGHT if direction.x > 0 else LPCEnum.LPCAnimation.WALK_LEFT
	else:
		# Vertical movement dominates
		facing_direction = LPCEnum.LPCAnimation.WALK_DOWN if direction.y > 0 else LPCEnum.LPCAnimation.WALK_UP

func handle_animation() -> void:
	# Get base direction from facing_direction
	var current_direction = get_direction_from_anim(facing_direction)
	
	if is_attacking:
		# Use normal slash animations
		match current_direction:
			"UP": lpc_sprite.play(LPCEnum.LPCAnimation.SLASH_UP)
			"LEFT": lpc_sprite.play(LPCEnum.LPCAnimation.SLASH_LEFT)
			"DOWN": lpc_sprite.play(LPCEnum.LPCAnimation.SLASH_DOWN)
			"RIGHT": lpc_sprite.play(LPCEnum.LPCAnimation.SLASH_RIGHT)
	elif is_blocking:
		# Use thrust animations for blocking
		match current_direction:
			"UP": lpc_sprite.play(LPCEnum.LPCAnimation.THRUST_UP)
			"LEFT": lpc_sprite.play(LPCEnum.LPCAnimation.THRUST_LEFT)
			"DOWN": lpc_sprite.play(LPCEnum.LPCAnimation.THRUST_DOWN)
			"RIGHT": lpc_sprite.play(LPCEnum.LPCAnimation.THRUST_RIGHT)
	elif is_mining:
		# Use slash reverse animations for mining
		match current_direction:
			"UP": lpc_sprite.play(LPCEnum.LPCAnimation.SLASH_REVERSE_UP)
			"LEFT": lpc_sprite.play(LPCEnum.LPCAnimation.SLASH_REVERSE_LEFT)
			"DOWN": lpc_sprite.play(LPCEnum.LPCAnimation.SLASH_REVERSE_DOWN)
			"RIGHT": lpc_sprite.play(LPCEnum.LPCAnimation.SLASH_REVERSE_RIGHT)
	elif not is_on_floor():
		# Use thrust animations for jumping/falling
		match current_direction:
			"UP": lpc_sprite.play(LPCEnum.LPCAnimation.THRUST_UP)
			"LEFT": lpc_sprite.play(LPCEnum.LPCAnimation.THRUST_LEFT)
			"DOWN": lpc_sprite.play(LPCEnum.LPCAnimation.THRUST_DOWN)
			"RIGHT": lpc_sprite.play(LPCEnum.LPCAnimation.THRUST_RIGHT)
	elif velocity.length() > 10:
		# Use walk animations for movement
		match current_direction:
			"UP": lpc_sprite.play(LPCEnum.LPCAnimation.WALK_UP)
			"LEFT": lpc_sprite.play(LPCEnum.LPCAnimation.WALK_LEFT)
			"DOWN": lpc_sprite.play(LPCEnum.LPCAnimation.WALK_DOWN)
			"RIGHT": lpc_sprite.play(LPCEnum.LPCAnimation.WALK_RIGHT)
	else:
		# Use idle animations for standing still
		match current_direction:
			"UP": lpc_sprite.play(LPCEnum.LPCAnimation.IDLE_UP)
			"LEFT": lpc_sprite.play(LPCEnum.LPCAnimation.IDLE_LEFT)
			"DOWN": lpc_sprite.play(LPCEnum.LPCAnimation.IDLE_DOWN)
			"RIGHT": lpc_sprite.play(LPCEnum.LPCAnimation.IDLE_RIGHT)

func get_direction_from_anim(anim: LPCEnum.LPCAnimation) -> String:
	if anim in [LPCEnum.LPCAnimation.WALK_UP, LPCEnum.LPCAnimation.IDLE_UP,
				LPCEnum.LPCAnimation.SLASH_UP, LPCEnum.LPCAnimation.THRUST_UP]:
		return "UP"
	elif anim in [LPCEnum.LPCAnimation.WALK_LEFT, LPCEnum.LPCAnimation.IDLE_LEFT,
				 LPCEnum.LPCAnimation.SLASH_LEFT, LPCEnum.LPCAnimation.THRUST_LEFT]:
		return "LEFT"
	elif anim in [LPCEnum.LPCAnimation.WALK_DOWN, LPCEnum.LPCAnimation.IDLE_DOWN,
				 LPCEnum.LPCAnimation.SLASH_DOWN, LPCEnum.LPCAnimation.THRUST_DOWN]:
		return "DOWN"
	else:
		return "RIGHT"

func handle_equipment_direction() -> void:
	# Update equipment facing direction
	if equipment_mount:
		# Convert LPC direction to scale
		equipment_mount.scale.x = -1 if get_direction_from_anim(facing_direction) == "LEFT" else 1

func can_move() -> bool:
	# Check if any equipment is restricting movement
	var shield = equipped_items.get(EquipSlot.OFF_HAND)
	return not (shield and shield is Shield and shield.block_area.monitoring)

func handle_actions(delta: float) -> void:
	# Handle mining
	if Input.is_action_pressed("mine") and not check_blocking_state():
		handle_mining(delta)
	else:
		is_mining = false
		mining_timer = 0.0

	# Handle block placement
	if Input.is_action_just_pressed("place") and not check_blocking_state():
		handle_block_placement()

	# Handle equipment use
	handle_equipment()

	# Handle hotbar selection
	for i in range(HOTBAR_SIZE):
		if Input.is_action_just_pressed("hotbar_" + str(i + 1)):
			selected_slot = i

func check_blocking_state() -> bool:
	var shield = equipped_items.get(EquipSlot.OFF_HAND)
	return shield and shield is Shield and shield.block_area.monitoring

func handle_equipment() -> void:
	# Handle main hand equipment (usually weapons)
	var main_hand = equipped_items.get(EquipSlot.MAIN_HAND)
	if main_hand and Input.is_action_just_pressed("attack") and not check_blocking_state():
		is_attacking = true
		main_hand.use()
		# Wait for animation to finish
		await get_tree().create_timer(0.4).timeout
		is_attacking = false

	# Handle off hand equipment (usually shields)
	var off_hand = equipped_items.get(EquipSlot.OFF_HAND)
	if off_hand:
		if Input.is_action_just_pressed("block"):
			is_blocking = true
			off_hand.use()
		elif Input.is_action_just_released("block"):
			is_blocking = false
			off_hand.stop_use()

func handle_mining(delta: float) -> void:
	# Get mouse position relative to player
	var mouse_pos = get_local_mouse_position()
	mining_ray.target_position = mouse_pos.normalized() * MINING_RANGE
	
	if mining_ray.is_colliding():
		var collision_point = mining_ray.get_collision_point()
		var tile_pos = world.tile_map.local_to_map(collision_point)
		
		# Update facing direction based on mining target
		var direction_to_target = (collision_point - global_position).normalized()
		update_facing_direction(direction_to_target)
		
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
	
	# Update facing direction based on placement target
	var direction_to_target = (mouse_pos - global_position).normalized()
	update_facing_direction(direction_to_target)
	
	# Check if selected hotbar slot has blocks
	var selected_item = hotbar[selected_slot]
	if selected_item and selected_item.begins_with("BLOCK_"):
		if remove_from_inventory(selected_item, 1):
			world.modify_block(tile_pos, selected_item.trim_prefix("BLOCK_"))

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
	# Animation is handled in handle_animation()
	pass

func _on_shield_use() -> void:
	# Animation is handled in handle_animation()
	pass

func _on_shield_stop_use() -> void:
	# Animation is handled in handle_animation()
	pass

func get_block_type(pos: Vector2i) -> String:
	# Get block type from world
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
