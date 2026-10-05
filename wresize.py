import os
import sys
import subprocess
import pygame
from pygame._sdl2 import Window

os.environ['DISPLAY'] = ':0'
TARGET_APP_ID = sys.argv[1] if len(sys.argv) > 1 else None

pygame.init()
SIZE = 24  # Bumped to 24px for cleaner high-DPI tracking on mobile touch
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
            
            sdl_window.position = (new_x, new_y)
            
            if TARGET_APP_ID:
                try:
                    res = subprocess.run(['xdotool', 'getwindowgeometry', '--shell', str(TARGET_APP_ID)], capture_output=True, text=True)
                    geo = {line.split('=')[0]: int(line.split('=')[1]) for line in res.stdout.strip().split('\n') if '=' in line}
                    app_x, app_y = geo.get('X'), geo.get('Y')
                    
                    # Math out target sizes
                    new_w = new_x - app_x
                    new_h = new_y - app_y
                    
                    # Enforce strict layout minimums so heavy apps like Firefox don't crash
                    new_w = max(200, new_w)
                    new_h = max(150, new_h)
                    
                    # Explicit geometry resizing configuration flag
                    subprocess.Popen(['xdotool', 'windowsize', str(TARGET_APP_ID), str(new_w), str(new_h)])
                except Exception:
                    pass

    frame.fill((70, 80, 90)) # Modern clean styling
    pygame.draw.rect(frame, (255, 213, 0), (0, 0, SIZE, SIZE), 2)  # High contrast yellow highlight matching Haiku themes
    pygame.display.flip()
    clock.tick(60)
