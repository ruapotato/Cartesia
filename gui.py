#!/usr/bin/python3

#AGPL by David Hamner 2023
import time
import pygame
import copy
import os
from datetime import datetime
#import gen_chunk
import yaml
import numpy as np
import random
#import blocks # TODO Broken
#from pygame.locals import *
#from entities.player import *
#from items.pickaxe import *
if "SDL_VIDEODRIVER" in os.environ:
    if  os.environ["SDL_VIDEODRIVER"] == "dummy":
        del os.environ["SDL_VIDEODRIVER"]






def chunk_rendered(needed_chunk):
    chunk_dir = f"{WORLD_DIR}/{needed_chunk}/"
    image_file = f"{chunk_dir}blocks.tga"
    if os.path.isfile(image_file):
        print("Chunk rendered")
        return(True)
    return(False)

def load_chunk_image(needed_chunk):
    chunk_dir = f"{WORLD_DIR}/{needed_chunk}/"
    image_file = f"{chunk_dir}blocks.tga"
    return(pygame.image.load(image_file).convert_alpha())


def get_block_data(needed_chunk):
    chunk_dir = f"{WORLD_DIR}/{needed_chunk}/"
    block_file = f"{chunk_dir}blocks.txt"
    data = np.loadtxt(block_file)
    return(data)


# Use blocks to find change of speed
def environmentSpeedChange(pos, hitbox_size, current_speed, is_climbing, can_jump, is_jumping):
    damage = 0
    
    #Make points around object
    head_pos_altu = pos[1] - hitbox_size[0]//4 - 15
    
    right_foot_pos_altr = pos[0] + hitbox_size[0]//4
    right_foot_pos_altu = pos[1] + hitbox_size[1]//2
    right_foot_pos = [right_foot_pos_altr, right_foot_pos_altu]
    right_foot_block = get_block_at(right_foot_pos)
    
    right_head_pos = [right_foot_pos[0] - 1, head_pos_altu]
    right_top_head_block =  get_block_at(right_head_pos)
    
    left_foot_pos = [right_foot_pos[0]-hitbox_size[0]/2, right_foot_pos[1]]
    left_foot_block = get_block_at(left_foot_pos)
    
    center_foot_pos = [right_foot_pos[0]-hitbox_size[0]/4, right_foot_pos[1]]
    center_foot_block = get_block_at(center_foot_pos)
    
    left_head_pos = [left_foot_pos[0] + 1,head_pos_altu]
    left_top_head_block =  get_block_at(left_head_pos)
    right_mid_pos = [right_foot_pos[0], right_foot_pos[1]-hitbox_size[1]/2]
    right_mid_block = get_block_at(right_mid_pos)
    right_knee_pos = [right_foot_pos[0], right_foot_pos[1]-hitbox_size[1]/8]
    right_knee_block = get_block_at(right_knee_pos)
    
    left_mid_pos = [right_mid_pos[0]-hitbox_size[1]/4, right_mid_pos[1]]
    left_mid_block = get_block_at(left_mid_pos)
    left_knee_pos = [right_knee_pos[0]-hitbox_size[1]/4, right_knee_pos[1]]
    left_knee_block = get_block_at(left_knee_pos)
    
    if current_speed[1] < 0:
        #print("Not jumpping")
        is_jumping = False
    
    blocked_on = {"head": False,
                  "right": False,
                  "left": False}
    
    #Check if offscreen
    if right_knee_block[0] == -1 or left_knee_block == -1:
        current_speed = [0,0]
        return(pos, current_speed, False, False, False, 10000)
    
    #Walk up 1 block on right
    is_climbing = False
    if right_knee_block[0] != 1:
        if right_mid_block[0] != 1:
            if current_speed[0] > 0:
                #print("Block on right")
                blocked_on["right"] = True
                current_speed[0] = -.2
        else:
            if not is_jumping:
                if int(current_speed[0]) > 0:
                    #print("climbing right")
                    #current_speed[1] = 2.5
                    pos[1] -= 6
                    is_climbing = True
    
    #Walk up 1 block on left
    if left_knee_block[0] != 1:
        if left_mid_block[0] != 1:
            if current_speed[0] < 0:
                #print("Block on left")
                blocked_on["left"] = True
                current_speed[0] = .2
        else:
            if  not is_jumping:
                if int(current_speed[0]) < 0:
                    #print("climbing left")
                    #current_speed[1] = 2.5
                    pos[1] -= 6
                    is_climbing = True
            
    
    #Don't jump into blocks
    if left_top_head_block[0] != 1 or right_top_head_block[0] != 1:
         current_speed[1] = -.1
         is_jumping = False
         #print("Owhh my head")
         blocked_on["head"] = True
    
    
    # Eject from blocks you're stuck in
    if blocked_on["left"] and blocked_on["right"] and not blocked_on["head"]:
        print("Fixing...")
        pos[1] -= 6
    
    if DEBUG:
        pass
        #draw_img(dot, left_foot_pos)
        #draw_img(dot, right_foot_pos)
        #draw_img(dot, right_knee_pos)
        #draw_img(dot, right_mid_pos)
        #draw_img(dot, left_knee_pos)
        #draw_img(dot, left_mid_pos)
        #draw_img(dot, left_head_pos)
        #draw_img(dot, right_head_pos)
    
    #Foot pos hit points
    left = int(left_foot_block[0] == 1)
    right = int(right_foot_block[0] == 1)
    center = int(center_foot_block[0] == 1)
    #Under player is air
    if left + right + center >= 2:
        #player falling
        #print(f"Falling and climbing: {is_climbing}")
        current_speed[1] = current_speed[1] + gravity
        can_jump = False
    else:
        #print("Not falling")
        #not blocked_on["head"] and not blocked_on["left"] and not blocked_on["right"]:
        can_jump = True
        if current_speed[1] != 0:
            #player done falling
            damage = current_speed[1]//10
            
            #Snap to block
            
            #hit_at = (right_foot_block[1][1] // block_size) * block_size
            if not is_climbing:
                if not is_jumping:
                    #print(f"Was: {pos[1]}")
                    #print(f"SPEED: {current_speed}")
                    # 720 * x = 4
                    # 360 * x = 8
                    # height magic crap
                    #TODO replace Use block size and offset image size
                    #This is broken for some chunks
                    
                    last_fram_center_foot_pos = [center_foot_pos[0]-current_speed[0]//2, center_foot_pos[1] + current_speed[1]//2]
                    ground_block = get_block_at(last_fram_center_foot_pos)
                    block_type = ground_block[0]
                    block_pos = ground_block[1]
                    block_index = ground_block[2]
                    chunk_index  = ground_block[3].split("_")
                    chunk_index = [int(chunk_index[0]), int(chunk_index[1])]

                    new_x = (block_index[0] * block_size) + (chunk_index[0] * chunk_blocks * block_size)
                    new_x -= world_xy[0]
                    #new_y = (block_index[1] * block_size) + (chunk_index[1] * chunk_size)
                    new_y = (block_index[1] * block_size) - (chunk_index[1] * chunk_blocks * block_size)
                    new_y += world_xy[1]
                    
                    if DEBUG:
                        gameDisplay.blit(dot, [new_x,new_y])
                    
                    # Ajust for image size
                    new_y -= hitbox_size[1]//2
                    #new_y -= 3
                    
                    # Ajust for speed
                    #new_y += (//block_size) * block_size
                    current_speed[1] = 0
                    
                    new_pos = [new_x, new_y]
                    
                    #print(f"chunk: {chunk_index}")
                    #print(f"Block: {block_index}")
                    #print(new_pos)
                    #pos[1] += 1
                    pos[1] = new_pos[1] 
                    #print(f"set to: {pos[1]}")

    return((pos, current_speed, is_climbing, can_jump, is_jumping, damage))


def spawn_entities():
    global spawn_rates
    global game_time
    #off_screen_chunks = []
    x_center_chunk = int(world_xy[0]/chunk_size)
    y_center_chunk = int(world_xy[1]/chunk_size)
    write_player_data()
    #print(f"Center: {x_center_chunk}{y_center_chunk}")
    # if not night return:
    if not game_time < 30:
        return()
    for x_around_chunks in [-2,4]:
        for y_around_chunks in range(-3,3):
            this_x = x_center_chunk + x_around_chunks
            this_y = y_center_chunk + y_around_chunks
            
            chunk_index = f"{this_x}_{this_y}"
            if chunk_index in chunk_block_data:
                block_data = chunk_block_data[chunk_index]
                for block_x in range(0, chunk_blocks):
                    for block_y in range(0, chunk_blocks):
                        block_type = block_data[block_x][block_y]
                        if block_type in spawn_rates:
                            rate_of_spawn, spawn_init = spawn_rates[block_type]
                            #Get number from 0 to 100
                            this_guys_chance = random.randint(0,1000000)/10000
                            if this_guys_chance <= rate_of_spawn:
                                new_x = (block_x * block_size) + (this_x * chunk_blocks * block_size)
                                new_x -= world_xy[0]
                                #new_y = (block_index[1] * block_size) + (chunk_index[1] * chunk_size)
                                new_y = (block_y * block_size) - (this_y * chunk_blocks * block_size)
                                new_y += world_xy[1]
                                #new_y = new_y * -1
                                NPCs.append(spawn_init([new_x, new_y]))
                                if x_around_chunks == 4:
                                    print(f"Spawn at right {new_x} {new_y} {rate_of_spawn}")
                                else:
                                    print(f"Spawn at left {new_x} {new_y} {rate_of_spawn}")
            #off_screen_chunks.append(f"{this_x}_{this_y}")
    #print(off_screen_chunks)


def write_player_data():
    global world_xy

    player_data = {"pos": world_xy,
                   "seed": world_seed,
                   "time": datetime.now().strftime("%y-%m-%d %H:%M:%S.%f")}
    with open(player_datafile, "w") as fh:
        yaml.dump(player_data, fh, default_flow_style=False)


#Used for moving along a line at a speed
def get_point_along(point1, point2, speed):
    new_point = copy.deepcopy(point1)
    x_delta = abs(point1[0] - point2[0])
    y_delta = abs(point1[1] - point2[1])
    
    total_delta = x_delta + y_delta
    if total_delta == 0:
        return(point2)
    x_speed = (speed/total_delta)*x_delta
    y_speed = (speed/total_delta)*y_delta
    
    #game_actors[player_name]['lastPos'] = copy.deepcopy(game_actors[player_name]['pos'])
    if point1[0] - point2[0] < 0:
        new_point[0] += x_speed
    else:
        new_point[0] -= x_speed
    
    if point1[1] - point2[1] < 0:
        new_point[1] += y_speed
    else:
        new_point[1] -= y_speed
    
    if abs(new_point[0] - point2[0]) < speed:
        new_point[0] = point2[0]
    if abs(point1[1] - point2[1]) < speed:
        new_point[1] = point2[1]
    
    return(new_point)


def draw_NPC(images_by_path, pos, action_offset, image_buffer, img_base_path):
    global loaded_images
    image_buffer.fill((255,0,255))
    #print(action_offset)
    #action_offset = [-64,0]
    #print(action_offset)
    for image in images_by_path:
        full_path = f"{script_path}/img{img_base_path}{images_by_path[image]}.png"
        if full_path not in loaded_images:
            loaded_images[full_path] = pygame.image.load(full_path).convert_alpha()
        
        image_buffer.blit(loaded_images[full_path], action_offset)
        #print(action_offset)
    
    draw_img(image_buffer, pos)


def draw_inventory(full=False):
    x_size = 32
    y_size = 32
    
    
    x_offset = (display_width//2) - ((main_player["inventory_size"][0]/2) * x_size)
    y_offset = 25
    
    if full:
        max_index = main_player["inventory_size"][0] * main_player["inventory_size"][1]
    else:
        max_index = main_player["inventory_size"][0]
    
    for item_pos in range(0, max_index):
        image = None
        selected = False
        index_name = str(item_pos + 1)
        if  index_name in main_player["inventory"]:
            name =  main_player["inventory"][ index_name][0]
            if name in inventory_images:
                image = inventory_images[name]
        
        
            if main_player["inventory"][index_name][1] == main_player["selected_item"]:
                selected = True
        x_pos = x_offset + (item_pos % main_player["inventory_size"][0]) * x_size
        y_pos = y_offset + (item_pos // main_player["inventory_size"][0]) * y_size
        print(f"{image} {x_pos} {y_pos}")
        
        if not selected:
            draw_img(blank, [x_pos, y_pos])
        else:
            draw_img(selected_item_bg, [x_pos, y_pos])
        if image != None:
            draw_img(image, [x_pos, y_pos])

def draw_sun(surface, chunk_address, offset, undraw=False):
    global light_sources
    global game_time
    global last_game_time
    global sun
    
    max_time = (255//2)
    change_in_display = (display_height * 2)//max_time
    x_pos = main_player["offset"][0]
    # TODO this is a bit of a mess. 
    if undraw:
        if last_game_time > 255//4:
            time_offset = 255//4
        else:
            time_offset = last_game_time
        y_pos = time_offset * change_in_display - offset[1] - display_height//2
        sun_pos = [x_pos + offset[0], y_pos]
    else:
        #sun_pos = [game_time * change_in_display + offset[0] + display_width//2, y_pos - offset[1]]
        if game_time > 255//4:
            time_offset = 255//4
        else:
            time_offset = game_time
        y_pos = time_offset * change_in_display - offset[1] - display_height//2
        #print(y_pos, display_height, game_time)
        sun_pos = [x_pos + offset[0], y_pos]
    
    #print(sun_pos)
    y_offset = sun_pos[1] - (chunk_address[1] * chunk_size * -1)
    x_offset = sun_pos[0] - (chunk_address[0] * chunk_size)
    new_pos = [x_offset - int(sun.get_width()/2), y_offset - int(sun.get_height()/2)]
    #sun_pos = [x_offset,y_offset]
    #print(sun_pos)
    #x_offset += block_offset[0]  + block_size//2
    #y_offset += block_offset[1] + block_size//2
    #surface.blit(light_source, sun_pos, special_flags=pygame.BLEND_RGBA_SUB)
    if undraw:
        surface.blit(sun, new_pos, special_flags=pygame.BLEND_RGBA_SUB)
    else:
        surface.blit(sun, new_pos, special_flags=pygame.BLEND_RGBA_ADD)

def draw_lighting(surface, chunk_address, undraw=False):
    global light_sources
    global chunk_size
    #global darkness
    global light_source
    global DEBUG

    
    #print(f"Light me up: {light_sources}")
    for chunk_with_lights in light_sources:
        lights_in_this_chunk = light_sources[chunk_with_lights]
        for light in lights_in_this_chunk:
            address = light[0]
            block_offset = light[1]
            y_offset = ((address[1] - chunk_address[1]) * chunk_size * -1)
            x_offset = ((address[0] - chunk_address[0]) * chunk_size)
            x_offset += block_offset[0]  + block_size//2
            y_offset += block_offset[1] + block_size//2
            new_pos = [x_offset - int(light_source.get_width()/2), y_offset - int(light_source.get_height()/2)]
            if undraw:
                surface.blit(light_source, new_pos, special_flags=pygame.BLEND_RGBA_SUB)
            else:
                surface.blit(light_source, new_pos, special_flags=pygame.BLEND_RGBA_ADD)
            """
            address = light[0]
            block_offset = light[1]
            x_offset = (address[0] * chunk_size) - world_xy[0]

            y_offset = (address[1] * chunk_size * -1) + world_xy[1]
            
            x_offset += block_offset[0]  + block_size//2 
            y_offset += block_offset[1] + block_size//2
            
            #Draw in center of light
            new_pos = [x_offset - int(light_source.get_width()/2), y_offset - int(light_source.get_height()/2)]
            #y_offset *= -1
            #print(f"How about: {x_offset} {y_offset}")
            #darkness.blit(light_source, new_pos)
            surface.blit(light_source, new_pos, special_flags=pygame.BLEND_RGBA_ADD)
            if DEBUG:
                draw_img(dot, [x_offset, y_offset])
            """
# Returns damage done  
def attack(point, damage_on_hit, dist=10):
    
    #see if we hit the main player
    if abs(point[0] - main_player["offset"][0]) < dist and abs(point[1] - main_player["offset"][1]) < dist:
        print("Killl player")
        sound = sounds[main_player["hurt_sound"]]
        main_player["life"] -= damage_on_hit
        pygame.mixer.Sound.play(sound)
        return(damage_on_hit)
    #See if we hit any entities
    for npc in NPCs:
        npc["pos"]
        if abs(point[0] - npc["pos"][0]) < dist and abs(point[1] - npc["pos"][1]) < dist:
            print("Killl npc")
            sound = sounds[npc["hurt_sound"]]
            npc["life"] -= damage_on_hit
            pygame.mixer.Sound.play(sound)
            return(damage_on_hit)
    return(0)

def draw_img(img, pos, target="default", angle=None, flip=False):
    
    #Support strings as image input
    if type(img) == str:
        if img not in loaded_images:
            loaded_images[img] = pygame.image.load(img).convert_alpha()
        img = loaded_images[img]
    
    w, h = img.get_size()
    #TODO reuse tmp_surface, or clean or remove it up somehow.
    if flip:
        x = w
        y = 1
        tmp_surface = pygame.Surface((w*2, h*2), pygame.SRCALPHA)
        tmp_surface.blit(img, (x, y))
        img = pygame.transform.rotate(tmp_surface, angle)
        img = pygame.transform.flip(img, 1,0)
        #img = pygame.transform.flip(img,1,0)
        #pos = [pos[0] +  angle//6, pos[1] - img.get_height()//2 - angle//6]
    elif angle != None:
        x = w
        y = 1
        tmp_surface = pygame.Surface((w*2, h*2), pygame.SRCALPHA)
        tmp_surface.blit(img, (x, y))
        img = pygame.transform.rotate(tmp_surface, angle)
        #img = pygame.transform.rotate(img, angle)
        #pos = [pos[0] -  angle//6, pos[1] - int(img.get_height()/2) + angle//6]
    
    new_pos = [pos[0] - int(img.get_width()/2), pos[1] - int(img.get_height()/2)]
    if target == "default":
        gameDisplay.blit(img, new_pos)
    else:
        target.blit(img, new_pos)



#Old crap
"""
def draw_npc():
    global game_actors
    global gameDisplay
    global npc_imges
    
    for player_name in game_actors:
        status = game_actors[player_name]['when']
        if status == "active":
            #print("draw NPC")
            img = game_actors[player_name]['img']
            img = npc_imges[img]
            name = game_actors[player_name]['life_file']
            life = check_for_life(name)
            name = name.split("/")[-1]
            name = f"{name}:{life}"
            name_height_offset = int((img.get_height()/2) + 15) * -1
            
            #Clear old
            old_pos = game_actors[player_name]['lastPos']
            old_name_pos = [old_pos[0],old_pos[1]+name_height_offset]
            draw_name(name,old_name_pos, clear=True)
            clear_img(img, old_pos)
            #pygame.draw.rect(gameDisplay,(255,255,255),(pos[0],pos[1],img.get_width(),img.get_height()))
            #Draw new
            pos = game_actors[player_name]['pos']
            name_pos = [pos[0],pos[1]+name_height_offset]
            draw_img(img, pos)
            draw_name(name,name_pos)
            #gameDisplay.blit(img, pos)

"""

def update_game():
    global gameDisplay
    global world_xy
    global game_tick
    global PWD
    global player_life
    global game_actors
    global current_level_base
    global display_txt
    global player_target
    global player_speed
    #global player_image
    global redraw_forced
    global hurt_sound
    
    #decrement_sys_msgs()
    #Move player if needed

    """
    if world_xy != player_target:
        #print(f"Moving player: {world_xy}")
        #clear current pos
        clear_img(player_image, world_xy)
        #pygame.draw.rect(gameDisplay,(255,255,255),(world_xy[0],world_xy[1],player_image.get_width(),player_image.get_height()))
        #update pos
        world_xy_test_point = get_point_along(world_xy, player_target, get_player_speed())
        if can_move_to(world_xy_test_point, player_image):
            world_xy = world_xy_test_point
        #Redraw player
        draw_img(player_image, world_xy)
    """
    #Process NPCs
    #print(game_actors)
    new_NPCs = {}
    
    NPC_lines_to_process = []
    for player_name in game_actors:
        status = game_actors[player_name]['when']
        drop_chance = game_actors[player_name]['drop_chance']
        drops = game_actors[player_name]['drops']
        damage = game_actors[player_name]['damage']
        is_friendly = False
        if status.startswith("every"):
            #print(status)
            start_on = int(status.split(" ")[-1])
            #print(start_on)
            #print(game_tick)
            if game_tick % start_on == 0:
                print("Need to added active!")
                new_npc = copy.deepcopy(game_actors[player_name])
                spawn = new_npc['spawn_line']
                print(f"Process respawn line: {spawn}")
                NPC_lines_to_process.append(spawn)
                #process_NPC_line(spawn)
                """
                print(f"new_npc: {new_npc}")
                new_npc_name = new_npc['name']
                if "$RAND" in new_npc_name:
                    rand_string = ''.join(random.choices(string.ascii_uppercase + string.digits, k = 7))
                    new_npc_name = new_npc_name.replace("$RAND", rand_string)
                
                #setup new life file for NPC
                new_npc['name'] = new_npc_name
                life_file = f"{chroot_PWD}/{new_npc_name}"
                life_value = new_npc['start_life']
                respawn = new_npc['respawn']
                print(f"respawn data: {respawn}")
                write_life_file(life_file, life_value, respawn)
                print(life_file)
                #with open(life_file, 'w') as fh:
                #    pass
                new_npc['when'] = "active"
                new_npc['life_file'] = life_file

                new_NPCs[new_npc_name] = new_npc

                #game_actors[new_npc_name] = new_npc
                #print(game_actors)
                """
                
        if status == "active":
            #print("Active NPC")
            life_file = game_actors[player_name]['life_file']
            allegiance = game_actors[player_name]['allegiance']
            #check if NPC killed
            if not os.path.isfile(life_file):
                print(f"Killed {life_file}| Hmmm:{drop_chance} drops:{drops}")
                if did_it_happen(drop_chance):
                    #examples drops
                    #5HP
                    #unlock/1
                    #msg some string to say
                    if drops.startswith("msg"):
                        msg = drops[3:]
                        write_sys_msg(msg, 65)
                    if drops.endswith("HP"):
                        life_drop = int(drops.strip("HP"))
                        change_life(life_drop)
                        if life_drop > 0:
                            #player_life = player_life + life_drop
                            msg = f"+{life_drop} HP"
                        else:
                            msg = f"-{life_drop} HP"
                            pygame.mixer.Sound.play(hurt_sound)
                        write_sys_msg(msg, 30)
                        print(f"Player life: {player_life}")
                    if drops.startswith("unlock"):
                        short_name = drops.split("unlock")[-1]
                        msg = f"A door has Opened!\nFind your way to:\n  {current_level_base}{short_name}"
                        write_sys_msg(msg, 65)
                        full_path = f"{chroot_path}{current_level_base}{short_name}"
                        print(f"Unlock: {full_path}")
                        unlock_door(full_path)
                    #Like unlock expect takes a full path
                    if drops.startswith("open"):
                        redraw_forced = True
                        path = drops[5:]

                        full_path = f"{chroot_path}{path}"
                        if os.path.isdir(full_path):
                            msg = f"{path} open!"
                            unlock_door(full_path)
                        else:
                            msg = f"Cannot unlock unknown or undiscovered path: \n  {full_path}"
                        write_sys_msg(msg, 65)
                    if drops == "touch_frog_pow":
                        #     good:  x:  y:status:          img: name:    AI:damage:life:    % drops
                        power = "1:100:100:active:good_frog.png:frog*:walk 3:     1:   3: 100% na"
                        write_player_spawn_power(power)
                        msg = "You can now spawn frogs with:\ntrouch frog_name"
                        write_sys_msg(msg, 65)
                    if drops == "touch_frog_pow_plus":
                        #     good:  x:  y:status:           img:  name:    AI:damage:life:    % drops
                        power = "1:100:100:active:power_frog.png:pfrog*:walk 3:     1:  10: 100% na"
                        write_player_spawn_power(power)
                        msg = "You can now spawn (powerful) frogs with:\ntrouch pfrog_name"
                        write_sys_msg(msg, 65)
                #Setup needed data
                img = game_actors[player_name]['img']
                img = npc_imges[img]
                pos = game_actors[player_name]['pos']
                
                #Draw laser
                clear_img(img, pos, color=(255,0,0))
                #pygame.draw.rect(gameDisplay,(255,0,0),(pos[0],pos[1],img.get_width(),img.get_height()))
                FIRE(pos)
                
                #clear npc
                clear_img(img, pos)
                #pygame.draw.rect(gameDisplay,(255,255,255),(pos[0],pos[1],img.get_width(),img.get_height()))
                game_actors[player_name]['when'] = "DEAD"
                continue
            
            #Check we have an ative attack
            if os.path.isfile(life_file):
                pos = game_actors[player_name]['lastPos']
                with open(life_file) as fh:
                    life_data = fh.readlines()
                for line in life_data:
                    if line.startswith("under_attack:True"):
                        #ative under_attack
                        FIRE(pos, clean_up_and_display=False)
            
            if allegiance > 0:
                target = [200,200]
            else:
                target = world_xy
            pos = game_actors[player_name]['pos']
            AI = game_actors[player_name]['AI']
            AI_args = game_actors[player_name]['AI_args']
            if AI.startswith("msg"):
                msg = f"{player_name}:\n  {AI_args}"
                write_sys_msg(msg, 1)
                #print(f"Writing: {msg}")
            #If this is a walk AI
            if AI.startswith("walk"):
                #If this is a bad NPC
                if allegiance < 0:
                    #check if we are hit
                    if abs(pos[0] - world_xy[0]) < 25 and abs(pos[1] - world_xy[1]) < 25:
                        change_life(damage * -1)
                        
                        #Play hit sound
                        pygame.mixer.Sound.play(hurt_sound)
                        
                        #player_life = player_life - damage
                        if get_player_life() <= 0:
                            #Reset
                            print("Player Dead!")
                            text = "Better luck next time!"
                            notify(text)
                            quit()
                        print("Hit")
                        continue
                speed = int(AI_args.strip())
                new_pos = get_point_along(pos, target, speed)
                #x_delta = pos[0] - world_xy[0]
                #y_delta = pos[1] - world_xy[1]
                
                #total_delta = x_delta + y_delta
                #x_speed = (speed/total_delta)*x_delta
                #y_speed = (speed/total_delta)*y_delta
                
                game_actors[player_name]['lastPos'] = copy.deepcopy(game_actors[player_name]['pos'])
                game_actors[player_name]['pos'] = new_pos
                #print(f"Moving with speed of {speed} {x_speed} {y_speed}")
                
            #print(pos)
    #add new NPCs outside of above eath loop
    #print(f"Needs added: {NPC_lines_to_process}")
    for npc_line in NPC_lines_to_process:
        process_NPC_line(npc_line)
    #mark files as known about
    if NPC_lines_to_process != []:
        set_processed_files(PWD)
    #for new_npc_name in new_NPCs:
        #game_actors[new_npc_name] = new_NPCs[new_npc_name]


def draw_world():
    global chunk_surfaces
    global rendered_chunks
    global world_xy
    global light_sources
    global rendered_sources
    global game_tick
    global fps
    global game_time
    global sun
    global last_sunspot
    
    sun_pos = [game_time, 50]
    
    for chunk_index in rendered_chunks:
        address = chunk_index.split("_")
        address = [int(address[0]), int(address[1])]
        x_offset = (address[0] * chunk_size) - world_xy[0]
        y_offset = (address[1] * chunk_size * -1) + world_xy[1]
        surface = chunk_surfaces[chunk_index]
        
        """
        if game_tick % 100 == 0:
            alpha = 200
            #surface.fill((0, 0, 0, alpha), None, pygame.BLEND_RGBA_SUB)
            #surface.set_alpha(5)
            rendered_sources = {}
            draw_lighting(surface, address, undraw=True)
        """
        if rendered_sources != light_sources:
            draw_lighting(surface, address)
        
        draw_sun(surface, address, last_sunspot, undraw=True)
        draw_sun(surface, address, world_xy)
        #draw_sun(surface, address, world_xy)
        
        gameDisplay.blit(surface, [x_offset,y_offset])
    last_sunspot = copy.deepcopy(world_xy)
    #Mark lights updated if we just did the lighting per chunk_index
    if rendered_sources != light_sources:
        rendered_sources = copy.deepcopy(light_sources)


def delete_block(pos,block_index,chunk_index):
    global chunk_block_data
    global chunk_surfaces
    global block_size
    block_data = chunk_block_data[chunk_index]
    block_data[block_index[0]][block_index[1]] = 1
    surface = chunk_surfaces[chunk_index]
    pygame.draw.rect(surface, (0,0,0,0), [block_index[0]*block_size, block_index[1]*block_size, block_size, block_size])
    surface.blit(block_images[1], [block_index[0]*block_size,block_index[1]*block_size])
    
    #TODO delete on image and save to file
    #TODO save new data to blocks.txt
    
    print(F"Deleted: {pos} {chunk_index} {block_index}")


#get the [block_type,pos,block_index,chunk_index] at a screen pixal
def get_block_at(xy):
    global world_xy
    global chunk_size
    global block_size
    global chunk_block_data
    
    new_x = xy[0] + world_xy[0]
    new_y = xy[1] - world_xy[1]
    
    #BUG fix avoid chunk edge pixel
    if new_x%chunk_size == 0:
        new_x = new_x + 1
    if new_y%chunk_size == 0:
        new_y = new_y + 1
    
    pos = [new_x, new_y]
    
    
    x_center_chunk = int(world_xy[0]/chunk_size)
    y_center_chunk = int(world_xy[1]/chunk_size)
    #print(f"World center: {x_center_chunk}:{y_center_chunk}")
    
    x_with_offset = int((pos[0])/chunk_size) 
    if pos[0] < 0:
        x_with_offset -= 1
    y_with_offset = int((pos[1])/chunk_size) * -1
    if pos[1] < 0:
        y_with_offset += 1
    
    
    block_x = pos[0] % chunk_size

    #block_x += int(pos[0]%chunk_size)
    block_x = int(block_x / block_size)
    
    block_y = int(pos[1]) % chunk_size
    #block_y += int(pos[1]%chunk_size) * -1
    block_y = abs(int(block_y / block_size))
    
    
    #Add player index to chunk_index TODO
    #print(f"Left: {pos}: Chunk {chunk_index}")
    #print(f"{chunk_size} Block? {block_x} x {block_y}")
    #print(block_data[block_x][block_y])
    chunk_index = f"{x_with_offset}_{y_with_offset}"
    block_index = [block_x,block_y]
    #If chunk is not loaded
    if chunk_index not in chunk_block_data:
        return(-1,pos,block_index, chunk_index)
    block_data = chunk_block_data[chunk_index]
    block_type = block_data[block_x][block_y]
    return_data = [block_type,pos,block_index,chunk_index]
    return(return_data)


def get_world_light_level():
    global world_xy
    global world_light
    global world_light_hight
    
    world_x_with_offset = world_xy[1] - (chunk_size * 3.5)
    min_point = world_light.get_width()//2 * -1
    change = (min_point/world_light_hight) * world_x_with_offset
    #light_level = min_point + (world_xy[1]//100)
    return([0,min_point - change])

def text_objects(text, font, color="Black"):
    textSurface = font.render(text, True, pygame.color.Color(color))
    return textSurface, textSurface.get_rect()

def value_bar(x,y,value, from_right=True, size=10, px_multiplayer=1.6, hide_text=False, unit="%", color="black"):
    x = int(x)
    y = int(y)
    
    size = int(size)
    value_txt = f"{value:.1f}{unit}"
    
    #set bar size to 160 px (1.6 times 100%)
    value *= px_multiplayer
    value = int(value)
    
    if from_right:
        #Grow from right
        x = x - value
    
    pygame.draw.rect(gameDisplay, pygame.color.Color(color),(x,y,value,size))
    if not hide_text:
        smallText = pygame.font.SysFont("comicsansms",15)
        textSurf, textRect = text_objects(value_txt, smallText, color="white")
        textRect.center = ( int(x+int(value/2)), int(y+int(size/2)) )
        gameDisplay.blit(textSurf, textRect)


def main_interface():
    #Globals needed by update_game
    global selected_crop
    global small_text_font
    global background_color
    #global player_image
    global world_xy
    global game_actors
    global game_tick
    global player_life
    global player_power
    global redraw_forced
    global std_out
    global prompt_text
    global view_tty
    global player_speed
    global player_target
    global player_start_pos
    global files_processed
    global pre_game
    global laser_sound
    global hurt_sound
    global main_player
    #global darkness
    global light_sources
    #global darkness_write_buffer
    global world_light
    global NPCs
    global game_time
    global last_game_time
    
    running = True
    
    background_color = pygame.color.Color(25,25,25)
    player_display_pos = [int(display_width/2), int(display_height/2)]

    player_target = world_xy
    max_speed = 3
    player_speed = [0,0]
    
    #player_image = pygame.image.load(f"{script_path}/img/player.png").convert()
    dir_pos = {}
    game_actors = {}
    game_tick = day_frames//4
    redraw_forced = False
    view_tty = False
    pre_game = False
    #laser_sound = pygame.mixer.Sound(f"{script_path}/sound/laser.ogg")
    #laser_sound.set_volume(.2)
    #hurt_sound = pygame.mixer.Sound(f"{script_path}/sound/drip.ogg")
    #hurt_sound.set_volume(1.5)
    #img = pygame.image.load(image_file_to_display)
    #img = pygame.transform.scale(img, (display_width, display_height))
    

    #PWD = get_PWD()
    rendered_path = None

    while running:
        #look for new events
        for event in pygame.event.get():
            #print(event)
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            """
            #Handel mouse press
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_presses = pygame.mouse.get_pressed()
                if mouse_presses[0]:
                    event_pos = pygame.mouse.get_pos()
                    block_type,pos,block_index,chunk_index = get_block_at(event_pos)
                    delete_block(pos,block_index,chunk_index)
                    print(f"Left: {pos}: Chunk {chunk_index}")
                    print(f"{block_index[0]} x {block_index[1]}")
                    print(f"type: {block_type}")
            """
            #Handel Key press
            if not pre_game:
                if event.type == pygame.KEYUP:
                    key_name = event.key
                    if key_name == pygame.K_LEFT or key_name == pygame.K_a:
                        main_player["wanted_speed"][0] = 0
                        main_player["player_is_walking"] = False
                    if key_name == pygame.K_RIGHT or key_name == pygame.K_d:
                        main_player["wanted_speed"][0] = 0
                        main_player["player_is_walking"] = False
                 
            if event.type == pygame.KEYDOWN:
                key = event.unicode
                key_name = event.key
                keys = pygame.key.get_pressed()
                arrow_pressed = False
                
                
                if keys[pygame.K_ESCAPE]:
                    pygame.quit()
                    #End gen_chunk.py
                    os.system("killall -4 gen_chunk.py")
                    quit()
                
                if not pre_game:
                    # Switch inventory
                    if key in main_player["inventory"]:
                        print(f"Switching active item to {key}")
                        main_player["selected_item"] = main_player["inventory"][key][1]
                    # Move left
                    if not main_player["magic_part_casted"]:
                        if key_name == pygame.K_LEFT or key_name == pygame.K_a:
                            main_player["wanted_speed"][0] = main_player["walk_speed"] * -1
                            arrow_pressed = True
                            main_player["image_state"] = "left"
                            main_player["player_is_walking"] = True
                    
                        # Move right
                        if key_name == pygame.K_RIGHT or key_name == pygame.K_d:
                            main_player["wanted_speed"][0] = main_player["walk_speed"]
                            arrow_pressed = True
                            main_player["image_state"] = "right"
                            main_player["player_is_walking"] = True
                    
                        # Jump
                        if main_player["can_jump"]:
                            if key_name == pygame.K_UP or key_name == pygame.K_w or key_name == pygame.K_SPACE:
                                main_player["wanted_speed"][1] = main_player["jump_speed"] 
                                main_player["is_jumping"] = True
                                arrow_pressed = True

                
                    # if left arrow key is pressed
                    #if keys[pygame.K_DOWN] :
                    #    main_player["speed"][1] = max_speed * -1
                    #    arrow_pressed = True
        
        #Reset lighting
        #darkness.fill((0,0,0))
        #print(f"speed: {main_player['speed']}")
        #Update worlds
        #print(f"play xy: {world_xy}")
        needed_chunks = []
        x_center_chunk = int(world_xy[0]/chunk_size)
        y_center_chunk = int(world_xy[1]/chunk_size)
        write_player_data()
        #print(f"Center: {x_center_chunk}{y_center_chunk}")
        for x_around_chunks in range(-2,5):
            for y_around_chunks in range(-3,3):
                this_x = x_center_chunk + x_around_chunks
                this_y = y_center_chunk + y_around_chunks
                needed_chunks.append(f"{this_x}_{this_y}")
        #needed_chunks = ['0_-2', '0_-1', '0_0', '0_1', '1_-2', '1_-1', '1_0', '1_1']
        #needed_chunks = ['0_-1', '0_0', '1_-1', '1_0', '1_1']
        #needed_chunks = ['0_0', '1_0']
        #print(f"Needed chunks: {needed_chunks}")
        #TODO update needed_chunks based on player x y
        for needed_chunk in needed_chunks:
            if needed_chunk not in rendered_chunks:
                #chunk_surfaces[needed_chunk] = pygame.Surface((chunk_size, chunk_size),flags=pygame.SRCALPHA)
                #chunk_surfaces[needed_chunk] = pygame.Surface((chunk_size, #chunk_size),flags=pygame.SRCALPHA)
                #chunk_surfaces[needed_chunk].fill((0,0,0,0))
                #chunk_surfaces[needed_chunk].set_colorkey((255,0,255))
                
                #TODO check if rendered yet
                if chunk_rendered(needed_chunk):
                    data = get_block_data(needed_chunk)
                    chunk_block_data[needed_chunk] = data
                    rendered_chunks.append(needed_chunk)
                    chunk_surfaces[needed_chunk] = load_chunk_image(needed_chunk)
                #data = render_chunk(needed_chunk, chunk_surfaces[needed_chunk])
                #chunk_block_data[needed_chunk] = data
                #rendered_chunks.append(needed_chunk)
        
        #Clean up old data
        for rendered_chunk in rendered_chunks:
            if rendered_chunk not in needed_chunks:
                print(f"del {rendered_chunk}")
                del rendered_chunks[rendered_chunks.index(rendered_chunk)]
                del(chunk_block_data[rendered_chunk])
                del(chunk_surfaces[rendered_chunk])
                if rendered_chunk in light_sources:
                     del(light_sources[rendered_chunk])
                
                #TODO
                #chunk_surfaces[rendered_chunk]
        

        #Draw stuff
        #Sky
        game_time = (255/day_frames) * game_tick
        game_time = abs(game_time - 255//2)
        #if game_time < 30:
        #    print("night")
        #else:
        #    print("day")
        #print(game_time)
        #print(game_time)
        #sky_color = (100,100,200,255-game_time)
        
        gameDisplay.fill((0,0,0))
        gameDisplay.set_alpha(0)
        draw_world()
        last_game_time = copy.deepcopy(game_time)
        
        #Update NPC
        #update_game()
        

        #entities  
        for npc in NPCs:
            npc["update"](npc)
            tile_size = npc["display_size"][0]
            action_offset = npc["image_states"][npc["image_state"]]
            action_offset = [npc["image_frame_offset"] * tile_size * -1,
                             action_offset * tile_size * -1]
            #print(npc["pos"])
            draw_NPC(npc["images"],
                npc["pos"],
                action_offset,
                npc["surface"],
                npc["image_base_path"])
        
        spawn_entities()
        
        #print(world_xy)
        #main_player["image_states"] = {"left":10, "right": 12}
        #main_player["image_state"] = "left"
        #main_player["image_frame_offset"] = 0
        
        

        update_player(main_player)
        tile_size = main_player["display_size"][0]
        action_offset = main_player["image_states"][main_player["image_state"]]
        action_offset = [main_player["image_frame_offset"] * tile_size * -1,
                         action_offset * tile_size * -1]
        
        
        draw_NPC(main_player["images"],
                main_player["offset"],
                action_offset,
                main_player["surface"],
                main_player["image_base_path"])
        
        

        #Draw interface stuff
        value_bar(display_width - 7,5,main_player["magic"], color="blue")
        value_bar(display_width - 7,15,main_player["strength"])
        value_bar(7,15,main_player["life"], color="red", from_right=False)
        
        draw_inventory()

                
        #World lighting
        #darkness.blit(world_light, get_world_light_level())
        #print(f"Light level: {get_world_light_level()}")
        #Object Lighting
        #draw_lighting()
        #darkness_write_buffer.fill((0,0,0))
        #darkness_write_buffer.blit(darkness, [0,0])
        #gameDisplay.blit(darkness, [0,0], special_flags=pygame.BLEND_ADD)
        
            
        
        #draw_img(player_image, player_display_pos)

        
        #print(f"time: {sky_darkness}")
        #Draw NPC
        #draw_npc()
        if game_tick > day_frames:
            game_tick = 2
        else:
            game_tick = game_tick + 1
        
        if fps > clock.get_fps() + 3:
            print(f"Warning, low fps: {clock.get_fps()}")
        #print("Tick")
        pygame.display.update()
        clock.tick(fps)


script_path = os.path.dirname(os.path.realpath(__file__))
inventory_images = {}
#Load into this namespace all needed spells
for entry in os.scandir('spells'):
    if entry.is_file():
        path = f"{script_path}/spells/{entry.name}"
        print(path)
        with open(path) as fh:
            python_script = fh.readlines()
        python_script = "\n".join(python_script)
        exec(python_script)


#Load into this namespace all needed items
for entry in os.scandir('items'):
    if entry.is_file():
        path = f"{script_path}/items/{entry.name}"
        print(path)
        with open(path) as fh:
            python_script = fh.readlines()
        python_script = "\n".join(python_script)
        exec(python_script)


#Load into this namespace all needed entities
for entry in os.scandir('entities'):
    if entry.is_file():
        path = f"{script_path}/entities/{entry.name}"
        print(path)
        with open(path) as fh:
            python_script = fh.readlines()
        python_script = "\n".join(python_script)
        exec(python_script)


#Globals not needing set by init
spawn_rates = {2: [.005, init_skeleton]}
save_data = os.path.expanduser("~/.cartesia")
if not os.path.isdir(save_data):
    os.mkdir(save_data)
player_datafile = os.path.expanduser(f"{save_data}/player")

chunk_block_data = {}
chunk_surfaces = {}
rendered_chunks = []
block_size = 16
chunk_blocks = 32
chunk_size = block_size * chunk_blocks
gravity = -1.5
day_len = 7 #Min
#day_len = .5

music = {"happy": f"{script_path}/music/Komiku - Hélice's Theme.mp3"}



def init(SEED, display_scale=1, FULLSCREEN=False):
    global display_info
    global display_width
    global display_height
    global fount_size
    global gameDisplay
    global fps
    global clock
    global main_player
    global DEBUG
    global small_text_font
    global text_font
    global loaded_images
    global dot
    global light_source
    global rendered_sources
    #global darkness
    global light_sources
    #global darkness_write_buffer
    global world_light
    global world_light_hight
    global sounds
    global NPCs
    global world_xy
    global last_sunspot
    global day_frames
    global sun
    global game_time
    global last_game_time
    global world_seed
    global WORLD_DIR
    global block_images
    global blank
    global selected_item_bg
    
    DEBUG = True
    world_seed = SEED
    #gen_chunk.set_seed(SEED)
    
    fps = 30
    WORLD_DIR = f"{save_data}/world/{SEED}"
    #Test at hight FPS
    #if DEBUG:
    #    fps = 60
    day_frames = fps * 60 * day_len
    game_time = (255/day_frames) * (day_frames//2)
    last_game_time = copy.deepcopy(game_time)
    
    pygame.init()
    pygame.display.init()
    display_info = pygame.display.Info()

    #display_width = int(1440/2)
    #display_height = int(720/2)
    loaded_images = {}
    player_start_pos = [0,0]
    world_xy = copy.deepcopy(player_start_pos)
    last_sunspot = copy.deepcopy(world_xy)
    display_width = int(display_info.current_w/display_scale)
    display_height = int(display_info.current_h/display_scale)
    clock = pygame.time.Clock()
    fount_size = int(display_width/80)
    fount_size = fount_size * 4
    text_font = pygame.font.SysFont("comicsansms",fount_size)
    small_text_font = pygame.font.SysFont("comicsansms",12)
    sky_color = (0,175,255,1)
    #Lighting stuff
    dark_block = pygame.Surface((16, 16),flags=pygame.SRCALPHA)
    dark_block.fill((0,0,0,254))
    blank = pygame.Surface((32, 32),flags=pygame.SRCALPHA)
    blank.fill((100,100,100,120))
    
    selected_item_bg = pygame.Surface((32, 32),flags=pygame.SRCALPHA)
    selected_item_bg.fill((0,0,200,120))
    
    #darkness = pygame.Surface((display_width, display_height))
    #darkness.fill((0,0,0))
    #darkness.set_colorkey((255,0,255))
    #darkness.set_colorkey((0,0,0))
    light_sources = {}
    rendered_sources = {}
    
    #darkness_write_buffer = pygame.Surface((display_width, display_height))
    #darkness_write_buffer.fill((0,0,0))
    #darkness_write_buffer.set_colorkey((255,0,255))

    if FULLSCREEN:
        gameDisplay = pygame.display.set_mode((display_width,display_height), pygame.FULLSCREEN)
    else:
        gameDisplay = pygame.display.set_mode((display_width,display_height))
    gameDisplay.set_colorkey((255,0,255))
    
    
    
    #Music:
    pygame.mixer.music.load(music["happy"])
    pygame.mixer.music.play(-1)
    sounds = {"magic_spell": pygame.mixer.Sound(f"{script_path}/sounds/80-CC0-RPG-SFX/creature_die_01.ogg"),
              "skeleton_hurt": pygame.mixer.Sound(f"{script_path}/sounds/80-CC0-RPG-SFX/creature_misc_03.ogg"),
              "player_hurt": pygame.mixer.Sound(f"{script_path}/sounds/80-CC0-RPG-SFX/creature_hurt_02.ogg")}

    
    #light_source = pygame.image.load(f"{script_path}/img/light.png").convert()
    #light_source.set_colorkey((0,0,0))
    
    
    sun = pygame.transform.scale(pygame.image.load(f"{script_path}/img/sun.png").convert_alpha(), [display_width, display_height])
    sun.set_colorkey((0,0,0))
    #sun = pygame.Surface((200, 200),flags=pygame.SRCALPHA)
    #sun.fill((0,0,0,0))
    #pygame.draw.circle(sun, (0,0,0,255//2), (100, 100), 100)
    light_source = pygame.image.load(f"{script_path}/img/light.png").convert_alpha()
    #sun = pygame.image.load(f"{script_path}/img/light.png").convert_alpha()
    
    
    #Would light
    world_light = pygame.image.load(f"{script_path}/img/world_light.png").convert()
    world_light.set_colorkey((0,0,0))
    world_light_hight = 1024
    
    
    # BUG this is a copy of blocks.py from setup block texterus down
    ######################
    #setup block texterus#
    ######################
    #Lighting stuff
    dark_block = pygame.Surface((16, 16),flags=pygame.SRCALPHA)
    dark_block.fill((0,0,0,254))


    block_images = {}
    texterus_path = f"{script_path}/img/pixelperfection"

    #Sky
    sky_color = (0,175,255,1)
    block_images[1] = pygame.Surface((16, 16), flags=pygame.SRCALPHA)
    block_images[1].fill(sky_color)
    #light_source.fill((0,0,0,0))
    #Dirt
    block_images[3] = pygame.image.load(f"{texterus_path}/default/default_dirt.png").convert_alpha()
    block_images[3].blit(dark_block, [0,0], special_flags=pygame.BLEND_RGBA_SUB)
    #Grass
    grass_top = pygame.image.load(f"{texterus_path}/default/default_grass_side.png").convert_alpha()
    block_images[2] = pygame.image.load(f"{texterus_path}/default/default_dirt.png").convert_alpha()
    block_images[2].blit(grass_top, [0, 0])
    block_images[2].blit(dark_block, [0,0], special_flags=pygame.BLEND_RGBA_SUB)

    #Test grass
    #block_images[2] = pygame.Surface((16, 16),flags=pygame.SRCALPHA)
    #block_images[2].fill((96,123,123))
    #block_images[2].blit(dark_block, [0,0], special_flags=pygame.BLEND_RGBA_SUB)

    #Stone
    block_images[4] = pygame.image.load(f"{texterus_path}/default/default_stone.png").convert_alpha()
    block_images[4].blit(dark_block, [0,0], special_flags=pygame.BLEND_RGBA_SUB)

    #default_torch
    tmp_toruch = pygame.image.load(f"{texterus_path}/default/default_torch.png").convert_alpha()
    block_images[5] = pygame.Surface((16, 16),flags=pygame.SRCALPHA)
    block_images[5].fill(sky_color)
    block_images[5].blit(tmp_toruch, [0,0])
    
    
    dot = pygame.Surface((20, 20),flags=pygame.SRCALPHA)
    dot.fill((0,0,0,0))
    pygame.draw.circle(dot, (255,0,255,255), (10, 10), 10)
    
    #entities
    world_zero_offset = [(display_width//2),(display_height//2)]
    main_player = init_player(world_zero_offset)
    NPCs = []
    #Test
    #NPCs.append(init_skeleton([300,300]))
    
    main_interface()
