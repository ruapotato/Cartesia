class_name Equipment
extends Node2D

signal on_use
signal on_stop_use

@onready var lpc_sprite = $LPCAnimatedSprite2D

var equipped := false
var cooldown := 0.0
var base_cooldown := 0.3

func _ready() -> void:
	set_physics_process(false)
	setup_lpc_sprite()

func setup_lpc_sprite() -> void:
	if not lpc_sprite:
		lpc_sprite = LPCAnimatedSprite2D.new()
		add_child(lpc_sprite)

func equip() -> void:
	equipped = true
	set_physics_process(true)
	show()

func unequip() -> void:
	equipped = false
	set_physics_process(false)
	hide()

func can_use() -> bool:
	return equipped and cooldown <= 0

func start_cooldown() -> void:
	cooldown = base_cooldown

func _physics_process(delta: float) -> void:
	if cooldown > 0:
		cooldown -= delta

func get_base_direction(parent_animation: LPCEnum.LPCAnimation) -> String:
	match parent_animation:
		LPCEnum.LPCAnimation.WALK_UP, LPCEnum.LPCAnimation.IDLE_UP, LPCEnum.LPCAnimation.SLASH_UP, LPCEnum.LPCAnimation.THRUST_UP, LPCEnum.LPCAnimation.SLASH_REVERSE_UP:
			return "UP"
		LPCEnum.LPCAnimation.WALK_LEFT, LPCEnum.LPCAnimation.IDLE_LEFT, LPCEnum.LPCAnimation.SLASH_LEFT, LPCEnum.LPCAnimation.THRUST_LEFT, LPCEnum.LPCAnimation.SLASH_REVERSE_LEFT:
			return "LEFT"
		LPCEnum.LPCAnimation.WALK_DOWN, LPCEnum.LPCAnimation.IDLE_DOWN, LPCEnum.LPCAnimation.SLASH_DOWN, LPCEnum.LPCAnimation.THRUST_DOWN, LPCEnum.LPCAnimation.SLASH_REVERSE_DOWN:
			return "DOWN"
		LPCEnum.LPCAnimation.WALK_RIGHT, LPCEnum.LPCAnimation.IDLE_RIGHT, LPCEnum.LPCAnimation.SLASH_RIGHT, LPCEnum.LPCAnimation.THRUST_RIGHT, LPCEnum.LPCAnimation.SLASH_REVERSE_RIGHT:
			return "RIGHT"
		_:
			print("Warning: Unknown animation state: ", parent_animation)
			return "DOWN"  # Default to DOWN instead of RIGHT

func update_animation(parent_animation: LPCEnum.LPCAnimation) -> void:
	if not lpc_sprite:
		print("No lpc_sprite in equipment")
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
	
	# Set base movement animation
	if abs(player.velocity.x) > 1 or abs(player.velocity.y) > 1:
		animation_name = "WALK_" + base_direction
		animated_sprite.speed_scale = 1.0  # Normal walking speed
	else:
		animation_name = "IDLE_" + base_direction
		animated_sprite.speed_scale = 1.0  # Normal idle speed
	
	print("Equipment base animation: ", animation_name)  # Debug print
	
	if animation_name in LPCEnum.LPCAnimation:
		lpc_sprite.play(LPCEnum.LPCAnimation[animation_name])
