#AGPL by David Hamner 2023

def update_pickaxe(pickaxe_data):
    global block_mine_type
    mouse_presses = pygame.mouse.get_pressed()
    if mouse_presses[0]:
        event_pos = pygame.mouse.get_pos()
        block_type,pos,block_index,chunk_index = get_block_at(event_pos)
        
        #TODO check dist
        pickaxe_data["active"] = True
        
        #Reset mine if block changes
        if pickaxe_data["target"] != (block_index,chunk_index):
            pickaxe_data["blocked_minded_amount"] = 0
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
        pickaxe_data["active"]





def init_pickaxe(offset, speed, pick_range):
    pickaxe_data = {}
    #pickaxe offset from would pos
    pickaxe_data["offset"] = offset
    pickaxe_data["speed"] = speed
    pickaxe_data["active"] = False
    pickaxe_data["blocked_minded_amount"] = 0
    pickaxe_data["image_frame_offset"] = 0
    pickaxe_data["target"] = None
    pickaxe_data["range"] = pick_range
    pickaxe_data["block_mine_type"] = {2:10, 
                                       3:10,
                                       4:40}
    pickaxe_data["update"] = update_pickaxe
    return(pickaxe_data)

