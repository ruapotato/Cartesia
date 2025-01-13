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
		LPCEnum.LPCAnimation.WALK_UP, LPCEnum.LPCAnimation.IDLE_UP, LPCEnum.LPCAnimation.SLASH_UP, LPCEnum.LPCAnimation.THRUST_UP:
			return "UP"
		LPCEnum.LPCAnimation.WALK_LEFT, LPCEnum.LPCAnimation.IDLE_LEFT, LPCEnum.LPCAnimation.SLASH_LEFT, LPCEnum.LPCAnimation.THRUST_LEFT:
			return "LEFT"
		LPCEnum.LPCAnimation.WALK_DOWN, LPCEnum.LPCAnimation.IDLE_DOWN, LPCEnum.LPCAnimation.SLASH_DOWN, LPCEnum.LPCAnimation.THRUST_DOWN:
			return "DOWN"
		_:
			return "RIGHT"

func update_animation(parent_animation: LPCEnum.LPCAnimation) -> void:
	if not lpc_sprite:
		return
		
	var base_direction = get_base_direction(parent_animation)
	match base_direction:
		"UP":
			lpc_sprite.play(LPCEnum.LPCAnimation.IDLE_UP)
		"LEFT":
			lpc_sprite.play(LPCEnum.LPCAnimation.IDLE_LEFT) 
		"DOWN":
			lpc_sprite.play(LPCEnum.LPCAnimation.IDLE_DOWN)
		"RIGHT":
			lpc_sprite.play(LPCEnum.LPCAnimation.IDLE_RIGHT)
