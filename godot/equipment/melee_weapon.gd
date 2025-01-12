class_name MeleeWeapon
extends Equipment

var damage := 10
var attack_angle := 90.0  # Degrees
var attack_range := 32.0  # Pixels

@onready var hitbox: Area2D = $Hitbox

func _ready() -> void:
	super._ready()
	setup_hitbox()

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
		emit_signal("on_use")
		
		# Disable hitbox after a short duration
		await get_tree().create_timer(0.15).timeout
		hitbox.monitoring = false

func _on_hitbox_body_entered(body: Node2D) -> void:
	if body.has_method("take_damage"):
		body.take_damage(damage)
