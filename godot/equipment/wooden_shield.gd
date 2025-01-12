extends Shield

func _ready() -> void:
	super._ready()
	block_angle = 90.0
	block_range = 24.0
	base_cooldown = 0.2
	
	# Optional: Add shield sprite and position/rotate hitbox
	var shield_sprite = Sprite2D.new()
	shield_sprite.texture = preload("res://img/player/Universal-LPC-spritesheet/weapons/left hand/male/shield_male_cutoutforbody.png")  # Your shield texture
	add_child(shield_sprite)
	
	# Position the block area relative to the shield sprite
	if block_area:
		block_area.position = Vector2(block_range/2, 0)
