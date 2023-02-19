#!/usr/bin/python3

#AGPL by David Hamner 2023

from perlin_noise import PerlinNoise
import numpy as np
import os
script_path = os.path.dirname(os.path.realpath(__file__))
WORLD_DIR = f"{script_path}/world/"

SEED = 0

def set_seed(New_seed):
    global SEED
    global ground_level_noise
    global ground_level_crazyness
    SEED = New_seed
    ground_level_noise = PerlinNoise(octaves=3, seed=SEED)
    ground_level_crazyness = PerlinNoise(octaves=8, seed=SEED)

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
    chunk_dir = f"{WORLD_DIR}{x_index}_{y_index}/"
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
    
