class_name Shield
extends Equipment

var block_angle := 120.0  # Degrees
var block_range := 24.0  # Pixels

@onready var block_area: Area2D = $BlockArea

func _ready() -> void:
	super._ready()
	setup_block_area()

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

func use() -> void:
	if can_use():
		block_area.monitoring = true
		emit_signal("on_use")

func stop_use() -> void:
	block_area.monitoring = false
	start_cooldown()
	emit_signal("on_stop_use")

func _on_block_area_area_entered(area: Area2D) -> void:
	if area.is_in_group("projectiles"):
		area.queue_free()  # Destroy blocked projectiles
