














# coding: utf-8
import sys
import pygame
from pygame.locals import *
import argparse

from chip8 import chip8













from chip8 import  chip8
def main():

    emulator=chip8()
    emulator.load_rom('/home/misha/Desktop/chip8/PONG2')
    emulator.run_cycle()




if __name__ == "__main__":
    main()


