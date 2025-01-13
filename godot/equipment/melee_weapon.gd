class_name MeleeWeapon
extends Equipment

var damage := 10
var attack_angle := 90.0  # Degrees
var attack_range := 32.0  # Pixels

@onready var hitbox: Area2D = $Hitbox

func _ready() -> void:
	super._ready()
	setup_hitbox()
	if lpc_sprite:
		var sprite_sheet = LPCSpriteSheet.new()
		sprite_sheet.SpriteType = LPCEnum.SpriteType.Normal
		sprite_sheet.Name = "sword"
		lpc_sprite.SpriteSheets.append(sprite_sheet)
		lpc_sprite.DefaultAnimation = LPCEnum.LPCAnimation.IDLE_DOWN

func setup_hitbox() -> void:
	# Create hitbox if it doesn't exist
	if not hitbox:
		hitbox = Area2D.new()
		var collision = CollisionShape2D.new()
		var shape = CircleShape2D.new()
		shape.radius = attack_range
		collision.shape = shape
		hitbox.add_child(collision)
		add_child(hitbox)
		
	hitbox.collision_layer = 0
	hitbox.collision_mask = 2  # Enemy layer
	hitbox.monitoring = false

func use() -> void:
	if can_use():
		hitbox.monitoring = true
		start_cooldown()
		
		# Get parent's facing direction
		var parent = get_parent()
		var player = parent.get_parent() if parent else null
		if player:
			update_animation(player.facing_direction)
		
		emit_signal("on_use")
		
		# Set up attack completion
		var timer = get_tree().create_timer(0.4)
		timer.timeout.connect(_on_attack_complete)

func _on_attack_complete() -> void:
	hitbox.monitoring = false
	
	# Get parent's facing direction and update our animation
	var parent = get_parent()
	var player = parent.get_parent() if parent else null
	if player:
		update_animation(player.facing_direction)

func _on_hitbox_body_entered(body: Node2D) -> void:
	if body.has_method("take_damage"):
		body.take_damage(damage)
