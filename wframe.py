import os
import sys
import subprocess
import pygame
from pygame._sdl2 import Window

# Windows hardware pointer framework for smooth dragging
if sys.platform == "win32":
    import ctypes
    from ctypes import wintypes
    
    def get_global_mouse_pos():
        """Fetches raw monitor coordinates completely independent of the window."""
        pt = wintypes.POINT()
        ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
        return pt.x, pt.y
else:
    # Linux/Termux X11 fallback
    def get_global_mouse_pos():
        # Uses xdotool to grab absolute desktop hardware pointer state safely
        try:
            res = subprocess.run(['xdotool', 'getmouselocation', '--shell'], capture_output=True, text=True)
            geo = {}
            for line in res.stdout.strip().split('\n'):
                if '=' in line:
                    k, v = line.split('=')
                    geo[k] = int(v)
            return geo.get('X', 0), geo.get('Y', 0)
        except Exception:
            return pygame.mouse.get_pos()

os.environ['DISPLAY'] = ':0'
TARGET_APP_ID = sys.argv[1] if len(sys.argv) > 1 else None

pygame.init()
frame = pygame.display.set_mode((800, 32), pygame.NOFRAME)
pygame.display.set_caption("NADETOP_WINDOW_FRAME")

sdl_window = Window.from_display_module()

is_dragging = False
# Holds where inside the title bar the click originally landed
click_offset_x = 0
click_offset_y = 0

clock = pygame.time.Clock()
walking = True

while walking:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            walking = False
            
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1: # Left click
                local_x, local_y = event.pos
                # Ensure the click happened inside the 32px height constraint
                if 0 <= local_y <= 32:
                    is_dragging = True
                    # Calculate exactly where the mouse is anchored inside the window box
                    wx, wy = sdl_window.position
                    gx, gy = get_global_mouse_pos()
                    click_offset_x = gx - wx
                    click_offset_y = gy - wy
                    
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                is_dragging = False

    # --- THE CLEAN DESKTOP TRACKING BLOCK ---
    if is_dragging:
        # Check if user released mouse while dragging outside window boundary
        if not pygame.mouse.get_pressed()[0]:
            is_dragging = False
        else:
            # Grab absolute desktop placement metric
            gx, gy = get_global_mouse_pos()
            
            # Snap window exactly to global mouse minus original anchor position
            new_x = gx - click_offset_x
            new_y = gy - click_offset_y
            
            sdl_window.position = (new_x, new_y)
            
            # Drag the target app cleanly behind us
            if TARGET_APP_ID:
                subprocess.Popen([
                    'xdotool', 'windowmove', 
                    str(TARGET_APP_ID), str(new_x), str(new_y + 32)
                ])

    frame.fill((0, 127, 255))
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
