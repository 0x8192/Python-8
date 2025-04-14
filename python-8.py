# Python-8
# Author: Kai Weston
# Description: A Chip-8 emulator in Python using the pygame and numpy external libraries.
#
# This project follows the MIT License.
#
# MIT License:
# 
# Copyright (c) 2025 Kai Weston
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import os
import random
import sys
import pickle
import tkinter as tk
from tkinter import filedialog
import configparser
import pygame
import numpy as np

class Chip8:

    # Assigning class constants
    SCREEN_WIDTH = 64
    SCREEN_HEIGHT = 32
    MEMORY_SIZE = 4096
    REGISTER_COUNT = 16
    STACK_DEPTH = 16
    KEYPAD_SIZE = 16
    DEBUG = False
    
    def __init__(self):
        #Initialise memory
        self.memory = np.zeros(self.MEMORY_SIZE, dtype=np.uint8) 

        #Initialise registers
        self.V = [0] * self.REGISTER_COUNT # 16 registers, V0 -> VF
        self.I = 0 # Index register
        self.PC = 0x200 # PC always starts at 0x200

        #Initialise Stack
        self.stack = [0] * self.STACK_DEPTH
        self.SP = 0

        #Initialise timers
        self.delay_timer = 0
        self.sound_timer = 0

        #Initialise graphics
        self.graphics = [0] * (self.SCREEN_WIDTH * self.SCREEN_HEIGHT)

        #Initialise Keypad
        self.keypad = [0] * self.KEYPAD_SIZE

        #Initialise Opcode
        self.opcode = 0

        #Initialise Logo (for the command line)
        self.logo =  r"""
         _____       _   _                       ___
        |  __ \     | | | |                     / _ \
        | |__) |   _| |_| |__   ___  _ __ _____| (_) |
        |  ___/ | | | __| '_ \ / _ \| '_ \______> _ <
        | |   | |_| | |_| | | | (_) | | | |    | (_) |
        |_|    \__, |\__|_| |_|\___/|_| |_|     \___/
                __/ |               *It works!*
               |___/
    ***Warning: This program may not be suitable for people with photosensitive epilepsy.***
            *Please play at your own risk.*
        """

        self.version = "0.8" # Version number

        self.graphics_changed = False # Flag to indicate graphics have changed since past render

        #Initialise Fontset (hex)
        self.fontset = [
            #=========
            #   0->9
            #=========
            0xF0,0x90,0x90,0x90,0xF0, #0
            0x20,0x60,0x20,0x20,0x70, #1
            0xF0,0x10,0xF0,0x80,0xF0, #2
            0xF0,0x10,0xF0,0x10,0xF0, #3
            0x90,0x90,0xF0,0x10,0x10, #4
            0xF0,0x80,0xF0,0x10,0xF0, #5
            0xF0,0x80,0xF0,0x90,0xF0, #6
            0xF0,0x10,0x20,0x40,0x40, #7
            0xF0,0x90,0xF0,0x90,0xF0, #8
            0xF0,0x90,0xF0,0x10,0xF0, #9
            #=========
            #   A->F
            #=========
            0xF0,0x90,0xF0,0x90,0x90, #A
            0xE0,0x90,0xE0,0x90,0xE0, #B
            0xF0,0x80,0x80,0x80,0xF0, #C
            0xE0,0x90,0x90,0x90,0xE0, #D
            0xF0,0x80,0xF0,0x80,0xF0, #E
            0xF0,0x80,0xF0,0x80,0x80  #F
        ]

        #Loading fontset into memory starting from 0x50
        for i in range(len(self.fontset)):
            self.memory[0x50+i] = self.fontset[i] & 0xFF

    def load_rom(self,rom_path: str):
        # Load rom into memory starting from 0x200
        with open(rom_path,'rb') as rom:
            rom_data = rom.read()
            for i in range(len(rom_data)):
                self.memory[0x200+i] = rom_data[i] & 0xFF

    def save_state(self, filename="savestate.ch8s"): # Save state feature (Saves when you press F5)
        state = {
            "memory": self.memory[:],
            "V": self.V[:],
            "I": self.I,
            "PC": self.PC,
            "stack": self.stack[:],
            "SP": self.SP,
            "delay_timer": self.delay_timer,
            "sound_timer": self.sound_timer,
            "graphics": self.graphics[:],
            "keypad": self.keypad[:],
        }
        with open(filename, "wb") as f:
            pickle.dump(state, f)

    def load_state(self, filename="savestate.ch8s"): # Load state feature (Loads save state when you press F9)
        try: # Try to load the file in
            with open(filename, "rb") as f:
                state = pickle.load(f)
                
            self.memory = state["memory"]
            self.V = state["V"]
            self.I = state["I"]
            self.PC = state["PC"]
            self.stack = state["stack"]
            self.SP = state["SP"]
            self.delay_timer = state["delay_timer"]
            self.sound_timer = state["sound_timer"]
            self.graphics = state["graphics"]
            self.keypad = state["keypad"]
            return True
        
        except FileNotFoundError as e: # If a savestate.ch8s file doesn't exist we should feed a proper message to the user
            print("Your save state (savestate.ch8s) doesn't exist...")

        except (pickle.UnpicklingError, EOFError) as e:
            print("Your save state (savestate.ch8s) is corrupted...")
    
    @staticmethod
    def play_tone(hz: int = 1000): # Unfinished - Currently only makes a single 5ms beep sound (will be worked upon in later releases).
        try:
            # Stop any currently playing sound
            pygame.mixer.stop()
            
            sample_rate = 44100 # Sample rate
            duration = 0.05  # 500ms beep
            amplitude = 0.5  # 50% volume
        
            # Generating samples
            samples = (amplitude * np.sin(2 * np.pi * np.arange(sample_rate * duration) * hz / sample_rate)).astype(np.float32)
        
            # Ensure pygame mixer is initialised (44100 Hz, 16-bit signed, mono)
            if pygame.mixer.get_init() is None:
                pygame.mixer.init(frequency=sample_rate, size=-16, channels=1)
        
            # Create sound buffer
            sound = pygame.mixer.Sound(buffer=samples)
            sound.play()
            
        except Exception as e:
            print(f"Error playing sound: {e}")

    def wait_for_key_press(self): # Waits for a key press and then returns the corresponding key value
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
            
                if event.type == pygame.KEYDOWN:
                    # Key mapping for the CHIP-8 keypad
                    key_map = {
                        pygame.K_1: 0x1, pygame.K_2: 0x2, pygame.K_3: 0x3, pygame.K_4: 0xC,
                        pygame.K_q: 0x4, pygame.K_w: 0x5, pygame.K_e: 0x6, pygame.K_r: 0xD,
                        pygame.K_a: 0x7, pygame.K_s: 0x8, pygame.K_d: 0x9, pygame.K_f: 0xE,
                        pygame.K_z: 0xA, pygame.K_x: 0x0, pygame.K_c: 0xB, pygame.K_v: 0xF
                    }
                
                    if event.key in key_map:
                        return key_map[event.key]
        
            # Small delay to prevent CPU hogging
            pygame.time.delay(10)
    
    def display_opcode_errors(self, error: str): # Display to the user that an error has occured (of any type) rather than outright crashing the program and displaying an exception that way
        print(f"Opcode error: {error}")
        print("Program halted. Please restart the emulator.")
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
    
    
    def cycle(self): #(CHIP-8 FDE cycle)

        #Fetch the 2 byte opcode
        self.opcode = int(self.memory[self.PC]) << 8 | int(self.memory[self.PC+1])

        #Decode and execute the opcode
        self.execute_opcode()

        #Update the timers
        if self.delay_timer > 0:
            self.delay_timer -=1
        if self.sound_timer > 0:
            if self.sound_timer ==1:
                self.play_tone()
            self.sound_timer -=1
    
    def execute_opcode(self):
        #Decoding and executing the opcode that is held in self.opcode
        match self.opcode & 0xF000:
            case 0x0000:
                match self.opcode & 0x00FF:
                    
                    case 0x00E0: #Clear screen
                        self.graphics = [0] * (self.SCREEN_WIDTH * self.SCREEN_HEIGHT)
                        self.PC +=2
                    
                    case 0x00EE: #Return from subroutine
                        if self.SP <= 0:# Preventing stack underflow
                            self.display_opcode_errors("Stack underflow at 00EE")
                        
                        self.SP -=1
                        self.PC = self.stack[self.SP]
                        self.PC +=2
            
            case 0x1000: #1NNN - Jump to address NNN
                self.PC = self.opcode & 0x0FFF
           
            case 0x2000: #2NNN - Call subroutine at NNN
                if self.SP >= self.STACK_DEPTH: # Preventing stack overflow
                    self.display_opcode_errors("Stack overflow at 2NNN")
                
                self.stack[self.SP] = self.PC 
                self.SP +=1 
                self.PC = self.opcode & 0x0FFF 
           
            case 0x3000: #3XNN - Skip next instruction if VX == NN
                x = (self.opcode & 0x0F00) >> 8
                if self.V[x] == (self.opcode & 0x00FF):
                    self.PC += 4
                else:
                    self.PC +=2
            
            case 0x4000: #4XNN - Skip next instruction if VX != NN
                x = (self.opcode & 0x0F00) >> 8
                if self.V[x] != (self.opcode & 0x00FF):
                    self.PC += 4
                else:
                    self.PC +=2

            case 0x5000: #5XY0 - Skip next instruction if VX == VY
                x = (self.opcode & 0x0F00) >> 8
                y = (self.opcode & 0x00F0) >> 4
                if self.V[x] == self.V[y]:
                    self.PC +=4
                else:
                    self.PC +=2
           
            case 0x6000: #6XNN - Setting VX to NN
                x = (self.opcode & 0x0F00) >> 8
                self.V[x] = self.opcode & 0x00FF
                self.PC +=2
           
            case 0x7000: #7XNN - Add NN to VX (no carry)
                x = (self.opcode & 0X0F00) >> 8
                self.V[x] = (self.V[x] + (self.opcode & 0x00FF)) & 0xFF
                self.PC += 2
            
            case 0x8000:
                x = (self.opcode & 0x0F00) >> 8
                y = (self.opcode & 0x00F0) >> 4
                match self.opcode & 0x000F:
                    case 0x0000: #0XY0 - Setting VX to VY
                        self.V[x] = self.V[y]
                        self.PC +=2
                    case 0x0001: #8XY1 - Setting VX to (VX or VY)
                        self.V[x] |= self.V[y]
                        self.PC +=2
                    case 0x0002: #8XY2 - Set vX to (VX AND VY)
                        self.V[x] &= self.V[y]                
                        self.PC +=2
                    case 0x0003: #8XY3 - Set VX = (VX XOR VY)
                        self.V[x] ^= self.V[y]                                 
                        self.PC+=2
                    case 0x0004: #8XY4 - Add VY to VX, VF equals Carry 
                        result = self.V[x] + self.V[y]
                        self.V[0xF] = 1 if result > 255 else 0
                        self.V[x] = result & 0xFF
                        self.PC +=2
                    case 0x0005: #8XY5 - Subtract VY from VX, VF equals NOT borrow
                        self.V[0xF] = 1 if self.V[x] >= self.V[y] else 0
                        self.V[x] = (self.V[x] - self.V[y]) & 0xFF
                        self.PC +=2
                    case 0x0006: #8XY6 - Shift VX right by 1, VF = LSB
                        self.V[0xF] = self.V[x] & 0x1
                        self.V[x] >>= 1
                        self.PC +=2
                    case 0x0007: #8XY7 - Set VX = VY - VX, VF NOT borrow
                        self.V[0xF] = 1 if self.V[y] >= self.V[x] else 0
                        self.V[x] = (self.V[y] - self.V[x]) & 0xFF
                        self.PC +=2
                    case 0x000E: #8XYE - Shift VX left by 1, VF = MSB
                        self.V[0xF] = (self.V[x] & 0x80) >> 7
                        self.V[x] = (self.V[x] << 1) & 0xFF
                        self.PC +=2
            
            case 0x9000: # 9XY0 - Skip next instruction if VX != VY
                x = (self.opcode & 0x0F00) >> 8
                y = (self.opcode & 0x00F0) >> 4

                if self.V[x] != self.V[y]:
                    self.PC +=4
                else:
                    self.PC +=2


            case 0xA000: #ANNN - Setting I to the address NNN
                self.I = self.opcode & 0x0FFF
                self.PC +=2

            case 0xB000: #BNNN - Jump to address NNN + V0
                self.PC = ((self.opcode & 0x0FFF) + self.V[0]) & 0xFFF

            case 0xC000: # CXNN - Set VX equals random byte and NN
                x = (self.opcode & 0x0F00) >> 8
                self.V[x] = random.randint(0,255) & (self.opcode & 0x00FF)
                self.PC +=2

            case 0xD000: #DXYN - Draw sprite at (Vx, Vy) with the height of N
                x = self.V[(self.opcode & 0x0F00) >> 8]
                y = self.V[(self.opcode & 0x00F0) >> 4]
                height = self.opcode & 0x000F
                self.draw_sprites(x,y,height)
                self.PC +=2

            case 0xE000:
                x = (self.opcode & 0x0F00) >> 8
                match self.opcode & 0x00FF:
                    case 0x009E: # EX9E - Skip next instruction if key with value VX is pressed
                        if self.keypad[self.V[x]]:
                            self.PC +=4
                        else:
                            self.PC +=2
                    case 0x00A1: # EXA1 - Skip the next instruction if key with value VX is not pressed
                        if not self.keypad[self.V[x]]:
                            self.PC +=4
                        else:
                            self.PC +=2
            
            case 0xF000:
                x = (self.opcode & 0x0F00) >> 8
                match self.opcode & 0x00FF:
                    case 0x0007: #FX07 - Set vx equal to the delay timer value
                        self.V[x] = self.delay_timer
                        self.PC +=2
                    case 0x000A: #FX0A - Wait for a keypress then store it in VX
                        key_pressed = self.wait_for_key_press()
                        if key_pressed is not None:
                            self.V[x] = key_pressed
                            self.PC +=2
                    case 0x0015: #FX15 - Set delay timer equal to VX
                        self.delay_timer = self.V[x]
                        self.PC +=2
                    case 0x0018: #FX18 - Set sound timer equal to VX
                        self.sound_timer = self.V[x]
                        self.PC +=2
                    case 0x001E: #FX1E - Add VX to I
                        self.I = (self.I + int(self.V[x])) & 0xFFFF
                        self.PC +=2
                    case 0x0033: # FX33 - Store BCD of VX in memory (I, I+1, I+2)
                        self.memory[self.I] = self.V[x] // 100 
                        self.memory[self.I + 1] = (self.V[x] // 10) % 10
                        self.memory[self.I + 2] = self.V[x] % 10
                        
                        if self.I >= self.MEMORY_SIZE - 2:
                            self.display_opcode_errors("Memory overflow when executing FX33")

                        if self.DEBUG:
                            print(f"Storing BCD of V{x} ({self.V[x]}) at {self.I}: {self.memory[self.I]}, {self.memory[self.I + 1]}, {self.memory[self.I + 2]}")
                        self.PC +=2


                    case 0x0055: #FX55 - Store registers V0 through VX in memory starting at I
                        for i in range(x + 1):
                            self.memory[self.I + i] = self.V[i] & 0xFF
                            if self.DEBUG:
                                print(f"Storing registers V0 through V{x} at memory locations {self.I} to {self.I + x}")
                        self.PC +=2



                    case 0x0065: #FX65 - Read registers V0 through to VX from memory starting at I
                        for i in range(x+1):
                            self.V[i] = self.memory[self.I + i]
                        self.PC+=2

            case _:
                print(f"Unknown opcode: {hex(self.opcode)}") # In the instance of unknown opcodes being used
                if self.DEBUG:
                    self.PC +=2
                
    
    def draw_sprites(self, x: int, y: int, height: int):
        x = int(x) # Explicit conversions
        y = int(y)
        
        
        # Drawing a sprite at x,y with the height of height
        self.V[0xF] = 0 # Reset VF register (the collision flag)

        self.graphics_changed = True # Indicate that the graphics have changed since

        for row in range(height):
            if self.I + row >= len(self.memory):
                break # Preventing OOB memory access
            
            sprite_byte = self.memory[self.I + row]
            
            for col in range(8): # Every row is 8 bits wide
                pixel = (sprite_byte >> (7 - col)) & 0x1
                
                screen_x = (x + col) % self.SCREEN_WIDTH
                screen_y = (y + row) % self.SCREEN_HEIGHT
                screen_index = screen_y * self.SCREEN_WIDTH + screen_x

                if pixel == 1:
                    if self.graphics[screen_index] == 1:
                        self.V[0xF] = 1 # Colision was detected
                    self.graphics[screen_index] ^= 1
        

    def set_keys(self,events):
        # Mapping the pygame keys to the CHIP-8 keypad using a keymap
        key_map = {
        pygame.K_1: 0x1, pygame.K_2: 0x2, pygame.K_3: 0x3, pygame.K_4: 0xC,
        pygame.K_q: 0x4, pygame.K_w: 0x5, pygame.K_e: 0x6, pygame.K_r: 0xD,
        pygame.K_a: 0x7, pygame.K_s: 0x8, pygame.K_d: 0x9, pygame.K_f: 0xE,
        pygame.K_z: 0xA, pygame.K_x: 0x0, pygame.K_c: 0xB, pygame.K_v: 0xF
        }
    
        for event in events:
            if event.type in (pygame.KEYDOWN, pygame.KEYUP):
                if event.key in key_map:
                    self.keypad[key_map[event.key]] = 1 if event.type == pygame.KEYDOWN else 0
                    
                    
    def get_screen_width(self): # Get the screen width at emulation startup
        return self.SCREEN_WIDTH
    
    def get_screen_height(self): # Get the screen height at emulation startup
        return self.SCREEN_HEIGHT


def open_file_dialog(): # Lets the user pick their own file if they haven't given it as a command line argument
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(filetypes=[("CHIP-8 ROMs", "*.ch8"),("CHIP-8 ROMs", "*.c8")])
    return file_path

def create_config(scale: int = 10): # Create a scale config in the instance that the config file doesn't exist
    config = configparser.ConfigParser()
    config["Display"] = {"scale": str(scale)}
    with open("config.ini", "w") as f:
        config.write(f)


def load_config(): # Loading the scale config
    config = configparser.ConfigParser()
    config_file = "config.ini"
    
    if not os.path.exists(config_file): # If the config file doesn't exist in the current path, create one.
        create_config()
        print("Created config.ini with default scale of 10.")
        return 10 # Return 10 as the default scale.
    
    config.read(config_file) # Read the config file
    
    try:
        return int(config["Display"].get("scale", 10)) # Try to return the scale value from the config file
    except Exception as e: # This will be raised in the case that the scale value isn't an integer or the config file is corrupted
        print(f"Error reading config.ini {e}. Using the default scale of 10.")
        return 10
   
def main():
    # Mac compatibility (known issue with pygame and tkinter)
    tk_root = tk.Tk()
    tk_root.withdraw() # Hides the root window  
    
    
    scale = load_config() # Initialising scale variable
    
    # Initialising pygame and the clock
    pygame.init()
    clock = pygame.time.Clock()

    # Clock speed variable (Can be changed using the + and - keys to pick your desired speed between 1000 and 100)
    clock_speed = 600

    # Attempting to load the icon
    try:
        icon = pygame.image.load("icon.bmp")
        pygame.display.set_icon(icon)
    except:
        pass

    # Creating the CHIP8
    chip8 = Chip8()
    
    # Initialising the local screen width and height constants
    SCREEN_WIDTH = Chip8.get_screen_width(chip8)
    SCREEN_HEIGHT = Chip8.get_screen_height(chip8)
    
    
    # Creating a window with a title and icon
    screen = pygame.display.set_mode((SCREEN_WIDTH * scale, SCREEN_HEIGHT * scale))
    pygame.display.set_caption("Python-8")
    
    
    # Displaying the custom logo plus some important information
    print(chip8.logo)
    print(f"Python-8 v{chip8.version}")
    print("INFO: \n-----")
    print(f"  Scale: {scale}")
    print(f"  Default clock speed: {clock_speed}Hz (Press +/- to increment/decrement)")
    print("  Press F5 to save the current state, F9 to load the state")
    print("  Press [/] to decrease/increase the size scale")
    print("="*64)
    
    # Loading the ROM
    if len(sys.argv) > 1:
        try:
            chip8.load_rom(sys.argv[1])
        except FileNotFoundError:
            print("ROM was not found")
            return
    
    if len(sys.argv) <= 1:
        rom_path = open_file_dialog()
        if not rom_path:
            print("No ROM selected.")
            return
        chip8.load_rom(rom_path)
    
    running = True # Initialising and setting up the forever unless quitting while loop
    while running:
        events = pygame.event.get()
        chip8.set_keys(events)
        for event in events:
            if event.type == pygame.QUIT:
                if load_config() != scale:
                    print(f"Updating config.ini with scale {scale}...")
                    create_config(scale)
                running = False
        
            if event.type == pygame.KEYDOWN:
                
                if event.key == pygame.K_F5:
                    chip8.save_state()
                    print("Saved state")  
                if event.key == pygame.K_F9:
                    load = chip8.load_state()
                    if load == True:
                        print("Loaded prior state")
                    
                if event.key == pygame.K_EQUALS:  # (+ key but lowercase)
                    clock_speed = min(1000, clock_speed + 50)
                    print(f"Clock speed: {clock_speed}")
                elif event.key == pygame.K_MINUS:
                    clock_speed = max(100, clock_speed - 50)
                    print(f"Clock speed: {clock_speed}")        
                    
                if event.key == pygame.K_LEFTBRACKET:
                    scale = max(1, scale - 1)
                    screen = pygame.display.set_mode((SCREEN_WIDTH * scale, SCREEN_HEIGHT * scale))
                    chip8.graphics_changed = True
                    print(f"Scale: {scale}")
                    
                elif event.key == pygame.K_RIGHTBRACKET:
                    root = tk.Tk()
                    scale = min(int((root.winfo_screenwidth()/SCREEN_WIDTH)), scale + 1) # Clamping the scale based on the formula of (resolution width / screen width)
                    screen = pygame.display.set_mode((SCREEN_WIDTH * scale, SCREEN_HEIGHT * scale))
                    chip8.graphics_changed = True
                    print(f"Scale: {scale}")
        
        # Emulating a cycle
        chip8.cycle()

        if chip8.graphics_changed:
            # Drawing the graphics
            for y in range(SCREEN_HEIGHT):
                for x in range(SCREEN_WIDTH):
                    color = (255,255,255) if chip8.graphics[y*SCREEN_WIDTH + x] == 1 else (0,0,0)
                    pygame.draw.rect(screen,color, (x*scale, y*scale, scale, scale))
           
            chip8.graphics_changed = False
            pygame.display.flip()

        # Limit the clock speed, different programs prefer different speed. A value between 400 - 800 is ideal.
        clock.tick(clock_speed)

    pygame.quit()

if __name__ == "__main__":
    main()