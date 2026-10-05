import os
import sys
import socket

# =====================================================================
# INTERCEPT AND AUTO-SCAN TERMUX ABSTRACT X11 SOCKETS
# =====================================================================
try:
    import Xlib.support.unix_connect as unix_connect
    
    def get_termux_abstract_socket(*args, **kwargs):
        # Scan through typical X11 display numbers in case :0 is occupied
        for dno in [0, 1, 2, 3]:
            abstract_address = f'\0.X11-unix/X{dno}'.encode()
            try:
                s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                s.connect(abstract_address)
                # Success! Dynamically match the environment variable to what we found
                os.environ['DISPLAY'] = f':{dno}'
                print(f"Connected successfully to Termux:X11 on display :{dno}!")
                return s
            except (socket.error, ConnectionRefusedError):
                s.close()
                continue
        
        # If everything fails, raise the original error to let us know it's truly dead
        raise ConnectionRefusedError("Could not find any active Termux:X11 server instances.")

    unix_connect.get_socket = get_termux_abstract_socket
except ImportError:
    pass

# Default fallback environment string
os.environ['DISPLAY'] = ':0'

# =====================================================================
# 2. IMPORTS
# =====================================================================
import pygame
from ewmh import EWMH
from Xlib import X, display
from pygame._sdl2 import Window

# Initialize Xlib Display
disp = display.Display(":0")
ewmh = EWMH(disp)
root = disp.screen().root

# Listen for window creation/mapping globally
root.change_attributes(event_mask=X.SubstructureNotifyMask)

# Initialize Pygame
pygame.init()

# Get screen resolution and create frameless window
desktop_size = pygame.display.get_desktop_sizes()[0]
screen = pygame.display.set_mode(desktop_size, pygame.NOFRAME)
pygame.display.set_caption("Frameless Window")

# Setup SDL2 Window hook to force position
sdl_window = Window.from_display_module()
sdl_window.position = (0, 0)

clock = pygame.time.Clock()
walking = True

print("Script started successfully! Listening for X11 events...")

# =====================================================================
# 3. MAIN LOOP
# =====================================================================
while walking:
    # Handle Pygame Events (Touch / Mouse / Keyboard)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            walking = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:  # Easy way to exit on Termux
                walking = False

    # Draw to screen
    screen.fill((0, 127, 255))
    pygame.display.flip()

    # Handle X11 Events without freezing Pygame (NON-BLOCKING)
    while disp.pending_events() > 0:
        ev = disp.next_event()
        
        if ev.type == X.CreateNotify:
            print(f" New window created! ID: {hex(ev.window.id)}")
        elif ev.type == X.MapNotify:
            print(f" Window mapped (shown): {hex(ev.window.id)}")

    clock.tick(60)

pygame.quit()
