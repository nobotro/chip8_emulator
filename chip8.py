import random
import time


class chip8():
    ram = [0] * 4096  # ram for chip8
    rom_load_addres = 0x200  # chip-8 program start from that adress

    v_registers = [0] * 15  # v registers
    vf_register = 0  # instruction flag

    i_register = 0  # memory register,stores memory adress,last 12 bit used

    delay_register = 0
    sound_register = 0  # When these registers are non-zero, they are automatically decremented at a rate of 60Hz

    pc_register = 0  # stores currently executing adress

    sp = 0  # stack pointer,it is used to point to the topmost level of the stack.

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

    font = [

        0xF0, 0x90, 0x90, 0x90, 0xF0,  # 0
        0x20, 0x60, 0x20, 0x20, 0x70,  # 1
        0xF0, 0x10, 0xF0, 0x80, 0xF0,  # 2
        0xF0, 0xF10, 0xF0, 0x10, 0xF0,  # 3
        0x90, 0x90, 0xF0, 0x10, 0x10,  # 4
        0xF0, 0x80, 0xF0, 0x10, 0xF0,  # 5
        0xF0, 0x80, 0xF0, 0x90, 0xF0,  # 6
        0xF0, 0x10, 0x20, 0x40, 0x40,  # 7
        0xF0, 0x90, 0xF0, 0x90, 0xF0,  # 8
        0xF0, 0x90, 0xF0, 0x10, 0xF0,  # 9
        0xF0, 0x90, 0xF0, 0x90, 0x90,  # A
        0xE0, 0x90, 0xE0, 0x90, 0xE0,  # B
        0xF0, 0x80, 0x80, 0x80, 0xF0,  # C
        0xE0, 0x90, 0x90, 0x90, 0xE0,  # D
        0xF0, 0x80, 0xF0, 0x80, 0xF0,  # E
        0xF0, 0x80, 0xF0, 0x80, 0x80  # F

    ]

    def del_sound_timer(self):
        if self.delay_register: self.delay_register -= 1
        if self.sound_register:
            # start buzzing
            self.sound_register -= 1
        else:
            pass
            #stop buzzing


        time.sleep(
            0.016)  # 60hz 1 decrement in 16 microseconds (1000/60)


    def load_rom(self, path):

        f = open(path, 'rb')
        rom_bytes = f.read()
        f.close()
        rom_size = len(rom_bytes)
        for i in range(rom_size):
            self.ram[i + self.rom_load_addres] = rom_bytes[i]

        # load fonts
        i = 0
        while i < len(self.font):
            self.ram[i] = self.font[i]

    def run_cycle(self):
        self.pc_register = self.rom_load_addres

        while True:
            self.del_sound_timer()

            # get opcode
            self.opcode = self.ram[self.pc_register] << 8 | self.ram[self.pc_register + 1]


            # incress current executing adress
            self.pc_register += 2

    # exevuting operations

    def _00E0(self):
        # 00E0 - CLS Clear the display.
        self.display = [0] * 64 * 32
        self.draw_flag = True

    def _00EE(self):
        '''
        00EE - RET
        Return from a subroutine.
        The interpreter sets the program counter to the address at the top of the stack, then subtracts 1 from the stack pointer.'''

        self.pc_register = self.stack.pop()
        self.sp -= 1

    def _1nnn(self):
        ''' 1nnn - JP addr
        jump to location nnn.
        The interpreter sets the program counter to nnn.'''

        self.pc_register = self.opcode & 0x0FFF

    def _2nnn(self):
        '''2nnn - CALL addr
        Call subroutine at nnn.
        The interpreter increments the stack pointer, then puts the current PC on the top of the stack. The PC is then set to nnn.
        '''

        self.sp += 1
        self.stack.append(self.pc_register)
        self.pc_register = self.opcode & 0x0FFF

    def _3xkk(self):
        '''3xkk - SE Vx, byte
            Skip next instruction if Vx = kk.
            The interpreter compares register Vx to kk, and if they are equal, increments the program counter by 2.
        '''

        x=(self.opcode & 0x0F00)>>8
        kk=self.opcode & 0x00FF
        if self.v_registers[x]==kk: self.pc_register+=2

    def _4xkk(self):

        '''4xkk - SNE Vx, byte
        Skip next instruction if Vx != kk.
        The interpreter compares register Vx to kk, and if they are not equal, increments the program counter by 2.'''
        x = (self.opcode & 0x0F00)>>8
        kk = self.opcode & 0x00FF
        if self.v_registers[x] != kk: self.pc_register += 2

    def _5xy0(self):
        '''5xy0 - SE Vx, Vy
        Skip next instruction if Vx = Vy.
        The interpreter compares register Vx to register Vy, and if they are equal, increments the program counter by 2.
        '''
        x = (self.opcode & 0x0F00)>>8
        y = (self.opcode & 0x00F0)>>4
        if self.v_registers[x]==self.v_registers[y]:self.pc_register+=2

    def _6xkk(self):
        '''6xkk - LD Vx, byte
        Set Vx = kk.
        The interpreter puts the value kk into register Vx.'''

        x = (self.opcode & 0x0F00) >> 8
        kk=self.opcode & 0x00FF

        self.v_registers[x]=kk

    def _7xkk(self):
        '''
        7xkk - ADD Vx, byte
        Set Vx = Vx + kk.
        Adds the value kk to the value of register Vx, then stores the result in Vx.
        '''
        x = (self.opcode & 0x0F00) >> 8
        kk = self.opcode & 0x00FF
        self.v_registers[x] += kk

    def _8xy0(self):
        '''8xy0 - LD Vx, Vy
        Set Vx = Vy.
        Stores the value of register Vy in register Vx.'''

        x = (self.opcode & 0x0F00) >> 8
        y = (self.opcode & 0x00F0)>>4
        self.v_registers[x]=self.v_registers[y]


    def _8xy1(self):
        '''8xy1 - OR Vx, Vy
        Set Vx = Vx OR Vy.
        Performs a bitwise OR on the values of Vx and Vy, then stores the result in Vx.
        A bitwise OR compares the corrseponding bits from two values, and if either bit is 1, then the same bit in the result is also 1. Otherwise, it is 0.
        '''

        x = (self.opcode & 0x0F00) >> 8
        y = (self.opcode & 0x00F0) >> 4

        self.v_registers[x]=self.v_registers[x] | self.v_registers[y]


    def _8xy2(self):
        '''8xy2 - AND Vx, Vy
        Set Vx = Vx AND Vy.
        Performs a bitwise AND on the values of Vx and Vy, then stores the result in Vx.
        A bitwise AND compares the corrseponding bits from two values, and if both bits are 1, then the same bit in the result is also 1. Otherwise, it is 0.
        '''

        x = (self.opcode & 0x0F00) >> 8
        y = (self.opcode & 0x00F0) >> 4

        self.v_registers[x] = self.v_registers[x] & self.v_registers[y]


    def _8xy3(self):
        '''8xy3 - XOR Vx, Vy
        Set Vx = Vx XOR Vy.
        Performs a bitwise exclusive OR on the values of Vx and Vy, then stores the result in Vx.
        An exclusive OR compares the corrseponding bits from two values, and if the bits are not both the same,
        then the corresponding bit in the result is set to 1. Otherwise, it is 0.
        '''

        x = (self.opcode & 0x0F00) >> 8
        y = (self.opcode & 0x00F0) >> 4

        self.v_registers[x] = self.v_registers[x] ^ self.v_registers[y]


    def _8xy4(self):
        '''8xy4 - ADD Vx, Vy
        Set Vx = Vx + Vy, set VF = carry.
        The values of Vx and Vy are added together. If the result is greater than 8 bits (i.e., > 255,)
        VF is set to 1, otherwise 0. Only the lowest 8 bits of the result are kept, and stored in Vx.
        '''

        x = (self.opcode & 0x0F00) >> 8
        y = (self.opcode & 0x00F0) >> 4
        if self.v_registers[x] + self.v_registers[y]>255:
            self.vf_register=1
        else:
            self.vf_register=0


    def _8xy5(self):
        '''8xy5 - SUB Vx, Vy
        Set Vx = Vx - Vy, set VF = NOT borrow.
        If Vx > Vy, then VF is set to 1, otherwise 0. Then Vy is subtracted from Vx, and the results stored in Vx.
        '''

        x = (self.opcode & 0x0F00) >> 8
        y = (self.opcode & 0x00F0) >> 4

        if self.v_registers[x] > self.v_registers[y]:
            self.vf_register = 1
        else:
            self.vf_register = 0

        self.v_registers[x] -= self.v_registers[y]


    def _8xy6(self):
        '''8xy6 - SHR Vx {, Vy} Set Vx = Vx SHR 1.
        If the least-significant bit of Vx is 1, then VF is set to 1, otherwise 0. Then Vx is divided by 2.
        '''

        x = (self.opcode & 0x0F00) >> 8
        y = (self.opcode & 0x00F0) >> 4

        if self.v_registers[x] & 0b00000001:
            self.vf_register=1
        else:self.vf_register=0

        self.v_registers[x] /= 2



    def _8xy7(self):
        '''8xy7 - SUBN Vx, Vy
        Set Vx = Vy - Vx, set VF = NOT borrow.
        If Vy > Vx, then VF is set to 1, otherwise 0. Then Vx is subtracted from Vy, and the results stored in Vx.
        '''

        x = (self.opcode & 0x0F00) >> 8
        y = (self.opcode & 0x00F0) >> 4

        if self.v_registers[y]>self.v_registers[x]:
            self.vf_register=1
        else:
            self.vf_register=0

        self.v_registers[y] -= self.v_registers[x]

    def _8xyE(self):
        '''8xyE - SHL Vx {, Vy}
        Set Vx = Vx SHL 1.
        If the most-significant bit of Vx is 1, then VF is set to 1, otherwise to 0. Then Vx is multiplied by 2.
        '''

        x = (self.opcode & 0x0F00) >> 8
        y = (self.opcode & 0x00F0) >> 4

        if self.v_registers[x] & 0b10000000:
            self.vf_register=1
        else:self.vf_register=0

        self.v_registers[x]*=2


    def _9xy0(self):
        '''9xy0 - SNE Vx, Vy
        Skip next instruction if Vx != Vy.
        The values of Vx and Vy are compared, and if they are not equal, the program counter is increased by 2.'''

        x = (self.opcode & 0x0F00) >> 8
        y = (self.opcode & 0x00F0) >> 4


        if x!=y:
            self.pc_register+=2


    def _Annn(self):
        '''Annn - LD I, addr
        Set I = nnn.
        The value of register I is set to nnn.'''

        nnn=self.opcode & 0x0FFF
        self.i_register=nnn


    def _Bnnn(self):
        '''Bnnn - JP V0, addr
        Jump to location nnn + V0.
        The program counter is set to nnn plus the value of V0.'''

        nnn = self.opcode & 0x0FFF

        self.pc_register=nnn+self.v_registers[0]

    def _Cxkk(self):
        '''Cxkk - RND Vx, byte
        Set Vx = random byte AND kk.
        The interpreter generates a random number from 0 to 255,
        which is then ANDed with the value kk.
        The results are stored in Vx. See instruction 8xy2 for more information on AND.'''

        x = (self.opcode & 0x0F00)>>8
        kk=self.opcode & 0x00FF
        rand=random.randint(0, 255)
        self.v_registers[x]=kk & rand


    def _Dxyn(self):
        '''Dxyn - DRW Vx, Vy, nibble
        Display n-byte sprite starting at memory location I at (Vx, Vy), set VF = collision.

        The interpreter reads n bytes from memory, starting at the address stored in I.
         These bytes are then displayed as sprites on screen at coordinates (Vx, Vy).
         Sprites are XORed onto the existing screen.
         If this causes any pixels to be erased, VF is set to 1, otherwise it is set to 0.
         If the sprite is positioned so part of it is outside the coordinates of the display, it wraps around to the opposite side of the screen.
         See instruction 8xy3 for more information on XOR, and section 2.4, Display, for more information on the Chip-8 screen and sprites.'''

        x = (self.opcode & 0x0F00) >> 8
        y = (self.opcode & 0x00F0) >> 4
        n = self.opcode & 0x000F
        sprite=self.ram[self.i_register:self.i_register+n] # 8 bit width ,len(sprites) height

        for i in range(len(sprite)):

            xx=0
            while xx<8:
                if i + y >= 32 or xx + 8 >= 64: continue

                self.display[x+xx+64*(y+i)]^=(sprite[i] & 0xFF>>xx)



                if self.display[x+xx+64*(y+i)]:
                    self.vf_register=0
                else:
                    self.vf_register=1
                xx += 1



    def _Ex9E(self):
        '''

        Ex9E - SKP Vx
        Skip next instruction if key with the value of Vx is pressed.
        Checks the keyboard, and if the key corresponding to the value of Vx is
        currently in the down position, PC is increased by 2.'''

        x = (self.opcode & 0x0F00)>>8

        if self.keyboard[self.v_register[x]]:
            self.pc_register+=2


    def _ExA1(self):
        '''ExA1 - SKNP Vx
        Skip next instruction if key with the value of Vx is not pressed.
        Checks the keyboard, and
        if the key corresponding to the value of Vx is currently in the up position,
        PC is increased by 2.
        '''

        x = (self.opcode & 0x0F00) >> 8

        if self.keyboard[self.v_register[x]]:
            self.pc_register += 2





    def _Fx07(self):
        '''
        Fx07 - LD Vx, DT
        Set Vx = delay timer value.
        The value of DT is placed into Vx'''
        x = (self.opcode & 0x0F00) >> 8

        self.v_registers[x]=self.delay_register

    def _Fx0A(self):
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

    def _Fx15(self):
        '''
        Set delay timer = Vx.

        DT is set equal to the value of Vx.
        '''

        x = (self.opcode & 0x0F00) >> 8
        self.delay_register=self.v_registers[x]


    def _Fx18(self):

        '''
        Set sound timer = Vx.

        ST is set equal to the value of Vx.

        '''

        x = (self.opcode & 0x0F00) >> 8
        self.sound_register = self.v_registers[x]


    def _Fx1E(self):
        '''
        Set I = I + Vx.

        The values of I and Vx are added, and the results are stored in I.'''

        x = (self.opcode & 0x0F00) >> 8
        self.i_register=self.i_register+self.v_registers[x]


    def _Fx29(self):

        '''

        Set I = location of sprite for digit Vx.

        The value of I is set to the location for the hexadecimal sprite corresponding to the value of Vx.
        See section 2.4, Display, for more information on the Chip-8 hexadecimal font.

        '''
        x = (self.opcode & 0x0F00) >> 8

        self.i_register=self.ram[self.v_registers[x]*5]


    def _Fx33(self):

        '''Store BCD representation of Vx in memory locations I, I+1, and I+2.

        The interpreter takes the decimal value of Vx, and places the hundreds digit in memory at location in I
        , the tens digit at location I+1, and the ones digit at location I+2.
        '''

        x = (self.opcode & 0x0F00) >> 8

        hundred=x//100
        ten=(x-(hundred*100))//10
        one=(x-(hundred*100)-(ten*10))
        self.ram[self.i_register]=hundred
        self.ram[self.i_register+1]=ten
        self.ram[self.i_register+2]=one

    def _Fx55(self):

        '''
        Store registers V0 through Vx in memory starting at location I.

        The interpreter copies the values of registers V0 through Vx into memory, starting at the address in I.

        '''

        x= (self.opcode & 0x0F00) >> 8

        for val in range(x+1):
            self.ram[self.i_register+val]=self.v_registers[val]


    def _Fx65(self):

        '''

        Read registers V0 through Vx from memory starting at location I.

        The interpreter reads values from memory starting at location I into registers V0 through Vx.
        '''

        x = (self.opcode & 0x0F00) >> 8

        for val in range(x + 1):

            self.v_registers[val]=self.ram[self.i_register + val]





















