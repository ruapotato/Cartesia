#AGPL by David Hamner 2023
#Flat obj like, imported into gui.py for native functions calls. 

def update_tree(tree_data):
    #Foreign function from gui.py
    global world_xy
    global gravity
    global DEBUG
    global dot
    global main_player
    
    #print(f"info: {tree_data['is_climbing']}")
    x_speed_change = 0
    y_speed_change = 0
    
    #Delete data on death
    if tree_data["life"] < 0:
        print("Tree down")
        del NPCs[NPCs.index(tree_data)]
        print(f"Removing: {tree_data['save_data_file']}")
        os.remove(tree_data["save_data_file"])
        return()
    

    tree_data["wanted_speed"] = [0,0]

    
    
    #Adjust tree speed to wanted_speed slowly
    if not tree_data["can_jump"]:
        tree_data["wanted_speed"][1] = 0
    if tree_data["wanted_speed"][0] != tree_data["speed"][0]:
        diff = tree_data["speed"][0] + tree_data["wanted_speed"][0] 
        x_speed_change = diff/2
    if tree_data["wanted_speed"][1] != tree_data["speed"][1]:
        if tree_data["wanted_speed"][1] == 0:
            y_speed_change = tree_data["speed"][1]
        else:
            diff = tree_data["speed"][1] + tree_data["wanted_speed"][1] 
            y_speed_change = diff/2
    tree_data["speed"] = [x_speed_change, y_speed_change]
    #print(tree_data["speed"])
    
    #Update world pos
    world_change_in_x = world_xy[0] - tree_data["last_world_pos"][0]
    world_change_in_y = world_xy[1] - tree_data["last_world_pos"][1]
    tree_data["pos"][0] -= world_change_in_x
    tree_data["pos"][1] += world_change_in_y
    tree_data["last_world_pos"] = copy.deepcopy(world_xy)

    
    pos = copy.deepcopy(tree_data["pos"])
    hitbox_size = tree_data["hitbox_size"]
    current_speed = tree_data["speed"]
    is_climbing = tree_data["is_climbing"]
    can_jump = tree_data["can_jump"]
    is_jumping = tree_data["is_jumping"]
    
    #Block hit checking
    
    pos_change, newSpeed, is_climbing, can_jump, is_jumping, fall_damage = environmentSpeedChange(pos,
                                                                                             hitbox_size,
                                                                                             current_speed,
                                                                                             is_climbing,
                                                                                             can_jump,
                                                                                             is_jumping)
    if fall_damage == 10000:
        del NPCs[NPCs.index(tree_data)]
        return
    
    #Fix inside blocks
    tree_data["pos"][0] -= pos_change[0] - tree_data["pos"][0]
    tree_data["pos"][1] += pos_change[1] - tree_data["pos"][1]                                                                  

    
    tree_data["speed"] = newSpeed
    tree_data["is_climbing"] = is_climbing
    tree_data["can_jump"] = can_jump
    tree_data["is_jumping"] = is_jumping
                    
    
    #add speed to tree (In this case edit the world_xy)
    if tree_data["speed"] != [0,0]:
        tree_data["pos"][0] += int(tree_data["speed"][0])
        tree_data["pos"][1] -= int(tree_data["speed"][1])

    #Update strength
    if tree_data["strength"] < tree_data["max_strength"]:
        tree_data["strength"] += tree_data["strength_regen"]
    
    # Update active_item
    #mouse_presses = pygame.mouse.get_pressed()
    
    #Update folder if needed
    block_type,block_pos,block_index,chunk_atm = get_block_at(tree_data["pos"])
    #Update save data
    data = {"pos": block_index,
            "life": tree_data["life"]}
    with open(tree_data["save_data_file"], "w") as fh:
         yaml.dump(data, fh, default_flow_style=False)

    new_save_data_file = f"{WORLD_DIR}/{chunk_atm}/{tree_data['name']}.yml"
    if new_save_data_file != tree_data["save_data_file"]:
        #Move old to new
        print(f"Moving {tree_data['save_data_file']} {new_save_data_file}")
        os.rename(tree_data["save_data_file"], new_save_data_file)
        tree_data["save_data_file"] = new_save_data_file

def init_tree(pos):
    global world_xy
    tree_data = {}
    #tree pos from would pos
    tree_data["life"] = 60
    tree_data["hurt_sound"] = "tree_hurt"
    tree_data["pos"] = pos
    tree_data["speed"] = [0,0]
    tree_data["walk_speed"] = 5
    tree_data["jump_speed"] = 15
    tree_data["wanted_speed"] = [0,0]
    tree_data["display_size"] = [90,135]
    tree_data["hitbox_size"] = [90,135]
    tree_data["active_item"] = None
    tree_data["shoot_bow"] = process_bow_shooting
    
    tree_data["body_strength"] = 5
    tree_data["strength"] = 90
    tree_data["strength_regen"] = .5
    tree_data["max_strength"] = 100
    tree_data["bow_draw_speed"] = 25
    tree_data["bow_draw"] = 0
        
    #tree_images = {"body": "/body/male/light"}
    
    tree_data["image"] = f"{script_path}/img/Krook Tree Small.png"
    tree_data["image_base_path"] = "/"

    tree_data["image_frame_offset"] = 0


    tree_data["is_jumping"] = False
    tree_data["is_climbing"] = False
    tree_data["can_jump"] = True
    #tree_data["surface"] = pygame.Surface(tree_data["display_size"])
    #tree_data["surface"].fill((255,0,255))
    #tree_data["surface"].set_colorkey((255,0,255))
    tree_data["update"] = update_tree
    tree_data["last_world_pos"] = copy.deepcopy(world_xy)
    tree_data["name"] = f"init_tree_{time.time()}"
    chunk_atm = get_block_at(tree_data["pos"])[-1]
    tree_data["save_data_file"] = f"{WORLD_DIR}/{chunk_atm}/{tree_data['name']}.yml"
    
    return(tree_data)
