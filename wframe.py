import os
import sys
import subprocess
import pygame
import time
from pygame._sdl2 import Window

os.environ['DISPLAY'] = ':0'
TARGET_APP_ID = sys.argv[1] if len(sys.argv) > 1 else None

pygame.init()
# Notice the smaller width! This makes it look like a Haiku OS Tab
TAB_WIDTH = 256
TAB_HEIGHT = 32
frame = pygame.display.set_mode((TAB_WIDTH, TAB_HEIGHT), pygame.NOFRAME)
pygame.display.set_caption("NADETOP_WINDOW_FRAME")

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
        
def get_geometry(wid):
    try:
        res = subprocess.run(['xdotool', 'getwindowgeometry', '--shell', str(wid)], capture_output=True, text=True, check=True)
        g = {line.split('=')[0]: int(line.split('=')[1]) for line in res.stdout.strip().split('\n') if '=' in line}
        return g.get('X'), g.get('Y'), g.get('WIDTH'), g.get('HEIGHT')
    except Exception:
        return None

def title(wid):
    try:
        name_res = subprocess.run(['xdotool', 'getwindowname', wid], capture_output=True, text=True)
        return name_res.stdout.strip()
    except Exception:
        return "App"

# Button dimensions & positions on the tab layout
font = pygame.font.Font(None, 20)
# Button layout bounding rects
btn_min = pygame.Rect(170, 6, 20, 20)
btn_max = pygame.Rect(195, 6, 20, 20)
btn_cls = pygame.Rect(220, 6, 20, 20)

is_dragging = False
click_offset_x = 0
click_offset_y = 0
titleupdate = time.time() + 1

currtitle = title(TARGET_APP_ID)

maximized = False
oldx = 0
oldy = 0
oldw = 0
oldh = 0

clock = pygame.time.Clock()
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            sys.exit()
            
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                mx, my = event.pos
                
                # Check button clicks instead of dragging!
                if btn_cls.collidepoint((mx, my)) and TARGET_APP_ID:
                    subprocess.Popen(['xdotool', 'windowkill', str(TARGET_APP_ID)])
                    sys.exit()
                elif btn_min.collidepoint((mx, my)) and TARGET_APP_ID:
                    subprocess.Popen(['xdotool', 'windowminimize', str(TARGET_APP_ID)])
                elif btn_max.collidepoint((mx, my)) and TARGET_APP_ID:
                    # Toggles full screen size window size layout
                    if not maximized:
                        maximized = True
                        oldx, oldy, oldw, oldh = get_geometry(TARGET_APP_ID)
                        subprocess.Popen(['xdotool', 'windowsize', str(TARGET_APP_ID), '100%', '100%'])
                        subprocess.Popen(['xdotool', 'windowmove', str(TARGET_APP_ID), '0', '32'])
                    else:
                        maximized = False
                        subprocess.Popen(['xdotool', 'windowsize', str(TARGET_APP_ID), str(oldw), str(oldh)])
                        subprocess.Popen(['xdotool', 'windowmove', str(TARGET_APP_ID), str(oldx), str(oldy)])
                # If clicking anywhere else on the tab bar, trigger normal drag
                elif 0 <= my <= TAB_HEIGHT:
                    is_dragging = True
                    wx, wy = sdl_window.position
                    gx, gy = get_global_mouse_pos()
                    click_offset_x = gx - wx
                    click_offset_y = gy - wy
                    
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                is_dragging = False

    if is_dragging:
        if maximized:
            maximized = False
            subprocess.Popen(['xdotool', 'windowsize', str(TARGET_APP_ID), str(oldw), str(oldh)])

        if not pygame.mouse.get_pressed()[0]:
            is_dragging = False
        else:
            gx, gy = get_global_mouse_pos()
            new_x = gx - click_offset_x
            new_y = gy - click_offset_y
            sdl_window.position = (new_x, new_y)
            
            if TARGET_APP_ID:
                subprocess.Popen(['xdotool', 'windowmove', str(TARGET_APP_ID), str(new_x), str(new_y + TAB_HEIGHT)])

    frame.fill((0, 127, 255))

    if titleupdate >= time.time():
        currtitle = title(TARGET_APP_ID)
        titleupdate = time.time() + 1
    
    # Label Text
    frame.blit(font.render(currtitle, True, (0, 0, 0)), (10, 10))
    
    # Draw Clear Buttons
    pygame.draw.rect(frame, (180, 50, 50) if btn_cls.collidepoint(pygame.mouse.get_pos()) else (140, 0, 0), btn_cls) # Close (Red)
    pygame.draw.rect(frame, (50, 180, 50) if btn_max.collidepoint(pygame.mouse.get_pos()) else (0, 140, 0), btn_max) # Max (Green)
    pygame.draw.rect(frame, (200, 200, 50) if btn_min.collidepoint(pygame.mouse.get_pos()) else (140, 140, 0), btn_min) # Min (Yellowish-orange)
    
    # Minimalist inner indicators
    frame.blit(font.render("_", True, (255,255,255)), (177, 9))
    frame.blit(font.render("[]", True, (255,255,255)), (201, 9))
    frame.blit(font.render("X", True, (255,255,255)), (227, 8))

    pygame.display.flip()
    clock.tick(120)
