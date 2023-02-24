#Flat obj like, imported into gui.py for native functions calls. 
def init_player(offset):
    player_data = {}
    #player offset from would pos
    player_data["offset"] = offset
    player_data["speed"] = [0,0]
    player_data["display_size"] = [64,64]
    player_data["hitbox_size"] = [32,64]
    
    
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

    head_pos_altu = player_data["offset"][1] - player_data["hitbox_size"][0]//4 - 15
    
    right_foot_pos_altr = player_data["offset"][0] + player_data["hitbox_size"][0]//4
    right_foot_pos_altu = player_data["offset"][1] + player_data["hitbox_size"][1]//2
    right_foot_pos = [right_foot_pos_altr, right_foot_pos_altu]
    right_foot_block = get_block_at(right_foot_pos)
    
    right_head_pos = [right_foot_pos[0], head_pos_altu]
    right_top_head_block =  get_block_at(right_head_pos)
    
    left_foot_pos = [right_foot_pos[0]-player_data["hitbox_size"][0]/2, right_foot_pos[1]]
    left_foot_block = get_block_at(left_foot_pos)
    
    left_head_pos = [left_foot_pos[0],head_pos_altu]
    left_top_head_block =  get_block_at(left_head_pos)
    right_mid_pos = [right_foot_pos[0], right_foot_pos[1]-player_data["hitbox_size"][1]/2]
    right_mid_block = get_block_at(right_mid_pos)
    right_knee_pos = [right_foot_pos[0], right_foot_pos[1]-player_data["hitbox_size"][1]/8]
    right_knee_block = get_block_at(right_knee_pos)
    
    left_mid_pos = [right_mid_pos[0]-player_data["hitbox_size"][1]/4, right_mid_pos[1]]
    left_mid_block = get_block_at(left_mid_pos)
    left_knee_pos = [right_knee_pos[0]-player_data["hitbox_size"][1]/4, right_knee_pos[1]]
    left_knee_block = get_block_at(left_knee_pos)
    
    if player_data["speed"][1] < 0:
        print("Not jumpping")
        player_data["is_jumping"] = False
    
    #Walk up 1 block on right
    player_data["is_climbing"] = False
    if right_knee_block[0] != 1:
        if right_mid_block[0] != 1:
            if player_data["speed"][0] > 0:
                print("Block")
                player_data["speed"][0] = -.1
        else:
            if  not player_data["is_jumping"]:
                player_data["speed"][1] = 2.5
                player_data["is_climbing"] = True
    
    #Walk up 1 block on left
    if left_knee_block[0] != 1:
        if left_mid_block[0] != 1:
            if player_data["speed"][0] < 0:
                print("Block")
                player_data["speed"][0] = .1
        else:
            if  not player_data["is_jumping"]:
                player_data["speed"][1] = 2.5
                player_data["is_climbing"] = True
            
    
    #Don't jump into blocks
    if left_top_head_block[0] != 1 or right_top_head_block[0] != 1:
         player_data["speed"][1] = -.1
         print("Owhh my head")
        

    
    if DEBUG:
        draw_img(dot, left_foot_pos)
        draw_img(dot, right_foot_pos)
        draw_img(dot, right_knee_pos)
        draw_img(dot, right_mid_pos)
        draw_img(dot, left_knee_pos)
        draw_img(dot, left_mid_pos)
        draw_img(dot, left_head_pos)
        draw_img(dot, right_head_pos)
    
    #print(right_mid_block)
    #print(right_knee_block)
    if right_foot_block[0] == 1 and left_foot_block[0] == 1:
        #player falling
        player_data["speed"][1] = player_data["speed"][1] + gravity
    
    else:
        if player_data["speed"][1] != 0:
            #player done falling
            damage = player_data["speed"][1]//10
            
            #Snap to block
            
            #hit_at = (right_foot_block[1][1] // block_size) * block_size
            #print(right_foot_block)
            #print(f"HIT foot pos: {right_foot_block[1][1]} \n Block {hit_at} \nwould: {world_xy[1] }")
            #world_xy[1] = hit_at
            if not player_data["is_climbing"]:
                if not player_data["is_jumping"]:
                    print(f"Was: {world_xy[1]}")
                    new_block_level = (((world_xy[1] + player_data["speed"][1] + 6) // block_size) * block_size)
                    new_block_level += 6
                    print(f"info: {new_block_level}")
                    #world_xy[1] += 1
                    world_xy[1] = new_block_level
                    print(f"set to: {world_xy[1]}")
                    player_data["speed"][1] = 0
                    print(f"TODO: Player damaged: {damage}")
    
   
    if player_data["speed"] != [0,0]:
        world_xy[0] += player_data["speed"][0]
        world_xy[1] += player_data["speed"][1]
   #Update frame
    if player_data["player_is_walking"]:
        player_data["image_frame_offset"] += 1
        player_data["image_frame_offset"] %= 9
    
    
        
