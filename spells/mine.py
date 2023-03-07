#AGPL by David Hamner 2023

def process_mine_cast(caster_data, end_spell=False):
    spell_casted = caster_data["magic_part_casted"] >= caster_data["magic_cast_speed"]
    if spell_casted:
        #Load new spell
        if caster_data["active_spell"] == None:
            caster_data["active_spell"] = init_mine_spell(list(pygame.mouse.get_pos()),
                                                                        caster_data["spell_strength"])
        if caster_data["active_spell"]["cost"] < caster_data["magic"]:
            caster_data["magic"] -= caster_data["active_spell"]["cost"]
        
            #Update spell
            caster_data["active_spell"]["update"](caster_data["active_spell"])
        else:
            end_spell = True
    if not spell_casted:
        if caster_data["magic_part_casted"] == 0:
            pygame.mixer.Sound.play(sounds["magic_spell"])
        caster_data["magic_part_casted"] += 1

    if end_spell:
        caster_data["magic_part_casted"] = 0
        if caster_data["active_spell"] != None:
            del caster_data["active_spell"]
            caster_data["active_spell"] = None
        
    #Update frame
    if caster_data["magic_part_casted"] != 0:
        if "cast" not in caster_data["image_state"]:
            caster_data["image_state"] = f"cast_{caster_data['image_state']}"
        if caster_data["magic_part_casted"] < caster_data["magic_cast_speed"]:
            caster_data["image_frame_offset"] = int((7/caster_data["magic_cast_speed"]) * caster_data["magic_part_casted"])
            #caster_data["image_frame_offset"] %= 7
    else:
        if "cast" in caster_data["image_state"]:
            caster_data["image_state"] = caster_data["image_state"].split("_")[-1]


def update_mine_spell(mine_spell_data):
    global gameDisplay
    mouse_presses = pygame.mouse.get_pressed()

    event_pos = list(pygame.mouse.get_pos())
    block_type,pos,block_index,chunk_index = get_block_at(event_pos)
    
    #Update world pos
    world_change_in_x = world_xy[0] - mine_spell_data["last_world_pos"][0]
    world_change_in_y = world_xy[1] - mine_spell_data["last_world_pos"][1]
    mine_spell_data["pos"][0] -= world_change_in_x
    mine_spell_data["pos"][1] += world_change_in_y
    mine_spell_data["last_world_pos"] = copy.deepcopy(world_xy)
    
    mine=False
    if abs(mine_spell_data["pos"][0] - event_pos[0]) < 5 and abs(mine_spell_data["pos"][1] - event_pos[1]) < 5:
        print("Mine")
        mine=True
    else:
        mine_spell_data["pos"] = get_point_along(mine_spell_data["pos"], event_pos, mine_spell_data["speed"])
    
    if mine:
        #TODO check dist
        if block_type == 1:
            mine_spell_data["active"] = False
        else:
            mine_spell_data["active"] = True
        
        #Reset mine if block changes
        if mine_spell_data["target"] != (block_index,chunk_index) or block_type == 1:
            mine_spell_data["blocked_minded_amount"] = 0
            mine_spell_data["image_frame_offset"] = 0
            mine_spell_data["target"] = (block_index,chunk_index)
        
        if mine_spell_data["active"]:
            mine_spell_data["blocked_minded_amount"] += mine_spell_data["speed"]
            mine_spell_data["image_frame_offset"] += 1
            
        if block_type in mine_spell_data["block_mine_type"]:
            needed_to_mine = mine_spell_data["block_mine_type"][block_type]
            if needed_to_mine < mine_spell_data["blocked_minded_amount"]:
                delete_block(pos,block_index,chunk_index)
                print(f"Left: {pos}: Chunk {chunk_index}")
                print(f"{block_index[0]} x {block_index[1]}")
                print(f"type: {block_type}")


    #draw
    frame = mine_spell_data["image_frame_offset"] % 15
    img = mine_spell_data["img"]
    if mine_spell_data["active"]:
        angle =  frame * -8
        #angle = game_tick % 360
    else:
        angle = 0

        
    #print(angle)
    if mine_spell_data["facing"] == "left":
        pos = [mine_spell_data["pos"][0] - 5, mine_spell_data["pos"][1] + 5]
        draw_img(img, pos, angle=angle, flip=True)
        #draw_img(pygame.transform.rotate(pygame.transform.flip(img,1,0), angle), pos)
        #draw_img(img, pos)
    else:
        pos = [mine_spell_data["pos"][0] + 5, mine_spell_data["pos"][1] + 5]
        draw_img(img, pos, angle=angle, flip=False)
        #draw_img(pygame.transform.rotate(img, angle), pos)
        #gameDisplay.blit(img, pos)
        



def init_mine_spell(pos, power):
    mine_spell_data = {}
    #mine_spell pos from would pos
    texterus_path = f"{script_path}/img/pixelperfection"
    mine_spell_data["img"] = f"{texterus_path}/default/default_tool_woodpick.png"
    mine_spell_data["cost"] = 5//power
    mine_spell_data["pos"] = pos
    mine_spell_data["speed"] = power // 1.5
    mine_spell_data["active"] = False
    mine_spell_data["blocked_minded_amount"] = 0
    mine_spell_data["image_frame_offset"] = 0
    mine_spell_data["target"] = None
    mine_spell_data["range"] = power // 3
    mine_spell_data["facing"] = "left"
    mine_spell_data["block_mine_type"] = {2:10, 
                                       3:10,
                                       4:40}
    mine_spell_data["update"] = update_mine_spell
    mine_spell_data["last_world_pos"] = copy.deepcopy(world_xy)
    return(mine_spell_data)

