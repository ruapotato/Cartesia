extends MeleeWeapon

func _ready() -> void:
	super._ready()
	damage = 5
	attack_range = 32.0
	base_cooldown = 0.25
