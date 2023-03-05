#AGPL by David Hamner 2023

def update_bow(bow_data):
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
            main_player["live"] -= bow_data["damage"]
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


def init_bow(from_pos, to_pos, power):
    bow_data = {}
    #bow pos from would pos
    texterus_path = f"{script_path}/img/player/Universal-LPC-spritesheet"
    bow_data["img"] = f"{texterus_path}/weapons/left hand/either/single_arrow.png"
    bow_data["pos"] = from_pos
    bow_data["to_pos"] = to_pos
    bow_data["speed"] = power * 3.5
    
    first_new_point = get_point_along(bow_data["pos"], bow_data["to_pos"], bow_data["speed"])
    
    speed_in_x = bow_data["pos"][0] - first_new_point[0]
    speed_in_y = bow_data["pos"][1] - first_new_point[1]
    bow_data["bow_speed_xy"] = [speed_in_x, speed_in_y]
    bow_data["cost"] = 50
    
    bow_data["active"] = False
    bow_data["blocked_minded_amount"] = 0
    bow_data["image_frame_pos"] = 0
    bow_data["target"] = None
    bow_data["range"] = power
    
    bow_data["damage"] =  power
    bow_data["facing"] = "left"
    bow_data["last_world_pos"] = copy.deepcopy(world_xy)
    bow_data["block_mine_type"] = {2:10, 
                                       3:10,
                                       4:40}
    bow_data["update"] = update_bow
    return(bow_data)

