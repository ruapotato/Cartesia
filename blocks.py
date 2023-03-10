import pygame
import os

#BUG Any changes to this file need made to gui.py init
# copy from setup block texterus down


os.environ["SDL_VIDEODRIVER"] = "dummy"
pygame.display.init()
pygame.font.init()
screen = pygame.display.set_mode((1,1),pygame.NOFRAME, 32)
#pygame.display.set_mode((640,300), pygame.FULLSCREEN | pygame.OPENGL | pygame.NOFRAME, 32)
script_path = os.path.dirname(os.path.realpath(__file__))


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
