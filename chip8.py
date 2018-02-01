import random
import time

import pygame
from pygame.rect import Rect


class chip8():
    ram = [0] * 4096  # ram for chip8
    rom_load_addres = 0x200  # chip-8 program start from that adress

    v_registers = [0] * 16 # v registers


    i_register = 0  # memory register,stores memory adress,last 12 bit used

    delay_register = 0
    sound_register = 0  # When these registers are non-zero, they are automatically decremented at a rate of 60Hz

    pc_register = 0  # stores currently executing adress

    stack = [0] * 16  # used to store the address that the interpreter shoud return to when finished with a subroutine.
    # Chip-8 allows for up to 16 levels of nested subroutines.(16 nested returns)


    draw_flag = False  # True when want to change screen

    keyboard = [0]*16

    # chip-8 keyboard layout
    # 1, 2, 3, 0xC,
    # 4, 5, 6, 0xD,
    # 7, 8, 9, 0xE,
    # 0xA, 0, 0xB, 0xF


    display = [0] * 64 * 32  # 64x32-pixel monochrome display

    ram[0x0: 0x50] = [
        0xF0, 0x90, 0x90, 0x90, 0xF0,
        0x20, 0x60, 0x20, 0x20, 0x70,
        0xF0, 0x10, 0xF0, 0x80, 0xF0,
        0xF0, 0x10, 0xF0, 0x10, 0xF0,
        0x90, 0x90, 0xF0, 0x10, 0x10,
        0xF0, 0x80, 0xF0, 0x10, 0xF0,
        0xF0, 0x80, 0xF0, 0x90, 0xF0,
        0xF0, 0x10, 0x20, 0x40, 0x40,
        0xF0, 0x90, 0xF0, 0x90, 0xF0,
        0xF0, 0x90, 0xF0, 0x10, 0xF0,
        0xF0, 0x90, 0xF0, 0x90, 0x90,
        0xE0, 0x90, 0xE0, 0x90, 0xE0,
        0xF0, 0x80, 0x80, 0x80, 0xF0,
        0xE0, 0x90, 0x90, 0x90, 0xE0,
        0xF0, 0x80, 0xF0, 0x80, 0xF0,
        0xF0, 0x80, 0xF0, 0x80, 0x80
    ]

    def del_sound_timer(self):
        if self.delay_register: self.delay_register -= 1
        if self.sound_register:
            # start buzzing
            self.sound_register -= 1
        else:
            pass
            #stop buzzing


        # time.sleep(
        #     0.016)  # 60hz 1 decrement in 16 microseconds (1000/60)


    def load_rom(self, path):

        f = open(path, 'rb')
        rom_bytes = f.read()
        f.close()
        rom_size = len(rom_bytes)
        for i in range(rom_size):
            self.ram[i + self.rom_load_addres] = rom_bytes[i]




    def exop(self,opcode):



        f = (self.opcode & 0xF000) >> 12

        try:
            if f == 8 or f == 0 or f == 14:

                l = self.opcode & 0x000F
                eval('self._'+hex(f)[2:].upper() + hex(l)[2:].upper() + '()')
            elif f == 15:
                l = self.opcode & 0x000F
                ll = (self.opcode & 0x00F0) >> 4

                eval('self._'+hex(f)[2:].upper() + hex(ll)[2:].upper() + hex(l)[2:].upper() + '()')


            else:
                eval('self._'+hex(f)[2:].upper() + '()')
        except Exception as e:
                print('error in  :'+hex(self.opcode)+' '+str(e))

        # print('executing '+hex(opcode)+' '+str(self.v_registers)+' ram '+str(self.ram[754 :757])+ ' ireg:'+str(self.i_register) )


    def run_cycle(self):
        self.pc_register = self.rom_load_addres
        screen = pygame.display.set_mode((640, 320))

        background = pygame.Surface(screen.get_size())
        background = background.convert()

        while True:
            self.del_sound_timer()

            # get opcode
            self.opcode = self.ram[self.pc_register] << 8 | self.ram[self.pc_register + 1]

            self.pc_register = (self.pc_register + 2)


            self.exop(self.opcode)
            # incress current executing adress

            events = pygame.event.get()
            for event in events:
                if event.type == pygame.KEYDOWN:
                    print(event.key)
                    if event.key == pygame.K_LEFT:
                        self.keyboard[12]=1
                    if event.key == pygame.K_LEFT:
                        self.keyboard[1]=1
                if event.type==pygame.KEYUP:
                    print(event.key)
                    if event.key == pygame.K_LEFT:
                        self.keyboard[12]=0
                    if event.key == pygame.K_LEFT:
                        self.keyboard[1]=0



            background.fill((0, 0, 0))
            for x in range(64):
                for y in range(32):
                    if self.get(x, y):
                        pixel = Rect(x * 10, y * 10, 10, 10)
                        pygame.draw.rect(background, (255, 255, 255), pixel)

            screen.blit(background, background.get_rect())

            pygame.display.update()






    # exevuting operations

    def _00(self):
        # 00E0 - CLS Clear the display.
        self.display = [0] * 64 * 32
        self.draw_flag = True

    def _0E(self):
        '''
        00EE - RET
        Return from a subroutine.
        The interpreter sets the program counter to the address at the top of the stack, then subtracts 1 from the stack pointer.'''

        self.pc_register = self.stack.pop()


    def _1(self):
        ''' 1nnn - JP addr
        jump to location nnn.
        The interpreter sets the program counter to nnn.'''

        self.pc_register = self.opcode & 0x0FFF

    def _2(self):
        '''2nnn - CALL addr
        Call subroutine at nnn.
        The interpreter increments the stack pointer, then puts the current PC on the top of the stack. The PC is then set to nnn.
        '''


        self.stack.append(self.pc_register)
        self.pc_register = self.opcode & 0x0FFF

    def _3(self):
        '''3xkk - SE Vx, byte
            Skip next instruction if Vx = kk.
            The interpreter compares register Vx to kk, and if they are equal, increments the program counter by 2.
        '''

        x=(self.opcode & 0x0F00)>>8
        kk=self.opcode & 0x00FF

        if self.v_registers[x]==kk: self.pc_register+=2

    def _4(self):

        '''4xkk - SNE Vx, byte
        Skip next instruction if Vx != kk.
        The interpreter compares register Vx to kk, and if they are not equal, increments the program counter by 2.'''
        x = (self.opcode & 0x0F00)>>8
        kk = self.opcode & 0x00FF
        if self.v_registers[x] != kk: self.pc_register += 2

    def _5(self):
        '''5xy0 - SE Vx, Vy
        Skip next instruction if Vx = Vy.
        The interpreter compares register Vx to register Vy, and if they are equal, increments the program counter by 2.
        '''
        x = (self.opcode & 0x0F00)>>8
        y = (self.opcode & 0x00F0)>>4
        if self.v_registers[x]==self.v_registers[y]:self.pc_register+=2

    def _6(self):
        '''6xkk - LD Vx, byte
        Set Vx = kk.
        The interpreter puts the value kk into register Vx.'''


        x = (self.opcode & 0x0F00) >> 8
        kk=self.opcode & 0x00FF

        self.v_registers[x]=kk

    def _7(self):
        '''
        7xkk - ADD Vx, byte
        Set Vx = Vx + kk.
        Adds the value kk to the value of register Vx, then stores the result in Vx.
        '''
        x = (self.opcode & 0x0F00) >> 8
        kk = self.opcode & 0x00FF
        self.v_registers[x] =  self.v_registers[x] + kk

    def _80(self):
        '''8xy0 - LD Vx, Vy
        Set Vx = Vy.
        Stores the value of register Vy in register Vx.'''

        x = (self.opcode & 0x0F00) >> 8
        y = (self.opcode & 0x00F0)>>4
        self.v_registers[x]=self.v_registers[y]
        self.v_registers[x] &= 0xff

    def _81(self):
        '''8xy1 - OR Vx, Vy
        Set Vx = Vx OR Vy.
        Performs a bitwise OR on the values of Vx and Vy, then stores the result in Vx.
        A bitwise OR compares the corrseponding bits from two values, and if either bit is 1, then the same bit in the result is also 1. Otherwise, it is 0.
        '''

        x = (self.opcode & 0x0F00) >> 8
        y = (self.opcode & 0x00F0) >> 4

        self.v_registers[x]=self.v_registers[x] | self.v_registers[y]
        self.v_registers[x] &= 0xff


    def _82(self):
        '''8xy2 - AND Vx, Vy
        Set Vx = Vx AND Vy.
        Performs a bitwise AND on the values of Vx and Vy, then stores the result in Vx.
        A bitwise AND compares the corrseponding bits from two values, and if both bits are 1, then the same bit in the result is also 1. Otherwise, it is 0.
        '''

        x = (self.opcode & 0x0F00) >> 8
        y = (self.opcode & 0x00F0) >> 4

        self.v_registers[x] = self.v_registers[x] & self.v_registers[y]
        self.v_registers[x] &= 0xff

    def _83(self):
        '''8xy3 - XOR Vx, Vy
        Set Vx = Vx XOR Vy.
        Performs a bitwise exclusive OR on the values of Vx and Vy, then stores the result in Vx.
        An exclusive OR compares the corrseponding bits from two values, and if the bits are not both the same,
        then the corresponding bit in the result is set to 1. Otherwise, it is 0.
        '''

        x = (self.opcode & 0x0F00) >> 8
        y = (self.opcode & 0x00F0) >> 4

        self.v_registers[x] = self.v_registers[x] ^ self.v_registers[y]
        self.v_registers[x] &= 0xff


    def _84(self):
        '''8xy4 - ADD Vx, Vy
        Set Vx = Vx + Vy, set VF = carry.
        The values of Vx and Vy are added together. If the result is greater than 8 bits (i.e., > 255,)
        VF is set to 1, otherwise 0. Only the lowest 8 bits of the result are kept, and stored in Vx.
        '''

        x = (self.opcode & 0x0F00) >> 8
        y = (self.opcode & 0x00F0) >> 4
        if self.v_registers[x] + self.v_registers[y]>255:
            self.v_registers[15]=1
        else:
            self.v_registers[15]=0
        self.v_registers[x]=(self.v_registers[x]+self.v_registers[y])
        self.v_registers[x] &= 0xff


    def _85(self):
        '''8xy5 - SUB Vx, Vy
        Set Vx = Vx - Vy, set VF = NOT borrow.
        If Vx > Vy, then VF is set to 1, otherwise 0. Then Vy is subtracted from Vx, and the results stored in Vx.
        '''

        x = (self.opcode & 0x0F00) >> 8
        y = (self.opcode & 0x00F0) >> 4

        if self.v_registers[x] > self.v_registers[y]:
            self.v_registers[15]=1
        else:
            self.v_registers[15]=0

        self.v_registers[x] = (self.v_registers[x] - self.v_registers[y])
        self.v_registers[x] &= 0xff

    def _86(self):
        '''8xy6 - SHR Vx {, Vy} Set Vx = Vx SHR 1.
        If the least-significant bit of Vx is 1, then VF is set to 1, otherwise 0. Then Vx is divided by 2.
        '''

        x = (self.opcode & 0x0F00) >> 8
        y = (self.opcode & 0x00F0) >> 4


        self.v_registers[15] = self.v_registers[x] & 1

        self.v_registers[x] = self.v_registers[y] >> 1
        self.v_registers[x] &= 0xff



    def _87(self):
        '''8xy7 - SUBN Vx, Vy
        Set Vx = Vy - Vx, set VF = NOT borrow.
        If Vy > Vx, then VF is set to 1, otherwise 0. Then Vx is subtracted from Vy, and the results stored in Vx.
        '''

        x = (self.opcode & 0x0F00) >> 8
        y = (self.opcode & 0x00F0) >> 4

        if self.v_registers[y]>self.v_registers[x]:
            self.v_registers[15]=1
        else:
            self.v_registers[15]=0

        self.v_registers[x]=self.v_registers[y] - self.v_registers[x]
        self.v_registers[x] &= 0xff
    def _8E(self):
        '''8xyE - SHL Vx {, Vy}
        Set Vx = Vx SHL 1.
        If the most-significant bit of Vx is 1, then VF is set to 1, otherwise to 0. Then Vx is multiplied by 2.
        '''

        x = (self.opcode & 0x0F00) >> 8
        y = (self.opcode & 0x00F0) >> 4


        self.v_registers[15] = self.v_registers[y] >> 7

        self.v_registers[x] = (self.v_registers[y] << 1)
        self.v_registers[x] &= 0xff

    def _9(self):
        '''9xy0 - SNE Vx, Vy
        Skip next instruction if Vx != Vy.
        The values of Vx and Vy are compared, and if they are not equal, the program counter is increased by 2.'''

        x = (self.opcode & 0x0F00) >> 8
        y = (self.opcode & 0x00F0) >> 4


        if x!=y:
            self.pc_register+=2


    def _A(self):
        '''Annn - LD I, addr
        Set I = nnn.
        The value of register I is set to nnn.'''

        nnn=self.opcode & 0x0FFF
        self.i_register=nnn


    def _B(self):
        '''Bnnn - JP V0, addr
        Jump to location nnn + V0.
        The program counter is set to nnn plus the value of V0.'''

        nnn = self.opcode & 0x0FFF

        self.pc_register=nnn+self.v_registers[0]

    def _C(self):
        '''Cxkk - RND Vx, byte
        Set Vx = random byte AND kk.
        The interpreter generates a random number from 0 to 255,
        which is then ANDed with the value kk.
        The results are stored in Vx. See instruction 8xy2 for more information on AND.'''

        x = (self.opcode & 0x0F00)>>8
        kk=self.opcode & 0x00FF
        rand=random.randint(0, 255)
        self.v_registers[x]=kk & rand
        self.v_registers[x] &= 0xff



    def _index(self, x, y):
        return (y * 64) + x

    def get(self, x, y):
        return self.display[self._index(x, y)]


    def _D(self):
        '''Dxyn - DRW Vx, Vy, nibble
        Display n-byte sprite starting at memory location I at (Vx, Vy), set VF = collision.

        The interpreter reads n bytes from memory, starting at the address stored in I.
         These bytes are then displayed as sprites on screen at coordinates (Vx, Vy).
         Sprites are XORed onto the existing screen.
         If this causes any pixels to be erased, VF is set to 1, otherwise it is set to 0.
         If the sprite is positioned so part of it is outside the coordinates of the display, it wraps around to the opposite side of the screen.
         See instruction 8xy3 for more information on XOR, and section 2.4, Display, for more information on the Chip-8 screen and sprites.'''


        self.draw_flag = True

        x = self.v_registers[(self.opcode & 0x0F00) >> 8]
        y = self.v_registers[(self.opcode & 0x00F0) >> 4]
        n = self.opcode & 0x000F
        sprites = self.ram[self.i_register:self.i_register + n]  # 8 bit width ,len(sprites) height

        self.v_registers[15]=0

        for i, sprite in enumerate(sprites):

            pixels = [int(k) for k in bin(sprite)[2:]]

            pll=len(pixels)
            if pll<8:
                for aa in range(8-pll):pixels.insert(0,0)


            for pl in range(pll):

                  if x + pl>=64 or y+i>=32:
                      continue



                  old=self.display[x + (y * 64) + pl]


                  self.display[x + (y * 64) + pl] = self.display[x + (y * 64) + pl] ^ pixels[pl]
                  if old==1 and self.display[x + (y * 64) + pl]==0:
                      self.v_registers[0xF] |= 1
                  else:
                      self.v_registers[15] |= 0

            y +=1
        #     if self.v_registers[15]:
        #         print('*************8crash')


    def _EE(self):
        '''

        Ex9E - SKP Vx
        Skip next instruction if key with the value of Vx is pressed.
        Checks the keyboard, and if the key corresponding to the value of Vx is
        currently in the down position, PC is increased by 2.'''

        x = (self.opcode & 0x0F00)>>8

        if self.keyboard[self.v_registers[x]&0xf]==1:
            self.pc_register+=2


    def _E1(self):
        '''ExA1 - SKNP Vx
        Skip next instruction if key with the value of Vx is not pressed.
        Checks the keyboard, and
        if the key corresponding to the value of Vx is currently in the up position,
        PC is increased by 2.
        '''

        x = (self.opcode & 0x0F00) >> 8

        if self.keyboard[self.v_registers[x]&0xf]==0:

            self.pc_register += 2





    def _F07(self):
        '''
        Fx07 - LD Vx, DT
        Set Vx = delay timer value.
        The value of DT is placed into Vx'''
        x = (self.opcode & 0x0F00) >> 8

        self.v_registers[x]=self.delay_register

    def _F0A(self):

        print('dgdgdggdgdg')
        '''Fx0A - LD Vx, K
        Wait for a key press, store the value of the key in Vx.
        All execution stops until a key is pressed, then the value of that key is stored in Vx.'''
        x = (self.opcode & 0x0F00) >> 8
        cur_state=self.keyboard
        while True:
            for i in self.keyboard:
                if i!=0 and not i in cur_state:
                    self.v_registers[x]=i
                    break

    def _F15(self):
        '''
        Set delay timer = Vx.

        DT is set equal to the value of Vx.
        '''

        x = (self.opcode & 0x0F00) >> 8
        self.delay_register=self.v_registers[x]


    def _F18(self):

        '''
        Set sound timer = Vx.

        ST is set equal to the value of Vx.

        '''

        x = (self.opcode & 0x0F00) >> 8
        self.sound_register = self.v_registers[x]


    def _F1E(self):
        '''
        Set I = I + Vx.

        The values of I and Vx are added, and the results are stored in I.'''

        x = (self.opcode & 0x0F00) >> 8
        self.i_register=self.i_register+self.v_registers[x]


    def _F29(self):

        '''

        Set I = location of sprite for digit Vx.

        The value of I is set to the location for the hexadecimal sprite corresponding to the value of Vx.
        See section 2.4, Display, for more information on the Chip-8 hexadecimal font.

        '''
        x = (self.opcode & 0x0F00) >> 8




        self.i_register= self.v_registers[x]*5



    def _F33(self):

        '''Store BCD representation of Vx in memory locations I, I+1, and I+2.

        The interpreter takes the decimal value of Vx, and places the hundreds digit in memory at location in I
        , the tens digit at location I+1, and the ones digit at location I+2.
        '''

        x = self.v_registers[(self.opcode & 0x0F00) >> 8]

        hundred=x//100
        ten=(x-(hundred*100))//10
        one=(x-(hundred*100)-(ten*10))
        self.ram[self.i_register]=hundred
        self.ram[self.i_register+1]=ten
        self.ram[self.i_register+2]=one

    def _F55(self):

        '''
        Store registers V0 through Vx in memory starting at location I.

        The interpreter copies the values of registers V0 through Vx into memory, starting at the address in I.

        '''

        x= (self.opcode & 0x0F00) >> 8

        for val in range(x+1):
            self.ram[self.i_register+val]=self.v_registers[val]


    def _F65(self):

        '''

        Read registers V0 through Vx from memory starting at location I.

        The interpreter reads values from memory starting at location I into registers V0 through Vx.
        '''

        x = (self.opcode & 0x0F00) >> 8

        for val in range(x + 1):

            self.v_registers[val]=self.ram[self.i_register + val]
























