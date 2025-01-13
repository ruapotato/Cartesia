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
		
		# Get the animated sprite node and setup default state
		for child in lpc_sprite.get_children():
			if child is AnimatedSprite2D:
				print("Found AnimatedSprite2D node: ", child.name)
				print("Setting up animation speed")
				child.speed_scale = 2.0
				# Connect animation finished signal
				child.animation_finished.connect(_on_animation_finished)
				break

func _on_animation_finished() -> void:
	var player = get_parent().get_parent()
	if player:
		# Use player's facing_direction instead of current_animation
		update_animation(player.facing_direction)

func update_animation(parent_animation: LPCEnum.LPCAnimation) -> void:
	print("Sword update_animation called with: ", LPCEnum.LPCAnimation.keys()[parent_animation])
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
		
	var animation_name = ""
	# Get parent node (should be the player)
	var player = get_parent().get_parent()
	
	# Determine base direction from parent animation
	var base_direction = ""
	match parent_animation:
		LPCEnum.LPCAnimation.WALK_UP, LPCEnum.LPCAnimation.IDLE_UP:
			base_direction = "UP"
		LPCEnum.LPCAnimation.WALK_LEFT, LPCEnum.LPCAnimation.IDLE_LEFT:
			base_direction = "LEFT"
		LPCEnum.LPCAnimation.WALK_DOWN, LPCEnum.LPCAnimation.IDLE_DOWN:
			base_direction = "DOWN"
		_:
			base_direction = "RIGHT"
	
	if player and player.is_attacking:
		animation_name = "SLASH_" + base_direction
		animated_sprite.speed_scale = 4.0  # Faster for attacks
		print("Playing attack animation: ", animation_name)
	else:
		# Use walking animations for movement, idle for standing still
		if abs(player.velocity.x) > 1 or abs(player.velocity.y) > 1:  # More precise movement check
			animation_name = "WALK_" + base_direction
			animated_sprite.speed_scale = 2.0
			print("Playing walk animation: ", animation_name)
		else:
			animation_name = "IDLE_" + base_direction
			animated_sprite.speed_scale = 2.0
			print("Playing idle animation: ", animation_name)
	
	if animation_name in LPCEnum.LPCAnimation:
		lpc_sprite.play(LPCEnum.LPCAnimation[animation_name])
	
	# Debug the actual sprite state after play
	print("After play - Animation: ", animation_name)
	print("After play - Is playing: ", animated_sprite.is_playing())
	print("After play - Speed scale: ", animated_sprite.speed_scale)
	print("After play - Base direction: ", base_direction)
