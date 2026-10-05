import os
import sys
import subprocess
import pygame
from pygame._sdl2 import Window

os.environ['DISPLAY'] = ':0'

# Read target app ID passed from wm.py
TARGET_APP_ID = sys.argv[1] if len(sys.argv) > 1 else None

pygame.init()
SIZE = 20  # Slightly larger box for easier grabbing
frame = pygame.display.set_mode((SIZE, SIZE), pygame.NOFRAME)
pygame.display.set_caption("NADETOP_RESIZE_GRIP")

sdl_window = Window.from_display_module()

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
            
            # 1. Update grip position instantly to track cursor 1:1
            sdl_window.position = (new_x, new_y)
            
            # 2. Resize app window directly based on the outer node coordinates
            if TARGET_APP_ID:
                try:
                    res = subprocess.run(['xdotool', 'getwindowgeometry', '--shell', str(TARGET_APP_ID)], capture_output=True, text=True)
                    geo = {line.split('=')[0]: int(line.split('=')[1]) for line in res.stdout.strip().split('\n') if '=' in line}
                    app_x, app_y = geo.get('X'), geo.get('Y')
                    
                    # Target dimension limits
                    new_w = max(150, new_x - app_x)
                    new_h = max(100, new_y - app_y)
                    
                    subprocess.Popen(['xdotool', 'windowsize', str(TARGET_APP_ID), str(new_w), str(new_h)])
                except Exception:
                    pass

    # Draw a clean, stylized retro outer grip square
    frame.fill((100, 110, 120))  # Slate gray accent box
    pygame.draw.rect(frame, (255, 255, 255), (0, 0, SIZE, SIZE), 2)  # Outer bright accent highlight border
    pygame.display.flip()
    clock.tick(60)
