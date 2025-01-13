class_name Shield
extends Equipment

var block_angle := 120.0  # Degrees
var block_range := 24.0  # Pixels

@onready var block_area: Area2D = $BlockArea

func _ready() -> void:
	super._ready()
	setup_block_area()
	if lpc_sprite:
		var sprite_sheet = LPCSpriteSheet.new()
		sprite_sheet.SpriteType = LPCEnum.SpriteType.Normal
		sprite_sheet.Name = "shield"
		lpc_sprite.SpriteSheets.append(sprite_sheet)
		lpc_sprite.DefaultAnimation = LPCEnum.LPCAnimation.IDLE_DOWN

func setup_block_area() -> void:
	# Create block area if it doesn't exist
	if not block_area:
		block_area = Area2D.new()
		var collision = CollisionShape2D.new()
		var shape = CircleShape2D.new()
		shape.radius = block_range
		collision.shape = shape
		block_area.add_child(collision)
		add_child(block_area)
	
	block_area.collision_layer = 0
	block_area.collision_mask = 4  # Projectile layer
	block_area.monitoring = false
	block_area.position = Vector2(block_range/2, 0)

func use() -> void:
	if can_use():
		block_area.monitoring = true
		
		# Update animation based on parent's facing
		var parent_sprite = get_parent().get_node_or_null("LPCAnimatedSprite2D")
		if parent_sprite and lpc_sprite:
			match parent_sprite.current_animation:
				LPCEnum.LPCAnimation.WALK_UP, LPCEnum.LPCAnimation.IDLE_UP:
					lpc_sprite.play(LPCEnum.LPCAnimation.THRUST_UP)
				LPCEnum.LPCAnimation.WALK_LEFT, LPCEnum.LPCAnimation.IDLE_LEFT:
					lpc_sprite.play(LPCEnum.LPCAnimation.THRUST_LEFT)
				LPCEnum.LPCAnimation.WALK_DOWN, LPCEnum.LPCAnimation.IDLE_DOWN:
					lpc_sprite.play(LPCEnum.LPCAnimation.THRUST_DOWN)
				_:
					lpc_sprite.play(LPCEnum.LPCAnimation.THRUST_RIGHT)
		
		emit_signal("on_use")

func stop_use() -> void:
	block_area.monitoring = false
	start_cooldown()
	
	# Return to idle animation
	var parent_sprite = get_parent().get_node_or_null("LPCAnimatedSprite2D")
	if parent_sprite:
		update_animation(parent_sprite.current_animation)
	
	emit_signal("on_stop_use")

func _on_block_area_area_entered(area: Area2D) -> void:
	if area.is_in_group("projectiles"):
		area.queue_free()  # Destroy blocked projectiles
