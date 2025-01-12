extends Node2D

# Atlas coordinates for different block types
const BLOCK_COORDS = {
	"AIR": Vector2i(-1, -1),  # Special case for air/empty
	"GRASS": Vector2i(0, 0),
	"DIRT": Vector2i(1, 0),
	"STONE": Vector2i(2, 0),
	"BEDROCK": Vector2i(3, 0),
	# Add more block types as needed
}

# World generation parameters
const CHUNK_SIZE = 16
const WORLD_HEIGHT = 128
const SURFACE_HEIGHT = 64  # Base surface height
const SURFACE_VARIATION = 12  # How much the surface can vary up/down
const DIRT_DEPTH = 5  # How many blocks of dirt below the surface
const NOISE_SCALE = 50.0  # Scale factor for noise
const CAVE_NOISE_SCALE = 25.0
const CAVE_THRESHOLD = 0.7  # Higher = fewer caves

@onready var tile_map = TileMapLayer.new()
@onready var player = $player
@onready var noise = FastNoiseLite.new()
@onready var cave_noise = FastNoiseLite.new()
var camera
var loaded_chunks = {}
var modified_blocks = {}  # Store player modifications: {Vector2i: block_type}

func _ready() -> void:
	# Setup noise generators
	noise.seed = randi()
	noise.frequency = 1.0/NOISE_SCALE
	noise.fractal_octaves = 4
	
	cave_noise.seed = randi()
	cave_noise.frequency = 1.0/CAVE_NOISE_SCALE
	cave_noise.fractal_octaves = 2
	
	camera = player.find_child("Camera2D")
	setup_tilemap()
	load_modifications()  # Load any saved modifications
	
	# Force initial chunk generation
	var player_chunk = int(tile_map.local_to_map(player.global_position).x) / CHUNK_SIZE
	for i in range(player_chunk - 2, player_chunk + 3):
		generate_chunk(i)

func setup_tilemap() -> void:
	add_child(tile_map)
	
	var new_tileset = TileSet.new()
	new_tileset.tile_size = Vector2i(16, 16)
	
	new_tileset.add_physics_layer()
	
	var atlas_texture = load("res://img/atlas.png")
	if atlas_texture:
		var atlas_source = TileSetAtlasSource.new()
		atlas_source.texture = atlas_texture
		atlas_source.texture_region_size = Vector2i(16, 16)
		
		new_tileset.add_source(atlas_source, 0)
		
		var atlas_width = atlas_texture.get_width() / 16
		var atlas_height = atlas_texture.get_height() / 16
		
		for x in range(atlas_width):
			for y in range(atlas_height):
				var coords = Vector2i(x, y)
				atlas_source.create_tile(coords)
				
				var tile_data = atlas_source.get_tile_data(coords, 0)
				if tile_data:
					tile_data.add_collision_polygon(0)
					var polygon = PackedVector2Array([
						Vector2(0, 0),
						Vector2(16, 0),
						Vector2(16, 16),
						Vector2(0, 16)
					])
					tile_data.set_collision_polygon_points(0, 0, polygon)

	new_tileset.set_physics_layer_collision_layer(0, 1)
	new_tileset.set_physics_layer_collision_mask(0, 1)
	
	tile_map.tile_set = new_tileset
	tile_map.collision_enabled = true

func _process(delta: float) -> void:
	var cam_pos = tile_map.local_to_map(camera.global_position)
	
	var start_chunk = int(cam_pos.x - (CHUNK_SIZE * 2)) / CHUNK_SIZE
	var end_chunk = int(cam_pos.x + (CHUNK_SIZE * 2)) / CHUNK_SIZE
	
	# Load new chunks
	for chunk in range(start_chunk, end_chunk + 1):
		if not loaded_chunks.has(chunk):
			generate_chunk(chunk)
	
	# Unload far chunks
	var chunks_to_unload = []
	for chunk in loaded_chunks:
		if chunk < start_chunk - 1 or chunk > end_chunk + 1:
			chunks_to_unload.append(chunk)
	
	for chunk in chunks_to_unload:
		unload_chunk(chunk)

func generate_chunk(chunk_index: int) -> void:
	loaded_chunks[chunk_index] = true
	var start_x = chunk_index * CHUNK_SIZE
	
	for x in range(start_x, start_x + CHUNK_SIZE):
		# Generate surface height using noise
		var surface_y = SURFACE_HEIGHT + int(noise.get_noise_1d(x) * SURFACE_VARIATION)
		
		for y in range(0, WORLD_HEIGHT):
			var pos = Vector2i(x, y)
			
			# Check for player modifications first
			if modified_blocks.has(pos):
				set_block(pos, modified_blocks[pos])
				continue
			
			# Generate natural terrain
			var block_type = get_natural_block_type(x, y, surface_y)
			set_block(pos, block_type)

func get_natural_block_type(x: int, y: int, surface_y: int) -> String:
	# Check for caves
	var cave_value = cave_noise.get_noise_2d(x, y)
	if y > surface_y + 5 and cave_value > CAVE_THRESHOLD:
		return "AIR"
	
	# Layer distribution
	if y < surface_y:
		return "AIR"
	elif y == surface_y:
		return "GRASS"
	elif y < surface_y + DIRT_DEPTH:
		return "DIRT"
	elif y >= WORLD_HEIGHT - 1:
		return "BEDROCK"
	else:
		return "STONE"

func set_block(pos: Vector2i, block_type: String) -> void:
	if block_type == "AIR":
		tile_map.erase_cell(pos)
	else:
		tile_map.set_cell(pos, 0, BLOCK_COORDS[block_type])

func unload_chunk(chunk_index: int) -> void:
	loaded_chunks.erase(chunk_index)
	var start_x = chunk_index * CHUNK_SIZE
	
	# Only erase cells, modifications are kept in modified_blocks
	for x in range(start_x, start_x + CHUNK_SIZE):
		for y in range(0, WORLD_HEIGHT):
			tile_map.erase_cell(Vector2i(x, y))

func modify_block(pos: Vector2i, block_type: String) -> void:
	modified_blocks[pos] = block_type
	set_block(pos, block_type)
	save_modifications()  # Save after each modification

func save_modifications() -> void:
	var save_data = {}
	for pos in modified_blocks:
		# Convert Vector2i to string for JSON compatibility
		save_data["%d,%d" % [pos.x, pos.y]] = modified_blocks[pos]
	
	var save_file = FileAccess.open("user://world_modifications.save", FileAccess.WRITE)
	save_file.store_string(JSON.stringify(save_data))

func load_modifications() -> void:
	if not FileAccess.file_exists("user://world_modifications.save"):
		return
	
	var save_file = FileAccess.open("user://world_modifications.save", FileAccess.READ)
	var json_string = save_file.get_as_text()
	var save_data = JSON.parse_string(json_string)
	
	modified_blocks.clear()
	for pos_str in save_data:
		var pos_arr = pos_str.split(",")
		var pos = Vector2i(int(pos_arr[0]), int(pos_arr[1]))
		modified_blocks[pos] = save_data[pos_str]
