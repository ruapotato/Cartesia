#!/usr/bin/python3

#AGPL by David Hamner 2023

from perlin_noise import PerlinNoise
import numpy as np
import os
import yaml
import time
from datetime import datetime


import blocks
pygame = blocks.pygame
fount_size = int(1080/80)
fount_size = fount_size * 4
text_font = pygame.font.SysFont("comicsansms",fount_size)
script_path = os.path.dirname(os.path.realpath(__file__))

save_data = os.path.expanduser("~/.cartesia/")

SEED = 0
block_size = 16
chunk_blocks = 32
chunk_size = block_size * chunk_blocks

rendered_chunks = []
chunk_block_data = {}
chunk_surfaces = {}

DEBUG = True

def set_seed(New_seed):
    global SEED
    global ground_level_noise
    global ground_level_crazyness
    global WORLD_DIR
    SEED = New_seed
    ground_level_noise = PerlinNoise(octaves=3, seed=SEED)
    ground_level_crazyness = PerlinNoise(octaves=8, seed=SEED)
    WORLD_DIR = f"{save_data}/world/{SEED}"

#Gen_block at a gen pos with a given seed
def solid_at_pos(x,y):
    global ground_level_noise
    global SEED
    global ground_level_crazyness
    ground_level = 0
    
    #noise2 = PerlinNoise(octaves=6, seed=SEED)
    #noise3 = PerlinNoise(octaves=12, seed=SEED)
    #noise4 = PerlinNoise(octaves=24, seed=SEED)
    ground_crazyness = ground_level_noise([x/1000, y/1000])
    ground_crazyness = ground_crazyness + ground_crazyness
    hills = ground_crazyness * 100
    #print(ground_crazyness)
    ground_alt = (ground_level_noise([x/100, y/100]) * 100) - 10
    ground_alt = ground_alt * ground_crazyness
    #print(ground_alt)
    if y < ground_level + ground_alt + hills:
        return(True)
    else:
        return(False)
    
    #is_air = y > ground_level + ground_alt
    #return(ground_alt, is_air)

def make_and_dress(x_zero,y_zero,size=32):
    blocks = []
    is_solid = []
    for y in range(y_zero,y_zero+size):
        row = []
        for x in range(x_zero,x_zero+size):
            is_land = solid_at_pos(x,y)
            if is_land:
                row.append(1)
            else:
                row.append(0)
        is_solid.append(row)
    
    
    
    
    #
    transposed = np.array(is_solid).T
    flipped = np.flip(transposed)
    for col in flipped:
        block_col = []
        ground_depth = 4
        print(f"INFO: {col}")
        for a_solid in col:
            
            if not a_solid:
               block_col.append(1) # Air
               ground_depth = -1
            elif ground_depth < 0:
                block_col.append(2) # Grass
                ground_depth = ground_depth + 1
            elif ground_depth >= 0 and ground_depth < 3:
                block_col.append(3) # dirt
                ground_depth = ground_depth + 1
            else:
                block_col.append(4) # stone
                ground_depth = ground_depth + 1
        blocks.append(block_col)
        
    #blocks = np.array(blocks)
    #blocks = np.flip(blocks)
    blocks = np.flip(blocks, 0)
    return(blocks)


def get_chunk(x_index,y_index):
    global WORLD_DIR
    x_zero = x_index * 32
    y_zero = y_index * 32
    chunk_dir = f"{WORLD_DIR}/{x_index}_{y_index}/"
    if not os.path.isdir(chunk_dir):
        print(f"Need to gen stuff {x_index} {y_index}")
        os.makedirs(chunk_dir, exist_ok=True)
        block_file = f"{chunk_dir}blocks.txt"
        new_data = make_and_dress(x_zero,y_zero)
        np.savetxt(block_file, new_data)
        #with open(block_file, "w+") as fh:
         #   fh.write(str(list(new_data)))
        return(new_data)
    else:
        print(f"{chunk_dir} already genned")
        block_file = f"{chunk_dir}blocks.txt"
        old_data = np.loadtxt(block_file)
        return(old_data)


def render_chunk(address_txt, surface):
    global small_text_font
    global light_sources
    print("Rendering {address_txt}")
    address = address_txt.split("_")
    address = [int(address[0]), int(address[1])]
    data = get_chunk(address[0],address[1])
    for y in range(0, chunk_blocks):
        for x in range(0, chunk_blocks):
            draw_x = x * block_size
            draw_y = y * block_size
            block_index = data[x][y]
            if block_index in blocks.block_images:
                #if block_index == 1:
                #    continue
                img = blocks.block_images[block_index]
                
                #5 = torch 
                # 2 = grass above -3 TODO change to top level air block
                #if block_index == 5 or (block_index == 2 and address[1] > -3):
                if block_index == 5:
                    where = [address,[draw_x, draw_y]]
                    if address_txt in light_sources:
                        light_sources[address_txt].append(where)
                    else:
                        light_sources[address_txt] = [where]
                #new_pos = [pos[0] - int(img.get_width()/2), pos[1] - int(img.get_height()/2)]
                surface.blit(img, [draw_x, draw_y])
                """
                if DEBUG:
                    text_info = f"{x}:{y}"
                    text_info_serface = small_text_font.render(text_info, False, (0, 0, 0))
                    surface.blit(text_info_serface, [draw_x, draw_y])
                """
    if DEBUG:
        text_info_serface = text_font.render(address_txt, False, (0, 0, 0))
        surface.blit(text_info_serface, [20, 20])
    
    image_file = f"{WORLD_DIR}/{address_txt}/blocks.tga"
    print("hi")


    pygame.image.save(surface, image_file)
    return(data)


player_datafile = os.path.expanduser("~/.cartesia/player")
def get_player_data():
    if not os.path.isfile(player_datafile):
        #print("No player data")
        return None
    with open(player_datafile) as fh:
        player_data = yaml.safe_load(fh)
    
    return(player_data)

fps_max = 1/30
while True:
    player_info = get_player_data()
    if player_info == None:
        print("No player data, yet")
        time.sleep(fps_max)
        continue
    #print(player_info)
    age = datetime.now() - datetime.strptime(player_info['time'], "%y-%m-%d %H:%M:%S.%f")
    #print(age.seconds)
    if age.seconds > 2 and age.seconds < 3:
        #Main program exited
        print("Main program missing!")
        exit()
    if player_info["seed"] != SEED:
        set_seed(player_info["seed"])
        SEED = player_info["seed"]
        print(f"Set new seed: {SEED}")
    time.sleep(fps_max)
    
    
    x_center_chunk = int(player_info["pos"][0]/chunk_size)
    y_center_chunk = int(player_info["pos"][1]/chunk_size)
    needed_chunks = []


    #print(f"Center: {x_center_chunk}{y_center_chunk}")
    for x_around_chunks in range(-1,5):
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
            chunk_surfaces[needed_chunk] = pygame.Surface((chunk_size, chunk_size),flags=pygame.SRCALPHA)
            chunk_surfaces[needed_chunk].fill((0,0,0,0))
            #chunk_surfaces[needed_chunk].set_colorkey((255,0,255))
            
            #TODO check if rendered yet
            data = render_chunk(needed_chunk, chunk_surfaces[needed_chunk])
            chunk_block_data[needed_chunk] = data
            rendered_chunks.append(needed_chunk)
