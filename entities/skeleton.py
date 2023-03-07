#AGPL by David Hamner 2023
#Flat obj like, imported into gui.py for native functions calls. 

def update_skeleton(skeleton_data):
    #Foreign function from gui.py
    global world_xy
    global gravity
    global DEBUG
    global dot
    global main_player
    
    #print(f"info: {skeleton_data['is_climbing']}")
    x_speed_change = 0
    y_speed_change = 0
    
    shoot_at = display_width//4
    if skeleton_data["active_item"] != None:
        shoot = True
    else:
        shoot = False
    if skeleton_data["pos"][0] < main_player["offset"][0] - shoot_at:
        skeleton_data["wanted_speed"][0] = skeleton_data["walk_speed"]
        skeleton_data["skeleton_is_walking"] = True
    elif skeleton_data["pos"][0] > main_player["offset"][0] + shoot_at:
        skeleton_data["wanted_speed"][0] = skeleton_data["walk_speed"] * -1
        skeleton_data["skeleton_is_walking"] = True
    else:
        skeleton_data["wanted_speed"][0] = 0
        shoot = True
    if skeleton_data["pos"][0] > main_player["offset"][0]:
        skeleton_data["image_state"] = "left"
    else:
        skeleton_data["image_state"] = "right"
    #Don't move when shooting
    if skeleton_data["active_item"] != None:
        skeleton_data["wanted_speed"] = [0,0]
        skeleton_data["skeleton_is_walking"] = False
    
    
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
    if fall_damage == 10000:
        del NPCs[NPCs.index(skeleton_data)]
        return
    #skeleton_data["pos"][1] += skeleton_data["pos"][1] - pos_change[1]
    skeleton_data["pos"][0] -= pos_change[0] - skeleton_data["pos"][0]
    skeleton_data["pos"][1] += pos_change[1] - skeleton_data["pos"][1]                                                                  

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

    #Update strength
    if skeleton_data["strength"] < skeleton_data["max_strength"]:
        skeleton_data["strength"] += skeleton_data["strength_regen"]
    
    # Update active_item
    #mouse_presses = pygame.mouse.get_pressed()
    
    #process shooting
    if shoot:
        skeleton_data["shoot_bow"](skeleton_data)
    
    elif skeleton_data["active_item"] != None:
        skeleton_data["shoot_bow"](skeleton_data, end_shooting=True)
        
    if skeleton_data["skeleton_is_walking"]:
        skeleton_data["image_frame_offset"] += 1
        skeleton_data["image_frame_offset"] %= 9

def init_skeleton(pos):
    global world_xy
    skeleton_data = {}
    #skeleton pos from would pos
    skeleton_data["pos"] = pos
    skeleton_data["speed"] = [0,0]
    skeleton_data["walk_speed"] = 5
    skeleton_data["jump_speed"] = 15
    skeleton_data["wanted_speed"] = [0,0]
    skeleton_data["display_size"] = [64,64]
    skeleton_data["hitbox_size"] = [32,64]
    skeleton_data["active_item"] = None
    skeleton_data["shoot_bow"] = process_bow_shooting
    
    skeleton_data["body_strength"] = 5
    skeleton_data["strength"] = 90
    skeleton_data["strength_regen"] = .5
    skeleton_data["max_strength"] = 100
    skeleton_data["bow_draw_speed"] = 25
    skeleton_data["bow_draw"] = 0
    
    skeleton_images = {"body": "/body/male/skeleton",
                       "bow": "/weapons/right hand/either/bow_skeleton"}
    #                   "arrow": "/weapons/left hand/either/arrow_skeleton"}
    
    #skeleton_images = {"body": "/body/male/light"}
    
    skeleton_data["images"] = skeleton_images
    skeleton_data["image_base_path"] = "/player/Universal-LPC-spritesheet"
    skeleton_data["image_states"] = {"left":9, "right": 11, "draw_left": 17, "draw_right": 19}
    skeleton_data["image_state"] = "left"
    skeleton_data["image_frame_offset"] = 0
    skeleton_data["skeleton_is_walking"] = False

    skeleton_data["is_jumping"] = False
    skeleton_data["is_climbing"] = False
    skeleton_data["can_jump"] = True
    skeleton_data["surface"] = pygame.Surface(skeleton_data["display_size"])
    skeleton_data["surface"].fill((255,0,255))
    skeleton_data["surface"].set_colorkey((255,0,255))
    skeleton_data["update"] = update_skeleton
    skeleton_data["last_world_pos"] = copy.deepcopy(world_xy)
    
    return(skeleton_data)
