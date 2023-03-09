#AGPL by David Hamner 2023


def process_bow_shooting(shooter_data, target, end=False):
    if not end:
        shooter_data["wanted_speed"] = [0,0]
        shooter_data["player_is_walking"] = False
    #Make new ite
    if not end:
        if shooter_data["active_item"] == None:
            #print("Making new!")
            shooter_data["active_item"] = init_bow(shooter_data["body_strength"])

            
        strength_to_shoot = shooter_data["active_item"]["cost"] < shooter_data["strength"]
        #print(f"Can shoot: {strength_to_shoot}")
        if strength_to_shoot:
            #Start drawing
            shooter_data["bow_draw"] += 1
            if shooter_data["bow_draw"] > shooter_data["bow_draw_speed"]:
                if not shooter_data["active_item"]["active"]:
                    shooter_data["strength"] -= shooter_data["active_item"]["cost"]
                    shooter_data["active_item"]["active"] = True
                    #print("Made active")
    
    #Update arrow
    if shooter_data["active_item"] and shooter_data["active_item"]["active"]:
        #Set target
        if shooter_data["active_item"]["to_pos"] == None:
            shooter_data["active_item"]["to_pos"] = copy.deepcopy(target)
            shooter_data["active_item"]["pos"] = copy.deepcopy(shooter_data["pos"])
            first_new_point = get_point_along(shooter_data["active_item"]["pos"], shooter_data["active_item"]["to_pos"], shooter_data["active_item"]["speed"])
            speed_in_x = shooter_data["active_item"]["pos"][0] - first_new_point[0]
            speed_in_y = shooter_data["active_item"]["pos"][1] - first_new_point[1]
            shooter_data["active_item"]["bow_speed_xy"] = [speed_in_x, speed_in_y]
            shooter_data["active_item"]["last_world_pos"] = copy.deepcopy(world_xy)
            
        #still_active = shooter_data["active_item"]["update"](shooter_data["active_item"])
        still_active = update_arrow(shooter_data["active_item"])
        if not still_active:
            del shooter_data["active_item"]
            shooter_data["active_item"] = None
            end = True
    
    
    if end:
        shooter_data["bow_draw"] = 0
    #    if shooter_data["active_item"] != None:
    #Not needed for arrows (Go until you hit something)
    #        del shooter_data["active_item"]
    #        shooter_data["active_item"] = None
        
    #Update frame
    if shooter_data["bow_draw"] != 0:
        if "draw" not in shooter_data["image_state"]:
            if "left" in shooter_data["image_state"]:
                shooter_data["image_state"] = f"draw_left"
            else:
                shooter_data["image_state"] = f"draw_right"
        if "draw" not in shooter_data["image_state"] and not end:
            shooter_data["image_state"] = f"draw_{shooter_data['image_state']}"
        if shooter_data["bow_draw"] < shooter_data["bow_draw_speed"] and not end:
            shooter_data["image_frame_offset"] = int((8/shooter_data["bow_draw_speed"]) * shooter_data["bow_draw"])
            #print(shooter_data["image_frame_offset"])
            if shooter_data["image_frame_offset"] == 7:
                shooter_data["image_frame_offset"] = 0
            #shooter_data["image_frame_offset"] %= 7
    else:
        if "draw" in shooter_data["image_state"]:
            shooter_data["image_state"] = shooter_data["image_state"].split("_")[-1]



def update_arrow(bow_data):
    global gameDisplay
    
    
    #Update world pos
    world_change_in_x = world_xy[0] - bow_data["last_world_pos"][0]
    world_change_in_y = world_xy[1] - bow_data["last_world_pos"][1]
    bow_data["pos"][0] -= world_change_in_x
    bow_data["pos"][1] += world_change_in_y
    bow_data["to_pos"][0] -= world_change_in_x
    bow_data["to_pos"][1] += world_change_in_y
    bow_data["last_world_pos"] = copy.deepcopy(world_xy)
    
    
    block_type,pos,block_index,chunk_index = get_block_at(bow_data["pos"])
    
    #TODO check dist
    if block_type == 1:
        new_point = [bow_data["pos"][0] - bow_data["bow_speed_xy"][0], bow_data["pos"][1] - bow_data["bow_speed_xy"][1]]
        
        #get_point_along(bow_data["pos"], bow_data["to_pos"], bow_data["speed"])
        #print(abs(new_point[0] - main_player["offset"][0]))
        if abs(new_point[0] - main_player["offset"][0]) < 10 and abs(new_point[1] - main_player["offset"][1]) < 10:
            print("Killl")
            main_player["life"] -= bow_data["damage"]
            return(False)
        else:
            bow_data["pos"] = new_point
        #bow_data["active"] = True
    else:
        return(False)
        #bow_data["active"] = False
    
        #TODO check what we hit
    
    #draw
    #frame = bow_data["image_frame_pos"] % 15
    img = bow_data["img"]


        
    #print(angle)
    if bow_data["facing"] == "left":
        #pos = [bow_data["pos"][0] - 5, bow_data["pos"][1] + 5]
        draw_img(img, bow_data["pos"], angle=0, flip=True)
        #draw_img(pygame.transform.rotate(pygame.transform.flip(img,1,0), angle), pos)
        #draw_img(img, pos)
    else:
        draw_img(img, bow_data["pos"])
        #pos = [bow_data["pos"][0] + 5, bow_data["pos"][1] + 5]
        #draw_img(img, pos, angle=angle, flip=False)
        #draw_img(pygame.transform.rotate(img, angle), pos)
        #gameDisplay.blit(img, pos)
        
    return(True)


def init_bow(power):
    bow_data = {}
    #bow pos from would pos
    texterus_path = f"{script_path}/img/player/Universal-LPC-spritesheet"
    bow_data["img"] = f"{texterus_path}/weapons/left hand/either/single_arrow.png"
    bow_data["pos"] = None
    bow_data["to_pos"] = None # Set after arrow is shot
    bow_data["speed"] = power * 3.5
    

    bow_data["cost"] = 50
    
    bow_data["active"] = False
    bow_data["blocked_minded_amount"] = 0
    bow_data["image_frame_pos"] = 0
    bow_data["target"] = None
    bow_data["range"] = power
    
    bow_data["damage"] =  power * 4
    bow_data["facing"] = "left"
    
    bow_data["block_mine_type"] = {2:10, 
                                       3:10,
                                       4:40}
    bow_data["update"] = process_bow_shooting
    return(bow_data)

