#AGPL by David Hamner 2023
#Flat obj like, imported into gui.py for native functions calls. 
def init_player(offset):
    player_data = {}
    #player offset from would pos
    player_data["offset"] = offset
    player_data["speed"] = [0,0]
    player_data["wanted_speed"] = [0,0]
    player_data["display_size"] = [64,64]
    player_data["hitbox_size"] = [32,64]
    player_data["active_item"] = init_pickaxe(offset, 1, 5)
    
    
    player_images = {"body": "/body/male/light",
                     "ears": "/body/male/ears/bigears_light",
                     "eyes": "/body/male/eyes/brown",
                     "nose": "/body/male/nose/buttonnose_light",
                     "shirt": "/torso/leather/chest_male",
                     "shoulders": "/torso/leather/shoulders_male",
                     "pants": "/legs/skirt/male/robe_skirt_male"}
    
    
    #player_images = {"body": "/body/male/light"}
    
    player_data["images"] = player_images
    player_data["image_base_path"] = "/player/Universal-LPC-spritesheet"
    player_data["image_states"] = {"left":9, "right": 11}
    player_data["image_state"] = "left"
    player_data["image_frame_offset"] = 0
    player_data["player_is_walking"] = False
    player_data["walk_speed"] = 3
    player_data["jump_speed"] = 12
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
    pos_change, newSpeed, is_climbing, can_jump, is_jumping, damage = environmentSpeedChange(pos,
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
   #Update frame
    if player_data["player_is_walking"]:
        player_data["image_frame_offset"] += 1
        player_data["image_frame_offset"] %= 9
    
    # Update ative active_item
    if player_data["active_item"] != None:
        player_data["active_item"]["update"](player_data["active_item"])
        
