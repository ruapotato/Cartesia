#!/usr/bin/python3

#AGPL by David Hamner 2023
#Setup: sudo pip3 install perlin_noise


import gui
import os

SEED = 1564654
script_path = os.path.dirname(os.path.realpath(__file__))
#os.system("killall -4 gen_chunk.py")
os.system(f"{script_path}/gen_chunk.py &")
#import matplotlib.pyplot as plt
gui.init(SEED, display_scale=1.5, FULLSCREEN=False)
#gui.init(SEED, display_scale=1.5, FULLSCREEN=True)

"""
SEED = 123456
gen_chunk.set_seed(SEED)
test = gen_chunk.make_and_dress(0,0,size=10)
print(test)


PLAYER_POS = [0,0]

chunks_loaded = {}

def update_chunks():
    global PLAYER_POS
    render_pos = PLAYER_POS # my need a divider
    
    for x in range(render_pos[0]-1,render_pos[0]+1):
        for y in range(render_pos[1]-1,render_pos[1]+1):
            blocks = gen_chunk.get_chunk(x,y)
            print(blocks)


#TODO keep running in bg
update_chunks()

gui.main_interface()
#test = gen_chunk.make_and_dress(10,0,size=10)
#print(test)
#test = reversed(list(test))
#for row in test:
#    for block in row:
#        print(block, end="")
#    print()
"""
"""
pic = []
for y in range(-250,250):
    row = []
    for x in range(-500,500):
        val, is_land = gen_chunk.at_pos(x,y)
        if is_land:
            row.append(1)
        else:
            row.append(0)
    pic.append(row)
pic.reverse()
plt.imshow(pic, cmap='gray')
plt.show()
"""
