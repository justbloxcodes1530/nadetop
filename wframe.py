import os
import sys
import subprocess
import pygame
from pygame._sdl2 import Window

os.environ['DISPLAY'] = ':0'

# Read the target Application Window ID passed from wm.py
TARGET_APP_ID = sys.argv[1] if len(sys.argv) > 1 else None

pygame.init()
frame = pygame.display.set_mode((800, 32), pygame.NOFRAME)
pygame.display.set_caption("NADATOP_WINDOW_FRAME")

sdl_window = Window.from_display_module()

is_dragging = False
drag_offset_x = 0
drag_offset_y = 0

walking = True
while walking:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            walking = False

    mouse_buttons = pygame.mouse.get_pressed()
    local_mouse_x, local_mouse_y = pygame.mouse.get_pos()
    
    if 0 <= local_mouse_x <= frame.get_width() and 0 <= local_mouse_y <= 32:
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
        if mouse_buttons[0]:
            if not is_dragging:
                is_dragging = True
                drag_offset_x = local_mouse_x
                drag_offset_y = local_mouse_y
        else:
            is_dragging = False
    else:
        if not mouse_buttons[0]:
            is_dragging = False
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)

    if is_dragging and mouse_buttons[0]:
        # Update our frame window canvas coordinate step
        current_x, current_y = sdl_window.position
        new_x = current_x + (local_mouse_x - drag_offset_x)
        new_y = current_y + (local_mouse_y - drag_offset_y)
        sdl_window.position = (new_x, new_y)
        
        # DRAG THE TARGET APP ALONG WITH IT!
        if TARGET_APP_ID:
            # Shift the application position right below our frame box (Y position offset by +32px)
            app_target_y = new_y + 32
            subprocess.run(['xdotool', 'windowmove', str(TARGET_APP_ID), str(new_x), str(app_target_y)])

    frame.fill((0, 127, 255))
    pygame.display.flip()

pygame.quit()
