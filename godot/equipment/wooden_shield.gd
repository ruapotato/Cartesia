extends Shield

func _ready() -> void:
	print("Shield _ready() called")
	super._ready()
	block_angle = 90.0
	block_range = 24.0
	base_cooldown = 0.2
	
	# Setup shield spritesheet
	if lpc_sprite:
		print("Setting up shield sprite")
		var sprite_sheet = LPCSpriteSheet.new()
		sprite_sheet.SpriteSheet = preload("res://img/player/Universal-LPC-spritesheet/weapons/left hand/male/shield_male_cutoutforbody.png")
		sprite_sheet.SpriteType = LPCEnum.SpriteType.Normal
		sprite_sheet.Name = "shield"
		
		# Setup sprite sheets
		lpc_sprite.SpriteSheets.clear()
		lpc_sprite.SpriteSheets.push_back(sprite_sheet)
		
		# Force reload of animations
		lpc_sprite._instantiate()
		
		# Get the animated sprite node
		for child in lpc_sprite.get_children():
			if child is AnimatedSprite2D:
				# Set default speed - walking animation speed
				child.speed_scale = 1.0
				child.animation_finished.connect(_on_animation_finished)
				break

func _on_animation_finished() -> void:
	var player = get_parent().get_parent()
	if player:
		update_animation(player.facing_direction)

func update_animation(parent_animation: LPCEnum.LPCAnimation) -> void:
	if not lpc_sprite:
		print("No lpc_sprite in shield")
		return
	
	# Get the animated sprite node
	var animated_sprite: AnimatedSprite2D = null
	for child in lpc_sprite.get_children():
		if child is AnimatedSprite2D:
			animated_sprite = child
			break
			
	if not animated_sprite:
		return
		
	var base_direction = get_base_direction(parent_animation)
	var animation_name = ""
	
	# Get parent node (should be the player)
	var player = get_parent().get_parent()
	if not player:
		return
	
	if player.is_blocking:
		animation_name = "THRUST_" + base_direction
		animated_sprite.speed_scale = 2.0  # Blocking animation speed
	else:
		# Use walking animations for movement, idle for standing still
		if abs(player.velocity.x) > 1 or abs(player.velocity.y) > 1:
			animation_name = "WALK_" + base_direction
			animated_sprite.speed_scale = 1.0  # Normal walking speed
		else:
			animation_name = "IDLE_" + base_direction
			animated_sprite.speed_scale = 1.0  # Normal idle speed
	
	print("Shield animation: ", animation_name)  # Debug print
	
	if animation_name in LPCEnum.LPCAnimation:
		lpc_sprite.play(LPCEnum.LPCAnimation[animation_name])
