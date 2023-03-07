#AGPL by David Hamner 2023
#Flat obj like, imported into gui.py for native functions calls. 
def init_player(offset):
    player_data = {}
    #player offset from would pos
    player_data["offset"] = offset
    player_data["pos"] = player_data["offset"]
    player_data["speed"] = [0,0]
    player_data["live"] = 100
    player_data["wanted_speed"] = [0,0]
    player_data["display_size"] = [64,64]
    player_data["hitbox_size"] = [32,64]
    
    player_data["active_item"] = None
    player_data["spell_strength"] = 5
    player_data["magic"] = 90
    player_data["magic_regen"] = .2
    player_data["max_magic"] = 100
    player_data["magic_cast_speed"] = 25
    player_data["magic_part_casted"] = 0
    
    
    player_data["body_strength"] = 5
    player_data["strength"] = 90
    player_data["strength_regen"] = .5
    player_data["max_strength"] = 100
    player_data["bow_draw_speed"] = 25
    player_data["bow_draw"] = 0
    
    
    player_data["inventory"] = {'1': ["mine", process_mine_cast],
                                '2': ["bow", process_bow_shooting]}
    
    player_data["selected_item"] = player_data["inventory"]['1'][1]
    player_images = {"body": "/body/male/light",
                     "ears": "/body/male/ears/bigears_light",
                     "eyes": "/body/male/eyes/brown",
                     "nose": "/body/male/nose/buttonnose_light",
                     "hair": "/hair/male/messy1",
                     "shirt": "/torso/leather/chest_male",
                     "shoulders": "/torso/leather/shoulders_male",
                     "pants": "/legs/skirt/male/robe_skirt_male",
                     "wand": "/weapons/right hand/male/woodwand_male"}
    
    
    #player_images = {"body": "/body/male/light"}
    
    player_data["images"] = player_images
    player_data["image_base_path"] = "/player/Universal-LPC-spritesheet"
    player_data["image_states"] = {"left":9, "right": 11, "cast_left": 1, "cast_right": 3, "draw_left": 17, "draw_right": 19}
    player_data["image_state"] = "left"
    player_data["image_frame_offset"] = 0
    player_data["player_is_walking"] = False
    player_data["walk_speed"] = 6
    player_data["jump_speed"] = 15
    player_data["is_jumping"] = False
    player_data["is_climbing"] = False
    player_data["can_jump"] = True
    player_data["surface"] = pygame.Surface(player_data["display_size"])
    player_data["surface"].fill((255,0,255))
    player_data["surface"].set_colorkey((255,0,255))
    
    return(player_data)

def update_player(player_data):
    #Foreign function from gui.py
    global world_xy
    global gravity
    global DEBUG
    global dot
    
    #print(f"info: {player_data['is_climbing']}")
    x_speed_change = 0
    y_speed_change = 0
    
    
    #Adjust player speed to wanted_speed slowly
    if not player_data["can_jump"]:
        player_data["wanted_speed"][1] = 0
    if player_data["wanted_speed"][0] != player_data["speed"][0]:
        diff = player_data["speed"][0] + player_data["wanted_speed"][0] 
        x_speed_change = diff/2
    if player_data["wanted_speed"][1] != player_data["speed"][1]:
        if player_data["wanted_speed"][1] == 0:
            y_speed_change = player_data["speed"][1]
        else:
            diff = player_data["speed"][1] + player_data["wanted_speed"][1] 
            y_speed_change = diff/2
    player_data["speed"] = [x_speed_change, y_speed_change]
    #print(player_data["speed"])
    
    
    pos = copy.deepcopy(player_data["offset"])
    hitbox_size = player_data["hitbox_size"]
    current_speed = player_data["speed"]
    is_climbing = player_data["is_climbing"]
    can_jump = player_data["can_jump"]
    is_jumping = player_data["is_jumping"]
    
    #Block hit checking
    pos_change, newSpeed, is_climbing, can_jump, is_jumping, fall_damage = environmentSpeedChange(pos,
                                                                                             hitbox_size,
                                                                                             current_speed,
                                                                                             is_climbing,
                                                                                             can_jump,
                                                                                             is_jumping)
    if pos_change != player_data["offset"]:
        world_xy[1] += player_data["offset"][1] - pos_change[1]
        world_xy[0] += player_data["offset"][0] - pos_change[0]
    
    player_data["speed"] = newSpeed
    player_data["is_climbing"] = is_climbing
    player_data["can_jump"] = can_jump
    player_data["is_jumping"] = is_jumping
                    
    
    #add speed to player (In this case edit the world_xy)
    if player_data["speed"] != [0,0]:
        world_xy[0] += int(player_data["speed"][0])
        world_xy[1] += int(player_data["speed"][1])

    #Update magic
    if player_data["magic"] < player_data["max_magic"]:
        player_data["magic"] += player_data["magic_regen"]
    
    #Update strength
    if player_data["strength"] < player_data["max_strength"]:
        player_data["strength"] += player_data["strength_regen"]
    
    # Update ative active_item
    mouse_presses = pygame.mouse.get_pressed()
    end_spell = False
    
    if mouse_presses[0]:
        player_data["selected_item"](player_data, list(pygame.mouse.get_pos()))
    #elif player_data["magic_part_casted"] != 0:
    else:
        player_data["selected_item"](player_data, list(pygame.mouse.get_pos()), end=True)
   
    if player_data["player_is_walking"]:
        player_data["image_frame_offset"] += 1
        player_data["image_frame_offset"] %= 9
