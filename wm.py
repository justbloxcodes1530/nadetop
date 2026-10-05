import os
import subprocess
import pygame
from pygame._sdl2 import Window

# Map directly to Termux:X11
os.environ['DISPLAY'] = ':0'

# =====================================================================
# GEOMETRY ENGINE FUNCTIONS (Using xdotool)
# =====================================================================
def get_window_geometry(window_id):
    """
    Returns (x, y, width, height) of a window using xdotool.
    Returns None if the window is closed or invalid.
    """
    try:
        # Run xdotool getwindowgeometry --shell to get clean parseable text output
        result = subprocess.run(
            ['xdotool', 'getwindowgeometry', '--shell', str(window_id)],
            capture_output=True, text=True, check=True
        )
        
        # Parse out variables from shell format (e.g., X=100\nY=200\nWIDTH=800\nHEIGHT=600)
        geo = {}
        for line in result.stdout.strip().split('\n'):
            if '=' in line:
                key, val = line.split('=')
                geo[key] = int(val)
                
        return geo.get('X'), geo.get('Y'), geo.get('WIDTH'), geo.get('HEIGHT')
    except (subprocess.CalledProcessError, ValueError):
        return None

# =====================================================================
# PYGAME INITIALIZATION
# =====================================================================
pygame.init()

frame = pygame.display.set_mode((800, 32), pygame.NOFRAME)
pygame.display.set_caption("NADATOP_WINDOW_FRAME")

sdl_window = Window.from_display_module()
sdl_window.position = (100, 100)

text = pygame.font.Font(None, 24)
clock = pygame.time.Clock()

# Window Dragging State Variables
is_dragging = False
drag_offset_x = 0
drag_offset_y = 0

walking = True

# TEST SCAN: Print the position of a window when your script launches
print("[WM-Log] Testing geometry acquisition on start...")
# Substitute with a real window ID from your xdotool search list output
test_id = "your_firefox_or_xeyes_id_here" 
# Example output usage:
# print(f"Window Geometry: {get_window_geometry(test_id)}")

# =====================================================================
# MAIN LOOP
# =====================================================================
while walking:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            walking = False
            
    # --- Smooth Title Bar Drag Logic ---
    mouse_buttons = pygame.mouse.get_pressed()
    # Read mouse coordinates relative to our Pygame frame window canvas
    local_mouse_x, local_mouse_y = pygame.mouse.get_pos() 
    
    # If hovering over the frame bar
    if 0 <= local_mouse_x <= frame.get_width() and 0 <= local_mouse_y <= 32:
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
        
        if mouse_buttons[0]:  # Left Click down
            if not is_dragging:
                is_dragging = True
                # Lock down where the cursor is relative to the absolute top-left window corner
                drag_offset_x = local_mouse_x
                drag_offset_y = local_mouse_y
        else:
            is_dragging = False
    else:
        if not mouse_buttons[0]:
            is_dragging = False
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)

    # Move the Window smoothly using system pointer mapping 
    if is_dragging and mouse_buttons[0]:
        # Get absolute mouse position on desktop screen using Pygame's global screen utility
        abs_mouse_x, abs_mouse_y = pygame.mouse.get_pos()
        # Reposition frame based on target dragging offset anchors
        sdl_window.position = (
            sdl_window.position[0] + (local_mouse_x - drag_offset_x),
            sdl_window.position[1] + (local_mouse_y - drag_offset_y)
        )

    # --- Rendering ---
    frame.fill((0, 127, 255)) # Fill blue canvas background
    
    # Blit text layout frame cleanly
    frame.blit(text.render("NADATOP Window Manager Frame", True, (255, 255, 255)), (12, 8))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
