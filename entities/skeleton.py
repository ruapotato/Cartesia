#AGPL by David Hamner 2023
#Flat obj like, imported into gui.py for native functions calls. 

def update_skeleton(skeleton_data):
    #Foreign function from gui.py
    global world_xy
    global gravity
    global DEBUG
    global dot
    
    #print(f"info: {skeleton_data['is_climbing']}")
    x_speed_change = 0
    y_speed_change = 0
    
    
    #Adjust skeleton speed to wanted_speed slowly
    if not skeleton_data["can_jump"]:
        skeleton_data["wanted_speed"][1] = 0
    if skeleton_data["wanted_speed"][0] != skeleton_data["speed"][0]:
        diff = skeleton_data["speed"][0] + skeleton_data["wanted_speed"][0] 
        x_speed_change = diff/2
    if skeleton_data["wanted_speed"][1] != skeleton_data["speed"][1]:
        if skeleton_data["wanted_speed"][1] == 0:
            y_speed_change = skeleton_data["speed"][1]
        else:
            diff = skeleton_data["speed"][1] + skeleton_data["wanted_speed"][1] 
            y_speed_change = diff/2
    skeleton_data["speed"] = [x_speed_change, y_speed_change]
    #print(skeleton_data["speed"])
    
    #Update world pos
    world_change_in_x = world_xy[0] - skeleton_data["last_world_pos"][0]
    world_change_in_y = world_xy[1] - skeleton_data["last_world_pos"][1]
    skeleton_data["pos"][0] -= world_change_in_x
    skeleton_data["pos"][1] += world_change_in_y
    skeleton_data["last_world_pos"] = copy.deepcopy(world_xy)

    
    pos = copy.deepcopy(skeleton_data["pos"])
    hitbox_size = skeleton_data["hitbox_size"]
    current_speed = skeleton_data["speed"]
    is_climbing = skeleton_data["is_climbing"]
    can_jump = skeleton_data["can_jump"]
    is_jumping = skeleton_data["is_jumping"]
    
    #Block hit checking
    
    pos_change, newSpeed, is_climbing, can_jump, is_jumping, fall_damage = environmentSpeedChange(pos,
                                                                                             hitbox_size,
                                                                                             current_speed,
                                                                                             is_climbing,
                                                                                             can_jump,
                                                                                             is_jumping)
    skeleton_data["pos"][1] += skeleton_data["pos"][1] - pos_change[1]
    skeleton_data["pos"][0] += skeleton_data["pos"][0] - pos_change[0]                                                                            
    #skeleton_data["pos"][1] -= pos_change[1]
    #skeleton_data["pos"][0] -= pos_change[0]
    
    skeleton_data["speed"] = newSpeed
    skeleton_data["is_climbing"] = is_climbing
    skeleton_data["can_jump"] = can_jump
    skeleton_data["is_jumping"] = is_jumping
                    
    
    #add speed to skeleton (In this case edit the world_xy)
    if skeleton_data["speed"] != [0,0]:
        skeleton_data["pos"][0] += int(skeleton_data["speed"][0])
        skeleton_data["pos"][1] -= int(skeleton_data["speed"][1])

    #Update magic
    if skeleton_data["magic"] < skeleton_data["max_magic"]:
        skeleton_data["magic"] += skeleton_data["magic_regen"]
    
    # Update ative active_item
    mouse_presses = pygame.mouse.get_pressed()
    end_spell = False
    spell_casted = skeleton_data["magic_part_casted"] >= skeleton_data["magic_cast_speed"]
    if mouse_presses[0]:
        if spell_casted:
            #Load new spell
            if skeleton_data["active_spell"] == None:
                skeleton_data["active_spell"] = skeleton_data["selected_spell"](list(pygame.mouse.get_pos()),
                                                                            skeleton_data["spell_strength"])
            if skeleton_data["active_spell"]["cost"] < skeleton_data["magic"]:
                skeleton_data["magic"] -= skeleton_data["active_spell"]["cost"]
            
                #Update spell
                skeleton_data["active_spell"]["update"](skeleton_data["active_spell"])
            else:
                end_spell = True
        if not spell_casted:
            if skeleton_data["magic_part_casted"] == 0:
                pygame.mixer.Sound.play(sounds["magic_spell"])
            skeleton_data["magic_part_casted"] += 1
    else:
        end_spell = True
    if end_spell:
        skeleton_data["magic_part_casted"] = 0
        if skeleton_data["active_spell"] != None:
            del skeleton_data["active_spell"]
            skeleton_data["active_spell"] = None
        
    #Update frame
    if skeleton_data["magic_part_casted"] != 0:
        if "cast" not in skeleton_data["image_state"]:
            skeleton_data["image_state"] = f"cast_{skeleton_data['image_state']}"
        if skeleton_data["magic_part_casted"] < skeleton_data["magic_cast_speed"]:
            skeleton_data["image_frame_offset"] = int((7/skeleton_data["magic_cast_speed"]) * skeleton_data["magic_part_casted"])
            #skeleton_data["image_frame_offset"] %= 7
    else:
        if "cast" in skeleton_data["image_state"]:
            skeleton_data["image_state"] = skeleton_data["image_state"].split("_")[-1]
    
    if skeleton_data["skeleton_is_walking"]:
        skeleton_data["image_frame_offset"] += 1
        skeleton_data["image_frame_offset"] %= 9
def init_skeleton(pos):
    global world_xy
    skeleton_data = {}
    #skeleton pos from would pos
    skeleton_data["pos"] = pos
    skeleton_data["speed"] = [0,0]
    skeleton_data["wanted_speed"] = [0,0]
    skeleton_data["display_size"] = [64,64]
    skeleton_data["hitbox_size"] = [32,64]
    skeleton_data["selected_spell"] = init_mine_spell
    skeleton_data["active_spell"] = None
    skeleton_data["spell_strength"] = 5
    skeleton_data["magic"] = 90
    skeleton_data["magic_regen"] = .2
    skeleton_data["max_magic"] = 100
    skeleton_data["magic_cast_speed"] = 25
    skeleton_data["magic_part_casted"] = 0
    
    skeleton_images = {"body": "/body/male/skeleton",
                       "bow": "/weapons/right hand/either/bow_skeleton"}
    
    
    #skeleton_images = {"body": "/body/male/light"}
    
    skeleton_data["images"] = skeleton_images
    skeleton_data["image_base_path"] = "/player/Universal-LPC-spritesheet"
    skeleton_data["image_states"] = {"left":9, "right": 11, "cast_left": 1, "cast_right": 3}
    skeleton_data["image_state"] = "left"
    skeleton_data["image_frame_offset"] = 0
    skeleton_data["skeleton_is_walking"] = False
    skeleton_data["walk_speed"] = 6
    skeleton_data["jump_speed"] = 15
    skeleton_data["is_jumping"] = False
    skeleton_data["is_climbing"] = False
    skeleton_data["can_jump"] = True
    skeleton_data["surface"] = pygame.Surface(skeleton_data["display_size"])
    skeleton_data["surface"].fill((255,0,255))
    skeleton_data["surface"].set_colorkey((255,0,255))
    skeleton_data["update"] = update_skeleton
    skeleton_data["last_world_pos"] = copy.deepcopy(world_xy)
    
    return(skeleton_data)
