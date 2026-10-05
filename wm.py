import os
import sys
import socket

# =====================================================================
# 1. FIXED ABSTRACT NETWORK SCANNER FOR TERMUX:X11
# =====================================================================
try:
    import Xlib.support.unix_connect as unix_connect
    
    def get_termux_abstract_socket(*args, **kwargs):
        # We loop through possible formats since Termux apps isolate paths dynamically.
        # Abstract socket names begin with a null byte (\0).
        possible_addresses = [
            b'\0.X11-unix/X0',
            b'\0.X11-unix/X1',
            b'\0/tmp/.X11-unix/X0',
            b'\0/tmp/.X11-unix/X1'
        ]
        
        for address in possible_addresses:
            try:
                s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                s.connect(address)
                # Found it! Update our environment string to match the successful binding
                display_num = address[-1:] # grab '0' or '1'
                os.environ['DISPLAY'] = f':{display_num.decode()}'
                print(f"[WM-Log] Successfully attached to abstract socket address: {address}")
                return s
            except (socket.error, ConnectionRefusedError):
                s.close()
                continue
                
        raise ConnectionRefusedError(
            "Could not connect to any abstract Termux:X11 socket addresses. "
            "Please ensure the Termux:X11 app is open and visible on your screen."
        )

    # Inject the scanner directly over Xlib's default connector
    unix_connect.get_socket = get_termux_abstract_socket
except ImportError:
    pass

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
