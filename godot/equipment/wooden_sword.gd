extends MeleeWeapon

func _ready() -> void:
	print("Sword _ready() called")
	super._ready()
	damage = 5
	attack_range = 32.0
	base_cooldown = 0.25
	
	# Setup sword spritesheet
	if lpc_sprite:
		print("Setting up sword sprite")
		var sprite_sheet = LPCSpriteSheet.new()
		sprite_sheet.SpriteSheet = preload("res://img/player/Universal-LPC-spritesheet/weapons/right hand/male/dagger_male.png")
		sprite_sheet.SpriteType = LPCEnum.SpriteType.Normal
		sprite_sheet.Name = "sword"
		
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
		print("No lpc_sprite in sword")
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
	
	if player.is_attacking:
		animation_name = "SLASH_" + base_direction
		animated_sprite.speed_scale = 2.0  # Attack animation speed
	else:
		# Use walking animations for movement, idle for standing still
		if abs(player.velocity.x) > 1 or abs(player.velocity.y) > 1:
			animation_name = "WALK_" + base_direction
			animated_sprite.speed_scale = 1.0  # Normal walking speed
		else:
			animation_name = "IDLE_" + base_direction
			animated_sprite.speed_scale = 1.0  # Normal idle speed
	
	print("Sword animation: ", animation_name)  # Debug print
	
	if animation_name in LPCEnum.LPCAnimation:
		lpc_sprite.play(LPCEnum.LPCAnimation[animation_name])
