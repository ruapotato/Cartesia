class_name Equipment
extends Node2D

signal on_use
signal on_stop_use

var equipped := false
var cooldown := 0.0
var base_cooldown := 0.3

func _ready() -> void:
	set_physics_process(false)

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
