#AGPL by David Hamner 2023

def update_bow(bow_data):
    global gameDisplay
    
    block_type,pos,block_index,chunk_index = get_block_at(bow_data["pos"])
    
    #TODO check dist
    if block_type == 1:
        bow_data["pos"] = get_point_along(bow_data["pos"], bow_data["to_pos"], bow_data["speed"])
        bow_data["active"] = True
    else:
        bow_data["active"] = False
    
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
        



def init_bow(from_pos, to_pos, power):
    bow_data = {}
    #bow pos from would pos
    texterus_path = f"{script_path}/img/player/Universal-LPC-spritesheet"
    bow_data["img"] = f"{texterus_path}/weapons/left hand/either/single_arrow.png"
    bow_data["pos"] = from_pos
    bow_data["to_pos"] = to_pos
    bow_data["cost"] = 5//power
    bow_data["speed"] = power
    bow_data["active"] = False
    bow_data["blocked_minded_amount"] = 0
    bow_data["image_frame_pos"] = 0
    bow_data["target"] = None
    bow_data["range"] = power
    bow_data["facing"] = "left"
    
    bow_data["block_mine_type"] = {2:10, 
                                       3:10,
                                       4:40}
    bow_data["update"] = update_bow
    return(bow_data)

