import os
import sys
import subprocess
import pygame
from pygame._sdl2 import Window

os.environ['DISPLAY'] = ':0'

# Read target app ID passed from wm.py
TARGET_APP_ID = sys.argv[1] if len(sys.argv) > 1 else None

pygame.init()
# A tiny 16x16 square grip
SIZE = 16
frame = pygame.display.set_mode((SIZE, SIZE), pygame.NOFRAME)
pygame.display.set_caption("NADETOP_RESIZE_GRIP")

sdl_window = Window.from_display_module()

# Fallback hardware mouse tracking
if sys.platform == "win32":
    import ctypes
    from ctypes import wintypes
    def get_global_mouse_pos():
        pt = wintypes.POINT()
        ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
        return pt.x, pt.y
else:
    def get_global_mouse_pos():
        try:
            res = subprocess.run(['xdotool', 'getmouselocation', '--shell'], capture_output=True, text=True)
            geo = {line.split('=')[0]: int(line.split('=')[1]) for line in res.stdout.strip().split('\n') if '=' in line}
            return geo.get('X', 0), geo.get('Y', 0)
        except Exception:
            return pygame.mouse.get_pos()

is_dragging = False
click_offset_x = 0
click_offset_y = 0

clock = pygame.time.Clock()
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            sys.exit()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                is_dragging = True
                wx, wy = sdl_window.position
                gx, gy = get_global_mouse_pos()
                click_offset_x = gx - wx
                click_offset_y = gy - wy
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                is_dragging = False

    if is_dragging:
        if not pygame.mouse.get_pressed()[0]:
            is_dragging = False
        else:
            gx, gy = get_global_mouse_pos()
            new_x = gx - click_offset_x
            new_y = gy - click_offset_y
            
            # Instantly follow cursor
            sdl_window.position = (new_x, new_y)
            
            if TARGET_APP_ID:
                # Use xdotool to query where the app currently stands
                try:
                    res = subprocess.run(['xdotool', 'getwindowgeometry', '--shell', str(TARGET_APP_ID)], capture_output=True, text=True)
                    geo = {line.split('=')[0]: int(line.split('=')[1]) for line in res.stdout.strip().split('\n') if '=' in line}
                    app_x, app_y = geo.get('X'), geo.get('Y')
                    
                    # Math out new width/height based on the position of our grip handle!
                    new_w = (new_x + SIZE) - app_x
                    new_h = (new_y + SIZE) - app_y
                    
                    # Enforce minimum size boundaries
                    new_w = max(150, new_w)
                    new_h = max(100, new_h)
                    
                    subprocess.Popen(['xdotool', 'windowsize', str(TARGET_APP_ID), str(new_w), str(new_h)])
                except Exception:
                    pass

    # Render a retro diagonally-striped resize grip
    frame.fill((200, 200, 200)) # Grey handle background
    pygame.draw.line(frame, (100, 100, 100), (SIZE, 0), (0, SIZE), 2)
    pygame.draw.line(frame, (100, 100, 100), (SIZE, 6), (6, SIZE), 2)
    pygame.draw.line(frame, (100, 100, 100), (SIZE, 12), (12, SIZE), 2)
    
    pygame.display.flip()
    clock.tick(60)
