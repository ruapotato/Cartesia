#AGPL by David Hamner 2023

def update_pickaxe(pickaxe_data):
    global gameDisplay
    mouse_presses = pygame.mouse.get_pressed()
    if mouse_presses[0]:
        event_pos = pygame.mouse.get_pos()
        block_type,pos,block_index,chunk_index = get_block_at(event_pos)
        
        #TODO check dist
        if block_type == 1:
            pickaxe_data["active"] = False
        else:
            pickaxe_data["active"] = True
        
        #Reset mine if block changes
        if pickaxe_data["target"] != (block_index,chunk_index) or block_type == 1:
            pickaxe_data["blocked_minded_amount"] = 0
            pickaxe_data["image_frame_offset"] = 0
            pickaxe_data["target"] = (block_index,chunk_index)
        
        if pickaxe_data["active"]:
            pickaxe_data["blocked_minded_amount"] += pickaxe_data["speed"]
            pickaxe_data["image_frame_offset"] += 1
            
        if block_type in pickaxe_data["block_mine_type"]:
            needed_to_mine = pickaxe_data["block_mine_type"][block_type]
            if needed_to_mine < pickaxe_data["blocked_minded_amount"]:
                delete_block(pos,block_index,chunk_index)
                print(f"Left: {pos}: Chunk {chunk_index}")
                print(f"{block_index[0]} x {block_index[1]}")
                print(f"type: {block_type}")
    else:
        pickaxe_data["blocked_minded_amount"] = 0
        pickaxe_data["image_frame_offset"] = 0
        pickaxe_data["active"] = False

    #draw
    frame = pickaxe_data["image_frame_offset"] % 15
    img = pickaxe_data["img"]
    if pickaxe_data["active"]:
        angle =  frame * -8
        #angle = game_tick % 360
    else:
        angle = 0

        
    #print(angle)
    if pickaxe_data["facing"] == "left":
        offset = [pickaxe_data["offset"][0] - 5, pickaxe_data["offset"][1] + 5]
        draw_img(img, offset, angle=angle, flip=True)
        #draw_img(pygame.transform.rotate(pygame.transform.flip(img,1,0), angle), offset)
        #draw_img(img, offset)
    else:
        offset = [pickaxe_data["offset"][0] + 5, pickaxe_data["offset"][1] + 5]
        draw_img(img, offset, angle=angle, flip=False)
        #draw_img(pygame.transform.rotate(img, angle), offset)
        #gameDisplay.blit(img, offset)
        



def init_pickaxe(offset, speed, pick_range):
    pickaxe_data = {}
    #pickaxe offset from would pos
    texterus_path = f"{script_path}/img/pixelperfection"
    pickaxe_data["img"] = f"{texterus_path}/default/default_tool_woodpick.png"
    pickaxe_data["offset"] = offset
    pickaxe_data["speed"] = speed
    pickaxe_data["active"] = False
    pickaxe_data["blocked_minded_amount"] = 0
    pickaxe_data["image_frame_offset"] = 0
    pickaxe_data["target"] = None
    pickaxe_data["range"] = pick_range
    pickaxe_data["facing"] = "left"
    pickaxe_data["block_mine_type"] = {2:10, 
                                       3:10,
                                       4:40}
    pickaxe_data["update"] = update_pickaxe
    return(pickaxe_data)

